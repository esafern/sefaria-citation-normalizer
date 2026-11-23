"""Resolve a raw Anglo-Orthodox citation to a Sefaria URL: propose -> verify.

Generate candidate normalizations with rules.candidates(), ask Sefaria's
/api/name which one is a real reference, cache the answer. The rules never have
to be exactly right; Sefaria is the authority and the cache makes it
deterministic and offline-replayable.

A second pass canonicalizes the tractate/parsha name itself via Sefaria's own
/api/name completions ("Yerushalmi Brachot" -> ask Sefaria what "Brachot"
canonicalizes to -> "Berakhot" -> recompose as "Jerusalem Talmud Berakhot"),
instead of a hand-maintained spelling list: such a list can never keep up with
every Anglo transliteration a writer might use (Brachot/Brachos/B'rachot/...),
but Sefaria's own alt-title data already covers what the rules layer misses.
Ported from rav-shvat-blog's pipeline/sefaria_linker/resolver.py, which had
the same idea but a bug that silently excluded every Tosefta/Mishnah
candidate from ever reaching it (fixed here and there — see INTEGRATION-PLAN.md).
"""
import json
import os
import re
import time
import urllib.parse
import urllib.request

from . import rules
from . import shared_dialect

BASE = "https://www.sefaria.org"

# The renamed corpus-prefix forms rules.candidates() can produce (the
# replacement side of shared_dialect.PREFIXES), longest first so a shorter
# prefix can't shadow a longer one it's a substring of.
_RENAMED_PREFIXES = sorted({repl for _, repl in shared_dialect.PREFIXES}, key=len, reverse=True)


_UNSET = object()


class Cache:
    def __init__(self, path=None):
        self.path = path
        self.data = json.load(open(path)) if path and os.path.exists(path) else {}
        self._dirty = False

    def get(self, k):
        return self.data.get(k)

    def __contains__(self, k):
        return k in self.data

    def set(self, k, v):
        # dict.get's default (None) is indistinguishable from a stored
        # known-miss (also None) -- use a sentinel so setting a *fresh*
        # known-miss actually persists instead of silently no-op'ing (it
        # otherwise never lands in self.data, so every genuinely-unresolved
        # citation gets re-queried against Sefaria on every run, forever).
        if self.data.get(k, _UNSET) != v:
            self.data[k] = v
            self._dirty = True

    def save(self):
        if self.path and self._dirty:
            json.dump(self.data, open(self.path, "w"), ensure_ascii=False, indent=1, sort_keys=True)
            self._dirty = False


def _name(q, timeout=15):
    d = json.loads(urllib.request.urlopen(
        BASE + "/api/name/" + urllib.parse.quote(q), timeout=timeout).read())
    if d.get("is_ref") and d.get("url"):
        return BASE + "/" + d["url"].lstrip("/")
    return None


def _name_candidates(work, limit=5, timeout=15):
    """Candidate canonical titles for a bare work name, best-first: an exact
    ref match, then typed ref completions (skipping AuthorTopic/Topic
    entries, e.g. "Bereshit" the Topic vs "Bereshit Rabbah" the text), then
    bare completion strings as a last resort (older API shape)."""
    d = json.loads(urllib.request.urlopen(
        BASE + "/api/name/" + urllib.parse.quote(work), timeout=timeout).read())
    out = []

    def add(x):
        if x and x not in out:
            out.append(x)

    if d.get("is_ref") and d.get("ref"):
        add(d["ref"])
    for o in (d.get("completion_objects") or []):
        if o.get("type") == "ref":
            add(o.get("title"))
    for c in (d.get("completions") or []):
        add(c)
    return out[:limit]


# Words a canonical title may legitimately drop: connectors and generic
# structural/editorial words that never distinguish one work from another.
# Anything NOT in this set (Tosafot, Mishnah, Midrash, Palagi, YD, Lav, ...)
# carries meaning, and a canonical title that drops it is a different work.
_DROPPABLE = {
    "of", "the", "on", "to", "and", "in", "a",
    "laws", "hilchot", "hilchos", "hilkhot", "hil",
    "sefer", "seifer", "tractate", "masechet", "maseches", "masechta",
    "mesechet", "meseches", "mesechta", "mesechtas", "masekhet",
    "talmud", "bavli", "babylonian", "gemara",
    "note", "notes", "verse", "verses", "chapter", "chap", "ch",
    "introduction", "intro",
    # numbering words: they label the number, they don't pick a section
    # (unlike Lav / Prohibition / responsa, which stay distinctive)
    "mitzvah", "mitzva", "mitvah", "siman", "seif", "no", "number",
    "page", "pg", "daf", "vol", "volume",
}

