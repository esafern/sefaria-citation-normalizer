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
Ported from the private blog repo's pipeline/sefaria_linker/resolver.py, which had
the same idea but a bug that silently excluded every Tosefta/Mishnah
candidate from ever reaching it (fixed here and there — see docs/notes/INTEGRATION-PLAN.md).
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

from . import __version__  # noqa: E402

# Identify ourselves to Sefaria's API (their etiquette, and so they can reach us).
USER_AGENT = f"citenorm/{__version__} (+https://github.com/esafern/sefaria-citation-normalizer)"


def _cache_dir():
    """Where downloaded data lives: $CITENORM_CACHE, else ~/.cache/citenorm."""
    d = os.environ.get("CITENORM_CACHE") or os.path.join(os.path.expanduser("~"), ".cache", "citenorm")
    os.makedirs(d, exist_ok=True)
    return d


def _get_json(path, timeout=15):
    """GET a Sefaria API path (e.g. "/api/name/Berakhot 2a") as JSON, with our User-Agent."""
    req = urllib.request.Request(BASE + path, headers={"User-Agent": USER_AGENT})
    return json.loads(urllib.request.urlopen(req, timeout=timeout).read())

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
    d = _get_json("/api/name/" + urllib.parse.quote(q), timeout=timeout)
    if d.get("is_ref") and d.get("url"):
        return BASE + "/" + d["url"].lstrip("/")
    return None


def _name_candidates(work, limit=5, timeout=15):
    """Candidate canonical titles for a bare work name, best-first: an exact
    ref match, then typed ref completions (skipping AuthorTopic/Topic
    entries, e.g. "Bereshit" the Topic vs "Bereshit Rabbah" the text), then
    bare completion strings as a last resort (older API shape)."""
    d = _get_json("/api/name/" + urllib.parse.quote(work), timeout=timeout)
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
    # ("laws"/"hilchot" are NOT droppable: "Hilchot Shabbat 2:3" -> "Shabbat 2:3" would
    # make Sefaria read Mishnah Shabbat 2:3. Hilchot says "a halachic code".)
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
# On the title side only these count: "Yad." alone is Sefaria's abbreviation for
# tractate Yadayim, so it must not satisfy "Rambam".
_RAMBAM_TITLE = {"rambam", "maimonides", "mishneh"}


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
    k = re.sub(r"(?<=.{3})h$", "", k)          # Metziah/Metzia, Rabbah/Rabba
    k = k.replace("tz", "z").replace("ts", "z")  # Metzia/Metsia
    k = k.replace("kh", "k").replace("ch", "k").replace("q", "k").replace("th", "t")
    k = k.replace("sh", "S").replace("s", "t").replace("ph", "f").replace("v", "b")  # bet/vet
    k = k[0] + re.sub(r"[aeiouy]", "", k[1:]) if k else k
    return re.sub(r"(.)\1+", r"\1", k)


def _translit(k):
    """Consonant skeleton of a word key for comparing Hebrew transliterations.
    Merges only genuine variants: tav as s or t (Kesubos/Ketubot), tz = ts, sh,
    th = t, ph = f, v = b (bet/vet), q = k, ch = kh, and a NON-initial k = ch
    (Berakoth/Berakhot; but Kallah != Challah: kaf vs chet). A y before a vowel is
    a consonant (Kilayim != Kelim). Vowels are compared separately (_vowel_groups)."""
    k = re.sub(r"(?<=[aeiou])h$", "", k)                 # final h after a vowel
    k = k.replace("tz", "z").replace("ts", "z").replace("sh", "S").replace("kh", "C")
    k = k.replace("ch", "C").replace("th", "t").replace("ph", "f").replace("q", "k")
    k = k.replace("w", "v").replace("v", "b").replace("c", "k").replace("s", "t")
    k = k.replace("h", "C")                              # academic h for chet (Bahya/Bachya)
    k = k[:1] + k[1:].replace("k", "C")                  # non-initial k = chaf
    out = []
    for i, ch in enumerate(k):
        nxt = k[i + 1] if i + 1 < len(k) else ""
        # y is a consonant before a/e/o/u (Vayera, Kilayim's "ya"... ), a vowel otherwise
        # (Chayim = Chaim)
        vowel = ch in "aeiou" or (ch == "y" and not (nxt and nxt in "aeou"))
        if not vowel and (not out or out[-1] != ch):
            out.append(ch)
    return "".join(out), None


