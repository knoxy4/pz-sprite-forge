"""Give moveable sprites explicit Noffset/Eoffset/Soffset/Woffset so pick-up/place and Rotate work.

The engine only generates those props at tiledef load for a GroupName+CustomName group of at
most 4 sprites (one per facing). Pieces with fill states or material variants carry 8-40
sprites under one name, get no faces, and can't be rotated once picked up
(mods/furniture-rotation-bug-20260925.md). ISMoveableSpriteProps reads the props straight
from the sprite (spriteID + offset, same sheet), so writing them fixes rotation without
renaming anything.

Pairing rule: within one tileset and one (GroupName, CustomName), bucket sprites by Facing;
the k-th sprite of each facing (by sheet index) is the same state. Groups the engine already
handles (a GroupName and <= 4 members), multi-tile grid pieces, uneven buckets and offsets
outside -96..96 are left alone and reported.

    python tools/rotation_offsets.py <file.tiles> [--write] [--txt <file.tiles.txt>]
"""
from __future__ import annotations

import argparse
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pzforge.tiledef import TileDefinitions  # noqa: E402

FACINGS = ("N", "E", "S", "W")
LIMIT = 96


def plan(td: TileDefinitions) -> tuple[list[tuple[str, int, dict[str, str]]], list[str]]:
    """Return (edits, skipped): edits = (tileset, index, {prop: value})."""
    edits, skipped = [], []
    for ts in td.tilesets:
        groups: dict[tuple[str, str], dict[str, list[int]]] = defaultdict(lambda: defaultdict(list))
        for i, t in enumerate(ts.tiles):
            p = t.props
            if not p or "CustomName" not in p or p.get("Facing") not in FACINGS or "SpriteGridPos" in p:
                continue
            groups[(p.get("GroupName", ""), p["CustomName"])][p["Facing"]].append(i)
        for (grp, name), byf in sorted(groups.items()):
            total = sum(len(v) for v in byf.values())
            label = f"{ts.name}: {grp} {name}".strip()
            if grp and total <= 4:
                continue
            if len(byf) < 2:
                continue
            sizes = {len(v) for v in byf.values()}
            if len(sizes) != 1:
                skipped.append(f"{label}: uneven facings {dict((f, len(v)) for f, v in byf.items())}")
                continue
            n = sizes.pop()
            ok = True
            pending = []
            for k in range(n):
                for f, idxs in byf.items():
                    me = idxs[k]
                    props = {}
                    for g, gidxs in byf.items():
                        d = gidxs[k] - me
                        if abs(d) > LIMIT:
                            ok = False
                        props[f"{g}offset"] = str(d)
                    pending.append((ts.name, me, props))
            if not ok:
                skipped.append(f"{label}: an offset exceeds +-{LIMIT}")
                continue
            edits += pending
    return edits, skipped


def apply(td: TileDefinitions, edits) -> None:
    by = {ts.name: ts for ts in td.tilesets}
    for name, idx, props in edits:
        by[name].tiles[idx].props.update(props)


def verify(td: TileDefinitions) -> list[str]:
    """Every offset lands on a sprite of the same name and facing letter, and points back."""
    bad = []
    for ts in td.tilesets:
        for i, t in enumerate(ts.tiles):
            for f in FACINGS:
                v = t.props.get(f"{f}offset")
                if v is None:
                    continue
                j = i + int(v)
                if not (0 <= j < len(ts.tiles)):
                    bad.append(f"{ts.name}_{i}: {f}offset {v} off the sheet")
                    continue
                o = ts.tiles[j].props
                if o.get("CustomName") != t.props.get("CustomName") or o.get("Facing") != f:
                    bad.append(f"{ts.name}_{i}: {f}offset {v} -> {ts.name}_{j} ({o.get('CustomName')}, {o.get('Facing')})")
                back = o.get(f"{t.props.get('Facing')}offset")
                if back is not None and int(back) != -int(v):
                    bad.append(f"{ts.name}_{i}: {f}offset not reciprocal")
    return bad


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("tiles")
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--txt", default="")
    a = ap.parse_args()
    td = TileDefinitions.read(a.tiles)
    edits, skipped = plan(td)
    names = sorted({(e[0], td.tilesets[[t.name for t in td.tilesets].index(e[0])].tiles[e[1]].props.get("CustomName")) for e in edits})
    print(f"{len(edits)} sprites get offsets across {len(names)} pieces")
    for s, n in names:
        print(f"  {s}: {n}")
    for s in skipped:
        print(f"  SKIP {s}")
    apply(td, edits)
    bad = verify(td)
    for b in bad:
        print(f"  BAD {b}")
    if bad:
        return 1
    if a.write:
        td.write(a.tiles)
        if a.txt:
            Path(a.txt).write_text(td.to_text(), encoding="utf-8", newline="\n")
        print("written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
