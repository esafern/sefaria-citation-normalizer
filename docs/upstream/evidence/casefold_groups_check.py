#!/usr/bin/env python3
"""Check every case-only title group in Sefaria's title list, live.

Sefaria's /api/index/titles contains ~1,100 groups of titles that differ only
in letter case (Rosh HaShanah / Rosh Hashanah, Meilah / meilah, ...). For each
group this checks:

  1. consistency: every member resolves via /api/name, and all members resolve
     to the SAME ref. This is the safety claim behind the proposed case-insensitive
     fallback (SEFARIA-CASE-SENSITIVITY-PR.md): if every case variant Sefaria has
     points at one node, case-folding can't merge two different texts.
  2. bug scale: one synthetic casing NOT in the title list (first letter upper,
     rest lower: "Rosh hashanah") is expected to FAIL today. Every failure is a
     citation Sefaria would resolve with the fix.

Polite: serial, paced, cached to disk (resumable; rerun to continue).

  python3 casefold_groups_check.py            # run / resume
  python3 casefold_groups_check.py --report   # summarize from cache only
"""
import collections
import json
import os
import sys
import time
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
TITLES_URL = "https://www.sefaria.org/api/index/titles"
TITLES = os.path.join(HERE, "sefaria_titles_snapshot.json")
CACHE = os.path.join(HERE, "casefold_groups_cache.json")
RESULTS = os.path.join(HERE, "casefold_groups_results.json")
PACE = 0.5


def fetch(url):
    for attempt in range(4):
        try:
            return json.load(urllib.request.urlopen(url, timeout=30))
        except Exception:
            time.sleep(5 * (attempt + 1))
    raise RuntimeError(f"giving up on {url}")


def groups():
    if not os.path.exists(TITLES):
        json.dump(fetch(TITLES_URL), open(TITLES, "w"), ensure_ascii=False)
    titles = json.load(open(TITLES))["books"]
    by_fold = collections.defaultdict(set)
    for t in titles:
        by_fold[t.casefold()].add(t)
    return set(titles), [sorted(v) for v in by_fold.values() if len(v) > 1]


def main():
    exact, grps = groups()
    cache = json.load(open(CACHE)) if os.path.exists(CACHE) else {}
    report_only = "--report" in sys.argv

    def resolve(q):
        if q not in cache:
            if report_only:
                return "PENDING"
            d = fetch("https://www.sefaria.org/api/name/" + urllib.parse.quote(q) + "?limit=0")
            cache[q] = d.get("ref") if d.get("is_ref") else None
            time.sleep(PACE)
            if len(cache) % 50 == 0:
                json.dump(cache, open(CACHE, "w"), ensure_ascii=False)
                print(f"  {len(cache)} queries cached", flush=True)
        return cache[q]

    out = {"consistent": [], "DIVERGENT": [], "member_unresolved": [],
           "synthetic_fails_today": [], "synthetic_resolves_today": [], "pending": 0}
    for g in grps:
        refs = {t: resolve(t) for t in g}
        if "PENDING" in refs.values():
            out["pending"] += 1
            continue
        vals = set(refs.values())
        if None in vals:
            out["member_unresolved"].append(refs)
        elif len(vals) > 1:
            out["DIVERGENT"].append(refs)
        else:
            out["consistent"].append(g)
        syn = g[0][:1].upper() + g[0][1:].lower()
        if syn not in exact:
            r = resolve(syn)
            if r == "PENDING":
                continue
            target = next((v for v in vals if v), None)
            (out["synthetic_fails_today"] if r is None else out["synthetic_resolves_today"]).append(
                {"query": syn, "got": r, "group_ref": target})
    json.dump(cache, open(CACHE, "w"), ensure_ascii=False)
    json.dump(out, open(RESULTS, "w"), ensure_ascii=False, indent=1)

    print(f"groups {len(grps)}: consistent {len(out['consistent'])}, "
          f"DIVERGENT {len(out['DIVERGENT'])}, member unresolved {len(out['member_unresolved'])}, "
          f"pending {out['pending']}")
    print(f"synthetic casing: fails today {len(out['synthetic_fails_today'])}, "
          f"resolves today {len(out['synthetic_resolves_today'])}")
    for d in out["DIVERGENT"][:20]:
        print("  DIVERGENT", d)
    for d in out["member_unresolved"][:10]:
        print("  member unresolved", d)


if __name__ == "__main__":
    main()
