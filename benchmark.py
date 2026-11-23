#!/usr/bin/env python3
"""Score the deterministic rules against the verified dataset.

Every resolved citation is compared with the row's `sefaria_ref` and given one
of these outcomes:

  correct     same ref as the label
  coarser     an ancestor of the label (Exodus 13 for Exodus 13:9): less
              precise, but points at the right place, so not a mislink
  finer       a descendant of the label (the label itself was too coarse)
  WRONG       anything else: a mislink, the one outcome that must stay at 0
  unresolved  no link (the safe failure)

"Resolved" (the old headline number) = correct + coarser + finer + WRONG.
Uses the resolver cache, so reruns are cheap. Online on a cold cache.

  python3 benchmark.py            # summary + every WRONG row
  python3 benchmark.py --misses   # also list unresolved rows
  python3 benchmark.py --all      # also list coarser/finer rows
  python3 benchmark.py --strict   # exit 1 if any WRONG (for CI / pre-commit)
"""
import json
import os
import re
import sys
import urllib.parse

sys.path.insert(0, os.path.dirname(__file__))
from normalizer.resolve import resolve, Cache

HERE = os.path.dirname(__file__)


def ref_tokens(s):
    """Comparable token list for a ref ("Exodus 13:9") or a Sefaria URL
    ("https://www.sefaria.org/Exodus.13.9"). URLs use '.' between book and
    sections and '_' for spaces; refs use ' ' and ':'."""
    if "sefaria.org/" in s:
        s = urllib.parse.unquote(s.split("sefaria.org/", 1)[1]).split("?")[0]
    return re.sub(r"[.:_,\s]+", " ", s).strip().split(" ")


def classify(url, label):
    if not url:
        return "unresolved"
    got, want = ref_tokens(url), ref_tokens(label)
    if got == want:
        return "correct"
    if want[:len(got)] == got:
        return "coarser"
    if got[:len(want)] == want:
        return "finer"
    return "WRONG"


def main():
    data = json.load(open(os.path.join(HERE, "data", "citation_dataset.json")))
    cache = Cache(os.path.join(HERE, "pipeline", "verify_cache.json"))
    rows = {k: [] for k in ("correct", "coarser", "finer", "WRONG", "unresolved")}
    for d in data:
        url = resolve(d["raw"], cache=cache, polite=0.03)
        rows[classify(url, d["sefaria_ref"])].append((d["raw"], url, d["sefaria_ref"]))
    cache.save()

    n = len(data)
    resolved = n - len(rows["unresolved"])
    print(f"resolved {resolved}/{n} ({100 * resolved // n}%): "
          f"correct {len(rows['correct'])}, coarser {len(rows['coarser'])}, "
          f"finer {len(rows['finer'])}, WRONG {len(rows['WRONG'])}; "
          f"unresolved {len(rows['unresolved'])}")

    def show(kind):
        if rows[kind]:
            print(f"\n{kind}:")
            for raw, url, label in rows[kind]:
                got = " ".join(ref_tokens(url)) if url else "-"
                print(f"   {raw!r}\n      got   {got}\n      label {label}")

    show("WRONG")
    if "--all" in sys.argv:
        show("coarser")
        show("finer")
    if "--misses" in sys.argv:
        print("\nunresolved (the knowledge tier):")
        for raw, _, _ in rows["unresolved"]:
            print("  ", raw)
    if "--strict" in sys.argv and rows["WRONG"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
