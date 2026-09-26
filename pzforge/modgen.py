"""Assemble a loadable Project Zomboid mod around a generated pack and tiledef.

A tile mod is only three things beyond the art: the ``.pack``, the ``.tiles``, and a
``mod.info`` that points at both::

    name=My Tiles
    id=MyTiles
    tiledef=mytiles 2282
    pack=mytiles

The number after ``tiledef`` is a global id. Two enabled mods sharing one will fight
over the same tile range and one of them loses its sprites, so :func:`free_tiledef_id`
scans what is already installed rather than picking a number and hoping.
"""

from __future__ import annotations

import os
import re
import string
from dataclasses import dataclass, field
from pathlib import Path

#: Steam puts its Workshop cache under whichever library drive the user picked, so a
#: hardcoded C: list silently finds nothing and every "free id" answer is a guess.
#: Probe every fixed drive instead, and let PZ_MOD_PATHS (os.pathsep-separated)
#: override the lot -- the same escape hatch PZ_MEDIA gives compare.py/preview.py.
WORKSHOP_SUFFIXES = (
    Path("SteamLibrary/steamapps/workshop/content/108600"),
    Path("steamapps/workshop/content/108600"),
    Path("Program Files (x86)/Steam/steamapps/workshop/content/108600"),
    Path("PZServer/steamapps/workshop/content/108600"),
)


def mod_search_paths() -> list[Path]:
    """Every folder that may hold installed mods, on any Steam library drive."""
    env = os.environ.get("PZ_MOD_PATHS", "")
    if env.strip():
        return [Path(p) for p in env.split(os.pathsep) if p.strip()]
    found = [Path.home() / "Zomboid" / "mods"]
    for letter in string.ascii_uppercase:
        drive = Path(letter + ":/")
        try:
            if not drive.exists():
                continue
        except OSError:
            continue
        for suffix in WORKSHOP_SUFFIXES:
            candidate = drive / suffix
            try:
                if candidate.is_dir():
                    found.append(candidate)
            except OSError:
                continue
    seen, out = set(), []
    for path in found:
        key = str(path).lower()
        if key not in seen:
            seen.add(key)
            out.append(path)
    return out


#: Back-compat alias, resolved at import. Call mod_search_paths() to re-probe.
MOD_SEARCH_PATHS = mod_search_paths()

#: Ids below this are vanilla/reserved territory.
TILEDEF_ID_FLOOR = 2000

#: The engine's hard range for a tiledef file number. Outside it the game refuses
#: the whole mod: "tiledef=... file number must be from 100 to 8189" from
#: ChooseGameInfo.readModInfoAux, then "MOD NOT LOADED". Measured on B42.20 by a
#: pzkit headless boot on 2026-09-20 -- the census lists ids up to 15000, so those
#: are B41-era or simply broken on B42. Nothing above this can ship.
TILEDEF_ID_MIN = 100
TILEDEF_ID_MAX = 8189

#: The low range (1300-3600) is dense with map and build-menu packs, so Badlands
#: claims a block of its own instead of picking a "free-looking" low number.
#: 6470-6499 sits in the widest hole in KNOWN_WORKSHOP_IDS below the engine cap
#: (6264-6766: nearest neighbours 6263 Battlefield Louisville and 6767 Greenleaf),
#: well clear of the cap itself, which is where anyone who has read the error
#: message lands. Was 8470-8499 until the boot above proved 8470 unloadable.
#: Assignments live in the project's tiledef registry doc, not in code.
BADLANDS_BLOCK = (6470, 6499)

