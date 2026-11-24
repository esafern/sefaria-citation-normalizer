"""Deterministic transformation rules for Anglo-Orthodox Torah citations.

Each rule is a *candidate generator*: given a raw citation it yields plausible
normalized forms. It never has to be exactly right — the resolver proposes every
candidate to Sefaria's /api/name and keeps the first that resolves. This is why
approximate rules work: over-generation is cheap, Sefaria is the oracle.

The families and their weights come from a measured corpus (see PROVENANCE): of
~107 verified `raw -> Sefaria ref` pairs mined from Sefaria source sheets, about
half collapse into the families below; the other half is irreducible knowledge
(alternate names, English-translated titles, Hebrew) that no rule captures and
that belongs to the LLM/SLM tier.
"""
import re

from . import shared_dialect

PROVENANCE = "citation corpus mined from Sefaria source sheets; see data/citation_dataset.json"

# Prefixes / editions / structural words to strip from the front.
_STRIP_PREFIX = re.compile(
    r"^\s*(?:ArtScroll|Artscroll|Bomberg|Soncino|Koren|Steinsaltz|"
    r"William Davidson(?: Talmud)?|Vilna|Completes|Study Sheet|Source Sheet|"
    r"B\.?\s*Talmud|Babylonian Talmud|Talmud Bavli|Bavli|Talmud|"
    r"(?:The\s+)?Gem[ao]r[ao]h?(?: of)?|Gemera|"
    r"Mesechtas?|Mesechet|Meseches|Masechet|Masekhet|Masechta?|Maseches|Tractate|Seifer|Sefer)\s+",
    re.I)

# Words that may sit outside a parenthesized citation without changing what
# it refers to: "Talmud (Chagiga 13b:14)" == "Chagiga 13b:14".
_GENERIC_OUTER = {"talmud", "gemara", "bavli", "babylonian", "b", "see", "cf"}

# Trailing editorial noise: notes, s.v., page/verse tails, Hebrew dibur-hamatchil.
_STRIP_TAIL = re.compile(
    r"(?:,?\s*note[s]?\s+\d+.*"
    r"|\s*s\.?v\.?.*"
    r"|\s*\(sources?\s+[\d\- ]+\)"
    r"|\s*[֐-׿].*"           # a Hebrew tail (commentary quote); apostrophes kept (M'lachim)
    r"|\s+\d+\s*$)?$")   # trailing NOTE number ("15b 4"); space required so ":3" segments survive

# Word-final Ashkenazi / academic transliteration endings -> Sefaria's -ot form.
_ENDINGS = [("oth", "ot"), ("os", "ot"), ("us", "ut"), ("ois", "ot")]

# Small spelling swaps seen repeatedly. Tractate-name variants live in
# shared_dialect.TRACTATE_ALIASES instead (general dialect knowledge, not
# specific to this repo's candidate-generation strategy).
_SPELLING = [
    (r"\bPirke\b", "Pirkei"), (r"\bd'?e?[- ]?(?:Rebb?i|Rabb?i)\b", "DeRabbi"),
    (r"\bNoss?on\b", "Natan"), (r"\bNassan\b", "Natan"),
    (r"\bDerekh\b", "Derech"), (r"\bShul[hk]han\b", "Shulchan"), (r"\bShulkhan\b", "Shulchan"),
    (r"\bShemos\b", "Exodus"), (r"\bDevorim\b", "Deuteronomy"),
    (r"\bOlas\b", "Olat"), (r"\bChovos\b", "Chovot"),
    (r"\bShabbos\b", "Shabbat"), (r"\bToras\b", "Torat"),
    (r"\bHilchos\b", "Hilchot"), (r"\bTumas\b", "Tumat"),
    (r"\bNathan\b", "Natan"),
]

_ROMAN = {"i": 1, "v": 5, "x": 10, "l": 50, "c": 100}


def _roman_to_int(s):
    s = s.lower()
    if not re.fullmatch(r"[ivxlc]+", s):
        return None
    total, prev = 0, 0
    for ch in reversed(s):
        v = _ROMAN[ch]
        total += -v if v < prev else v
        prev = max(prev, v)
    return total