def _vowel_groups(k):
    """Vowel classes per gap between consonants, e-class dropped."""
    k = re.sub(r"(?<=[aeiou])h$", "", k)
    groups, cur = [], ""
    for i, ch in enumerate(k):
        nxt = k[i + 1] if i + 1 < len(k) else ""
        is_v = ch in "aeiou" or (ch == "y" and not (nxt and nxt in "aeou"))
        if is_v:
            cur += ch
        elif cur:
            groups.append(cur)
            cur = ""
    if cur:
        groups.append(cur)
    out = []
    for g in groups:
        g = g.replace("ei", "e").replace("ey", "e")            # tzere: same class as e (dropped)
        g = g.replace("ee", "i").replace("oo", "u").replace("ou", "u").replace("y", "i")
        cls = "".join(sorted({"a": "A", "o": "A", "u": "U", "i": "I"}.get(c, "") for c in g if c != "e"))
        cls = "".join(dict.fromkeys(cls))
        if cls:
            out.append(cls)
    return out


def _words_match(a, b):
    """Same word up to Hebrew transliteration (see _translit). Short words must
    match exactly. The ratio fallback is strict (0.9, same first letter): a
    looser one matched Megillah/Me'ilah and Orlah/Torah."""
    if a == b:
        return True
    if min(len(a), len(b)) <= 3:
        return False
    ca, _ = _translit(a)
    cb, _ = _translit(b)
    if ca == cb and _vowel_groups(a) == _vowel_groups(b):
        return True
    # Fallback for vowel-only differences (Tosfot/Tosafot): the consonants must be
    # identical. A ratio alone accepted Vaera/Vayera (different parashot).
    from difflib import SequenceMatcher
    return (ca == cb and a[0] == b[0] and min(len(a), len(b)) >= 5
            and SequenceMatcher(None, a, b).ratio() >= 0.85)


# What a canonical title may ADD that the citation lacks: connectors only.
# (The citation may contain any _DROPPABLE word the title lacks, but a title
# that adds "Introduction" or "Volume" has picked a section.)
# ("Sefer" is NOT here: "Sefer Yesodei HaTorah" is a different book from the
# Rambam's "Yesodei HaTorah".)
_CANON_MAY_ADD = {"of", "the", "on", "to", "and", "in", "a", "talmud", "bavli"}


def _distinctive(words):
    out = []
    for w in words:
        if w in ("I", "II", "III", "IV"):   # I Samuel vs II Samuel: meaningful
            out.append(w.lower())
            continue
        k = _word_key(w)
        if k and w.lower() not in _DROPPABLE and k not in _DROPPABLE:
            out.append(k)
    return out


def _book_group(k):
    """The English book title for a Hebrew book-name word key, else None."""
    from .rules import BOOKS
    for pat, eng in BOOKS:
        if " " not in eng and re.fullmatch(pat.lower().replace("'", ""), k):
            return eng.lower()
    return k if any(k == e.lower() for _, e in BOOKS) else None


def _matches_any(k, keys, keys_are_title=True):
    """Does citation/title word k match any of keys? The Rambam name group is
    asymmetric: a citation's "Yad"/"Moses" may stand for the Rambam, but a title's
    "Yad." is tractate Yadayim, so only rambam/maimonides/mishneh count on the
    title side."""
    if keys_are_title:
        if k in _RAMBAM and _RAMBAM_TITLE & set(keys):
            return True
    elif k in _RAMBAM_TITLE and _RAMBAM & set(keys):
        return True
    bg = _book_group(k)
    if bg and any(_book_group(c) == bg for c in keys if c):
        return True
    return any(_words_match(k, c) for c in keys if c)