#: Block ids already spoken for but not visible to used_tiledef_ids(), which only
#: sees installed mods. Without this the forge hands the first unpublished
#: assignment straight back out to the next new sheet. Keep in step with the
#: tiledef registry doc; the registry is authoritative.
BADLANDS_RESERVED: dict[int, str] = {
    6470: "KNXDrugs (knx_cooklab_01) -- cook lab, KNXDrugs 0.9.0",
    6471: "FullBookcases (badlands_bookcase_01) -- moves here at wipe",
    6472: "BadlandsPower (badlands_power_01) -- moves here at wipe",
    6473: "BadlandsPosters (badlands_posters_01) -- boot-tested, not yet published",
    6474: "BadlandsPowerControllers (badlands_powerctl_01) -- built 2026-09-24 (0.1.0), unpublished",
    6476: "ikag_garage (ikag_garage_01) -- Tokin's garage mod, reserved 2026-09-24, unpublished",
    6477: "BadlandsFence (badlands_fence_01) -- electric fence M1, reserved 2026-09-25, unpublished",
    6478: "BadlandsPowerSteam (badlands_steam_01) -- moved off 6476 2026-09-26 (0.1.2), public",
}

#: Community census of tiledef ids above 1300, keyed id -> mod. Used to check a
#: candidate id against the wider Workshop rather than only what happens to be
#: installed on this box -- used_tiledef_ids() can only see local mods, and "free
#: here" is not "free". Operator-supplied, not independently verified; treat a hit
#: as a reason to pick another number, not as proof of a live collision. Entries
#: above TILEDEF_ID_MAX cannot load on B42.20 and are kept only for completeness --
#: they are NOT evidence that high ids work.
def _census(entries: dict[tuple[int, ...], str]) -> dict[int, str]:
    return {i: mod for ids, mod in entries.items() for i in ids}


KNOWN_WORKSHOP_IDS: dict[int, str] = _census({
    (1300,): "Veracious Network Garage", (1313,): "playershop",
    (1337, 1338): "Project Arcade / Neon City",
    (1421,): "Renewable Food Resources", (1590,): "Project New Vegas",
    (1861,): "Yule's Farm Tiles", (1875,): "Improved Build Menu",
    (1877,): "Hallowtiles", (1944,): "Improved Build Menu (milcratedefs)",
    (1956,): "Drazion's Tilepack", (1985,): "sfbuild", (1991,): "Erika's Tiles",
    (2002,): "MidRiver", (2101,): "BravensRappelKit", (2112,): "Excavation",
    (2347,): "FunctionalAppliances2", (2351,): "MateuszKimTiles",
    (2592,): "Grapeseed", (2605,): "ShopStuff", (2606,): "gunrack",
    (2607,): "FloralDecorations", (2609,): "DragonGravestone",
    (2610,): "GatedBase", (2611,): "ManncoTiles", (2619,): "AP_DesktopTiles",
    (2629,): "Shops_KWRR", (2630,): "kwrr_fixes_tiles", (2631,): "PineHosting",
    (2639,): "XmasDecor", (2649,): "Electro", (2697,): "Fish Farm",
    (2698,): "TOMorePaintSigns", (2699,): "DriedFishMod", (2700,): "PumpPlumb",
    (2701,): "Mortar", (2702,): "AnimeStuff", (2704,): "RestrictedArea",
    (2705,): "Uta Mod", (2707,): "MoreTraps", (2708,): "BrowningM2",
    (2709,): "PostApocFences", (2710,): "Corkboard", (2711,): "PokerTiles",
    (2799,): "HashimaIsland", (2800,): "FortKnox / EerieCountry",
    (2900,): "TWD ProjectPack", (3002,): "0pop_climbing_roof_01L",
    (3333,): "simonMDsTiles", (3371,): "RoadBlock Fix",
    (3373, 3374): "Tile Fixes", (3401,): "ImprovisedFlooring",
    (3452,): "AutoGate", (3483,): "DoubleDeckerBusInterior",
    (3573,): "Crafting Enhanced Core", (4002,): "0pop_climbing_roof_01CH",
    (4200,): "PZCFHobbies2", (4242, 4243): "PertsPartyTiles",
    (4244,): "Basements", (4637,): "CookieTileDef",
    (4657, 4658, 4659, 4660, 4662, 4663): "Gargisnar's Goonie Base",
    (4661,): "Gargisnar's Goonie Base / Bourstrange (known upstream clash)",
    (4827,): "Blackwood", (4834,): "SafeCrackerMod", (5001,): "ResearchBase",
    (5002,): "Camp Hill", (5481,): "Pitstop legacy", (5484,): "NewEkron",
    (5520,): "EN_Newburbs", (5535,): "EN_Flags", (5669,): "Muldraugh Cottages",
    (5947,): "ProjectRPContraband", (5970, 5971): "Facility 7",
    (6002,): "Lakewood Cabin", (6263,): "Battlefield Louisville (secretz)",
    (6767,): "Greenleaf", (6817,): "Breakable Road Barricades",
    (6941,): "SaveOurStationKnoxCountry", (6969,): "AoqiaCarwannaExtended",
    (6985,): "DylansTiles", (6987,): "GreggiesGarageDoors",
    (7001,): "DiederikTiles", (7077,): "BuryLoot",
    (7175,): "bigzombiemonkeys_tiles", (7231,): "Blowtorch Gates",
    (7503,): "MockinBird (ghostbuster)", (7575,): "Little Crutown",
    (7636,): "PissWater Lake", (7777,): "Satispunk", (7811,): "Neat_Building",
    (7853,): "Ammo Shelves", (7871,): "CamoNetting", (7919,): "Biogas Reactor",
    (7920,): "BandSaw", (7921,): "Drill Press", (7979,): "GreensCustomTiles",
    (7989,): "Petrovick (SundayDrivers)", (8008,): "SinkHole",
    (8028,): "Gnome Gnoises", (8100,): "Basement Bunker",
    (8103,): "Simple Blacksmithing", (8676,): "LightSwitch Overhaul",
    (8737,): "Zen Faction Graffiti", (8912,): "AzaMountainTiles",
    (9090,): "Petrovick (BigBearLake)", (9476, 9477, 9478): "LibertyCity",
    (9830,): "DTilesPack_Elysium", (13244,): "Wildberries",
    (14000,): "Ratchat's Outdoor Tiles", (14001,): "Simple Wall Building",
    (15000,): "Farming Expansion B42",
})

