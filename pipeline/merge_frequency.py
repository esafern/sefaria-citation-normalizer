#!/usr/bin/env python3
"""Merge the original 0-250 frequency table with the widened cache (250-640).

The original 250-page find-refs cache didn't survive the fresh container clone,
but its *reduction* did (work_frequency_0_250.json). Re-mining those pages would
be redundant load on Sefaria, so instead we add the new cache's per-detection
counts on top of the committed base. The two page ranges are disjoint, so summing
counts by work key is exactly equivalent to rebuilding from the union — without
re-hitting find-refs for pages already mined.

Writes the full-corpus work_frequency.json that build_final.py consumes.
"""
import glob, json, os, re
from collections import Counter
from build_mostwanted import work_name, normkey, FRDIR

HERE = os.path.dirname(__file__)
freq = Counter()
surfaces = {}
linked = set()


def add(work_or_disp, n, is_linked):
    if len(work_or_disp) < 3 or re.fullmatch(r"[A-Za-z]{1,2}", work_or_disp):
        return
    k = normkey(work_or_disp)
    if len(k) < 3:
        return
    freq[k] += n
    surfaces.setdefault(k, Counter())[work_or_disp] += n
    if is_linked:
        linked.add(k)


# base: the committed 0-250 reduction (already work-name reduced)
base = json.load(open(os.path.join(HERE, "work_frequency_0_250.json")))["ranked"]
base_detections = sum(n for _, n, _ in base)
for disp, n, lk in base:
    add(disp, n, lk)

# add: the widened cache (250-640), reduced per detection
cache_detections = 0
for f in glob.glob(os.path.join(FRDIR, "fr_*.json")):
    for r in json.load(open(f)):
        t = (r.get("text") or "").strip()
        if not (t and re.search(r"[A-Za-z]", t)):
            continue
        cache_detections += 1
        add(work_name(t), 1, bool(r.get("refs")) and not r.get("linkFailed"))

ranked = [[surfaces[k].most_common(1)[0][0], n, (k in linked)] for k, n in freq.most_common()]
json.dump({"ranked": ranked}, open(os.path.join(HERE, "work_frequency.json"), "w"),
          ensure_ascii=False, indent=1)
print(f"base(0-250) detections={base_detections}  cache(250-640) detections={cache_detections}")
print(f"merged: {len(ranked)} distinct works, {sum(n for _, n, _ in ranked)} total detections")
print("top 15:")
for disp, n, lk in ranked[:15]:
    print(f"  {n:4}  {'linked' if lk else 'UNRESOLVED':10}  {disp}")
