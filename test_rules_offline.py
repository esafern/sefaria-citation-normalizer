#!/usr/bin/env python3
"""Offline regression tests for the normalizer: no network.

Every case here came from a real failure found with the web-pairs test set or the
benchmark (2026-11-23/24). Two kinds:

  GUARD:      normalizer.resolve._keeps_all_words(source, canonical_title) must accept
              same-name-different-spelling and reject anything that changes meaning.
  CANDIDATES: normalizer.rules.candidates(raw) must (or must not) propose a string.

Run: python3 test_rules_offline.py   (exit 1 on any failure)
"""
import sys

from normalizer.resolve import _keeps_all_words, _book_group
from normalizer.rules import candidates
from benchmark import classify

# (source, canonical title, should accept?, why)
GUARD = [
    # spelling / casing only: accept
    ("Berakoth", "Berakhot", True, "academic spelling"),
    ("Kesubos", "Ketubot", True, "Ashkenazi s for tav"),
    ("Bava Metziah", "Bava Metsia", True, "tz/ts, final h"),
    ("Mo'ed Qatan", "Moed Katan", True, "q/k, apostrophe"),
    ("Tosfot Avodah Zarah", "Tosafot on Avodah Zarah", True, "connector 'on' may be added"),
    ("Yad, Yesodey Hatorah", "Rambam, Yesodey haTorah", True, "Rambam name group"),
    ("Rosh Ha-Shanah", "Rosh Hashanah", True, "hyphenated article"),
    ("Kav HaYosher , chapter", "Kav HaYashar", True, "vowel shift; 'chapter' droppable"),
    ("Rambam, Hilchot Eidus", "Rambam, Hilchot Edut", True, "Ashkenazi vowels"),
    ("Rambam, Hilchot Tfila", "Rambam, Hilchot Tefilah and Birkat Kohanim", True, "MT compound title"),
    ("Abarbanel on Genesis", "Abarbanel on Torah, Genesis", True, "'on Torah,' structure"),
    ("Guide for the Perplexed, Introduction", "Guide for the Perplexed", True, "source may drop 'Introduction'"),
    # dropped words: reject
    ("Kaf Hachaim Palagi", "Kaf HaChayim on Shulchan Arukh, Orach Chayim", False, "drops the author"),
    ("Kaf Hachaim YD", "Kaf HaChayim on Shulchan Arukh, Orach Chayim", False, "drops the section"),
    ("Maharik. Tosfot Avodah Zarah", "Avodah Zarah", False, "drops the commentary layer"),
    ("Sefer Hamitzvot Lav", "Sefer HaMitzvot, Shorashim", False, "drops Lav"),
    ("Hamitzvot of Rambam", "Sefer Hamitzvot of Rasag", False, "wrong author"),
    ("Hilchot Berachot", "Berachot", False, "'hilchot' is not droppable (would become Bavli/Mishnah)"),
    # added words / numbers / order: reject
    ("Moreh Nevuchim", "Guide for the Perplexed, Prefatory Remarks", False, "adds a section"),
    ("Aruch Hashulchan", "Arukh HaShulchan, Yoreh De'ah", False, "picks a section"),
    ("Shmuel", "I Samuel", False, "picks I vs II"),
    ("MB IN", "MB, Introduction", False, "adds Introduction"),
    ("HaIkkarim", "Sefer HaIkkarim, Introduction", False, "adds Introduction"),
    ("Yesodei Hatorah", "Sefer Yesodei HaTorah", False, "'Sefer' may not be added: different book"),
    ("Pirkei Avot, Commentary on", "German Commentary on Pirkei Avot", False, "prefixes another work"),
    ("Aruch Hashulchan YD", "Shulchan Aruch YD", False, "reordered words = different book"),
    ("Guide for the Perplexed, part", "Guide for the Perplexed, Part 1", False, "adds a number"),
    ("Rambam, Hilchot Tfila", "Rambam, Hilchot Teshuva", False, "different section"),
    ("Bekhorot", "Berakhot", False, "similar spelling, different tractate"),
]

