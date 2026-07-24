#!/usr/bin/env python3
"""Run the deterministic resolver over the trawl candidates. Everything that
resolves (rules propose -> Sefaria verifies) becomes an auto-verified pair with
no labeling. What's left is the knowledge tier for hand-labeling.

Polite: low concurrency, per-call delay, cached. Uses the lightweight /api/name
(not the ML find-refs), but still paced to be a light guest.
"""
import json, os, sys, time, urllib.parse, urllib.request
from concurrent.futures import ThreadPoolExecutor
import threading

HERE = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(HERE, ".."))
from normalizer import rules

BASE = "https://www.sefaria.org"
cands = json.load(open(os.path.join(HERE, "hp_failures.json")))
already = {d["raw"] for d in json.load(open(os.path.join(HERE, "..", "data", "citation_dataset.json")))}
todo = [c for c in cands if c not in already]

cache_path = os.path.join(HERE, "hp_name_cache.json")
cache = json.load(open(cache_path)) if os.path.exists(cache_path) else {}
_lock = threading.Lock()
WORKERS = 2            # gentle
DELAY = 0.2          # per /api/name call

def name(q):
    if q in cache:
        return cache[q]
    try:
        d = json.loads(urllib.request.urlopen(BASE + "/api/name/" + urllib.parse.quote(q), timeout=15).read())
        r = {"ref": d.get("ref"), "url": d.get("url")} if d.get("is_ref") and d.get("url") else None
    except Exception:
        r = None
    with _lock:
        cache[q] = r
    time.sleep(DELAY)
    return r

resolved, unresolved = [], []
done = [0]
def work(raw):
    hit = None
    for cand in rules.candidates(raw):
        r = name(cand)
        if r:
            hit = (cand, r)
            break
    with _lock:
        if hit:
            resolved.append({"raw": raw, "matched": hit[0],
                             "sefaria_ref": hit[1]["ref"], "url": BASE + "/" + hit[1]["url"].lstrip("/")})
        else:
            unresolved.append(raw)
        done[0] += 1
        if done[0] % 200 == 0:
            print(f"  {done[0]}/{len(todo)}  resolved so far: {len(resolved)}", flush=True)
            json.dump(cache, open(cache_path, "w"), ensure_ascii=False)

print(f"{len(todo)} new candidates (excl. {len(cands)-len(todo)} already in dataset)", flush=True)
with ThreadPoolExecutor(WORKERS) as ex:
    list(ex.map(work, todo))
json.dump(cache, open(cache_path, "w"), ensure_ascii=False)
json.dump(resolved, open(os.path.join(HERE, "hp_auto_resolved.json"), "w"), ensure_ascii=False, indent=1)
json.dump(sorted(unresolved), open(os.path.join(HERE, "hp_unresolved.json"), "w"), ensure_ascii=False, indent=1)
print(f"\nDONE: {len(resolved)} auto-verified pairs (rules+Sefaria); "
      f"{len(unresolved)} unresolved -> knowledge tier for labeling")
