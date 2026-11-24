#!/usr/bin/env python3
"""Mine labeled (raw citation -> Sefaria ref) test pairs from the web, for free.

When a writer hyperlinks a citation to Sefaria, the anchor text is the citation
as a human wrote it ("Berachos 5a", "S\"A O\"C 271:1") and the href is the
correct ref (sefaria.org/Berakhot.5a). No LLM or hand labeling needed.

Sources (all CC BY-SA, bulk/API access only, no crawling):
  miyodeya   Judaism Stack Exchange data dump (archive.org), Posts.xml bodies
  wikipedia  en/he Wikipedia articles that link to sefaria.org (MediaWiki API)

Steps (each resumable; raw files live in pipeline/web_pairs_raw/, gitignored):
  python3 web_pairs.py miyodeya     # dump -> web_pairs_raw/miyodeya_pairs.jsonl
  python3 web_pairs.py miyodeya_api  # posts since the dump, via SE API -> miyodeya_api_pairs.jsonl
  python3 web_pairs.py stackexchange hermeneutics christianity history
                                    # other SE dumps -> web_pairs_raw/se_<site>_pairs.jsonl
  python3 web_pairs.py wikipedia    # API  -> web_pairs_raw/wikipedia_<lang>_pairs.jsonl
  python3 web_pairs.py verify [N]   # dedup, filter, sample N per source, verify the
                                    # gold ref live -> data/web_pairs.json
  python3 web_pairs.py eval         # run the resolver on data/web_pairs.json, score it
                                    # with benchmark.classify (correct/coarser/finer/WRONG)

The 7z dump is read with py7zr (python3 -m venv /tmp/wpvenv && /tmp/wpvenv/bin/pip
install py7zr; run the miyodeya step with /tmp/wpvenv/bin/python).
"""
import collections
import html
import json
import os
import random
import re
import sys
import time
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RAW = os.path.join(HERE, "web_pairs_raw")
# WEB_PAIRS_OUT lets a full run write elsewhere without clobbering the committed sample
OUT = os.environ.get("WEB_PAIRS_OUT", os.path.join(ROOT, "data", "web_pairs.json"))
NAME_CACHE = os.path.join(RAW, "name_cache.json")
UA = "sefaria-citation-normalizer/0.1 (research; github.com/esafern)"
SEED = 20261124

# ---------------------------------------------------------------- href -> ref

_NON_TEXT = {"sheets", "topics", "texts", "search", "static", "profile", "collections",
             "api", "util", "groups", "visualize", "explore", "calendars", "translations",
             "donate", "about", "login", "register", "settings", "notifications", "updates",
             "people", "community", "story_editor", "admin", "my", "add", "edit", "activity",
             "william-davidson-talmud", "daf-yomi", "parashat-hashavua", "jobs", "team"}


def href_to_tref(url):
    """'https://www.sefaria.org/Shulchan_Arukh%2C_Orach_Chayim.271.1?lang=bi'
    -> 'Shulchan Arukh, Orach Chayim.271.1' (or None for non-text pages)."""
    try:
        u = urllib.parse.urlparse(html.unescape(url.strip()))
    except ValueError:
        return None
    host = (u.netloc or "").lower().split(":")[0]
    if not re.fullmatch(r"(?:[\w-]+\.)*sefaria\.org(?:\.il)?", host):
        return None
    path = u.path
    for _ in range(3):  # Wikipedia links are often double-encoded (%252C -> %2C -> ,)
        nxt = urllib.parse.unquote(path)
        if nxt == path:
            break
        path = nxt
    path = path.strip("/")
    if not path or path.split("/")[0].lower() in _NON_TEXT or "." not in path and "/" in path:
        return None
    tref = path.split("/")[0].replace("_", " ").strip()
    if not re.search(r"[A-Za-z\u0590-\u05FF]", tref):
        return None
    return tref


# ---------------------------------------------------------------- anchors

_STOP = {"here", "link", "see", "source", "sources", "sefaria", "ibid", "there", "also",
         "english", "hebrew", "translation", "text", "full", "page", "this", "that", "it",
         "click", "online", "available", "inside", "original", "commentary", "loc", "cit",
         "op", "id", "the", "a", "an", "of", "on", "in", "and", "at", "sic"}