# Hebrew/transliterated Tanakh book names -> Sefaria's English titles. A
# bounded list (the 24 books), not an open-ended spelling tail, so it's the
# acceptable kind of table. Deliberately omitted: Shoftim (also a parasha in
# Deuteronomy, so "Shoftim 12" is ambiguous), and Shmuel / Melachim / Divrei
# HaYamim, which split into I/II and can't be decided from the name alone.
# Torah books are safe even though they double as parasha names: every parasha
# lies inside its book, so chapter:verse means the same thing either way.
BOOKS = [
    (r"B'?e?r[ae]?['e]?i?sh(?:i|ee)?[ts]", "Genesis"),
    (r"Sh'?e?mo[ts]", "Exodus"),
    (r"Vayi[kq]ra", "Leviticus"),
    (r"B[ae]-?midbar", "Numbers"),
    (r"D'?e?v[ao]rim", "Deuteronomy"),
    (r"Yehoshua", "Joshua"),
    (r"Y'?e?sha[iy]ah?u?", "Isaiah"),
    (r"Yirm[ie]yahu?", "Jeremiah"),
    (r"Y'?e?[ch]?h?ezkel", "Ezekiel"),
    (r"Hoshea", "Hosea"), (r"Yoel", "Joel"), (r"Ovadi?y?ah?", "Obadiah"),
    (r"Yonah?", "Jonah"), (r"Mich?ah?", "Micah"), (r"Nachum", "Nahum"),
    (r"Chavakuk", "Habakkuk"), (r"Tz'?e?fan[iy]ah?", "Zephaniah"),
    (r"Chaggai", "Haggai"), (r"Z'?e?char[iy]ah?u?", "Zechariah"),
    (r"T'?e?h?ill?im", "Psalms"), (r"Mishle[iy]?", "Proverbs"),
    (r"Iyy?ov", "Job"), (r"Shir Ha-?[Ss]hirim", "Song of Songs"),
    (r"Eic?hah?|Echah?", "Lamentations"), (r"[KQ]oh[ae]le[ts]", "Ecclesiastes"),
    (r"Nech[ae]m[iy]ah?", "Nehemiah"),
]


def _strip_tail(s):
    """Strip editorial tails (notes, s.v., footnote numbers), but never the
    only number: "Megillah 15b 4" -> "Megillah 15b", while "Yalkut Shimoni
    1046" stays (stripping it lets Sefaria pick a default section)."""
    t = re.sub(_STRIP_TAIL, "", s).strip()
    return t if re.search(r"\d", t) or not re.search(r"\d", s) else s


def _numbers_to_colon(s):
    s = re.sub(r"(\d)\s*,\s*(\d)", r"\1:\2", s)
    return re.sub(r"(?<=\s)(\d+)\.(\d+)\b", r"\1:\2", s)   # "Hil. Melachim 11.1" -> 11:1


