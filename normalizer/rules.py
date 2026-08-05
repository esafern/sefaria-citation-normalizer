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
    r"B\.?\s*Talmud|Babylonian Talmud|Talmud Bavli|Bavli|"
    r"Gemara(?: of)?|Mishnah of Tractate|Mishnah of|"
    r"Mesechtas?|Meseches|Masechet|Masekhet|Masechta?|Maseches|Tractate|Seifer|Sefer)\s+",
    re.I)

# Trailing editorial noise: notes, s.v., page/verse tails, Hebrew dibur-hamatchil.
_STRIP_TAIL = re.compile(
    r"(?:,?\s*note[s]?\s+\d+.*"
    r"|\s*s\.?v\.?.*"
    r"|\s*\(sources?\s+[\d\- ]+\)"
    r"|\s*[֐-׿].*"           # a Hebrew tail (commentary quote); apostrophes kept (M'lachim)
    r"|\s+\d+\s*$)?$")   # trailing NOTE number ("15b 4"); space required so ":3" segments survive

# Word-final Ashkenazi / academic transliteration endings -> Sefaria's -ot form.
_ENDINGS = [("oth", "ot"), ("os", "ot"), ("us", "ut"), ("ois", "ot")]

# Small spelling swaps seen repeatedly.
_SPELLING = [
    (r"\bPirke\b", "Pirkei"), (r"\bd'?e?[- ]?(?:Rebb?i|Rabb?i)\b", "DeRabbi"),
    (r"\bNoss?on\b", "Natan"), (r"\bNassan\b", "Natan"),
    (r"\bDerekh\b", "Derech"), (r"\bShul[hk]han\b", "Shulchan"), (r"\bShulkhan\b", "Shulchan"),
    (r"\bShemos\b", "Exodus"), (r"\bDevorim\b", "Deuteronomy"),
    (r"\bBerachos\b", "Berakhot"), (r"\bBerakoth\b", "Berakhot"),
    (r"\bKesubos\b", "Ketubot"), (r"\bYevamos\b", "Yevamot"),
    (r"\bMenachos\b", "Menachot"), (r"\bMenachoth\b", "Menachot"),
    (r"\bBava Basra\b", "Bava Batra"), (r"\bMo'?ed Qatan\b", "Moed Katan"),
    (r"\bOlas\b", "Olat"), (r"\bChovos\b", "Chovot"),
    (r"\bAvos\b", "Avot"), (r"\bShabbos\b", "Shabbat"), (r"\bToras\b", "Torat"),
    (r"\bHilchos\b", "Hilchot"), (r"\bTumas\b", "Tumat"), (r"\bMoed Qatan\b", "Moed Katan"),
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


def _numbers_to_colon(s):
    return re.sub(r"(\d)\s*,\s*(\d)", r"\1:\2", s)


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
    add(_numbers_to_colon(citation))

    base = citation
    # split a concatenated edition prefix: "ArtScrollBava Metzia" -> "ArtScroll Bava Metzia"
    base = re.sub(r"\b(ArtScroll|Artscroll)(?=[A-Z])", r"\1 ", base)
    # leading "N - " enumerations ("2 - Oral Torah Tur, ...")
    base = re.sub(r"^\s*\d+\s*[-.)]\s*(?:Oral Torah\s+)?", "", base)
    stripped = base
    for _ in range(3):  # peel stacked prefixes ("Artscroll Masechet ...")
        nxt = _STRIP_PREFIX.sub("", stripped, count=1)
        if nxt == stripped:
            break
        stripped = nxt
    stripped = re.sub(_STRIP_TAIL, "", stripped).strip()
    if stripped != base:
        add(_numbers_to_colon(stripped))

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
            add(_STRIP_TAIL.sub("", _numbers_to_colon(sp)).strip())

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

    return out