def anchor_ok(a):
    """A usable citation anchor: names a work (not 'here', 'ibid 5b', '5a', a URL)."""
    if not a or len(a) < 3 or len(a) > 120 or "://" in a or a.lower().startswith("www."):
        return False
    # a word, or an abbreviation unit like S"A / O"C / M.B. / Shu"t
    words = re.findall(r"[A-Za-z\u0590-\u05FF]+(?:[\"'\u2019\u05F4.][A-Za-z\u0590-\u05FF]+)*", a)
    has_num = bool(re.search(r"\d", a))
    return any(w.lower() not in _STOP and (len(w) >= 3 or not w.isalpha()
                                           or (has_num and len(w) == 2 and w.isupper()))
               for w in words)


def clean_anchor(a):
    a = html.unescape(re.sub(r"<[^>]+>", "", a))
    return re.sub(r"\s+", " ", a).strip(" .,;:()[]\u200f\u200e")


_GENERIC = {"mishna", "mishnah", "mishnayot", "gemara", "gemora", "talmud", "bavli", "verse",
            "pasuk", "posuk", "perek", "chapter", "daf", "amud", "ibid", "there", "siman",
            "seif", "halacha", "halakha", "halakhah", "se'if", "no", "number", "page", "see",
            "law", "laws", "rule", "and", "the", "of", "in", "on"}


def consistent(raw, tref):
    """Do the anchor and the href plausibly name the same place? The anchor must
    carry a number, every number in it must appear in the href's sections
    ('Yevamos 3b' -> Yevamot.3b.17 ok; 'Shabbat 105b' -> Joshua.24.31 no;
    'Mishna Brura 451:34' -> SA OC 451.4 no), and it must name something beyond
    generic words ('Mishna 2:10' needs context, so no)."""
    nums = re.findall(r"\d+[ab]?", raw)
    if not nums:
        return False
    sec = set(re.split(r"[.:\s,\-]+", tref.lower()))
    if not all(n.lower() in sec for n in nums):
        return False
    words = [w.lower() for w in re.findall(r"[A-Za-z]+(?:[\"'\u2019.][A-Za-z]+)*", raw)]
    return any(w not in _GENERIC and len(w) >= 2 and not re.fullmatch(r"[ab]", w) for w in words)


# ---------------------------------------------------------------- Mi Yodeya

_A = re.compile(r"<a\s[^>]*href=\"([^\"]+)\"[^>]*>(.*?)</a>", re.S | re.I)


def mine_stackexchange(site="judaism", source="miyodeya"):
    """Any Stack Exchange site dump: <site>.stackexchange.com.7z from archive.org."""
    import py7zr  # noqa: F401  (venv only)
    dump = os.path.join(RAW, f"{site}.stackexchange.com.7z")
    sitedir = os.path.join(RAW, site)
    posts = os.path.join(sitedir, "Posts.xml")
    if site == "judaism" and os.path.exists(os.path.join(RAW, "Posts.xml")):
        posts = os.path.join(RAW, "Posts.xml")   # extracted before per-site dirs existed
    if not os.path.exists(posts):
        os.makedirs(sitedir, exist_ok=True)
        with py7zr.SevenZipFile(dump) as z:
            z.extract(path=sitedir, targets=["Posts.xml"])
    out = open(os.path.join(RAW, f"{source}_pairs.jsonl"), "w")
    n_posts = n_pairs = 0
    import xml.etree.ElementTree as ET
    for _, el in ET.iterparse(posts, events=("end",)):
        if el.tag != "row":
            continue
        body = el.get("Body") or ""
        if "sefaria" in body:
            n_posts += 1
            for href, inner in _A.findall(body):
                tref = href_to_tref(href)
                a = clean_anchor(inner)
                if tref and anchor_ok(a):
                    n_pairs += 1
                    out.write(json.dumps({"raw": a, "href": html.unescape(href), "tref": tref,
                                          "source": source,
                                          "where": f"https://{site}.stackexchange.com/a/{el.get('Id')}"},
                                         ensure_ascii=False) + "\n")
        el.clear()
    print(f"{source}: {n_posts} posts with sefaria links, {n_pairs} pairs")


