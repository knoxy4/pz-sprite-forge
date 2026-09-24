"""Paintover: repaint rendered tile cells with FLUX (THOR imagegen), silhouette locked.

The Blender recipe owns geometry; klein owns the paint. Each cell is framed on flat
green and sent to imagegen as --ref with a "repaint this exact object" prompt. The
result is mapped back into the cell box and composited under the ORIGINAL alpha, so
trims, facings and overlays still line up pixel for pixel -- the retouch rule
(alpha is invariant), automated.

    uv run --python 3.12 --with pillow python tools/paintover.py build/<name>_cells \
        --subject "a stainless steel vertical steam boiler" --groups 0
    # then:  python -m pzforge.cli build build/<name>_cells_paint --no-style ...

Long jobs: the device shell times out at ~60 s, so launch detached
(Start-Process) and poll <out>/paintover.log -- one JSON line per step.
--recompose skips generation and rebuilds the cells from the logged images, for
iterating on the compositing knobs without touching the GPU.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

from PIL import Image, ImageChops, ImageFilter

IMAGEGEN_PY = r"X:\imagegen\.venv\Scripts\python.exe"
IMAGEGEN_CLI = r"X:\imagegen\src\imagegen\cli.py"
GREEN = (0, 177, 64)
REF_SIZE, REF_H, PAD = 1024, 900, 12

STYLE = (
    "Repaint exactly the object in the reference image as a finished isometric "
    "pixel-art video game sprite in the style of Project Zomboid. Keep the exact same "
    "silhouette, pose, camera angle, proportions and every part in the same place. "
    "Crisp hand-painted pixel art, thin dark outline, clean bright highlights and "
    "firm shading, rich saturated colours, top-left light, flat solid bright green "
    "background, no shadow, no text."
)


def log(out: Path, **row) -> None:
    row["at"] = time.strftime("%H:%M:%S")
    with (out / "paintover.log").open("a", encoding="utf-8") as f:
        f.write(json.dumps(row) + "\n")
    print(json.dumps(row), flush=True)


def gpu_busy() -> str | None:
    """Someone else owns the card (thor-imagegen rule): None if free, else why."""
    status = subprocess.run([IMAGEGEN_PY, IMAGEGEN_CLI, "--status"],
                            capture_output=True, text=True)
    try:
        if json.loads(status.stdout).get("loaded"):
            return None
    except json.JSONDecodeError:
        pass
    q = subprocess.run(["nvidia-smi", "--query-gpu=utilization.gpu,memory.used",
                        "--format=csv,noheader,nounits"], capture_output=True, text=True)
    util, mem = (int(v) for v in q.stdout.strip().split(","))
    if util > 30 or mem > 2500:
        return f"gpu util {util}% mem {mem} MiB"
    return None


def clear_port() -> None:
    """A daemon the watchdog dropped can still hold 8391; kill only that listener."""
    ps = ("Get-NetTCPConnection -LocalPort 8391 -State Listen -EA 0 | "
          "% { Stop-Process -Id $_.OwningProcess -Force }")
    subprocess.run(["powershell", "-NoProfile", "-Command", ps], capture_output=True)
    time.sleep(6)


def frame(cell: Image.Image) -> tuple[Image.Image, tuple[int, int, int, int]]:
    """Cell on green, scaled to REF_H, centred. Returns the ref and the cell box it maps to."""
    x0, y0, x1, y1 = cell.getbbox()
    box = (x0 - PAD, y0 - PAD, x1 + PAD, y1 + PAD)
    bg = Image.new("RGBA", cell.size, GREEN + (255,))
    bg.alpha_composite(cell)
    crop = bg.crop(box).convert("RGB")
    s = REF_H / crop.height
    crop = crop.resize((round(crop.width * s), REF_H), Image.LANCZOS)
    ref = Image.new("RGB", (REF_SIZE, REF_SIZE), GREEN)
    ref.paste(crop, ((REF_SIZE - crop.width) // 2, (REF_SIZE - REF_H) // 2))
    return ref, box


def unframe(painted: Image.Image, box, cell_size) -> Image.Image:
    """Inverse of frame(): the painted pixels back in cell space (RGB only)."""
    bw, bh = box[2] - box[0], box[3] - box[1]
    w = round(bw * REF_H / bh)
    left, top = (REF_SIZE - w) // 2, (REF_SIZE - REF_H) // 2
    region = painted.convert("RGB").crop((left, top, left + w, top + REF_H))
    region = region.resize((bw, bh), Image.LANCZOS)
    out = Image.new("RGB", cell_size, GREEN)
    out.paste(region, (box[0], box[1]))
    return out


def is_green(px) -> bool:
    r, g, b = px[:3]
    return g > r + 45 and g > b + 35


def composite(cell: Image.Image, paint: Image.Image, outline: float) -> Image.Image:
    """Painted RGB under the original alpha; background leaks fall back to the render."""
    out = cell.copy()
    src, pp, op = cell.load(), paint.load(), out.load()
    w, h = cell.size
    for y in range(h):
        for x in range(w):
            a = src[x, y][3]
            if a == 0:
                continue
            p = pp[x, y]
            op[x, y] = (src[x, y][:3] if is_green(p) else p) + (a,)
    if outline > 0:
        alpha = cell.split()[3].point(lambda v: 255 if v > 100 else 0)
        edge = ImageChops.subtract(alpha, alpha.filter(ImageFilter.MinFilter(3)))
        ep = edge.load()
        for y in range(h):
            for x in range(w):
                if ep[x, y]:
                    r, g, b, a = op[x, y]
                    op[x, y] = (int(r * outline), int(g * outline), int(b * outline), a)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("cells", type=Path)
    ap.add_argument("--out", type=Path)
    ap.add_argument("--subject", required=True, help="one line: what the object is")
    ap.add_argument("--groups", default="0", help="manifest groups to paint, comma list; "
                    "the rest (overlays) are copied, outlined only")
    ap.add_argument("--seed", type=int, default=6476)
    ap.add_argument("--steps", type=int, default=0, help="0 = style preset")
    ap.add_argument("--outline", type=float, default=0.45,
                    help="inner silhouette edge darkened to this fraction; 0 disables")
    ap.add_argument("--back-facings", default="",
                    help="facings that show the object's plain back, e.g. N,W; they get "
                    "--back-subject so klein does not paint the front onto the back")
    ap.add_argument("--back-subject", default="",
                    help="one line for the back view: what is (and is NOT) on it")
    ap.add_argument("--redo", default="", help="facings to regenerate even if logged, e.g. N,W")
    ap.add_argument("--recompose", action="store_true",
                    help="no generation: rebuild cells from images already logged")
    a = ap.parse_args()

    out = a.out or a.cells.with_name(a.cells.name + "_paint")
    out.mkdir(parents=True, exist_ok=True)
    manifest = json.loads((a.cells / "manifest.json").read_text(encoding="utf-8"))
    groups = {int(g) for g in a.groups.split(",") if g.strip()}
    targets = [c for c in manifest["cells"] if c.get("group", 0) in groups]

    done: dict[str, str] = {}
    if (out / "paintover.log").exists():
        for line in (out / "paintover.log").read_text(encoding="utf-8").splitlines():
            row = json.loads(line)
            if row.get("step") == "painted":
                done[row["cell"]] = row["image"]
    redo = {f.strip() for f in a.redo.split(",") if f.strip()}
    for c in targets:
        if c["facing"] in redo:
            done.pop(c["file"], None)
    todo = [c for c in targets if c["file"] not in done]
    if todo and not a.recompose:
        busy = gpu_busy()
        if busy:
            log(out, step="abort", why=f"GPU busy ({busy}); queue and retry later")
            return 2
    else:
        todo = []

    backs = {f.strip() for f in a.back_facings.split(",") if f.strip()}
    for c in todo:
        subject = a.back_subject if (c["facing"] in backs and a.back_subject) else a.subject
        prompt = f"{STYLE} The object: {subject}."
        cell = Image.open(a.cells / c["file"]).convert("RGBA")
        ref, _ = frame(cell)
        ref_path = out / f"ref_{c['file']}"
        ref.save(ref_path)
        clear_port()
        cmd = [IMAGEGEN_PY, IMAGEGEN_CLI, "--json", "--style", "raw", "--seed", str(a.seed),
               "--ref", str(ref_path), prompt]
        if a.steps:
            cmd[3:3] = ["--steps", str(a.steps)]
        r = subprocess.run(cmd, capture_output=True, text=True)
        try:
            res = json.loads(r.stdout.strip().splitlines()[-1])
        except (json.JSONDecodeError, IndexError):
            res = {"ok": False, "error": (r.stderr or r.stdout)[-400:]}
        if not res.get("ok"):
            log(out, step="failed", cell=c["file"], error=res.get("error"))
            return 1
        done[c["file"]] = res["path"]
        log(out, step="painted", cell=c["file"], image=res["path"], s=res.get("elapsed_s"))

    for c in manifest["cells"]:
        for key in ("normal", "element", "light"):
            if c.get(key) and (a.cells / c[key]).exists():
                shutil.copy2(a.cells / c[key], out / c[key])
        cell = Image.open(a.cells / c["file"]).convert("RGBA")
        if c["file"] in done:
            _, box = frame(cell)
            paint = unframe(Image.open(done[c["file"]]), box, cell.size)
            final = composite(cell, paint, a.outline)
        else:
            final = composite(cell, cell.convert("RGB"), a.outline)
        final.save(out / c["file"])
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    log(out, step="composed", cells=len(manifest["cells"]), painted=len(done))
    return 0


if __name__ == "__main__":
    sys.exit(main())