def _keeps_all_words(source, canon):
    """True if `canon` is a safe canonicalization of `source`:
    1. every distinctive word of `source` has a match in `canon` (nothing
       dropped: "Kaf Hachaim Palagi" -> "Kaf HaChayim on Shulchan Arukh" drops
       the author; "Tosfot Avodah Zarah" -> "Avodah Zarah" drops the
       commentary layer; "of Rambam" -> "of Rasag" swaps the author), and
    2. every distinctive word of `canon` has a match in `source` (nothing
       added). An added word means Sefaria's suggestion picked a section or
       sub-work the writer never named: "Moreh Nevuchim" -> "Guide for the
       Perplexed, Prefatory Remarks"; "Aruch Hashulchan 529:4" -> "Arukh
       HaShulchan, Yoreh De'ah"; "Shmuel" -> "I Samuel"; "Pirkei Avot,
       Commentary on" -> "German Commentary on Pirkei Avot". Choosing one is
       guessing, so the citation is left unlinked instead.
    So canonicalization may change spelling and casing, never meaning.
    """
    # Sefaria titles some Torah commentaries "X on Torah, Genesis"; that's the
    # same thing as "X on Genesis", not an added word.
    canon = re.sub(r"\bon Torah, ", "on ", canon)
    src = _distinctive(_split_words(source))
    can = _distinctive(_split_words(canon))
    if not src or not can:
        return False
    if not all(_matches_any(k, can) for k in src):
        return False
    # same order: "Aruch Hashulchan" -> "Shulchan Aruch" is a different book
    pos = [next(i for i, c in enumerate(can) if _matches_any(k, [c])) for k in src]
    if pos != sorted(pos):
        return False
    # no added numbers: "..., part" -> "..., Part 1" picks a part
    if set(re.findall(r"\d+", canon)) - set(re.findall(r"\d+", source)):
        return False
    # Sefaria titles some Mishneh Torah sections only by their full compound
    # name ("Rambam, Hilchot Tefilah and Birkat Kohanim"); a writer citing the
    # first half ("Hilchot Tfila") means the same section. Allow a trailing
    # "and ..." clause for that title family only.
    if re.match(r"^Rambam, Hilchot ", canon) and re.search(r"\s(?:and|u|v')\s?\S", canon):
        canon = re.split(r"\s(?:and)\s", canon)[0]
    src_all = [_word_key(w) for w in _split_words(source)]
    canon_words = _split_words(canon)
    added = [w for i, w in enumerate(canon_words)
             if (w.lower() not in _CANON_MAY_ADD
                 or (w.lower() in ("talmud", "bavli") and i > 0))
             and not _matches_any(_word_key(w) if w not in ("I", "II", "III", "IV") else w.lower(),
                                  src_all + src, keys_are_title=False)]
    return not added


_ROMAN_PART = re.compile(r"(?:^|[\s_,])(I{1,3}|IV)(?=[\s_,.]|$)")


def _adds_part_numeral(source, url):
    """Sefaria alt titles sometimes pick an edition/part for you: "Noda
    B'Yehudah, Yoreh Deah" resolves to "Noda BiYehudah I, ..." (Mahadura
    Kamma). If the resolved title carries a part numeral the citation never
    wrote, the part was guessed."""
    title = urllib.parse.unquote(url.split("sefaria.org/", 1)[-1]).split(".")[0]
    return bool(_ROMAN_PART.search(title)) and not _ROMAN_PART.search(" " + source + " ")


# A number right after one of these words is a sub-locator (a footnote, a se'if
# katan), not the work's top-level section: "Mishna Berurah in note 48" is note 48
# of some siman, not siman 48. Canonicalizing such a head would drop the word and
# promote the number.
_SUBLOCATOR_TAIL = re.compile(
    r"\b(?:notes?|footnotes?|fn|n\.|s\.?\s?k\.?|s\"k|se'?if\s+katan|seif\s+katan|comment|"
    r"para(?:graph)?|\u00b6)\s*$", re.I)


