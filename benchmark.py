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
from citenorm.resolve import resolve, Cache

HERE = os.path.dirname(__file__)


def ref_tokens(s):
    """Comparable token list for a ref ("Exodus 13:9") or a Sefaria URL
    ("https://www.sefaria.org/Exodus.13.9"). URLs use '.' between book and
    sections and '_' for spaces; refs use ' ' and ':'."""
    if "sefaria.org/" in s:
        s = urllib.parse.unquote(s.split("sefaria.org/", 1)[1]).split("?")[0]
    return re.sub(r"[.:_,\s]+", " ", s).strip().split(" ")


def _covers(got, want):
    """Does ref `got` contain ref `want`? Prefix-ancestry, plus two Sefaria
    addressing cases: a bare daf covers either amud ("Shabbat 88" covers
    "Shabbat 88a"), and a final range covers a point inside it ("Leviticus
    13:12-13" covers "Leviticus 13:12"; "Bava Batra 15" covers "15a:11-15b:11")."""
    if want[:len(got)] == got:
        return True
    if len(got) > len(want) or not got:
        return False
    head, last, w = got[:-1], got[-1], want[len(got) - 1]
    if want[:len(head)] != head:
        return False
    w0 = w.split("-")[0]
    if re.fullmatch(r"\d+", last) and re.fullmatch(rf"{last}[ab]", w0):
        return True                                   # daf covers amud
    m = re.fullmatch(r"(\d+)([ab]?)-(\d+)([ab]?)", last)
    n = re.fullmatch(r"(\d+)([ab]?)", w0)
    if m and n:
        lo = (int(m.group(1)), m.group(2) or "a")
        hi = (int(m.group(3)), m.group(4) or "b")
        return lo <= (int(n.group(1)), n.group(2) or "a") <= hi
    return False


def classify(url, label):
    if not url:
        return "unresolved"
    got, want = ref_tokens(url), ref_tokens(label)
    if got == want:
        return "correct"
    if _covers(got, want):
        return "coarser"
    # gold is a range ("Bava Metzia 85a:23-85b:1") and ours sits at one end of
    # it ("Bava Metzia 85b"): the writer cited part of what they linked
    if "-" in label:
        start, tail = label.rsplit("-", 1)
        st, tt = ref_tokens(start), ref_tokens(tail)
        if tt and tt[0][:1].isdigit() and len(tt) <= len(st):
            end = st[:len(st) - len(tt)] + tt
            if any(_covers(got, e) or _covers(e, got) for e in (st, end)):
                return "coarser"
    if _covers(want, got):
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