#: Sheets that only ever exist as per-piece scratch builds: _furniture_merge.py
#: folds them into badlands_bookcase_01 and their own mod.info never ships. Their
#: printed tiledef id is noise, and counting it produces a false collision on
#: whatever block slot the forge last handed out. Read live from the merge script
#: when it is present; this list is the fallback.
INTERMEDIATE_SHEETS = frozenset({
    "badlands_shelving_01", "badlands_seating_01", "badlands_rain_01",
    "badlands_theater_01", "badlands_medical_01", "badlands_closet_01",
})

_TILEDEF_LINE = re.compile(r"^\s*tiledef\s*=\s*(\S+)\s+(\d+)", re.MULTILINE)
_ID_LINE = re.compile(r"^\s*id\s*=\s*(\S+)", re.MULTILINE)
_INCOMPATIBLE_LINE = re.compile(r"^\s*incompatible\s*=\s*(.+)$", re.MULTILINE)
_BUILD_DIR = re.compile(r"^(4[12](\.\d+)?|common)$", re.IGNORECASE)
_EXTRA_SHEET = re.compile(r"""\(\s*["']([A-Za-z0-9_]+)["']\s*,\s*\d+\s*,""")


def _mod_identity(info: Path, text: str) -> str:
    """Which mod a mod.info belongs to.

    B42 mods carry the same mod.info at the root and inside every build folder
    (42/, 42.13/, common/), so the containing directory name is not an identity.
    The declared ``id=`` is; fall back to the first non-build ancestor.
    """
    declared = _ID_LINE.search(text)
    if declared:
        return declared.group(1)
    parent = info.parent
    while parent.parent != parent and _BUILD_DIR.match(parent.name):
        parent = parent.parent
    return parent.name


def intermediate_sheets(merge_script: Path | None = None) -> frozenset[str]:
    """Sheet names that only exist as pre-merge scratch builds.

    Parsed out of ``_furniture_merge.py``'s EXTRA list when it can be found, so the
    two never drift; :data:`INTERMEDIATE_SHEETS` is the fallback when it cannot.
    """
    candidates = [merge_script] if merge_script else [
        Path(__file__).resolve().parent.parent / "build" / "_furniture_merge.py",
        Path.cwd() / "build" / "_furniture_merge.py",
    ]
    for path in candidates:
        try:
            if path and path.is_file():
                found = set(_EXTRA_SHEET.findall(path.read_text(
                    encoding="utf-8", errors="replace")))
                if found:
                    return frozenset(found | set(INTERMEDIATE_SHEETS))
        except OSError:
            continue
    return INTERMEDIATE_SHEETS