def candidates(citation):
    """Yield normalized candidate strings, most-promising first. The original is
    always first, so anything Sefaria already understands costs nothing."""
    out, seen = [], set()
    citation = citation.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')

    def add(s):
        s = re.sub(r"\s+", " ", s or "").strip(" .,;:-")
        if s and s not in seen:
            seen.add(s)
            out.append(s)

    add(citation)
    # Stray brackets inside a locator ("I Chronicles 1:]43-54"): clean them up
    # front so the precise form is tried before any truncated one.
    if re.search(r"[\[\]{}]", citation):
        citation = re.sub(r"\s*[\[\]{}]\s*", lambda m: " " if m.group(0).strip() != m.group(0) else "", citation)
        add(citation)
    add(_numbers_to_colon(citation))

    base = citation
    # split a concatenated edition prefix: "ArtScrollBava Metzia" -> "ArtScroll Bava Metzia"
    base = re.sub(r"\b(ArtScroll|Artscroll)(?=[A-Z])", r"\1 ", base)
    # leading "N - " enumerations ("2 - Oral Torah Tur, ...")
    base = re.sub(r"^\s*\d+\s*[-.)]\s*(?:Oral Torah\s+)?", "", base)
    # "Mishnah of (Tractate) X" -> "Mishnah X". The word "Mishnah" is what
    # separates Mishnah Chagigah from Bavli Chagigah, so it must be kept, not
    # stripped like an edition prefix (stripping it mislinked to the Bavli).
    base = re.sub(r"^\s*Mishnah? of (?:Tractate\s+)?", "Mishnah ", base, flags=re.I)
    stripped = base
    for _ in range(3):  # peel stacked prefixes ("Artscroll Masechet ...")
        nxt = _STRIP_PREFIX.sub("", stripped, count=1)
        if nxt == stripped:
            break
        stripped = nxt
    # a trailing Hebrew year is a date, not a locator ("Mishpatim 5776")
    stripped = re.sub(r"\s+5[78]\d\d\s*$", "", stripped)
    stripped = _strip_tail(stripped)
    if stripped != base:
        add(_numbers_to_colon(stripped))

    # Casing/spacing: /api/name is case- and whitespace-sensitive and does
    # not fuzzy-match casing itself ("Chovot Halevavot" misses, "Chovot
    # HaLevavot" resolves to "Duties of the Heart"). Title-case every word,
    # then capitalize the letter right after a mid-word "Ha" definite
    # article ("Halevavot" -> "HaLevavot", "Hachinuch" -> "HaChinuch"), and
    # tidy comma/period spacing ("Zohar , vayigash" -> "Zohar, Vayigash").
    # Just an extra over-generated candidate; wrong casing simply won't
    # resolve.
    def _cap_ha(s):
        s = re.sub(r"\b([a-z])", lambda m: m.group(1).upper(), s)
        return re.sub(r"\bHa([a-z])", lambda m: "Ha" + m.group(1).upper(), s)

    def _fix_spacing(s):
        s = re.sub(r"\s+([,.;:])", r"\1", s)
        return re.sub(r"([,.;:])(?=\S)", r"\1 ", s)

    for src in (citation, stripped):
        add(_numbers_to_colon(_fix_spacing(_cap_ha(src))))

    # spelling swaps (on both raw and prefix-stripped)
    # Colonize BEFORE tail-stripping: _STRIP_TAIL's trailing-footnote-number
    # rule (\s+\d+\s*$) can't tell "chapter, verse" from a stray trailing
    # number when they're both just "<space><digits>" at the end — converting
    # "N, N" to "N:N" first removes the ambiguity.
    for src in (base, stripped):
        sp = src
        for pat, rep in _SPELLING:
            sp = re.sub(pat, rep, sp, flags=re.I)
        for pat, rep in shared_dialect.TRACTATES:
            sp = re.sub(pat, rep, sp, flags=re.I)
        if sp != src:
            add(_strip_tail(_numbers_to_colon(sp)))

    # Shulchan Aruch section abbreviations (O.Ch., Y.D., E.H., C.M.)
    for pat, full in shared_dialect.SECTIONS:
        if re.search(pat, citation):
            expanded = re.sub(pat, full, citation)
            add(_numbers_to_colon(expanded))
            if not re.match(r"^\s*Shulchan", expanded, re.I):
                add(_numbers_to_colon("Shulchan Aruch, " + expanded.lstrip(", ")))
            else:
                add(_numbers_to_colon(re.sub(r"^(\s*Shulchan Aruch)\s+", r"\1, ", expanded)))

    # Structural corpus prefix: "Tosefta, X" -> "Tosefta X" (Sefaria's trie
    # rejects the comma); Yerushalmi/Tanchuma also get renamed to Sefaria's
    # corpus name. Runs early, before any candidate gets truncated by the
    # "trim to first ref" rule below, so the precise (untruncated) form is
    # proposed first. Composed over every candidate found so far.
    for cand in list(out):
        for pat, repl in shared_dialect.PREFIXES:
            nc = re.sub(pat, repl, cand, flags=re.I)
            if nc != cand:
                add(nc)

    # Ashkenazi/academic endings: rewrite the tractate-like leading word
    mw = re.match(r"^([A-Za-z']+)(\b.*)$", stripped)
    if mw:
        head, rest = mw.group(1), mw.group(2)
        for a, b in _ENDINGS:
            if head.lower().endswith(a):
                add(_numbers_to_colon((head[: -len(a)] + b + rest)))
        if head.lower() == "shabbos":
            add(_numbers_to_colon("Shabbat" + rest))

    # Rambam sections
    mr = re.match(r"^(?:.*?\b(?:Rambam|Maimonides|Mishneh Torah|Hil(?:chot|chos|khot)?|Laws of|Yad)\b[ ,.]*)+"
                  r"(?P<sec>[A-Za-z'’ ]+?)\s*(?P<nums>\d[\d:,\- ]*)$", citation, re.I)
    if mr:
        key = re.sub(r"[^a-z]", "", mr.group("sec").lower())
        book = shared_dialect.RAMBAM_SECTIONS.get(key)
        if book:
            add(f"Mishneh Torah, {book} {_numbers_to_colon(mr.group('nums'))}")

    # Keep two levels before falling back to one: "Pirkei Avot 4:5:7" (one level
    # too deep for Sefaria) -> "Pirkei Avot 4:5", "Exod 13:9.7" -> "Exod 13:9",
    # "Yerushalmi Berachos 4:2. IV" -> "... 4:2". Coarser beats unlinked, but
    # the less coarse the better.
    m2 = re.match(r"^([A-Za-z'’.\- ]+?\s\d+[ab]?[:.]\s?\d+[ab]?(?:-\d+(?:[:.]\d+)?)?)(?=[:.,\s]|$)", stripped)
    if m2 and m2.group(1) != stripped:
        add(_numbers_to_colon(m2.group(1).replace(". ", ":").replace(".", ":")))

    # Trim to the first ref when several are jammed together
    # ("Chagigah 14b:8-9 15a:3-16a:4" -> "Chagigah 14b")
    mt = re.match(r"^([A-Za-z'’.\- ]+?\s\d+[ab]?)\b", stripped)
    if mt and mt.group(1) != stripped:
        add(mt.group(1))
        for a, b in _ENDINGS:  # apply ending-fix to the trimmed head too
            hw = re.match(r"^([A-Za-z']+)", mt.group(1))
            if hw and hw.group(1).lower().endswith(a):
                add(hw.group(1)[:-len(a)] + b + mt.group(1)[len(hw.group(1)):])

    # Roman-numeral chapter/verse ("Genesis xxxvi 31-43")
    def _roman_sub(m):
        n = _roman_to_int(m.group(0))
        return str(n) if n else m.group(0)
    rom = re.sub(r"\b[ivxlcIVXLC]{2,}\b", _roman_sub, citation)
    if rom != citation:
        add(_numbers_to_colon(rom))

    # Wrapping parens around the whole reference ("Talmud (Chagiga 13b:14)",
    # "Rambam (Hilkhot Brakhot 1:16)"): flatten to "prefix inner" and to
    # "inner" alone, then recurse so the flattened form gets every rule
    # above for free (prefix strip, spelling, Rambam-section map, ...). Safe
    # against infinite recursion: the flattened forms have no parens left.
    mp = re.match(r"^(?P<pre>[A-Za-z][A-Za-z'.\s]*?)\s*\(\s*(?P<inner>[^()]+?)\s*\)\s*$", citation)
    if mp:
        pre, inner = mp.group("pre").strip(" ,."), mp.group("inner").strip()
        flats = [f"{pre} {inner}"]
        # "inner" alone only when the outside is a generic corpus word.
        # "Tosafos (Kesubos 30b)" must not become bare "Kesubos 30b": that
        # drops the commentary layer and links the Gemara instead.
        if all(w.lower() in _GENERIC_OUTER for w in re.findall(r"[A-Za-z]+", pre)):
            flats.append(inner)
        for flat in flats:
            for c in candidates(flat):
                add(c)

    # --- 2026-11-24 batch, from the web-pairs gap analysis -------------------
    # Each rewrite produces a new string and recurses through every rule above.
    # Over-generation is safe: a candidate only counts if Sefaria verifies it,
    # and the canonicalization guard rejects anything that adds or drops meaning.
    def _also(variant):
        if variant and variant != citation:
            for c in candidates(variant):
                add(c)

    # Verse-part letters after a verse number: "Esther 9:20f", "Exodus 15:1b-18",
    # "Psalm 145:13a" -> 9:20, 15:1-18, 145:13. Only after a colon, so a Talmud
    # folio ("Shabbat 13a") is untouched.
    if re.search(r":\s?\d+[abf]\b", citation):
        _also(re.sub(r"(:\s?\d+)[abf]\b", r"\1", citation))

    # Link text cut off at an unclosed parenthesis: "Shabbat (23a", "Pirkei Avot (3:2"
    if citation.count("(") > citation.count(")"):
        _also(citation.replace("(", " "))

    # Wikipedia-style locators: "chapter 2, ¶ 3" -> "2:3", "chapter 24" -> "24",
    # "§ 1" / "# 594" -> "1" / "594", "chap. 10 mishna 3" -> "10:3"
    loc = re.sub(r",?\s*\b(?:chapter|chap\.?|ch\.|perek)\s*(\d+)\s*,?\s*"
                 r"(?:\u00b6|paragraph|para\.?|halacha|halakhah|halakha|mishna|mishnah|\u00a7)\s*(\d+)",
                 r" \1:\2", citation, flags=re.I)
    loc = re.sub(r",?\s*\b(?:chapter|chap\.?|perek)\s+(\d+)", r" \1", loc, flags=re.I)
    loc = re.sub(r"(?:\u00a7|#)\s*(\d+)", r" \1", loc)
    _also(loc)

    # Stray word-final apostrophe: "Hoshea' 14:2"
    _also(re.sub(r"(?<=[A-Za-z])'(?=\s|,|$)", "", citation))

    # Ashkenazi final s for tav beyond -os (handled above): Koheles, Bereshis, Megillas
    _also(re.sub(r"\b(?!Genesis\b|Moses\b|Ramses\b|Exodus\b|Chronicles\b|Judges\b|Ecclesiastes\b|Lamentations\b|Maccabees\b)([A-Za-z]{3,}[aei])s\b", r"\1t", citation))

    # "SA"/"S.A."/"Sh\"A"/"Shu\"A" before a section name -> Shulchan Arukh
    sa = re.sub(r"^\s*(?:S\.?\s?A\.?|Sh\.?\s?A\.?|SH?U?\"A|Sh\"A|Shu\"A)\s+"
                r"(?=(?:Orach|Yoreh|Even|Choshen|O\.?\s?[CH]\b|Y\.?\s?D\b|E\.?\s?H\b|C\.?\s?M\b))",
                "Shulchan Arukh, ", citation)
    sa = re.sub(r"\bO\.?\s?H\b", "Orach Chayim", sa) if sa != citation else sa
    _also(sa)

    # Hebrew book names -> English (Ohr HaChaim to Shemot 23:2 -> ... Exodus 23:2).
    # A "Rabbah" right after the name means the midrash, which Sefaria titles in
    # Hebrew (Bereshit Rabbah), so those are left alone.
    bk = citation
    for pat, eng in BOOKS:
        # only in book position: at the start or after on/to/of/a comma or
        # paren, and followed by a chapter number ("Rabbeinu Yonah 3:5" stays)
        bk = re.sub(rf"(?:^|(?<=\bon )|(?<=\bto )|(?<=\bof )|(?<=, )|(?<=\())\s*(?:{pat})(?=\s+\d)",
                    eng, bk, flags=re.I)
    _also(bk)

    # Commentator "X to Y" -> "X on Y" (Prisha to Tur ..., Malbim to Micah ...)
    if re.search(r"\s+to\s+", citation):
        _also(re.sub(r"\s+to\s+", " on ", citation))

    # Quoted Hebrew abbreviations (the dotted forms are handled in SECTIONS).
    ab = citation
    for pat, rep in [(r'\bB"M\b', "Bava Metzia"), (r'\bB"K\b', "Bava Kamma"),
                     (r'\bB"B\b', "Bava Batra"), (r'\bB"R\b', "Bereshit Rabbah"),
                     (r'\bO"[CH]\b', "Orach Chayim"), (r'\bYo?"D\b', "Yoreh Deah"),
                     (r'\bE"H\b', "Even HaEzer"), (r'\bC[h]?"M\b', "Choshen Mishpat"),
                     (r'\bRash"i\b', "Rashi"), (r'\bM"B\b', "Mishnah Berurah")]:
        ab = re.sub(pat, rep, ab)
    _also(ab)

    # Corpus prefixes and junk around the citation
    pre = re.sub(r"^\s*(?:BT|B\.|Bavli)\s+", "", citation)
    pre = re.sub(r"^\s*JT\s+", "Jerusalem Talmud ", pre)
    pre = re.sub(r"^\s*Sefaria:?\s+|\s*@\s*sefaria\.org\s*$", "", pre, flags=re.I)
    _also(pre)

    # Midrash Tanchuma by parasha: "Midrash Tanhuma Ki Sisa 9" -> "Midrash Tanchuma, Ki Sisa 9"
    tn = re.sub(r"\bTanhuma\b", "Tanchuma", citation, flags=re.I)
    tn = re.sub(r"^\s*(?:Midrash\s+)?Tanchuma,?\s+(?!Buber)", "Midrash Tanchuma, ", tn, flags=re.I)
    _also(tn)

    # I/II books written with a marker: "Shmuel A 9:2", "Sh'muel B 15:4",
    # "Melachim A 1:24", "Samuel 1 13:1", "Shemuel I:26:6", "Shmuel 1:1:3-4"
    two = {r"Sh'?e?muel|Samuel": "Samuel", r"M'?e?la[ck]h?im|Kings": "Kings",
           r"Divrei Ha-?[Yy]amim|Chronicles": "Chronicles"}
    for pat, eng in two.items():
        mm = re.match(rf"^\s*(?:Sefer\s+)?(?:{pat})\s*(?:(A|Alef|Aleph|I|1)|(B|Bet|Beis|II|2))"
                      rf"(?:\s+|:)(\d+[:.]\d+.*|\d+\s*$|\d+:\d+.*)$", citation, flags=re.I)
        if mm:
            num = "I" if mm.group(1) else "II"
            _also(f"{num} {eng} {mm.group(3)}")

    # Torah commentaries Sefaria titles as "X, Book" or "X on Torah, Book"
    if re.search(r"\s+(?:on|to)\s+", citation) and "Torah, " not in citation:
        _also(re.sub(r"\s+(?:on|to)\s+", ", ", citation, count=1))
        _also(re.sub(r"\s+(?:on|to)\s+", " on Torah, ", citation, count=1))

    # Commentaries that exist only on Orach Chayim: the section name is noise
    # ("Magen Avraham OC 189:1" -> "Magen Avraham 189:1"). Bounded list.
    if re.match(r"^\s*(Magen Avraham|Mishnah Berurah|Mishna Brura|Kaf Ha[Cc]hayi?m|Biur Halacha|"
                r"Be'?ur Halakhah|Shaar HaTziyun|Eliyah? Rabbah?|Machatzit HaShekel)\b", citation, re.I):
        _also(re.sub(r"[\s,(]+(?:O\.?\s?C\.?|O\"C|OC|Orach Ch?a[iy]+m)\b", " ", citation, flags=re.I))

    # Leading filler: "in Eruvin 43b", "See Rashi to Genesis 19:1"
    _also(re.sub(r"^\s*(?:see also|see|cf\.?|in)\s+", "", citation, flags=re.I))

    # "MT, Kings and Wars 11.1" -> "Mishneh Torah, Kings and Wars 11:1"
    _also(re.sub(r"^\s*MT,?\s+", "Mishneh Torah, ", citation))

    # A citation that STARTS with Hilchot/Hilchos ("Hilchos Eidus 4:1") is the
    # Rambam by near-universal convention (Sefaria's own bare "Hilchot Teshuva"
    # alias assumes the same). Rewrite to Sefaria's "Rambam, Hilchot X" alt-title
    # form; the canonicalization pass then fixes the spelling (Eidus -> Edut).
    m = re.match(r"^\s*(?:(?:Rambam|Mishneh Torah|Mishnah Torah)[,:]?\s+(?:in\s+)?)?"
                 r"(?:Hilchot|Hilchos|Hilkhot|Hil\.)\s+(.+)$", citation, flags=re.I)
    if m:
        _also("Rambam, Hilchot " + m.group(1))

    return _specific_first(out)


def _specific_first(cands):
    """Stable reorder: a candidate whose locator is a strict prefix of another
    candidate's locator for the same work ("Esther 9" vs "Esther 9:20") goes
    after it, so the precise form is tried first and the truncation is only a
    fallback."""
    def split(c):
        m = re.match(r"^(.*?[A-Za-z'’)])\s*,?\s+(\d[\d:ab\-\s]*)$", c)
        if not m:
            return None, None
        return m.group(1).casefold(), [t for t in re.split(r"[:\s]+", m.group(2).strip()) if t]
    parsed = [split(c) for c in cands]
    out, deferred = [], []
    for i, c in enumerate(cands):
        head, nums = parsed[i]
        less_specific = head is not None and any(
            h == head and n is not None and len(n) > len(nums) and n[:len(nums)] == nums
            for j, (h, n) in enumerate(parsed) if j != i)
        (deferred if less_specific else out).append(c)
    return out + deferred
