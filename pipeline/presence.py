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


# Leading structural words on a Sefaria title that a prefix-match can't see past
# ("Teshuvot Maharil", "Responsa Rav Pealim"). Stripped so the work name aligns.
_TITLE_PREFIX = re.compile(
    r"^(?:Responsa|Teshuvot|Teshuvos|Sefer|Commentary of[^,]*? on|Commentary on)\s+", re.I)


def _wmatch(a, b, strict=False):
    if a == b:
        return True
    r = difflib.SequenceMatcher(None, a, b).ratio()
    if not strict:
        return r >= 0.75
    # A single distinctive token (an abbreviated work name): allow transliteration
    # length-diffs (Smak/Semak) but reject equal-length letter substitutions, which
    # mark a *different* work (Maharsham vs Maharshal vs Maharshag).
    return r >= (0.95 if len(a) == len(b) else 0.8)


def _title_starts_with(qw, tw):
    if not qw or len(qw) > len(tw):
        return False
    strict = len(qw) == 1
    return all(_wmatch(q, t, strict) for q, t in zip(qw, tw))


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
                if o.get("type") not in REF_TYPES:
                    continue
                title = o.get("title", "")
                stripped = _TITLE_PREFIX.sub("", title)
                if (_title_starts_with(qw, _words(title))
                        or (stripped != title and _title_starts_with(qw, _words(stripped)))):
                    r = {"present": True, "match": title}
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