def _resolve_via_canonicalization(cands, polite):
    """Second-pass fallback: split a candidate into (corpus prefix, work
    head, numbers), ask Sefaria to canonicalize just the head, recompose."""
    for cand in cands:
        m = re.match(r"^(?P<head>.*?[A-Za-z])\s+(?P<nums>\d[\d:,.\s\-ab]*)$", cand)
        if not m:
            continue
        head, nums = m.group("head"), m.group("nums").strip()
        if _SUBLOCATOR_TAIL.search(head):
            continue
        if re.search(r"\d", head):
            # A number inside the work name ("Foundations of Torah 5 Rambam 1")
            # means the locator is split; recomposing with only the trailing
            # number would point at the wrong chapter.
            continue
        prefix = ""
        full_head = head
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
        # Try the head without its corpus prefix, then the whole head: "Mishna
        # Brura" must not be canonicalized as the Mishnah of tractate "Brura".
        attempts = [(prefix, head)] + ([("", full_head)] if prefix else [])
        for pre, hd in attempts:
            url = _canonicalize_and_resolve(pre, hd, nums, polite)
            if url == "ERROR":
                return None
            if url:
                return url
    return None


def _canonicalize_and_resolve(prefix, head, nums, polite):
    try:
        canons = _name_candidates(head)
    except Exception:
        return "ERROR"
    if True:
        for canon in canons:
            if not canon or canon == head:
                continue
            if not _keeps_all_words(head, canon):
                continue  # completion drops part of the citation: a different work
            try:
                url = _name(f"{prefix}{canon} {nums}")
            except Exception:
                return "ERROR"
            if polite:
                time.sleep(polite)
            if url and _adds_part_numeral(head, url):
                continue
            if url:
                return url
    return None


def _name_ref_completions(work, limit=10, timeout=15):
    """Like _name_candidates, but keeps each completion's canonical `key`
    (not just its display `title`) — needed to resolve a target whose
    canonical form isn't textually close to the query."""
    d = _get_json("/api/name/" + urllib.parse.quote(work) + f"?limit={limit}", timeout=timeout)
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
    project deliberately rejects that shape, see docs/notes/HANDOFF.md) or a bounded
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


def _hilchot_is_ambiguous(citation, url):
    """rules.candidates() rewrites a bare "Hilchot X n:m" to the Rambam's
    "Rambam, Hilchot X". That's only safe if no OTHER work is called "Hilchot
    X": "Hilchot Talmud Torah 3:7" is also the Baal HaTanya's Hilkhot Talmud
    Torah. If the bare head (spelling-matched) is a non-Rambam title in
    Sefaria's completions, the citation is ambiguous: leave it unlinked."""
    if not url:
        return False
    m = re.match(r"^\s*(Hil(?:chot|chos|khot|khos|\.)\s+.+?)\s*\(?\d", citation, re.I)
    if not m or re.search(r"\b(Rambam|Mishneh Torah|Mishnah Torah|Maimonides|Yad)\b", citation, re.I):
        return False
    head = m.group(1)
    if "Mishneh_Torah" not in url:
        # We picked another work's "Hilchot X"; ambiguous if the Rambam has one too.
        sec = re.sub(r"^\s*Hil(?:chot|chos|khot|khos|\.)\s+", "", head, flags=re.I)
        for t in _vocab_matches("Rambam, Hilchot " + sec)[:4]:
            try:
                u = _name(t)
            except Exception:
                return True
            if u and "Mishneh_Torah" in u:
                return True
        return False
    try:
        titles = [o.get("title", "") for o in _name_ref_completions(head, limit=15)]
    except Exception:
        return True   # can't check, so don't guess
    titles += _vocab_matches(head)
    seen = set()
    for t in titles:
        if t in seen or re.match(r"^(Rambam|Mishneh Torah)\b", t) or not _keeps_all_words(head, t):
            continue
        seen.add(t)
        # same name; does it belong to a different work? (a lowercase or variant
        # alt title of the Mishneh Torah itself doesn't count)
        try:
            other = _name(t[:1].upper() + t[1:])
        except Exception:
            return True
        if other and "Mishneh_Torah" not in other:
            return True
        if len(seen) >= 6:
            break
    return False


