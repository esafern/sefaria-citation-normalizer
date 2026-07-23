#!/usr/bin/env python3
import glob, json, os, re, urllib.parse, urllib.request, time
from concurrent.futures import ThreadPoolExecutor
from collections import Counter

HERE = os.path.dirname(__file__)
cands = json.load(open(os.path.join(HERE, "v2_candidates.json")))
labels = {}
for f in sorted(glob.glob(os.path.join(HERE, "labels_*.tsv"))):
    for line in open(f):
        line = line.rstrip("\n")
        if "\t" not in line:
            continue
        i, canon = line.split("\t", 1)
        labels[int(i)] = canon.strip()

pairs = [(cands[i], labels[i]) for i in sorted(labels)]

_cache = os.path.join(HERE, "verify_cache.json")
seen = json.load(open(_cache)) if os.path.exists(_cache) else {}

def resolves(q):
    if q in seen:
        return seen[q]
    try:
        d = json.loads(urllib.request.urlopen(
            "https://www.sefaria.org/api/name/" + urllib.parse.quote(q), timeout=15).read())
        r = d.get("ref") if d.get("is_ref") else False
    except Exception:
        r = None
    seen[q] = r
    time.sleep(0.05)
    return r

with ThreadPoolExecutor(6) as ex:
    canons = [p[1] for p in pairs]
    refs = list(ex.map(resolves, canons))
json.dump(seen, open(_cache, "w"), ensure_ascii=False)

verified = [(raw, canon, ref) for (raw, canon), ref in zip(pairs, refs) if ref]
print(f"labeled real citations: {len(pairs)}")
print(f"verified (my canonical resolves on Sefaria): {len(verified)}")
print(f"my recall misses (real citation, my ref string didn't resolve): {len(pairs)-len(verified)}\n")


def classify(raw, canon):
    r = raw.lower()
    tags = []
    if re.search(r"\b\w+(os|us|oth|as)\b", r) and re.search(r"os|us|oth|as", r):
        # crude: Ashkenazi/academic ending present in raw not in canon
        if re.search(r"(chos|kos|vos|nos| chas|choth|koth| berachos|berakoth|avos|shabbos|menachos|kesubos|yevamos|meseches|mesechtas|shemos|seifer|igros|chovos|tumas|hilchos|nosson|toras)", r):
            tags.append("ashkenazi/academic transliteration (-os/-oth, o->a)")
    if re.search(r"artscroll|bomberg|soncino|vilna|koren|steinsaltz|william davidson", r):
        tags.append("edition prefix strip")
    if re.search(r"mesechta|meseches|masechet|maseches|tractate|\btalmud\b|\bgemara\b|\bbavli\b|mishnah? of|mishnayos", r):
        tags.append("tractate/talmud word strip")
    if re.search(r"\bhilch|laws of|yad,|yesodey|mishneh torah|maimonides|rambam", r):
        tags.append("rambam section -> Mishneh Torah English")
    if re.search(r"[ivxlc]{2,}\b", raw) and re.search(r"\b(xxx|xiv|iii|vii|viii)\b", r):
        tags.append("roman numerals")
    if re.search(r"[֐-׿]", raw):
        tags.append("hebrew -> english")
    if re.search(r"pirke\b|rebi |rebbi|d'rebbi|nassan|nosson|brakhot|berachos|shemos|kesubos|chovos|igros|olas|seifer|meseches|shulhan|shulkhan", r):
        tags.append("spelling variant")
    if not tags:
        tags.append("other / knowledge / structural")
    return tags[0]

fam = Counter(classify(raw, canon) for raw, canon, ref in verified)
print("=== transformation families among VERIFIED rescues (count) ===")
for k, n in fam.most_common():
    print(f"  {n:3}  {k}")

# show a few examples per family
byfam = {}
for raw, canon, ref in verified:
    byfam.setdefault(classify(raw, canon), []).append((raw, ref))
print("\n=== examples ===")
for k in fam:
    print(f"\n[{k}]")
    for raw, ref in byfam[k][:6]:
        print(f"    {raw[:42]:42} -> {ref}")

json.dump([{"raw": r, "my_canonical": c, "sefaria_ref": ref} for r, c, ref in verified],
          open(os.path.join(HERE, "citation_dataset.json"), "w"), ensure_ascii=False, indent=1)
print(f"\ndataset written: citation_dataset.json ({len(verified)} verified raw->ref pairs)")
