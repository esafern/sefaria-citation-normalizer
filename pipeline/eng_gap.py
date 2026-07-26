#!/usr/bin/env python3
"""Which works are most cited in English halachic text but lack a real English
translation on Sefaria? Count linked detections per index title, then sample each
title's text and measure English coverage (versions-existence is too noisy — even
Hebrew-only works carry stub/community 'en' versions)."""
import glob, json, os, re, time, urllib.parse, urllib.request
from collections import Counter

HERE = os.path.dirname(__file__)
UA = {"User-Agent": "citation-research/0.1"}
_LOC = re.compile(r"[\s,]+\d+[ab]?(?:[:.\-]\d+[ab]?)*$")


def index_title(ref):
    prev = None
    while ref != prev:
        prev, ref = ref, _LOC.sub("", ref).strip()
    return ref


def flatten(x):
    if isinstance(x, str):
        return [x]
    out = []
    for e in (x or []):
        out += flatten(e)
    return out


def coverage(title, cache):
    if title in cache:
        return cache[title]
    try:
        d = json.loads(urllib.request.urlopen(urllib.request.Request(
            "https://www.sefaria.org/api/texts/" + urllib.parse.quote(title) + "?context=0",
            headers=UA), timeout=15).read())
        he = [s for s in flatten(d.get("he")) if s.strip()]
        en = [s for s in flatten(d.get("text")) if s.strip()]
        cov = len(en) / max(len(he), 1)
    except Exception as e:
        cov = -1  # error / not a base text
    cache[title] = cov
    time.sleep(0.3)
    return cov


# count linked detections per index title
freq = Counter()
for f in glob.glob(os.path.join(HERE, "hp_cache", "fr_*.json")):
    for r in json.load(open(f)):
        if r.get("refs"):
            for ref in r["refs"]:
                freq[index_title(ref)] += 1

cache_path = os.path.join(HERE, "eng_cov_cache.json")
cache = json.load(open(cache_path)) if os.path.exists(cache_path) else {}
rows = []
for title, n in freq.most_common(160):
    if n < 4 or not re.search(r"[A-Za-z]{3}", title):
        continue
    cov = coverage(title, cache)
    rows.append((title, n, cov))
    if len(rows) % 25 == 0:
        json.dump(cache, open(cache_path, "w"), ensure_ascii=False)
json.dump(cache, open(cache_path, "w"), ensure_ascii=False)

gap = sorted([(t, n, c) for t, n, c in rows if 0 <= c < 0.4], key=lambda x: -x[1])
json.dump([{"work": t, "citations": n, "en_coverage": round(c, 2)} for t, n, c in gap],
          open(os.path.join(HERE, "..", "data", "english_gap.json"), "w"), ensure_ascii=False, indent=1)
print(f"checked {len(rows)} present index-titles; {len(gap)} with <40% English coverage")
print("\nMOST-CITED works lacking (near-)full English translation:")
for t, n, c in gap[:30]:
    print(f"  {n:5}  {int(c*100):3}% en  {t}")
