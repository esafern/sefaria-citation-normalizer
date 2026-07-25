#!/usr/bin/env python3
"""Widen the Halachipedia sample — gently.

Mines the alphabetical page block *after* the original 250-page sample, so it
adds a fresh, non-overlapping sample without re-hitting find-refs for pages
already mined. Deliberately slow and serial to stay a polite guest on two hosts
(Halachipedia's MediaWiki API and Sefaria's find-refs ML endpoint):

  - one request at a time (no thread pool),
  - >=1s between page fetches, >=1.5s between find-refs polls,
  - a pause between every find-refs submission,
  - everything cached (deterministic keys) so a re-run resumes for free.

Writes to hp_failures_wide.json — does NOT touch the committed hp_failures.json.

Usage: python3 mine_wide.py [START] [COUNT]   (default START=250 COUNT=250)
"""
import hashlib, json, os, re, sys, time, urllib.parse, urllib.request

HERE = os.path.dirname(__file__)
WIKI = "https://www.halachipedia.com/api.php"
SEF = "https://www.sefaria.org"
CACHE = os.path.join(HERE, "hp_cache")
os.makedirs(CACHE, exist_ok=True)
UA = {"User-Agent": "citation-research/0.1 (research; contact via github)"}

START = int(sys.argv[1]) if len(sys.argv) > 1 else 250
COUNT = int(sys.argv[2]) if len(sys.argv) > 2 else 250
PAGE_DELAY = 1.0      # between MediaWiki fetches
FR_SUBMIT_DELAY = 1.5  # between find-refs submissions (extra courtesy)
POLL_DELAY = 1.5      # between async status polls
log = lambda *a: print(*a, flush=True)


def wiki(params):
    u = WIKI + "?" + params + "&format=json"
    return json.loads(urllib.request.urlopen(
        urllib.request.Request(u, headers=UA), timeout=25).read())


def list_pages(n):
    out, cont = [], None
    while len(out) < n:
        p = "action=query&list=allpages&aplimit=200&apminsize=2500&apfilterredir=nonredirects"
        if cont:
            p += "&apcontinue=" + urllib.parse.quote(cont)
        d = wiki(p)
        out += [pg["title"] for pg in d["query"]["allpages"]]
        cont = d.get("continue", {}).get("apcontinue")
        time.sleep(PAGE_DELAY)
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
        time.sleep(PAGE_DELAY)
    refs = re.findall(r"<ref[^>]*>(.*?)</ref>", wt, re.S)
    clean = []
    for r in refs:
        r = re.sub(r"\[https?://\S+\s?", " ", r)
        r = re.sub(r"<[^>]+>", " ", r)
        r = re.sub(r"\[\[|\]\]|\{\{|\}\}", " ", r)
        r = re.sub(r"\s+", " ", r).strip()
        if r:
            clean.append(r)
    return " . ".join(clean)


def find_refs(body):
    key = os.path.join(CACHE, "fr_" + hashlib.md5(body.encode()).hexdigest() + ".json")
    if os.path.exists(key):
        return json.load(open(key))
    time.sleep(FR_SUBMIT_DELAY)
    req = urllib.request.Request(SEF + "/api/find-refs",
        data=json.dumps({"text": {"title": "", "body": body}}).encode(),
        headers={"Content-Type": "application/json", **UA})
    tid = json.loads(urllib.request.urlopen(req, timeout=40).read())["task_id"]
    for _ in range(20):
        time.sleep(POLL_DELAY)
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
    all_pages = list_pages(START + COUNT)
    pages = all_pages[START:START + COUNT]
    log(f"widening: pages [{START}:{START+COUNT}] -> {len(pages)} new pages")
    ascii_h = re.compile(r"[A-Za-z]")
    failed, detected, done = set(), 0, 0
    for title in pages:
        try:
            txt = footnote_text(title)
            if len(txt) >= 30:
                for chunk in [txt[i:i + 3500] for i in range(0, min(len(txt), 10500), 3500)]:
                    for r in find_refs(chunk):
                        t = (r.get("text") or "").strip()
                        if not t or not ascii_h.search(t):
                            continue
                        detected += 1
                        if r.get("linkFailed") or not r.get("refs"):
                            failed.add(t)
        except Exception as e:
            log("  err", title[:30], str(e)[:40])
        done += 1
        if done % 10 == 0:
            log(f"  {done}/{len(pages)} pages | detected {detected} | distinct failures {len(failed)}")
            json.dump(sorted(failed), open(os.path.join(HERE, "hp_failures_wide.json"), "w"),
                      ensure_ascii=False, indent=0)
    json.dump(sorted(failed), open(os.path.join(HERE, "hp_failures_wide.json"), "w"),
              ensure_ascii=False, indent=0)
    log(f"\nDONE: {detected} citations detected across {len(pages)} pages, "
        f"{len(failed)} distinct unresolved -> hp_failures_wide.json")


if __name__ == "__main__":
    main()
