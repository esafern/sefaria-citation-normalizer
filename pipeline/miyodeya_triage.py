#!/usr/bin/env python3
"""Triage the unresolved Mi Yodeya citations into labelable / coverage / noise.

Run AFTER the auto-harvest finishes (single Sefaria stream). For each unresolved
citation, reduce to its base work and ask /api/name whether that work exists on
Sefaria (deduped per work, cached):
  - present  -> LABELABLE  (Sefaria has it; the raw just needs normalization -> tier-2)
  - absent   -> coverage   (Sefaria lacks the work; not normalization training)
  - junk     -> noise      (no real work name)

Writes miyodeya_labelable.json — the queue for the labeling pass.
"""
import json, os, re, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from build_mostwanted import work_name, normkey
import presence

HERE = os.path.dirname(__file__)
_JUNK = re.compile(r"http|street|philosoph|traditio|anchor|antiquities|apocrypha|codex|translation", re.I)


def main():
    batch = json.load(open(os.path.join(HERE, "miyodeya_dataset_batch.json")))
    unresolved = batch["unresolved"]
    cache = json.load(open(os.path.join(HERE, "presence_cache.json"))) \
        if os.path.exists(os.path.join(HERE, "presence_cache.json")) else {}

    # group citations by base work; presence-check each distinct work once
    by_work = {}
    for c in unresolved:
        w = work_name(c)
        if len(w) < 4 or _JUNK.search(c) or not re.search(r"[A-Za-z]{4}", w):
            continue
        by_work.setdefault(w, []).append(c)

    labelable, coverage, checked = {}, {}, 0
    for w, cites in sorted(by_work.items(), key=lambda x: -len(x[1])):
        r = presence.check(w, cache=cache, delay=0.25)
        checked += 1
        if r["present"]:
            labelable[w] = {"present_as": r["match"], "citations": cites}
        else:
            coverage[w] = cites
        if checked % 25 == 0:
            json.dump(cache, open(os.path.join(HERE, "presence_cache.json"), "w"), ensure_ascii=False)
            print(f"  checked {checked} works | labelable {len(labelable)} | coverage {len(coverage)}", flush=True)
    json.dump(cache, open(os.path.join(HERE, "presence_cache.json"), "w"), ensure_ascii=False)

    json.dump(labelable, open(os.path.join(HERE, "miyodeya_labelable.json"), "w"),
              ensure_ascii=False, indent=1)
    n_lab_cites = sum(len(v["citations"]) for v in labelable.values())
    print(f"\ndistinct works: {len(by_work)}")
    print(f"LABELABLE (present on Sefaria): {len(labelable)} works, {n_lab_cites} citations -> miyodeya_labelable.json")
    print(f"coverage gaps (absent): {len(coverage)} works")
    print("\ntop labelable works (by citation count):")
    for w, v in sorted(labelable.items(), key=lambda x: -len(x[1]['citations']))[:20]:
        print(f"  {len(v['citations']):3}  {w[:34]:34} present as: {v['present_as']}")


if __name__ == "__main__":
    main()
