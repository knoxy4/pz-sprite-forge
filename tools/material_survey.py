"""Survey Material= values across the shipped B42 tiledefs, and show what vanilla puts on
lab glassware / jugs / burners, so we pick a real value instead of a preset default."""
import collections, glob, os, re, sys

MEDIA = os.environ.get("PZ_MEDIA") or r"X:\SteamLibrary\steamapps\common\ProjectZomboid\media"
TD = os.path.join(MEDIA, "tiledefinitions")


def txts():
    for p in glob.glob(os.path.join(TD, "*.tiles.txt")):
        yield p
    for p in glob.glob(os.path.join(MEDIA, "**", "*.tiles.txt"), recursive=True):
        yield p


def tiles(path):
    """yield (tileset_file, index, {prop: val}) per tile block, in sheet order."""
    t = open(path, encoding="utf-8", errors="replace").read()
    for ts in re.finditer(r'tileset\s*\{(.*?)\n\}', t, re.S):
        body = ts.group(1)
        fm = re.search(r'file\s*=\s*(\S+)', body)
        fname = fm.group(1) if fm else "?"
        for i, tb in enumerate(re.finditer(r'tile\s*\{(.*?)\}', body, re.S)):
            props = {}
            for line in tb.group(1).splitlines():
                m = re.match(r'\s*([A-Za-z0-9_]+)\s*=\s*(.*?)\s*$', line)
                if m:
                    props[m.group(1)] = m.group(2)
            yield fname, i, props


def main():
    mats = collections.Counter()
    by_mat_files = collections.defaultdict(collections.Counter)
    hits = []
    WANT = re.compile(r'glass|beaker|flask|jug|burner|bunsen|chem|lab|bottle|stove|cooker|hotplate',
                      re.I)
    seen = set()
    for p in txts():
        if p in seen:
            continue
        seen.add(p)
        for fname, i, props in tiles(p):
            m = props.get("Material")
            if m is not None:
                mats[m] += 1
                by_mat_files[m][fname] += 1
            if WANT.search(fname) or WANT.search(props.get("CustomName", "")) \
               or WANT.search(props.get("GroupName", "")):
                hits.append((fname, i, props))

    print("=" * 76)
    print("Material= values across all shipped tiledefs")
    print("=" * 76)
    for m, n in mats.most_common():
        top = ", ".join(f for f, _ in by_mat_files[m].most_common(3))
        print("  %-16s %6d   e.g. %s" % (m, n, top))

    print()
    print("=" * 76)
    print("lab / glass / jug / burner tiles and what vanilla puts on them")
    print("=" * 76)
    shown = collections.Counter()
    for fname, i, props in hits:
        key = (fname, props.get("Material"), props.get("CustomName"))
        if shown[key] >= 2:
            continue
        shown[key] += 1
        keep = {k: v for k, v in props.items() if k not in ("xy",)}
        print("  %-34s #%-3d %s" % (fname, i, keep))


if __name__ == "__main__":
    main()