# --------------------------------------------------------------------------
# Vocabulary-anchored pass ("tier 1.5"): match the work name against Sefaria's
# full title list instead of relying on /api/name's top-N autocomplete ranking,
# which often omits the right title ("Rambam, Hilchot Eidus" never surfaces
# "Rambam, Hilchot Edut"). Same _keeps_all_words guard; every pick is still
# verified live by _name().
def _titles_path():
    return os.path.join(_cache_dir(), "titles.json")
_TITLE_INDEX = None


def _title_index():
    """first-distinctive-word skeleton -> [titles]. Fetches /api/index/titles once
    (cached next to this file, gitignored); returns {} if offline."""
    global _TITLE_INDEX
    if _TITLE_INDEX is not None:
        return _TITLE_INDEX
    try:
        path = _titles_path()
        if not os.path.exists(path):
            json.dump(_get_json("/api/index/titles", timeout=60), open(path, "w"), ensure_ascii=False)
        titles = json.load(open(path))["books"]
    except Exception:
        _TITLE_INDEX = {}
        return _TITLE_INDEX
    idx = {}
    for t in titles:
        if "<" in t or re.search(r"[-\u2010-\u2015]", t):
            continue  # markup / hyphenated titles can't resolve anyway
        words = _distinctive(_split_words(re.sub(r"\bon Torah, ", "on ", t)))
        if words:
            idx.setdefault(_skeleton(words[0]), []).append(t)
    _TITLE_INDEX = idx
    return idx


def _vocab_matches(head):
    words = _distinctive(_split_words(head))
    if not words:
        return []
    keys = {_skeleton(words[0])}
    if words[0] in _RAMBAM:
        keys |= {_skeleton(w) for w in _RAMBAM}
    bg = _book_group(words[0])
    if bg:
        keys.add(_skeleton(bg))
    out = []
    for k in keys:
        for t in _title_index().get(k, []):
            if _keeps_all_words(head, t):
                out.append(t)
    return out


def _resolve_via_vocabulary(cands, polite):
    """For each head+locator candidate, find titles in Sefaria's list that are the
    same name up to spelling/casing. Accept only if every such title that
    resolves lands on the same ref (two different works -> ambiguous -> skip)."""
    for cand in cands:
        m = re.match(r"^(?P<head>.*?[A-Za-z])\s+(?P<nums>\d[\d:,.\s\-ab]*)$", cand)
        if not m or re.search(r"\d", m.group("head")) or _SUBLOCATOR_TAIL.search(m.group("head")):
            continue
        head, nums = m.group("head"), m.group("nums").strip()
        titles = _vocab_matches(head)[:8]
        if not titles:
            continue
        hits = {}
        for t in titles:
            try:
                url = _name(f"{t} {nums}")
            except Exception:
                return None
            if polite:
                time.sleep(polite)
            if url and not _adds_part_numeral(head, url):
                hits[url] = t
        if len(hits) == 1:
            return next(iter(hits))
        # >1 distinct refs: genuinely ambiguous name, leave it
    return None


_SECTION_NAMES = re.compile(r"Orach_Ch|Yoreh_De|Even_HaEzer|Choshen_Mishpat", re.I)
_SECTION_IN_TEXT = re.compile(
    r"\b(O\.?\s?C[h.]?|O\"[CH]|OC|OH|Or(?:ach|ah)?\s*Ch?a[iy]+m|Y\.?\s?D|Yo?\"D|YD|Yoreh|"
    r"E\.?\s?H|E\"H|EH|Even|Ev\.?\s?H|C\.?\s?M|Ch?\"M|CM|Choshen|Hoshen)\b", re.I)


