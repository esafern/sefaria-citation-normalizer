#!/usr/bin/env python3
"""Bounded, polite trawl of Hebrew Wikisource (he.wikisource.org) for citations to
works absent from Sefaria — parallel to the Halachipedia and source-sheet mines.

Seeds a set of citation-dense classic works (responsa + Acharonim), enumerates their
leaf sub-pages via the MediaWiki API, runs each page's text through Sefaria's
`find-refs`, and aggregates the citations the linker DETECTS but can't resolve,
counted by (noise-filtered) surface. Reports the resolve rate too, since the whole
question is whether classic Hebrew text yields an *absence* signal or just
surface-form misses of present works.

Polite: descriptive UA, maxlag=5, cached, low concurrency, paced.
"""
import json, os, re, time, urllib.parse, urllib.request
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
import threading

WS = "https://he.wikisource.org/w/api.php"
SEF = "https://www.sefaria.org"
UA = {"User-Agent": "citation-research/0.1 (Torah citation study; eric.safern@gmail.com)"}
CACHE = os.path.join(os.path.dirname(__file__), "wiki_cache")
os.makedirs(CACHE, exist_ok=True)
_lock = threading.Lock()
log = lambda *a: print(*a, flush=True)

SEEDS = ['שו"ת הרא"ש', 'שו"ת הרשב"א', 'נודע ביהודה', 'שו"ת חתם סופר',
         'ערוך השולחן', 'בן איש חי', 'מטה אפרים', 'שולחן ערוך הרב']
PER_SEED = 16

# structural / non-work noise in the unresolved surfaces
NOISE = re.compile(r"^===|סעיף|^סימן\b|פרשת|^פרק\b|^שנה\b|להורדה|הקדמה|^==|^\W*$")
GEM = re.compile(r'^[א-ת"\'\s.():\-–]{0,6}$')  # tiny gematria/punct fragments
LOC = re.compile(r'\s*(?:סימן|ס"?ק|דף|פרק|עמוד|הלכה|סעיף|כלל|ד"ה|ע"[אב]|\(.*?\)|['
                 r'א-ת]{1,3}[.:]?)\s*$')


def cached_get(url, tag):
    key = os.path.join(CACHE, tag + "_" + re.sub(r"\W+", "_", url)[-90:] + ".json")
    if os.path.exists(key):
        return json.load(open(key))
    d = json.loads(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30).read())
    json.dump(d, open(key, "w"), ensure_ascii=False)
    time.sleep(0.15)
    return d


def wapi(**p):
    p.setdefault("format", "json"); p.setdefault("maxlag", "5")
    return cached_get(WS + "?" + urllib.parse.urlencode(p), "ws")


def leaf_pages(prefix):
    out = []
    ap = wapi(action="query", list="allpages", apprefix=prefix, aplimit="60")
    for p in ap.get("query", {}).get("allpages", []):
        t = p["title"]
        if t == prefix or "הקדמה" in t or "להורדה" in t or "שער" in t:
            continue
        out.append(t)
    return out[:PER_SEED]


def page_text(title):
    d = wapi(action="query", prop="extracts", explaintext="1", titles=title)
    txt = next(iter(d["query"]["pages"].values())).get("extract", "")
    return re.sub(r"={2,}[^=]+={2,}", " ", txt)  # strip section headers


def find_refs(body):
    key = os.path.join(CACHE, "fr_" + str(abs(hash(body))) + ".json")
    if os.path.exists(key):
        return json.load(open(key))
    req = urllib.request.Request(SEF + "/api/find-refs",
        data=json.dumps({"text": {"title": "", "body": body}}).encode(),
        headers={"Content-Type": "application/json", "User-Agent": UA["User-Agent"]})
    try:
        tid = json.loads(urllib.request.urlopen(req, timeout=40).read())["task_id"]
    except Exception:
        return []
    for _ in range(25):
        time.sleep(1.3)
        try:
            d = json.loads(urllib.request.urlopen(f"{SEF}/api/async/{tid}", timeout=40).read())
        except Exception:
            continue
        if d.get("ready"):
            r = d["result"]["body"]["results"]
            json.dump(r, open(key, "w"), ensure_ascii=False)
            return r
    return []


def work_key(surface):
    prev = None
    s = surface.strip()
    while s != prev:
        prev, s = s, LOC.sub("", s).strip()
    return s


def main():
    titles = []
    for seed in SEEDS:
        try:
            lp = leaf_pages(seed)
            titles += lp
            log(f"  {seed}: {len(lp)} leaf pages")
        except Exception as e:
            log("seed err", seed, str(e)[:40])
    titles = list(dict.fromkeys(titles))
    log(f"{len(titles)} leaf pages total")

    stats = {"detected": 0, "resolved": 0, "unresolved": 0, "pages": 0}
    surf = Counter(); works = Counter(); example = {}
    done = [0]

    def mine(t):
        try:
            txt = page_text(t)
        except Exception:
            return
        res = find_refs(txt[:3800])
        with _lock:
            stats["pages"] += 1
            for r in res:
                stats["detected"] += 1
                txt2 = (r.get("text") or "").strip()
                if not (r.get("linkFailed") or not r.get("refs")):
                    stats["resolved"] += 1
                    continue
                stats["unresolved"] += 1
                if NOISE.search(txt2) or GEM.match(txt2) or len(txt2) < 4:
                    continue
                surf[txt2] += 1
                w = work_key(txt2)
                if w and len(w) >= 3 and not GEM.match(w):
                    works[w] += 1
                    example.setdefault(w, txt2)
            done[0] += 1
            if done[0] % 20 == 0:
                log(f"  find-refs {done[0]}/{len(titles)}  resolved={stats['resolved']} unresolved={stats['unresolved']}")

    with ThreadPoolExecutor(3) as ex:
        list(ex.map(mine, titles))

    out = {"stats": stats,
           "top_works": [{"work": w, "count": c, "example": example.get(w, "")}
                         for w, c in works.most_common(60)],
           "top_surfaces": [{"surface": s, "count": c} for s, c in surf.most_common(40)]}
    path = os.path.join(os.path.dirname(__file__), "wiki_freq.json")
    json.dump(out, open(path, "w"), ensure_ascii=False, indent=1)
    rr = stats["resolved"] / max(stats["detected"], 1)
    log(f"\nDONE: {stats['pages']} pages | detected {stats['detected']} | "
        f"resolved {stats['resolved']} ({rr:.0%}) | unresolved {stats['unresolved']}")
    log("top unresolved works (pre-classification):")
    for w, c in works.most_common(25):
        log(f"  {c:4}  {w}")


if __name__ == "__main__":
    main()
