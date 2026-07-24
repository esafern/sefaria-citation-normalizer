#!/usr/bin/env python3
"""Refine the most-wanted list: strip false-absents.

The raw classifier flags a work 'absent' when its surface spelling doesn't match
a Sefaria title. But many are present under a transliteration variant (Ben Ish
Chai -> Ben Ish Hai, Chatom Sofer -> Chatam Sofer). Re-check every 'absent' work
through the normalizer's own candidate forms; anything that now resolves is
present, not wanted. What survives is genuinely absent (modern responsa, etc.).
"""
import json, os, sys, time, urllib.parse, urllib.request
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from normalizer import rules

HERE = os.path.dirname(__file__)
mw = json.load(open(os.path.join(HERE, "..", "data", "sefaria_most_wanted.json")))
cache_path = os.path.join(HERE, "refine_cache.json")
cache = json.load(open(cache_path)) if os.path.exists(cache_path) else {}


def resolves(q):
    if q in cache:
        return cache[q]
    try:
        d = json.loads(urllib.request.urlopen(
            "https://www.sefaria.org/api/name/" + urllib.parse.quote(q), timeout=15).read())
        r = bool(d.get("is_ref") and d.get("url"))
    except Exception:
        r = False
    cache[q] = r
    time.sleep(0.25)
    return r


def truly_absent(work, n):
    # try the work name + a location so /api/name can return is_ref
    for base in [work, work + " 1", work + " 1:1"]:
        for cand in rules.candidates(base):
            if resolves(cand):
                return False, cand
    return True, None


genuine, reclassified = [], []
for i, (work, n) in enumerate(mw["hebrew_source_works_absent"]):
    absent, hit = truly_absent(work, n)
    (genuine if absent else reclassified).append((work, n) if absent else (work, n, hit))
    if i % 20 == 0:
        json.dump(cache, open(cache_path, "w"), ensure_ascii=False)
        print(f"  {i}/{len(mw['hebrew_source_works_absent'])} checked", flush=True)
json.dump(cache, open(cache_path, "w"), ensure_ascii=False)

genuine.sort(key=lambda x: -x[1])
mw["hebrew_source_works_absent"] = genuine
mw["reclassified_present_after_normalization"] = reclassified
mw["total_citations_to_absent_hebrew"] = sum(n for _, n in genuine)
json.dump(mw, open(os.path.join(HERE, "..", "data", "sefaria_most_wanted.json"), "w"),
          ensure_ascii=False, indent=1)

print(f"\n=== MOST-WANTED (refined): genuinely absent Hebrew works ===\n")
for work, n in genuine[:35]:
    print(f"  {n:4}  {work}")
print(f"\n{len(genuine)} genuinely-absent works, {sum(n for _,n in genuine)} citations")
print(f"removed {len(reclassified)} false-absents (present under a variant spelling), e.g.:")
for work, n, hit in reclassified[:10]:
    print(f"  {work}  ->  {hit}")
