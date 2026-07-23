#!/usr/bin/env python3
"""Bigger trawl: many tags (author/dialect diversity) -> find-refs -> dump the
full distinct set of English citations Sefaria DETECTS but can't resolve, plus a
noise-filtered candidate list for LLM labeling. Polite: cached, bounded workers.
"""
import json, os, re, sys, time, urllib.parse, urllib.request
from concurrent.futures import ThreadPoolExecutor
import threading

BASE = "https://www.sefaria.org"
CACHE = os.path.join(os.path.dirname(__file__), "mine_cache")
os.makedirs(CACHE, exist_ok=True)
TAGS = ["Halakhah", "Parashat Hashavua", "Talmud", "Prayer", "Holidays", "Tanakh",
        "Musar", "Chasidut", "Kabbalah", "Mishnah", "Shabbat", "Israel", "Tefillah",
        "Rosh Hashanah", "Pesach", "Chumash", "Rashi", "Rambam", "Ethics", "Women"]
PER_TAG = 22
FR_WORKERS = 4
_lock = threading.Lock()
log = lambda *a: print(*a, flush=True)

# noise the labeler shouldn't waste time on
NOISE = re.compile(
    r"&nbsp|&amp|Song of Ice|Wiki of Ice|Android|Apocrypha|Ancient Near|\bBCE\b|\bCE\b|"
    r"\bActs\b|\bLXX\b|Septuagint|New Testament|Matthew|\bLuke\b|\bJohn \d|Corinthians|"
    r"Romans|Revelation|Gospel|Apostles|Celsum|Britannica|\bDSM|Encyclopedia|Enc\.|"
    r"\bBDB\b|Cuneiform|Conservative Judaism|Azure|Contemporary|Chabad\.org|Wikipedia|"
    r"Zornberg|Dor-Shav|Measure for Measure|Modern Commentator", re.I)
NUM_ONLY = re.compile(r"^\W*\d+[ab]?([:.\-]\d+[ab]?)*\W*$")
STOP = {"Chapter", "Source", "Sources", "Verse", "Part", "Section", "Oral", "Torah",
        "Song", "Wiki", "Chapters", "Note", "Notes", "Book", "Books", "Around", "Between"}


def cached_get(url, tag):
    key = os.path.join(CACHE, tag + "_" + re.sub(r"\W+", "_", url)[-80:] + ".json")
    if os.path.exists(key):
        return json.load(open(key))
    req = urllib.request.Request(url, headers={"User-Agent": "citation-research/0.1"})
    d = json.loads(urllib.request.urlopen(req, timeout=30).read())
    json.dump(d, open(key, "w"))
    time.sleep(0.12)
    return d


def free_text(sheet):
    parts = []
    for s in sheet.get("sources", []):
        for k in ("comment", "outsideText"):
            v = s.get(k)
            if isinstance(v, str):
                parts.append(v)
            elif isinstance(v, dict):
                parts.append(v.get("en", ""))
        ob = s.get("outsideBiText")
        if isinstance(ob, dict):
            parts.append(ob.get("en", ""))
    txt = " ".join(re.sub(r"<[^>]+>", " ", p or "") for p in parts)
    txt = re.sub(r"&nbsp;?|&amp;", " ", txt)
    return re.sub(r"\s+", " ", txt).strip()


def find_refs(body):
    key = os.path.join(CACHE, "fr_" + str(abs(hash(body))) + ".json")
    if os.path.exists(key):
        return json.load(open(key))
    req = urllib.request.Request(BASE + "/api/find-refs",
        data=json.dumps({"text": {"title": "", "body": body}}).encode(),
        headers={"Content-Type": "application/json", "User-Agent": "citation-research/0.1"})
    tid = json.loads(urllib.request.urlopen(req, timeout=40).read())["task_id"]
    for _ in range(20):
        time.sleep(1.5)
        d = json.loads(urllib.request.urlopen(f"{BASE}/api/async/{tid}", timeout=40).read())
        if d.get("ready"):
            res = d.get("result")
            if isinstance(res, str):
                res = json.loads(res)
            body_r = res.get("body", res) if isinstance(res, dict) else {}
            results = body_r.get("results", []) if isinstance(body_r, dict) else []
            json.dump(results, open(key, "w"), ensure_ascii=False)
            return results
    return []


def is_candidate(t):
    if NOISE.search(t) or NUM_ONLY.match(t):
        return False
    words = re.findall(r"[A-Za-z']{3,}", t)
    real = [w for w in words if w[0].isupper() and w not in STOP]
    return len(real) >= 1 and len(t) <= 60


def main():
    ids = []
    for tag in TAGS:
        try:
            d = cached_get(f"{BASE}/api/sheets/tag/{urllib.parse.quote(tag)}", "tag")
            ids += [s["id"] for s in d.get("sheets", [])][:PER_TAG]
        except Exception as e:
            log("tag err", tag, str(e)[:40])
    ids = list(dict.fromkeys(ids))
    log(f"{len(ids)} distinct sheets across {len(TAGS)} tags")

    def load(i):
        try:
            return free_text(cached_get(f"{BASE}/api/sheets/{i}", "sheet"))
        except Exception:
            return ""
    with ThreadPoolExecutor(6) as ex:
        texts = [t for t in ex.map(load, ids) if len(t) > 40]
    log(f"{len(texts)} sheets with usable free-text")

    ascii_h = re.compile(r"[A-Za-z]")
    failed = set()
    done = [0]
    def mine(t):
        try:
            for r in find_refs(t[:4000]):
                txt = (r.get("text") or "").strip()
                if txt and ascii_h.search(txt) and (r.get("linkFailed") or not r.get("refs")):
                    with _lock:
                        failed.add(txt)
        except Exception:
            pass
        with _lock:
            done[0] += 1
            if done[0] % 30 == 0:
                log(f"  find-refs {done[0]}/{len(texts)}  (distinct failures so far: {len(failed)})")
    with ThreadPoolExecutor(FR_WORKERS) as ex:
        list(ex.map(mine, texts))

    allf = sorted(failed)
    cands = sorted(c for c in allf if is_candidate(c))
    json.dump(allf, open(os.path.join(os.path.dirname(__file__), "v2_all_failures.json"), "w"), ensure_ascii=False, indent=0)
    json.dump(cands, open(os.path.join(os.path.dirname(__file__), "v2_candidates.json"), "w"), ensure_ascii=False, indent=0)
    log(f"\nDONE: {len(allf)} distinct EN failures; {len(cands)} plausible candidates for labeling")


if __name__ == "__main__":
    main()