def mine_miyodeya_api(since=1712448000):
    """Mi Yodeya posts after the archive.org dump (2024-04), via the public SE API.
    No key: pages stop at 25, so slide the fromdate window instead of paging on.
    ~120 requests for 2024-04 -> 2026-11; well inside the 300/day keyless quota."""
    import gzip
    import urllib.error
    H = {"User-Agent": "curl/8.7.1 (sefaria-citation-normalizer research)", "Accept-Encoding": "gzip"}

    def fetch(params):
        q = urllib.parse.urlencode(params)
        for i in range(4):
            try:
                raw = urllib.request.urlopen(urllib.request.Request(
                    "https://api.stackexchange.com/2.3/posts?" + q, headers=H), timeout=60).read()
                return json.loads(gzip.decompress(raw) if raw[:2] == b"\x1f\x8b" else raw)
            except urllib.error.HTTPError as e:
                b = e.read()
                print("  HTTP", e.code, (gzip.decompress(b) if b[:2] == b"\x1f\x8b" else b)[:160])
                time.sleep(30 * (i + 1))
        raise SystemExit("giving up")

    out = open(os.path.join(RAW, "miyodeya_api_pairs.jsonl"), "w")
    seen, total, n_pairs, last, quota = set(), 0, 0, since, None
    while True:
        for page in range(1, 26):
            d = fetch(dict(site="judaism", fromdate=since, filter="withbody", pagesize=100,
                           page=page, order="asc", sort="creation"))
            for p in d["items"]:
                if p["post_id"] in seen:
                    continue
                seen.add(p["post_id"])
                total += 1
                last = p["creation_date"]
                body = p.get("body", "")
                for href, inner in (_A.findall(body) if "sefaria" in body else []):
                    tref, a = href_to_tref(href), clean_anchor(inner)
                    if tref and anchor_ok(a):
                        n_pairs += 1
                        out.write(json.dumps({"raw": a, "href": html.unescape(href), "tref": tref,
                                              "source": "miyodeya_2024on",
                                              "where": f"https://judaism.stackexchange.com/a/{p['post_id']}"},
                                             ensure_ascii=False) + "\n")
            quota = d.get("quota_remaining")
            time.sleep(max(2.0, d.get("backoff", 0)))
            if not d.get("has_more"):
                break
        if not d.get("has_more") or quota < 30:
            break
        since = last
    print(f"miyodeya_2024on: {total} posts, {n_pairs} pairs, quota left {quota}")


# ---------------------------------------------------------------- Wikipedia

def _wapi(lang, **params):
    params.update(format="json", formatversion="2")
    url = f"https://{lang}.wikipedia.org/w/api.php?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    for attempt in range(4):
        try:
            d = json.load(urllib.request.urlopen(req, timeout=60))
            time.sleep(1.0)
            return d
        except Exception:
            time.sleep(10 * (attempt + 1))
    raise RuntimeError(url)


_WEXT = re.compile(r"\[(https?://[^\s\]]*sefaria\.org[^\s\]]*)\s+([^\]]+)\]", re.I)
_CITE = re.compile(r"\{\{\s*cite[^{}]*?\burl\s*=\s*(https?://[^\s|}]*sefaria\.org[^\s|}]*)[^{}]*?\}\}", re.I | re.S)
_TITLE = re.compile(r"\|\s*title\s*=\s*([^|}]+)", re.I)


def mine_wikipedia(lang):
    pages = set()
    for query in ("www.sefaria.org", "sefaria.org", "www.sefaria.org.il"):
        for proto in ("https", "http"):
            cont = {}
            while True:
                d = _wapi(lang, action="query", list="exturlusage", euquery=query,
                          euprotocol=proto, eunamespace=0, eulimit=500, **cont)
                pages.update(p["title"] for p in d["query"]["exturlusage"])
                if "continue" not in d:
                    break
                cont = d["continue"]
    pages = sorted(pages)
    print(f"wikipedia/{lang}: {len(pages)} articles link to Sefaria")
    out = open(os.path.join(RAW, f"wikipedia_{lang}_pairs.jsonl"), "w")
    n = 0
    for i in range(0, len(pages), 50):
        d = _wapi(lang, action="query", prop="revisions", rvprop="content", rvslots="main",
                  titles="|".join(pages[i:i + 50]))
        for p in d["query"]["pages"]:
            try:
                text = p["revisions"][0]["slots"]["main"]["content"]
            except (KeyError, IndexError):
                continue
            found = [(u, a) for u, a in _WEXT.findall(text)]
            for m in _CITE.finditer(text):
                t = _TITLE.search(m.group(0))
                if t:
                    found.append((m.group(1), t.group(1)))
            for href, a in found:
                a = clean_anchor(re.sub(r"'{2,}", "", a))
                tref = href_to_tref(href)
                if tref and anchor_ok(a):
                    n += 1
                    out.write(json.dumps({"raw": a, "href": href, "tref": tref,
                                          "source": f"wikipedia_{lang}",
                                          "where": f"https://{lang}.wikipedia.org/wiki/"
                                                   + urllib.parse.quote(p["title"].replace(" ", "_"))},
                                         ensure_ascii=False) + "\n")
        print(f"  {min(i + 50, len(pages))}/{len(pages)} articles, {n} pairs", flush=True)


