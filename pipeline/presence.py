#!/usr/bin/env python3
"""Robust 'is this work on Sefaria?' test, shared by the most-wanted builder.

/api/name returns completion_objects. A work is PRESENT when some ref/book
completion's title begins with the query words (fuzzy per word, to absorb
transliteration: Pri Megadim -> 'Pri Megadim on Yoreh De'ah', Ben Ish Chai ->
'Ben Ish Hai'). Only a PersonTopic/Topic (or an unrelated title) => ABSENT.
"""
import difflib, json, re, time, urllib.parse, urllib.request

REF_TYPES = {"ref", "book"}


def _words(s):
    return [w for w in (re.sub(r"[^a-z]", "", t.lower()) for t in s.split()) if w]


def _wmatch(a, b):
    return a == b or difflib.SequenceMatcher(None, a, b).ratio() >= 0.75


def _title_starts_with(qw, tw):
    if not qw or len(qw) > len(tw):
        return False
    return all(_wmatch(q, t) for q, t in zip(qw, tw))


def check(work, cache=None, delay=0.25):
    if cache is not None and work in cache:
        return cache[work]
    r = {"present": False, "match": None}
    try:
        d = json.loads(urllib.request.urlopen(
            "https://www.sefaria.org/api/name/" + urllib.parse.quote(work), timeout=15).read())
        if d.get("is_ref") and d.get("url"):
            r = {"present": True, "match": d.get("ref")}
        else:
            qw = _words(work)
            for o in (d.get("completion_objects") or []):
                if o.get("type") in REF_TYPES and _title_starts_with(qw, _words(o.get("title", ""))):
                    r = {"present": True, "match": o.get("title")}
                    break
    except Exception as e:
        r = {"present": None, "match": "err:" + str(e)[:30]}
    if cache is not None:
        cache[work] = r
    time.sleep(delay)
    return r


if __name__ == "__main__":
    import sys
    tests = ["Ben Ish Chai", "Birkei Yosef", "Pri Megadim", "Levush", "Shaar Hatziyun",
             "Chatom Sofer", "Meiri", "Chazon Ish", "Yalkut Yosef", "Shevet Halevi",
             "Yabia Omer", "Chelkat Binyamin", "Minchat Shlomo", "Halichot Shlomo",
             "Nitei Gavriel", "Piskei Teshuvot", "Or Letzion", "Yechave Daat"]
    for t in tests:
        r = check(t)
        print(f"  {t:22} {'PRESENT' if r['present'] else 'absent ':8}  {r['match']}")
