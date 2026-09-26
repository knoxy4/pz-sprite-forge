"""Fold every extra built sheet into the Badlands furniture mod's single tiledef (2000):
one .tiles file with all tilesets, one .pack with all pages.  Supersedes
_shelving_merge.py.  Always merges from the pristine bookcase-only originals in BAK, so
reruns are idempotent; each extra sheet comes from its own pzforge build output."""
import shutil
import sys
from pathlib import Path

sys.path.insert(0, r"C:\Users\KNX\dev\pz-sprite-forge")
from pzforge.packfile import TexturePack
from pzforge.tiledef import TileDefinitions

FORGE = Path(r"C:\Users\KNX\dev\pz-sprite-forge\dist")
MOD = Path(r"C:\Users\KNX\dev\pz-jarvis-mods\mods\FullBookcases\42\media")
BAK = Path(r"C:\Users\KNX\.claude\tmp\FullBookcases_media_pre_shelving")
EXTRA = [  # (sheet, tileset id, build folder under dist)
    ("badlands_shelving_01", 2, r"_shelving_build\ShelvingBuild\42\media"),
    ("badlands_seating_01", 3, r"_seating_build\SeatingBuild\42\media"),
    ("badlands_rain_01", 4, r"_rain_build\RainBuild\42\media"),
    ("badlands_theater_01", 5, r"_theater_build\TheaterBuild\42\media"),
    ("badlands_medical_01", 6, r"_medical_build\MedicalBuild\42\media"),
    ("badlands_closet_01", 7, r"_closet_build\ClosetBuild\42\media"),
    ("badlands_bbq_01", 8, r"_bbq_build\BbqBuild\42\media"),
    ("badlands_hive_01", 9, r"_hive_build\HiveBuild\42\media"),
    ("badlands_dryrack_01", 10, r"_dryrack_build\DryrackBuild\42\media"),
    ("badlands_corrugated_01", 11, r"_corrugated_build\CorrugatedBuild\42\media"),
    ("badlands_scrapshelf_01", 12, r"_scrapshelf_build\ScrapshelfBuild\42\media"),
    ("badlands_spikepit_01", 13, r"_spikepit_build\SpikepitBuild\42\media"),
    # verbatim copies of vanilla art (build/_yard_vanilla_copy.py) so fences, gates and
    # the cell stop claiming vanilla sprite names -- 0.8.3
    ("badlands_fencing_01", 14, r"_yardfence_build\YardfenceBuild\42\media"),
    ("badlands_gates_01", 15, r"_yardgate_build\YardgateBuild\42\media"),
    ("badlands_cell_01", 16, r"_yardcell_build\YardcellBuild\42\media"),
    # (the greenhouse was 17/18 here for one commit; it is its own mod now,
    #  BadlandsGreenhouse on tiledef 6475 -- build/_greenhouse_mod.py)
]

tilesets = TileDefinitions.read(BAK / "badlands_bookcase_01.tiles")
book_p = TexturePack.read(BAK / "badlands_bookcase_01.pack")
assert [t.name for t in tilesets.tilesets] == ["badlands_bookcase_01"]
pages = list(book_p.pages)
for sheet, tid, rel in EXTRA:
    d = FORGE / rel
    t = TileDefinitions.read(d / f"{sheet}.tiles")
    assert [x.name for x in t.tilesets] == [sheet]
    t.tilesets[0].id = tid
    tilesets.tilesets += t.tilesets
    pages += TexturePack.read(d / "texturepacks" / f"{sheet}.pack").pages
    shutil.copyfile(d / f"{sheet}.png", MOD / f"{sheet}.png")
names = [p.name for p in pages]
assert len(names) == len(set(names)), names
ids = [t.id for t in tilesets.tilesets]
assert len(ids) == len(set(ids)), ids

# Fill-state pieces (> 4 sprites per name) get explicit N/E/S/W offsets, or they can't be
# rotated after a pick-up (mods/furniture-rotation-bug-20260925.md).
sys.path.insert(0, r"C:\Users\KNX\dev\pz-sprite-forge\tools")
import rotation_offsets  # noqa: E402

_edits, _skipped = rotation_offsets.plan(tilesets)
rotation_offsets.apply(tilesets, _edits)
assert not rotation_offsets.verify(tilesets)
print(f"rotation offsets: {len(_edits)} sprites; skipped {_skipped}")

tilesets.write(MOD / "badlands_bookcase_01.tiles")
(MOD / "badlands_bookcase_01.tiles.txt").write_text(tilesets.to_text(), encoding="utf-8", newline="\n")
TexturePack(pages=pages, version=book_p.version, has_header=book_p.has_header).write(
    MOD / "texturepacks" / "badlands_bookcase_01.pack")

rt = TileDefinitions.read(MOD / "badlands_bookcase_01.tiles")
rp = TexturePack.read(MOD / "texturepacks" / "badlands_bookcase_01.pack")
for ts in rt.tilesets:
    filled = [i for i, t in enumerate(ts.tiles) if not t.empty]
    facings = "".join(ts.tiles[i].props.get("Facing", "-") for i in filled)
    print(f"tileset {ts.name} id={ts.id} {ts.cols}x{ts.rows} tiles={len(filled)} facings={facings}")
    step = 4 if "seating" in ts.name else 12
    for i in range(0, len(filled), step):
        p = ts.tiles[i].props
        extra = [k for k in p if k.startswith("chair")]
        print(f"   _{i}: {p.get('CustomName')} cap={p.get('ContainerCapacity')} bed={p.get('BedType')} {extra}")
print("pack pages", [p.name for p in rp.pages], "entries", sum(len(p.entries) for p in rp.pages))
