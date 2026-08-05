"""Anglo-Orthodox citation dialect: shared abbreviation/prefix data.

Vendored byte-identically into two repos — this file, and
`rav-shvat-blog/pipeline/sefaria_linker/shared_dialect.py`. Each repo's test
suite has a diff-check test that fails loudly the moment the two copies
diverge (see `test_shared_dialect.py` at this repo's root). This is a
deliberate choice over a live cross-repo import: the two repos' Sefaria
linkers evolve on independent, uncoordinated schedules, and a live dependency
would mean an unrelated change here could silently break the blog's build.
See `INTEGRATION-PLAN.md` for the full rationale.

Scope is deliberately narrow: abbreviation maps, Shulchan Aruch section
names, the Rambam-section name map, and structural corpus prefixes — general
Anglo-Orthodox dialect knowledge that holds regardless of how a consumer
turns a citation into a link (propose-many-candidates-and-verify against
Sefaria's /api/name, or a hardcoded per-work regex). Per-work URL
construction, mislink-avoidance precision logic, and each repo's own
candidate-generation/composition strategy are NOT here — they stay local to
whichever repo needs them.
"""
import re

# Shulchan Aruch / responsa section abbreviations.
SECTIONS = [
    (r"\bOr?\.?\s?Ch\.?", "Orach Chayim"),
    (r"\bO\"?C\b", "Orach Chayim"),
    (r"\bY\.?\s?D\.?", "Yoreh Deah"),
    (r"\bE\.?\s?H\.?", "Even HaEzer"),
    (r"\bEv\.?\s?H\.?", "Even HaEzer"),
    (r"\bC\.?\s?M\.?", "Choshen Mishpat"),
]

# Rambam (Mishneh Torah) section names -> Sefaria canonical English book.
# Keyed letters-only (re.sub(r"[^a-z]", "", ...)) so punctuation/apostrophe
# style ("Kr.Sh.", "KrSh", "M'lachim", "Y'sodei") never matters at lookup
# time. Reconciled 2026-08-05 from two independently-grown lists (this
# repo's normalizer/rules.py and the blog's pipeline/sefaria_linker/
# dialect.py) — keep the union, don't drop either side's spelling variants.
RAMBAM_SECTIONS = {
    # Kings and Wars
    "melachim": "Kings and Wars", "milachim": "Kings and Wars", "mlachim": "Kings and Wars",
    "melachimumilchamoteihem": "Kings and Wars", "mlachimumilchamoteihem": "Kings and Wars",
    "milachimumilchamoteihem": "Kings and Wars",
    # Repentance
    "teshuva": "Repentance", "teshuvah": "Repentance", "tshuva": "Repentance",
    # Rebels
    "mamrim": "Rebels",
    # Reading the Shema
    "kriatshema": "Reading the Shema", "krsh": "Reading the Shema",
    # Foundations of the Torah
    "yesodeihatorah": "Foundations of the Torah", "yesodeihaatorah": "Foundations of the Torah",
    "ysodeihatorah": "Foundations of the Torah", "ysodeihaatorah": "Foundations of the Torah",
    # Gifts to the Poor
    "matnotaniim": "Gifts to the Poor", "matnotaniyim": "Gifts to the Poor",
    # Scroll of Esther and Hanukkah
    "chanuka": "Scroll of Esther and Hanukkah", "chanukah": "Scroll of Esther and Hanukkah",
    # Blessings
    "brachot": "Blessings", "berachot": "Blessings", "berakhot": "Blessings",
    # Forbidden Intercourse
    "issureibiah": "Forbidden Intercourse", "isuraybiah": "Forbidden Intercourse",
    # Tefillin, Mezuzah, and the Torah Scroll
    "mezuza": "Tefillin Mezuzah and the Torah Scroll",
    # Foreign Worship and Customs of the Nations — also reachable via the
    # "Av.Z." abbreviation as a Rambam-section shorthand, distinct from (but
    # coincidentally the same target as) the Tosefta tractate TRACTATES
    # expands below.
    "avodazara": "Foreign Worship and Customs of the Nations",
    "avz": "Foreign Worship and Customs of the Nations",
    # Sabbath
    "shabbat": "Sabbath", "shabbos": "Sabbath",
    # Mourning
    "avel": "Mourning",
}

# Tractate-name abbreviations, valid wherever they appear (Mishnah, Talmud,
# Tosefta, Rambam Hilchot ...), not just as a Rambam section.
#
# \b sits right after the literal Z, before the optional trailing period —
# \b after an *optional* character backtracks unpredictably when what's on
# both sides of it is non-word (the dot and following space/comma), and
# silently drops the dot from the match instead of consuming it.
TRACTATES = [
    (r"\bAv\.?\s*Z\b\.?", "Avodah Zarah"),
]

# Corpus prefixes that change which work a tractate/parsha name belongs to.
# Sefaria's /api/name trie rejects "Tosefta, X" but accepts "Tosefta X"
# (measured, not assumed) — Tosefta/Mishnah/Mishna's entries below are
# comma-only rewrites; Yerushalmi/Tanchuma's entries additionally rename to
# Sefaria's corpus name, since the bare Anglo name isn't in Sefaria's trie.
PREFIXES = [
    (r"^Yerushalmi,?\s+", "Jerusalem Talmud "),
    (r"^Talmud Yerushalmi,?\s+", "Jerusalem Talmud "),
    (r"^Tanchuma,?\s+", "Midrash Tanchuma, "),
    (r"^Midrash Tanchuma,?\s+", "Midrash Tanchuma, "),
    (r"^Tosefta,?\s+", "Tosefta "),
    (r"^Mishnah,?\s+", "Mishnah "),
    (r"^Mishna,?\s+", "Mishna "),
]