# ---------------------------------------------------------------- verify + eval

def _name(q, cache):
    if q not in cache:
        url = "https://www.sefaria.org/api/name/" + urllib.parse.quote(q) + "?limit=0"
        for attempt in range(4):
            try:
                d = json.load(urllib.request.urlopen(url, timeout=30))
                break
            except Exception:
                time.sleep(5 * (attempt + 1))
        else:
            return None
        cache[q] = d.get("ref") if d.get("is_ref") else None
        time.sleep(0.5)
        if len(cache) % 50 == 0:
            json.dump(cache, open(NAME_CACHE, "w"), ensure_ascii=False)
    return cache[q]


def verify(per_source):
    cache = json.load(open(NAME_CACHE)) if os.path.exists(NAME_CACHE) else {}
    rows = []
    first = ["miyodeya_pairs.jsonl", "wikipedia_en_pairs.jsonl", "wikipedia_he_pairs.jsonl"]  # then the rest, alphabetically
    files = [f for f in os.listdir(RAW) if f.endswith("_pairs.jsonl")]
    for fn in sorted(files, key=lambda f: (f not in first, first.index(f) if f in first else 0, f)):
        if fn.endswith("_pairs.jsonl"):
            rows += [json.loads(l) for l in open(os.path.join(RAW, fn))]
    # dedup on (raw, tref); Latin-script anchors only for now (Hebrew is a later tier)
    seen, uniq = set(), []
    for r in rows:
        r["tref"] = href_to_tref(r["href"])  # recompute with the current parser
        if not r["tref"]:
            continue
        k = (r["raw"], r["tref"])
        if (k not in seen and re.search(r"[A-Za-z]", r["raw"])
                and not re.search(r"[\u0590-\u05FF]", r["raw"]) and consistent(r["raw"], r["tref"])):
            seen.add(k)
            uniq.append(r)
    by_src = collections.defaultdict(list)
    for r in uniq:
        by_src[r["source"]].append(r)
    rnd = random.Random(SEED)
    out = []
    # original sources first, in their original order, so adding a source never
    # reshuffles an existing source's sample
    order = ["miyodeya", "wikipedia_en", "wikipedia_he"]
    for src, rs in sorted(by_src.items(), key=lambda kv: (kv[0] not in order,
                                                         order.index(kv[0]) if kv[0] in order else 0,
                                                         kv[0])):
        rnd.shuffle(rs)
        kept = 0
        for r in rs:
            if kept >= per_source:
                break
            gold = _name(r["tref"], cache)  # canonical form of the href; None = dead link
            if not gold:
                continue
            asis = _name(r["raw"], cache)    # does Sefaria already resolve the anchor as written?
            r["sefaria_ref"] = gold
            r["clean"] = bool(asis)          # True: no normalization needed (regression case)
            out.append(r)
            kept += 1
        print(f"{src}: {len(rs)} unique pairs, kept {kept} with a live gold ref", flush=True)
    json.dump(cache, open(NAME_CACHE, "w"), ensure_ascii=False)
    json.dump({"source": "anchor-text -> href pairs from CC BY-SA sources; see `where` per row",
               "license": "CC BY-SA (attribution: `where` URL per row)",
               "pairs": out}, open(OUT, "w"), ensure_ascii=False, indent=1)
    m = sum(1 for r in out if not r["clean"])
    print(f"wrote {len(out)} pairs ({m} mangled, {len(out) - m} clean) -> {OUT}")


