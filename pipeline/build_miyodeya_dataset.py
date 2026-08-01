#!/usr/bin/env python3
"""Turn Mi Yodeya find-refs failures into verified raw->ref training pairs.

Pipeline: filter the noisy failure strings to plausible halachic/Torah citations,
then run each through the normalizer (propose -> /api/name verify). Splits into:
  - RESOLVED: the normalizer found a real Sefaria ref where find-refs failed ->
    verified raw->ref pairs (training gold + proof the rule layer complements
    the ML linker).
  - UNRESOLVED: real-looking citations that still don't resolve -> either Sefaria
    lacks the work (coverage) or a tier-2 knowledge case for the model/labeler.

Usage: python3 build_miyodeya_dataset.py [LIMIT]   (default: first 200 filtered)
"""
import json, os, re, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from normalizer.resolve import resolve, Cache

HERE = os.path.dirname(__file__)
LIMIT = int(sys.argv[1]) if len(sys.argv) > 1 else 200

# ---- noise filter: drop what isn't a work+location citation ----
_NOISE = re.compile(
    r"http|\bwest\b|\bstreet\b|\bave\b|%|\bequal\b|\bsections?\b|\bwomen\b|"
    r"philosoph|traditio|anchor bible|antiquities|apocrypha|codex|\bpp?\.\b\s*\d|"
    r"^\W*\d|\bvol\.?\s*\d+\s*$|^\s*[a-z]{1,3}\s*$", re.I)
_BARE_LOC = re.compile(r"^[\s,.]*\d+[ab]?[\s.:]*\d*\s*$")           # "24a", ", 25b", "88a. 5"
_HAS_WORD = re.compile(r"[A-Za-z]{4,}")                             # a work-name-like token


def is_citation(s):
    s = s.strip()
    if len(s) < 5 or _NOISE.search(s) or _BARE_LOC.match(s):
        return False
    if not _HAS_WORD.search(s):
        return False
    # need >=2 alphabetic tokens OR one token + a location number (work + place)
    words = re.findall(r"[A-Za-z']{2,}", s)
    has_num = bool(re.search(r"\d", s))
    return len(words) >= 2 or (len(words) >= 1 and has_num)


def ref_from_url(url):
    if not url:
        return None
    return url.rsplit("/", 1)[-1].replace("_", " ")


def main():
    fails = json.load(open(os.path.join(HERE, "miyodeya_failures.json")))
    cand = [s for s in fails if is_citation(s)]
    print(f"{len(fails)} failures -> {len(cand)} pass the citation filter; "
          f"processing first {min(LIMIT, len(cand))}", flush=True)

    cache = Cache(os.path.join(HERE, "miyodeya_resolve_cache.json"))
    resolved, unresolved = [], []
    for i, raw in enumerate(cand[:LIMIT], 1):
        url = resolve(raw, cache=cache, polite=0.2)
        if url:
            resolved.append({"raw": raw, "sefaria_ref": ref_from_url(url), "sefaria_url": url})
        else:
            unresolved.append(raw)
        if i % 25 == 0:
            cache.save()
            print(f"  {i}/{min(LIMIT,len(cand))} | resolved {len(resolved)}", flush=True)
    cache.save()

    out = {"source": "Mi Yodeya (Judaism Stack Exchange), CC-BY-SA dump",
           "filtered_candidates": len(cand), "processed": min(LIMIT, len(cand)),
           "resolved_pairs": resolved, "unresolved": unresolved}
    json.dump(out, open(os.path.join(HERE, "miyodeya_dataset_batch.json"), "w"),
              ensure_ascii=False, indent=1)
    print(f"\nRESOLVED {len(resolved)} raw->ref pairs (normalizer succeeded where find-refs failed)")
    print(f"UNRESOLVED {len(unresolved)} (coverage gap or tier-2 knowledge case)")
    print("\nsample resolved pairs:")
    for p in resolved[:20]:
        print(f"  {p['raw'][:42]:42} -> {p['sefaria_ref']}")


if __name__ == "__main__":
    main()