# (raw, string that MUST be among candidates, or None) and (raw, string that must NOT be)
MUST = [
    ("Shabbat (23a", "Shabbat 23a"),
    ("Kitzur Shulchan Aruch, chapter 2, \u00b6 3", "Kitzur Shulchan Aruch 2:3"),
    ("Mishnah Sanhedrin chap. 10 mishna 3", "Mishnah Sanhedrin 10:3"),
    ("Hoshea' 14:2", "Hoshea 14:2"),
    ("Koheles Rabbah 7:16", "Kohelet Rabbah 7:16"),
    ("SA Yoreh Deah 69:16", "Shulchan Arukh, Yoreh Deah 69:16"),
    ("Hilchos Eidus 4:1", "Rambam, Hilchot Eidus 4:1"),
    ("Ohr HaChaim to Shemot 23:2", "Ohr HaChaim on Exodus 23:2"),
    ('B"M 59b', "Bava Metzia 59b"),
    ("BT Yoma 35b", "Yoma 35b"),
    ("Tehillim 23:1", "Psalms 23:1"),
    ("Shmuel A 9:2", "I Samuel 9:2"),
    ("Sh'muel B 15:4", "II Samuel 15:4"),
    ("Samuel 1 13:1", "I Samuel 13:1"),
    ("Magen Avraham OC 189:1", "Magen Avraham 189:1"),
    ("MT, Kings and Wars 11.1", "Mishneh Torah, Kings and Wars 11:1"),
    ("Pirkei Avot 4:5:7", "Pirkei Avot 4:5"),
    ("Esther 9:20f", "Esther 9:20"),
    ("Deuteronomy 5:6-21. Myth 3", "Deuteronomy 5:6-21"),
    ("I Chronicles 1:]43-54", "I Chronicles 1:43-54"),
    ("Mishpatim 5776", "Mishpatim"),
    ("Mishnah of Tractate Chagigah", "Mishnah Chagigah"),
]
MUST_NOT = [
    ("Mishnah of Tractate Chagigah", "Chagigah", "dropping 'Mishnah' linked the Bavli"),
    ("Yalkut Shimoni 1046", "Yalkut Shimoni", "only number stripped -> Sefaria picks a volume"),
    ("Vayigash 5", "Vayigash", "only number stripped -> parasha range"),
    ("Theodicy Tosafos ( Kesubos 30b sv. din )", "Kesubos 30b", "paren unwrap dropped Tosafos"),
    ("Rabbeinu Yonah 3:5", "Rabbeinu Jonah 3:5", "book-name map applied to a person"),
    ("Shmuel 23:8", "I Samuel 23:8", "no I/II marker: must not guess"),
    ("Exodus 15:1b-18", "Exodut 15:1-18", "(cosmetic) only Ashkenazi endings, never English words"),
]
# (raw, a candidate that must come BEFORE another)
ORDER = [
    ("Esther 9:20f", "Esther 9:20", "Esther 9"),
    ("Pirkei Avot 4:5:7", "Pirkei Avot 4:5", "Pirkei Avot 4"),
]
# scoring
SCORE = [
    ("https://www.sefaria.org/Shabbat.88", "Shabbat 88a", "coarser"),
    ("https://www.sefaria.org/Bava_Metzia.85b", "Bava Metzia 85a:23-85b:1", "coarser"),
    ("https://www.sefaria.org/Leviticus.13.12-13", "Leviticus 13:12", "coarser"),
    ("https://www.sefaria.org/Mishneh_Torah,_Marriage.1.1", "Mishneh Torah, Marriage 1", "finer"),
    ("https://www.sefaria.org/Shabbat.88", "Shabbat 89a", "WRONG"),
    ("https://www.sefaria.org/Genesis.1.27", "Genesis 1:2", "WRONG"),
]


def main():
    fails = []
    for src, canon, want, why in GUARD:
        if _keeps_all_words(src, canon) != want:
            fails.append(f"GUARD {src!r} -> {canon!r}: expected {want} ({why})")
    for raw, cand in MUST:
        if cand not in candidates(raw):
            fails.append(f"MUST {raw!r}: missing {cand!r}")
    for raw, cand, why in MUST_NOT:
        if cand in candidates(raw):
            fails.append(f"MUST_NOT {raw!r}: has {cand!r} ({why})")
    for raw, first, second in ORDER:
        c = candidates(raw)
        if first in c and second in c and c.index(first) > c.index(second):
            fails.append(f"ORDER {raw!r}: {first!r} should precede {second!r}")
    for url, label, want in SCORE:
        if classify(url, label) != want:
            fails.append(f"SCORE {url} vs {label!r}: expected {want}")
    if _book_group("bereishis") != "genesis" or _book_group("shoftim") is not None:
        fails.append("BOOKS: bereishis->genesis, shoftim excluded")
    total = len(GUARD) + len(MUST) + len(MUST_NOT) + len(ORDER) + len(SCORE) + 1
    for f in fails:
        print("FAIL", f)
    print(f"{total - len(fails)}/{total} passed")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