# Names for the Rambam / Mishneh Torah: any one in the citation is satisfied
# by any one in the canonical title ("Yad, Yesodey Hatorah" -> "Rambam,
# Yesodey haTorah"; "Moses Maimonides, Mishneh Torah, ..." -> "Mishneh Torah,
# ..."). Deliberately NOT satisfied by an unrelated title: "Sefer Hamitzvot of
# Rambam" -> "Sefer Hamitzvot of Rasag" still fails.
_RAMBAM = {"rambam", "maimonides", "moses", "yad", "mishneh"}


def _split_words(s):
    # rejoin a hyphenated/apostrophized article: Ha-Shanah, Ha'Shanah -> HaShanah
    s = re.sub(r"\b(ha|de|ve)[-'’](?=[a-z])", r"\1", s, flags=re.I)
    return re.findall(r"[A-Za-z'’]+", s)


def _word_key(w):
    """Lowercase, drop apostrophes/punctuation and a leading 'ha'/'de' article
    so HaChaim/Hachaim/Chaim and D'Rabbi/DeRabbi compare equal."""
    w = re.sub(r"[^a-z]", "", w.lower())
    return re.sub(r"^(?:ha|de)(?=[a-z]{3})", "", w)


def _skeleton(k):
    """Consonant skeleton for transliteration-insensitive comparison:
    kh/ch/q->k, th->t, Ashkenazi s->t (Kesubos/Ketubot), vowels and
    doubled letters dropped. HaYosher/HaYashar and Brachot/Berakhot agree;
    Bekhorot/Berakhot (bkrt vs brkt) do not."""
    k = k.replace("kh", "k").replace("ch", "k").replace("q", "k").replace("th", "t")
    k = k.replace("sh", "S").replace("s", "t").replace("ph", "f")
    k = k[0] + re.sub(r"[aeiouy]", "", k[1:]) if k else k
    return re.sub(r"(.)\1+", r"\1", k)


def _words_match(a, b):
    """Same word up to transliteration. Short words must match exactly: at
    2-3 letters nothing can tell YD from OC."""
    if a == b:
        return True
    if min(len(a), len(b)) <= 3:
        return False
    if _skeleton(a) == _skeleton(b):
        return True
    from difflib import SequenceMatcher
    return SequenceMatcher(None, a, b).ratio() >= 0.8


def _distinctive(words):
    return [k for w in words if (k := _word_key(w)) and w.lower() not in _DROPPABLE
            and k not in _DROPPABLE]


def _matches_any(k, keys):
    if k in _RAMBAM and _RAMBAM & set(keys):
        return True
    return any(_words_match(k, c) for c in keys if c)


def _keeps_all_words(source, canon):
    """True if `canon` is a safe canonicalization of `source`:
    1. every distinctive word of `source` has a match in `canon` (nothing
       dropped: "Kaf Hachaim Palagi" -> "Kaf HaChayim on Shulchan Arukh" drops
       the author; "Tosfot Avodah Zarah" -> "Avodah Zarah" drops the
       commentary layer; "of Rambam" -> "of Rasag" swaps the author), and
    2. canon's first distinctive word comes from `source` (nothing prefixed:
       "Pirkei Avot, Commentary on" -> "German Commentary on Pirkei Avot" is
       a different work about the cited one). Expansions after the cited
       name are fine ("Kaf Hachaim" -> "Kaf HaChayim on Shulchan Arukh, ...").
    """
    src = _distinctive(_split_words(source))
    can = _distinctive(_split_words(canon))
    if not src or not can:
        return False
    if not all(_matches_any(k, can) for k in src):
        return False
    return _matches_any(can[0], src)


