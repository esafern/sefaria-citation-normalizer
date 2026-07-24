#!/usr/bin/env python3
"""'Most-wanted' list: works Halachipedia cites often that Sefaria lacks.

Stage 1 (local, no API): recount every citation detection from the find-refs
cache, reduce each to a work name, and rank works by citation frequency.
Stage 2 (gentle API): classify the top works as present / absent on Sefaria.
The absent ones, ranked by frequency, are a licensing-priority list for Sefaria.
"""
import glob, json, os, re, sys, time, urllib.parse, urllib.request
from collections import Counter

HERE = os.path.dirname(__file__)
FRDIR = os.path.join(HERE, "hp_cache")

# strip a leading responsa/sefer marker, then take the work name up to the first
# location token (digit / open-paren / section keyword).
_LEAD = re.compile(r"^\s*(?:Shu\"?t|Sh\"?t|Shut|Responsa|Resp\.?|Sefer|Teshuvot|She'?elot u'?Teshuvot)\s+", re.I)
_SECTION = re.compile(r"\b(?:OC|O\"?C|YD|Y\"?D|EH|E\"?H|CM|C\"?M|Orach Chaim|Orach Chayim|Yoreh Deah|"
                      r"Even Haezer|Choshen Mishpat|siman|vol\.?|volume|perek|chelek|page|pg|p\.|no\.?|fnt)\b.*$", re.I)


def work_name(citation):
    s = _LEAD.sub("", citation).strip()
    s = re.sub(r"\(.*$", "", s)                 # drop parenthetical location
    s = _SECTION.sub("", s)                       # drop section keyword + rest
    s = re.split(r"\s+\d", s)[0]                   # cut at first number
    s = re.sub(r"[.,;:\"'’\-–\s]+$", "", s).strip()
    return s


def normkey(w):
    return re.sub(r"[^a-z]", "", w.lower())


def main():
    detections = []
    for f in glob.glob(os.path.join(FRDIR, "fr_*.json")):
        for r in json.load(open(f)):
            t = (r.get("text") or "").strip()
            if t and re.search(r"[A-Za-z]", t):
                detections.append((t, bool(r.get("refs")) and not r.get("linkFailed")))
    print(f"{len(detections)} total detections from cache", flush=True)

    freq = Counter()          # workkey -> citation count
    display = {}              # workkey -> a readable display name (most common surface form)
    surfaces = {}
    resolved_any = set()      # workkeys that had at least one detection Sefaria resolved
    for text, ok in detections:
        w = work_name(text)
        if len(w) < 3 or re.fullmatch(r"[A-Za-z]{1,2}", w):
            continue
        k = normkey(w)
        if len(k) < 3:
            continue
        freq[k] += 1
        surfaces.setdefault(k, Counter())[w] += 1
        if ok:
            resolved_any.add(k)
    for k, c in surfaces.items():
        display[k] = c.most_common(1)[0][0]

    ranked = freq.most_common()
    json.dump({"ranked": [[display[k], n, (k in resolved_any)] for k, n in ranked]},
              open(os.path.join(HERE, "work_frequency.json"), "w"), ensure_ascii=False, indent=1)
    print(f"{len(ranked)} distinct works\n")
    print("top 40 most-cited works (resolved? = a location of it linked on Sefaria):")
    for k, n in ranked[:40]:
        print(f"  {n:4}  {'linked' if k in resolved_any else 'UNRESOLVED':10}  {display[k]}")


if __name__ == "__main__":
    main()