def mod_incompatibilities(search_paths: list[Path] | None = None) -> dict[str, set[str]]:
    """Map each mod id to the mod ids it declares ``incompatible=``.

    Two mods on one tiledef id that name each other here are mutually exclusive
    variants of the same mod -- the game will never load both -- so they are not a
    collision. Neat_Building and Neat_Building_Buildables_SESCompat are the live
    example: both declare NeatBuilding_Tiles 7811, and each lists the other.
    """
    out: dict[str, set[str]] = {}
    for info, text in _iter_mod_infos(search_paths):
        owner = _mod_identity(info, text)
        names = out.setdefault(owner, set())
        for line in _INCOMPATIBLE_LINE.findall(text):
            for raw in line.split(","):
                cleaned = raw.strip().lstrip("\\/").strip()
                if cleaned:
                    names.add(cleaned)
    return out


def _iter_mod_infos(search_paths: list[Path] | None = None):
    for root in (search_paths if search_paths is not None else mod_search_paths()):
        if not root.exists():
            continue
        for info in root.rglob("mod.info"):
            try:
                yield info, info.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue


def used_tiledef_ids(search_paths: list[Path] | None = None,
                     skip_intermediates: bool = True) -> dict[int, list[str]]:
    """Map every tiledef id already claimed by an installed mod to the mods using it.

    Scratch builds whose sheet is folded into another mod by the furniture merge are
    skipped by default: their mod.info never ships, so the id they print is noise.
    """
    skip = intermediate_sheets() if skip_intermediates else frozenset()
    found: dict[int, list[str]] = {}
    for info, text in _iter_mod_infos(search_paths):
        owner = _mod_identity(info, text)
        for name, raw in _TILEDEF_LINE.findall(text):
            if name in skip:
                continue
            found.setdefault(int(raw), []).append(f"{owner}:{name}")
    return found


def census_holder(tiledef_id: int) -> str | None:
    """The Workshop mod known to claim ``tiledef_id``, if any. See KNOWN_WORKSHOP_IDS."""
    return KNOWN_WORKSHOP_IDS.get(tiledef_id)


def _squash(text: str) -> str:
    return re.sub(r"[^a-z0-9]", "", text.lower())


def census_conflicts(taken: dict[int, list[str]]) -> dict[int, tuple[list[str], str]]:
    """Locally claimed ids that the census says belong to a DIFFERENT mod.

    An installed mod that is itself the census entry (simonMDsTiles on 3333) is the
    census confirming it, not a conflict, so holders whose mod id or sheet name
    matches the census name are dropped.
    """
    out: dict[int, tuple[list[str], str]] = {}
    for tid, holders in taken.items():
        known = KNOWN_WORKSHOP_IDS.get(tid)
        if not known:
            continue
        name = _squash(known)
        strangers = sorted({h for h in holders
                            if not any(part and (part in name or name in part)
                                       for part in map(_squash, h.split(":", 1)))})
        if strangers:
            out[tid] = (strangers, known)
    return out


def free_tiledef_id(search_paths: list[Path] | None = None,
                    start: int | None = None,
                    block: tuple[int, int] | None = None) -> int:
    """Lowest unclaimed id inside ``block`` (default: the Badlands block).

    An explicit ``start`` with ``block=None`` walks upward without a ceiling, which
    is the old behaviour, kept for callers that still want it.
    """
    if block is None and start is None:
        block = BADLANDS_BLOCK
    low = start if start is not None else block[0]
    taken = used_tiledef_ids(search_paths)
    ceiling = block[1] if block else None
    candidate = low
    # Skip anything claimed locally AND anything the census knows about: an id can
    # be free on this box and still belong to a mod a subscriber has installed.
    while (candidate in taken or candidate in KNOWN_WORKSHOP_IDS
           or candidate in BADLANDS_RESERVED):
        candidate += 1
        if ceiling is not None and candidate > ceiling:
            raise ValueError(
                "tiledef block %d-%d is full; widen modgen.BADLANDS_BLOCK and record "
                "the change in the tiledef registry" % (block[0], block[1]))
    if not TILEDEF_ID_MIN <= candidate <= TILEDEF_ID_MAX:
        raise ValueError(
            "tiledef id %d is outside the engine's %d-%d range; the game would refuse "
            "the whole mod" % (candidate, TILEDEF_ID_MIN, TILEDEF_ID_MAX))
    return candidate


