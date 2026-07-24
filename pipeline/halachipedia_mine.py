#!/usr/bin/env python3
"""Mine citation candidates from Halachipedia (dense halachic footnotes).

Halachipedia articles carry their sources in <ref> footnotes — nearly pure
Anglo-Orthodox citations (Magen Avraham, Mishna Brurah, Shaarei Teshuva, Sh"t
responsa), far less noise than crowd-sourced sheets. We pull page wikitext via
the MediaWiki API, extract footnote text, run find-refs, and keep what Sefaria
detects but can't resolve.

Polite: robots.txt allows content pages & the API; we pace fetches and cap
find-refs concurrency (ML). Everything cached.
"""
import json, os, re, sys, time, urllib.parse, urllib.request
from concurrent.futures import ThreadPoolExecutor
import threading

HERE = os.path.dirname(__file__)
WIKI = "https://www.halachipedia.com/api.php"
SEF = "https://www.sefaria.org"
CACHE = os.path.join(HERE, "hp_cache")
os.makedirs(CACHE, exist_ok=True)
UA = {"User-Agent": "citation-research/0.1 (research; contact via github)"}
MAX_PAGES = 250
FR_WORKERS = 2
_lock = threading.Lock()
log = lambda *a: print(*a, flush=True)


def wiki(params):
    u = WIKI + "?" + params + "&format=json"
    return json.loads(urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=25).read())


def list_pages(n):
    out, cont = [], None
    while len(out) < n:
        p = "action=query&list=allpages&aplimit=200&apminsize=2500&apfilterredir=nonredirects"
        if cont:
            p += "&apcontinue=" + urllib.parse.quote(cont)
        d = wiki(p)
        out += [pg["title"] for pg in d["query"]["allpages"]]
        cont = d.get("continue", {}).get("apcontinue")
        time.sleep(0.3)
        if not cont:
            break
    return out[:n]


def footnote_text(title):
    key = os.path.join(CACHE, "pg_" + re.sub(r"\W+", "_", title)[:80] + ".json")
    if os.path.exists(key):
        wt = json.load(open(key))
    else:
        d = wiki("action=parse&page=" + urllib.parse.quote(title) + "&prop=wikitext")
        wt = d.get("parse", {}).get("wikitext", {}).get("*", "")
        json.dump(wt, open(key, "w"))
        time.sleep(0.3)
    refs = re.findall(r"<ref[^>]*>(.*?)</ref>", wt, re.S)
    clean = []
    for r in refs:
        r = re.sub(r"\[https?://\S+\s?", " ", r)      # external links
        r = re.sub(r"<[^>]+>", " ", r)
        r = re.sub(r"\[\[|\]\]|\{\{|\}\}", " ", r)
        r = re.sub(r"\s+", " ", r).strip()
        if r:
            clean.append(r)
    return " . ".join(clean)


def find_refs(body):
    key = os.path.join(CACHE, "fr_" + str(abs(hash(body))) + ".json")
    if os.path.exists(key):
        return json.load(open(key))
    req = urllib.request.Request(SEF + "/api/find-refs",
        data=json.dumps({"text": {"title": "", "body": body}}).encode(),
        headers={"Content-Type": "application/json", **UA})
    tid = json.loads(urllib.request.urlopen(req, timeout=40).read())["task_id"]
    for _ in range(20):
        time.sleep(1.5)
        d = json.loads(urllib.request.urlopen(SEF + "/api/async/" + tid, timeout=40).read())
        if d.get("ready"):
            res = d.get("result")
            if isinstance(res, str):
                res = json.loads(res)
            body_r = res.get("body", res) if isinstance(res, dict) else {}
            results = body_r.get("results", []) if isinstance(body_r, dict) else []
            json.dump(results, open(key, "w"), ensure_ascii=False)
            return results
    return []


def main():
    pages = list_pages(MAX_PAGES)
    log(f"{len(pages)} content pages")
    ascii_h = re.compile(r"[A-Za-z]")
    failed, detected = set(), [0]
    done = [0]

    def mine(title):
        try:
            txt = footnote_text(title)
            if len(txt) < 30:
                return
            for chunk in [txt[i:i + 3500] for i in range(0, min(len(txt), 10500), 3500)]:
                for r in find_refs(chunk):
                    t = (r.get("text") or "").strip()
                    if not t or not ascii_h.search(t):
                        continue
                    with _lock:
                        detected[0] += 1
                        if r.get("linkFailed") or not r.get("refs"):
                            failed.add(t)
        except Exception as e:
            with _lock:
                log("  err", title[:30], str(e)[:40])
        with _lock:
            done[0] += 1
            if done[0] % 25 == 0:
                log(f"  {done[0]}/{len(pages)} pages | detected {detected[0]} | distinct failures {len(failed)}")

    with ThreadPoolExecutor(FR_WORKERS) as ex:
        list(ex.map(mine, pages))
    out = sorted(failed)
    json.dump(out, open(os.path.join(HERE, "hp_failures.json"), "w"), ensure_ascii=False, indent=0)
    log(f"\nDONE: {detected[0]} citations detected, {len(out)} distinct unresolved -> hp_failures.json")


if __name__ == "__main__":
    main()