def _resolve_via_canonicalization(cands, polite):
    """Second-pass fallback: split a candidate into (corpus prefix, work
    head, numbers), ask Sefaria to canonicalize just the head, recompose."""
    for cand in cands:
        m = re.match(r"^(?P<head>.*?[A-Za-z])\s+(?P<nums>\d[\d:,.\s\-ab]*)$", cand)
        if not m:
            continue
        head, nums = m.group("head"), m.group("nums").strip()
        if re.search(r"\d", head):
            # A number inside the work name ("Foundations of Torah 5 Rambam 1")
            # means the locator is split; recomposing with only the trailing
            # number would point at the wrong chapter.
            continue
        prefix = ""
        for pre in _RENAMED_PREFIXES:
            if head.startswith(pre):
                prefix, head = pre, head[len(pre):]
                break
        else:
            # No recognized (already-renamed) prefix found. If `head` still
            # carries a raw, un-renamed corpus qualifier ("Yerushalmi
            # Brachot"), a renamed sibling candidate exists elsewhere in
            # `cands` and gets processed correctly on its own turn instead;
            # canonicalizing this one whole would silently drop the
            # qualifier and risk a mislink (Yerushalmi Brachot -> Mishnah
            # Berakhot). This check must come after (not instead of) the
            # loop above: Tosefta/Mishnah/Mishna's PREFIXES rewrite only
            # normalizes a comma, so their "already renamed" and "still
            # raw" forms are the same string — checking this first would
            # wrongly exclude them too.
            if any(re.search(pat, cand, re.I) for pat, _ in shared_dialect.PREFIXES):
                continue
        try:
            canons = _name_candidates(head)
        except Exception:
            return None
        for canon in canons:
            if not canon or canon == head:
                continue
            if not _keeps_all_words(head, canon):
                continue  # completion drops part of the citation: a different work
            try:
                url = _name(f"{prefix}{canon} {nums}")
            except Exception:
                return None
            if polite:
                time.sleep(polite)
            if url:
                return url
    return None


def _name_ref_completions(work, limit=10, timeout=15):
    """Like _name_candidates, but keeps each completion's canonical `key`
    (not just its display `title`) — needed to resolve a target whose
    canonical form isn't textually close to the query."""
    d = json.loads(urllib.request.urlopen(
        BASE + "/api/name/" + urllib.parse.quote(work) + f"?limit={limit}",
        timeout=timeout).read())
    return [o for o in (d.get("completion_objects") or [])
            if o.get("type") == "ref" and o.get("key")]


def _normalize_word(w):
    return re.sub(r"[.'’\-,]", "", w).lower()


def _resolve_bare_via_canonicalization(cands, orig_citation, polite):
    """Third-pass fallback for candidates with NO trailing locator (a bare
    work name: "Kesubos", "Tosefta to Tractate Chagigah") -- the regex-based
    canonicalization above only fires on a head+numbers shape. Ask Sefaria
    for ref completions and accept one only if every word of its canonical
    `key` is already traceable, as a normalized whole-word match, to
    something the user actually wrote. Deliberately stricter than the
    locator-bearing fallback: with no page number to anchor on, a wrong
    accept here mislinks a whole book, not just widens a page match.

    This will NOT catch a genuine spelling correction ("Kesubos" ->
    "Ketubot" needs an actual letter change: Ashkenazi soft-tav as "s" vs.
    Sephardi/modern "t" -- not just reformatting). That's a known, disclosed
    gap, not a bug here: closing it needs either a hand-typed alias (this
    project deliberately rejects that shape, see HANDOFF.md) or a bounded
    phonetic-substitution generator (real mislink-risk surface of its own,
    not attempted). It does catch legitimate reformatting: connector words
    ("Tosefta to Tractate Chagigah" -> "Tosefta Chagigah"), hyphenation
    ("Rosh Ha-Shanah" -> "Rosh Hashanah"), and an unstripped prefix
    ("Mesechet Rosh Hashanah" -> "Rosh Hashanah").
    """
    orig_tokens = {_normalize_word(w) for w in re.findall(r"[A-Za-z'’\-.]+", orig_citation)}
    for cand in cands:
        if re.search(r"\d", cand):
            continue  # has a locator; handled by _resolve_via_canonicalization
        try:
            refs = _name_ref_completions(cand)
        except Exception:
            return None
        for o in refs:
            key = o["key"]
            words = re.findall(r"[A-Za-z'’\-.]+", key)
            if not words or not all(_normalize_word(w) in orig_tokens for w in words):
                continue
            if not _keeps_all_words(cand, key):
                continue  # same guard as pass 2, in the other direction
            try:
                url = _name(key)
            except Exception:
                return None
            if polite:
                time.sleep(polite)
            if url:
                return url
    return None


def resolve(citation, cache=None, online=True, polite=0.0):
    """Return a Sefaria URL for `citation`, or None. Cache holds citation->url
    (or None for a known miss)."""
    citation = citation.strip()
    if cache is not None and citation in cache:
        return cache.get(citation)
    url = None
    if online:
        cands = rules.candidates(citation)
        for cand in cands:
            try:
                url = _name(cand)
            except Exception:
                url = None
                break
            if polite:
                time.sleep(polite)
            if url:
                break
        if not url:
            url = _resolve_via_canonicalization(cands, polite)
        if not url:
            url = _resolve_bare_via_canonicalization(cands, citation, polite)
    if cache is not None:
        cache.set(citation, url)
    return url
