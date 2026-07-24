#!/usr/bin/env python3
"""Stage 2: classify the top works as present/absent on Sefaria, output the
ranked 'most-wanted' list (works Halachipedia cites often that Sefaria lacks).
Gentle: single-threaded, delayed, cached.
"""
import difflib, json, os, re, time, urllib.parse, urllib.request

HERE = os.path.dirname(__file__)
ranked = json.load(open(os.path.join(HERE, "work_frequency.json")))["ranked"]
cache_path = os.path.join(HERE, "work_presence_cache.json")
cache = json.load(open(cache_path)) if os.path.exists(cache_path) else {}

TOP = 250  # classify the most-cited works only

# English handbooks / topic pages, not Sefaria source texts -- flag separately.
ENGLISH = re.compile(r"\bHalachos of\b|\bLaws of\b|Handbook|by Rabbi|\bThe \b|Melachos|Guide", re.I)


def norm(s):
    return re.sub(r"[^a-z]", "", s.lower())


def presence(work):
    if work in cache:
        return cache[work]
    try:
        d = json.loads(urllib.request.urlopen(
            "https://www.sefaria.org/api/name/" + urllib.parse.quote(work), timeout=15).read())
        if d.get("is_ref"):
            r = "present"
        else:
            comps = d.get("completions") or []
            top = comps[0] if comps else ""
            ratio = difflib.SequenceMatcher(None, norm(work), norm(top)).ratio()
            r = "present" if ratio >= 0.8 else "absent"
    except Exception:
        r = "err"
    cache[work] = r
    time.sleep(0.3)
    return r


absent, present = [], []
for name, n, linked in ranked[:TOP]:
    if linked:                     # already had a location resolve -> present
        present.append((name, n)); continue
    kind = "english-handbook" if ENGLISH.search(name) else "hebrew-source"
    p = presence(name)
    (absent if p == "absent" else present).append((name, n) if p != "absent" else (name, n, kind))
    if len(cache) % 25 == 0:
        json.dump(cache, open(cache_path, "w"), ensure_ascii=False)
json.dump(cache, open(cache_path, "w"), ensure_ascii=False)

absent.sort(key=lambda x: -x[1])
heb = [(nm, n) for nm, n, k in absent if k == "hebrew-source"]
eng = [(nm, n) for nm, n, k in absent if k == "english-handbook"]
out = {"hebrew_source_works_absent": heb, "english_handbooks_absent": eng,
       "classified_top": TOP, "total_citations_to_absent_hebrew": sum(n for _, n in heb)}
json.dump(out, open(os.path.join(HERE, "..", "data", "sefaria_most_wanted.json"), "w"),
          ensure_ascii=False, indent=1)

print("=== MOST-WANTED: Hebrew source works Halachipedia cites but Sefaria lacks ===")
print("(ranked by citation count in the 250-page sample)\n")
for nm, n in heb[:30]:
    print(f"  {n:4}  {nm}")
print(f"\n({sum(n for _,n in heb)} citations point to these {len(heb)} absent Hebrew works)")
print(f"\nseparately, {len(eng)} English halacha handbooks (Feldheim/ArtScroll-type) also absent, e.g.:")
for nm, n in eng[:6]:
    print(f"  {n:4}  {nm}")