def _guessed_something(citation, url):
    """Sefaria (or one of its alt titles) filled in something the citation never
    said. Reject such results; choosing is guessing.
      - a Talmud amud: "Brakhot 11:13" -> Berakhot 11a:13, "Megilla 9:22" -> 9a:22
        (the citation has no a/b at all, the result has one)
      - a Shulchan Arukh section: "Kaf HaHayim 92:8" -> the Orach Chayim volume,
        though Kaf HaChayim also covers Yoreh De'ah (the citation names no section)"""
    path = urllib.parse.unquote(url.split("sefaria.org/", 1)[-1])
    if re.search(r"\.\d+[ab](?:[.\-]|$)", path) and not re.search(r"\d\s*[ab]\b|\bdaf\b|\bamud\b", citation, re.I):
        return True
    title = path.split(".")[0]
    if _SECTION_NAMES.search(title) and not _SECTION_IN_TEXT.search(citation):
        return True
    return False


CONVENTIONS = ("common", "strict")

_BARE_SECTION = re.compile(
    r"^\s*(?:O\.?\s?C[h.]?|O\"[CH]|OC|OH|Or(?:ach|ah)?\s*Ch?a[iy]+m|Y\.?\s?D\.?|Yo?\"D|YD|Yoreh\s+De'?ah|"
    r"E\.?\s?H\.?|E\"H|EH|Even\s+Ha-?\s?Ezer|C\.?\s?M\.?|Ch?\"M|CM|Choshen\s+Mishpat)\b", re.I)


def _convention_used(citation, url):
    """Which ambiguity convention (if any) a result depends on. Sefaria's own
    aliases and Ref() behavior answer these the "common" way; "strict" mode
    declines them. Measured on ~19k web-mined citations (docs/notes/HANDOFF.md):
      bare_section   "YD 289" -> Shulchan Arukh (87% of writers meant that; 13% a
                     different work on that section)
      mishnah        "Kilayim 9:3" -> Mishnah (some meant the Yerushalmi or the
                     Mishneh Torah section of the same name)
      short_alias    "Ber 9" -> Berakhot via a 2-3 letter alias (writers also use
                     "Ber." for Bereshit)
    """
    path = urllib.parse.unquote(url.split("sefaria.org/", 1)[-1])
    if _BARE_SECTION.match(citation) and path.startswith("Shulchan_Arukh"):
        return "bare_section"
    if path.startswith("Mishnah_") and not re.search(r"mishn|\bM\.\s", citation, re.I):
        return "mishnah"
    work = re.split(r"\s*\(?\d", citation.strip(), maxsplit=1)[0]
    tokens = re.findall(r"[A-Za-z]+", work)
    if len(tokens) == 1 and len(tokens[0]) <= 3 and '"' not in work:
        return "short_alias"
    return None


def resolve(citation, cache=None, online=True, polite=0.2, conventions="common"):
    """Return a Sefaria URL for `citation`, or None.

    conventions: "common" (default) follows Sefaria's own conventions for three
    ambiguous patterns; "strict" leaves them unlinked (see _convention_used).
    The cache holds the common answer (citation -> url, None for a known
    miss); strict mode is applied on top, so one cache serves both."""
    if conventions not in CONVENTIONS:
        raise ValueError(f"conventions must be one of {CONVENTIONS}")
    url = _resolve_common(citation, cache=cache, online=online, polite=polite)
    if url and conventions == "strict" and _convention_used(citation.strip(), url):
        return None
    return url


def _resolve_common(citation, cache=None, online=True, polite=0.2):
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
        if not url:
            url = _resolve_via_vocabulary(cands, polite)
        if url and _hilchot_is_ambiguous(citation, url):
            url = None
        if url and _guessed_something(citation, url):
            url = None
    if cache is not None:
        cache.set(citation, url)
    return url