def _mutually_exclusive(holders: list[str],
                        incompat: dict[str, set[str]]) -> bool:
    """True when no two holders of an id can ever be enabled together.

    Checked pairwise and treated as symmetric: one side declaring the other under
    ``incompatible=`` is enough, since the game refuses the pair either way.
    """
    owners = sorted({h.split(":", 1)[0] for h in holders})
    if len(owners) < 2:
        return True
    for i, a in enumerate(owners):
        for b in owners[i + 1:]:
            if b not in incompat.get(a, ()) and a not in incompat.get(b, ()):
                return False
    return True


def duplicate_tiledef_ids(search_paths: list[Path] | None = None) -> dict[int, list[str]]:
    """Ids where two mods that CAN load together fight over the same number.

    That is the sprite-loss condition: one of them silently wins the range. Two
    cases are excused. Same sheet name from several mods is one mod shipped as
    alternate variants. Mods that declare each other ``incompatible=`` can never be
    enabled at once -- the Neat_Building / SESCompat pair does both. Either way it
    is reported by :func:`shared_tiledef_ids` instead.
    """
    incompat = mod_incompatibilities(search_paths)
    out: dict[int, list[str]] = {}
    for tid, holders in used_tiledef_ids(search_paths).items():
        distinct = sorted(set(holders))
        if len({h.split(":", 1)[1] for h in distinct}) <= 1:
            continue
        if _mutually_exclusive(distinct, incompat):
            continue
        out[tid] = distinct
    return out


def shared_tiledef_ids(search_paths: list[Path] | None = None) -> dict[int, list[str]]:
    """Ids held by several mods that are not a fault.

    Either they declare the same sheet, or they declare each other
    ``incompatible=`` and so never load together.
    """
    incompat = mod_incompatibilities(search_paths)
    out: dict[int, list[str]] = {}
    for tid, holders in used_tiledef_ids(search_paths).items():
        distinct = sorted(set(holders))
        if len(distinct) < 2:
            continue
        if (len({h.split(":", 1)[1] for h in distinct}) == 1
                or _mutually_exclusive(distinct, incompat)):
            out[tid] = distinct
    return out


@dataclass
class ModInfo:
    id: str
    name: str
    description: str = ""
    author: str = ""
    poster: str = "poster.png"
    tiledef: str = ""
    tiledef_id: int = BADLANDS_BLOCK[0]
    pack: str = ""
    require: list[str] = field(default_factory=list)

    def render(self) -> str:
        lines = [f"name={self.name}", f"id={self.id}"]
        if self.description:
            lines.append(f"description={self.description}")
        if self.author:
            lines.append(f"author={self.author}")
        if self.poster:
            lines.append(f"poster={self.poster}")
        if self.tiledef:
            lines.append(f"tiledef={self.tiledef} {self.tiledef_id}")
        if self.pack:
            lines.append(f"pack={self.pack}")
        for req in self.require:
            lines.append(f"require={req}")
        return "\n".join(lines) + "\n"


@dataclass
class ModLayout:
    """Resolved paths inside a mod folder, for B41-style and B42-style layouts."""

    root: Path
    media: Path
    texturepacks: Path

    @classmethod
    def create(cls, out_dir: Path, mod_id: str, build: str | None = "42") -> "ModLayout":
        # B42 loads a versioned subfolder; B41 reads the mod root directly.
        root = out_dir / mod_id / build if build else out_dir / mod_id
        media = root / "media"
        texturepacks = media / "texturepacks"
        texturepacks.mkdir(parents=True, exist_ok=True)
        return cls(root, media, texturepacks)
