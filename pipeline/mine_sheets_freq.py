#!/usr/bin/env python3
"""Frequency-preserving trawl of Sefaria source sheets.

Like mine_v2.py, but instead of collapsing find-refs failures into a distinct set,
it COUNTS how often each unresolved citation's *work* appears across sheets — the
raw material for a source-sheet 'most-wanted' ranking (parallel to the Halachipedia
one in build_final.py). Absence + PD classification happen in a later step.

Polite: cached, bounded workers, paced. Writes pipeline/sheet_work_freq.json.
"""
import json, os, re, time, urllib.parse, urllib.request
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
import threading
from build_mostwanted import work_name

BASE = "https://www.sefaria.org"
CACHE = os.path.join(os.path.dirname(__file__), "sheet_cache")
os.makedirs(CACHE, exist_ok=True)
TAGS = ["Halakhah", "Talmud", "Mishnah", "Tanakh", "Rashi", "Rambam", "Chasidut",
        "Kabbalah", "Musar", "Prayer", "Tefillah", "Shabbat", "Pesach", "Rosh Hashanah",
        "Yom Kippur", "Sukkot", "Chanukah", "Purim", "Shavuot", "Parashat Hashavua",
        "Women", "Ethics", "Israel", "Kashrut", "Pirkei Avot", "Repentance", "Charity",
        "Prophets", "Marriage", "Halacha", "Chumash", "Holidays", "Prayer", "Blessings",
        "Torah", "Mitzvot", "Jewish Thought", "Midrash", "Responsa", "Minhag"]
PER_TAG = 30
FR_WORKERS = 4
_lock = threading.Lock()
log = lambda *a: print(*a, flush=True)

NOISE = re.compile(
    r"&nbsp|&amp|Song of Ice|Android|Apocrypha|Ancient Near|\bBCE\b|\bCE\b|\bActs\b|"
    r"\bLXX\b|Septuagint|New Testament|Matthew|\bLuke\b|\bJohn \d|Corinthians|Romans|"
    r"Revelation|Gospel|Apostles|Celsum|Britannica|Encyclopedia|Enc\.|\bBDB\b|Cuneiform|"
    r"Conservative Judaism|Azure|Chabad\.org|Wikipedia|Measure for Measure", re.I)
NUM_ONLY = re.compile(r"^\W*\d+[ab]?([:.\-]\d+[ab]?)*\W*$")
STOP = {"Chapter", "Source", "Sources", "Verse", "Part", "Section", "Oral", "Torah",
        "Song", "Wiki", "Chapters", "Note", "Notes", "Book", "Books", "Around",
        "Between", "See", "Ibid", "Idem", "Here", "There", "Above", "Below", "Rabbi"}


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
    try:
        tid = json.loads(urllib.request.urlopen(req, timeout=40).read())["task_id"]
    except Exception:
        return []
    for _ in range(20):
        time.sleep(1.5)
        try:
            d = json.loads(urllib.request.urlopen(f"{BASE}/api/async/{tid}", timeout=40).read())
        except Exception:
            continue
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
    freq = Counter()
    surface = {}
    done = [0]

    def mine(t):
        local = []
        for r in find_refs(t[:4000]):
            txt = (r.get("text") or "").strip()
            if txt and ascii_h.search(txt) and (r.get("linkFailed") or not r.get("refs")):
                if is_candidate(txt):
                    w = work_name(txt)
                    if w and len(w) >= 3 and w not in STOP:
                        local.append((w, txt))
        with _lock:
            for w, txt in local:
                freq[w] += 1
                surface.setdefault(w, txt)
            done[0] += 1
            if done[0] % 40 == 0:
                log(f"  find-refs {done[0]}/{len(texts)}  (distinct works so far: {len(freq)})")

    with ThreadPoolExecutor(FR_WORKERS) as ex:
        list(ex.map(mine, texts))

    out = {"n_sheets": len(texts),
           "works": [{"work": w, "count": c, "example": surface.get(w, "")}
                     for w, c in freq.most_common()]}
    path = os.path.join(os.path.dirname(__file__), "sheet_work_freq.json")
    json.dump(out, open(path, "w"), ensure_ascii=False, indent=1)
    log(f"\nDONE: {len(texts)} sheets, {len(freq)} distinct unresolved works -> {path}")
    log("top 25 unresolved (pre-classification):")
    for w, c in freq.most_common(25):
        log(f"  {c:4}  {w}")


if __name__ == "__main__":
    main()