def _layer_noise(raw, url, gold):
    """True when ours and gold point at the same sections and differ only by a
    commentary layer the WRITER never named: 'Kidushin 81a' -> gold 'Ritva on
    Kiddushin 81a', ours 'Kiddushin 81a'. That's label noise (the writer linked
    the commentary they were reading), not a mislink. If the raw DOES name the
    commentator ('Tosfot Avodah Zarah 11a') and we dropped it, it stays WRONG."""
    from benchmark import ref_tokens
    from normalizer.resolve import _distinctive, _split_words, _matches_any
    ours = " ".join(ref_tokens(url))
    g = " ".join(ref_tokens(gold))
    raw_words = _distinctive(_split_words(raw))
    # Same location, different work: if every word of OUR title is in the text
    # and our title names more of the text than gold's does, the writer named a
    # work and linked its base text ('Midrash Sechel Tov to Genesis 26:34' linked
    # to Genesis 26:34). We followed the text, so it's label noise.
    def split(t):
        m = re.match(r"^(.*?)\s+([\d][\w:.\- ]*)$", t)
        return (m.group(1), m.group(2)) if m else (t, "")
    (ot, osec), (gt, gsec) = split(ours), split(g)
    if osec and osec.split(" ")[:2] == gsec.split(" ")[:2]:
        ow, gw = _distinctive(_split_words(ot)), _distinctive(_split_words(gt))
        o_in = all(_matches_any(w, raw_words) for w in ow)
        n_o = sum(_matches_any(w, raw_words) for w in ow)
        n_g = sum(_matches_any(w, raw_words) for w in gw)
        if o_in and n_o > n_g:
            return True
    for base, layered, gold_is_layered in ((ours, g, True), (g, ours, False)):
        m = re.match(r"^(.+?) on (.+)$", layered)
        if not m:
            continue
        b2 = m.group(2)
        if not ((b2 + " ").startswith(base + " ") or (base + " ").startswith(b2 + " ")):
            continue
        named = any(_matches_any(c, raw_words) for c in _distinctive(_split_words(m.group(1))))
        # gold has a layer the writer never named -> label noise;
        # ours has a layer the writer DID name -> we're right, the link was coarse
        return (not named) if gold_is_layered else named
    return False


def evaluate():
    sys.path.insert(0, ROOT)
    from benchmark import classify
    from normalizer.resolve import resolve, Cache
    cache = Cache(os.path.join(RAW, "resolve_cache.json"))
    pairs = json.load(open(OUT))["pairs"]
    tally = collections.defaultdict(collections.Counter)
    wrong = []
    for i, r in enumerate(pairs, 1):
        url = resolve(r["raw"], cache=cache, polite=0.3)
        k = classify(url, r["sefaria_ref"])
        if k == "WRONG" and _layer_noise(r["raw"], url, r["sefaria_ref"]):
            k = "label_noise"
        tally["clean" if r["clean"] else "mangled"][k] += 1
        r["ours"], r["outcome"] = url, k
        if k == "WRONG":
            wrong.append((r["raw"], url, r["sefaria_ref"], r["where"]))
        if i % 25 == 0:
            cache.save()
            print(f"  {i}/{len(pairs)}", flush=True)
    cache.save()
    json.dump(pairs, open(OUT.replace(".json", "_scored.json"), "w"), ensure_ascii=False, indent=1)
    for kind, c in tally.items():
        n = sum(c.values())
        print(f"{kind:8} n={n}: " + ", ".join(f"{k} {c[k]}" for k in
              ("correct", "coarser", "finer", "label_noise", "WRONG", "unresolved")))
    for w in wrong:
        print("  WRONG", w)


if __name__ == "__main__":
    os.makedirs(RAW, exist_ok=True)
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "miyodeya":
        mine_stackexchange()
    elif cmd == "miyodeya_api":
        mine_miyodeya_api()
    elif cmd == "stackexchange":   # web_pairs.py stackexchange hermeneutics christianity ...
        for site in sys.argv[2:]:
            mine_stackexchange(site, f"se_{site}")
    elif cmd == "wikipedia":
        for lang in (sys.argv[2:] or ["en", "he"]):
            mine_wikipedia(lang)
    elif cmd == "verify":
        verify(int(sys.argv[2]) if len(sys.argv) > 2 else 300)
    elif cmd == "eval":
        evaluate()
    else:
        print(__doc__)
