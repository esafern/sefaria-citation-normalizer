#!/usr/bin/env python3
"""Final most-wanted builder: robust presence test + curated annotation.

Uses presence.check (prefix/fuzzy match against ref completions) over the most-
cited works, minus a small set of works I verified present under an abbreviation
or embedded layer that the trie can't reach by prefix. Emits JSON + a readable
markdown brief for Sefaria, tiered into public-domain (digitize) vs modern
(license).

Two run modes:
  (default)   live — hit /api/name to classify presence, then tier + write.
  --offline   reuse the committed data/sefaria_most_wanted.json absent-set
              (the frozen result of a prior live run) and only re-apply the
              era tiering + markdown. Lets the hand-classification below be
              regenerated with no network, e.g. when Sefaria egress is blocked.
The presence source is the only difference between the two modes; the era
classification, bucketing, and markdown are shared, so they can't drift.
"""
import json, os, re, sys
import presence
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from normalizer import rules

OFFLINE = "--offline" in sys.argv

_GEMARA = re.compile(r"^(?:Gemara|Talmud|Masechet|Masekhet|Mishnah|Mishna|Sefer)\s+", re.I)
_SUBPART = re.compile(r'\s+(?:M"?Z|E"?A|A"?A|S"?K)\b.*$')  # Pri Megadim sub-commentaries etc.


def is_present(name, cache):
    """Second-chance: try the raw name, a Gemara/Sefer-stripped form, sub-part-
    stripped form, and the normalizer's candidate spellings. Any hit => present."""
    forms = {name, _GEMARA.sub("", name), _SUBPART.sub("", name)}
    for f in list(forms):
        for c in rules.candidates(f):
            forms.add(c)
    for f in forms:
        if len(f) >= 3 and presence.check(f, cache=cache)["present"]:
            return True
    return False

HERE = os.path.dirname(__file__)
ranked = json.load(open(os.path.join(HERE, "work_frequency.json")))["ranked"]
cache_path = os.path.join(HERE, "presence_cache.json")
cache = json.load(open(cache_path)) if os.path.exists(cache_path) else {}
MW_PATH = os.path.join(HERE, "..", "data", "sefaria_most_wanted.json")

TOP = 250
ENGLISH = re.compile(r"\bHalachos of\b|\bLaws of\b|Handbook|by Rabbi|\bThe \b|Melachos|Guide", re.I)

# Verified present by hand (trie can't reach them by prefix): abbreviations and
# layers embedded in a parent work. Checked live against /api/name.
VERIFIED_PRESENT = {"benishchai", "gra", "shaarhatziyun", "shaarhatzion",
                    "nodehbeyehuda", "nodabeyehuda", "maggidmishna", "chokyaakov"}

# Author era for the top works -> tier. PD = public domain (digitize); MOD =
# modern/in-copyright (license). Keyed by normalized work name. Cutoff for PD is
# life+70: author died <=1955 as of 2026. Borderline years are noted inline.
ERA = {
    "yalkutyosef": ("Yitzchak Yosef", "MOD"), "yalkutyosefmoadim": ("Yitzchak Yosef", "MOD"),
    "shemiratshabbatkehilchata": ("Y.Y. Neuwirth (d.2013)", "MOD"),
    "halachabrurah": ("David Yosef", "MOD"), "halachaberura": ("David Yosef", "MOD"),
    "yabiaomer": ("Ovadia Yosef (d.2013)", "MOD"), "yechavedaat": ("Ovadia Yosef (d.2013)", "MOD"),
    "chazonovadyah": ("Ovadia Yosef (d.2013)", "MOD"), "chazonovadia": ("Ovadia Yosef (d.2013)", "MOD"),
    "taharathabayit": ("Ovadia Yosef (d.2013)", "MOD"),
    "chelkatbinyamin": ("on Hilchot Basar b'Chalav, modern", "MOD"),
    "piskeiteshuvot": ("Simcha Rabinowitz, modern", "MOD"),
    "chazonish": ("A.Y. Karelitz (d.1953)", "MOD"),
    "orletzion": ("Ben Zion Abba Shaul (d.1998)", "MOD"),
    "shevethalevi": ("S.H. Wosner (d.2015)", "MOD"),
    "badeihashulchan": ("modern, on Yoreh De'ah", "MOD"),
    "minchatyitzchak": ("Y.Y. Weiss (d.1989)", "MOD"),
    "halichotshlomo": ("S.Z. Auerbach (d.1995)", "MOD"),
    "minchatshlomo": ("S.Z. Auerbach (d.1995)", "MOD"),
    "niteigavriel": ("Gavriel Zinner, modern", "MOD"),
    "toratribbit": ("modern", "MOD"), "menuchatahava": ("modern", "MOD"),
    "toratamoadim": ("modern", "MOD"), "torathamoadim": ("modern", "MOD"),
    "britehuda": ("Y. Blau (d.2013)", "MOD"), "brityehuda": ("Y. Blau (d.2013)", "MOD"),
    "ginzeihakodesh": ("modern", "MOD"),
    "igrotmoshe": ("Moshe Feinstein (d.1986)", "MOD"),
    "tziteliezer": ("E. Waldenberg (d.2006)", "MOD"), "tzitzeliezer": ("E. Waldenberg (d.2006)", "MOD"),
    "taharathabayitv": ("Ovadia Yosef (d.2013)", "MOD"),
    "birkeiyosef": ("Chida (d.1806)", "PD"),
    "prichadash": ("H. da Silva (d.1698)", "PD"),
    "chavotdaat": ("Y. Lorberbaum (d.1832)", "PD"),

    # --- Tier-3 tail, hand-classified (2026-07). Author + life+70 status. ---
    # Modern / in-copyright:
    "beermoshe": ("Moshe Stern (d.1997)", "MOD"),
    "orchotshabbat": ("modern (contemp.)", "MOD"),
    "minchatasher": ("Asher Weiss (b.1953)", "MOD"),
    "rivevotefraim": ("Ephraim Greenblatt (d.2014)", "MOD"),
    "rivivotephraim": ("Ephraim Greenblatt (d.2014)", "MOD"),
    "mishnehhalachot": ("Menashe Klein (d.2011)", "MOD"),
    "ashreihaish": ("rulings of Y.S. Elyashiv (d.2012)", "MOD"),
    "chutshani": ("Nissim Karelitz (d.2019)", "MOD"),
    "yalkutyosefmilah": ("Yitzchak Yosef", "MOD"),
    "yalkutyosefkitzurshulchanaruch": ("Yitzchak Yosef", "MOD"),
    "yalkutyosefshabbat": ("Yitzchak Yosef", "MOD"),
    "yalkutyoseftefillah": ("Yitzchak Yosef", "MOD"),
    "yalkutyosefsovasemachot": ("Yitzchak Yosef", "MOD"),
    "chazonovadiayamimnoraim": ("Ovadia Yosef (d.2013)", "MOD"),
    "chazonovadiasukkot": ("Ovadia Yosef (d.2013)", "MOD"),
    "chazonovadiapesach": ("Ovadia Yosef (d.2013)", "MOD"),
    "chazonovadiapurim": ("Ovadia Yosef (d.2013)", "MOD"),
    "chazonovadiashabbat": ("Ovadia Yosef (d.2013)", "MOD"),
    "yachavadaat": ("Ovadia Yosef (d.2013)", "MOD"),
    "shtigrotmoshe": ("Moshe Feinstein (d.1986)", "MOD"),
    "shtshevethalevi": ("S.H. Wosner (d.2015)", "MOD"),
    "chelkesbinyomin": ("on Hilchot Basar b'Chalav, modern", "MOD"),
    "vehanhagot": ("Moshe Sternbuch (b.1926)", "MOD"),
    "teshuvoshanhagos": ("Moshe Sternbuch (b.1926)", "MOD"),
    "hartzvi": ("Tzvi Pesach Frank (d.1960)", "MOD"),
    "chelkatyakov": ("M.Y. Breisch (d.1976)", "MOD"),
    "chelkatyaakov": ("M.Y. Breisch (d.1976)", "MOD"),
    "ateretpaz": ("Pinchas Zvichi, contemp.", "MOD"),
    "isheiyisrael": ("A.Y. Pfoifer, modern", "MOD"),
    "shevethakehati": ("Shammai Gross (d.2020)", "MOD"),
    "nishmatavraham": ("A. Steinberg, contemp.", "MOD"),
    "shulchanshlomo": ("rulings of S.Z. Auerbach (d.1995)", "MOD"),
    "divreiyatziv": ("Y.Y. Halberstam (d.1994)", "MOD"),
    "aznidbaru": ("B.Y. Zilber (d.2008)", "MOD"),
    "yaskilavdi": ("Ovadia Hedaya (d.1969)", "MOD"),
    "tiltuleishabbat": ("modern", "MOD"),
    "halichotolam": ("Ovadia Yosef (d.2013)? — unverified", "MOD"),
    "birkathashem": ("modern — unverified", "MOD"),
    "shalmeiyehuda": ("rulings of Y.S. Elyashiv (d.2012)", "MOD"),
    "horahbrurah": ("modern — unverified", "MOD"),
    "dorhamelaktim": ("modern — unverified", "MOD"),
    "milvehhashem": ("modern, on hilchot ribbit — unverified", "MOD"),
    # Public domain (life+70 elapsed):
    "betefraim": ("E.Z. Margolis (d.1828)", "PD"),
    "darkeiteshuva": ("Tzvi Hirsch Shapira (d.1913)", "PD"),
    "daattorah": ("Maharsham, S.M. Schwadron (d.1911)", "PD"),
    "avneinezer": ("A. Bornsztain (d.1910)", "PD"),
    "sidreitahara": ("Elchanan Ashkenazi (d.1780)", "PD"),
    "mishkenotyakov": ("Yaakov of Karlin (d.1844)", "PD"),
    "maharamshik": ("Moshe Schick (d.1879)", "PD"),
    "gesherhachaim": ("Y.M. Tucazinsky (d.1955, borderline)", "PD"),
}


def normkey(w):
    return re.sub(r"[^a-z]", "", w.lower())


# Suspected FALSE-ABSENTS: classic rishonim/acharonim and Rambam sections whose
# absence flag I distrust — Sefaria very likely already has them under an
# embedded/abbreviated form the miner's prefix test missed. NOT tiered; queued
# for the live /api/name spot-check instead of being asserted as absent. This is
# the propose->verify discipline: I don't claim they're absent, I flag them.
VERIFY_PRESENCE = {
    "sma": "Sma (Sefer Meirat Einayim, on Choshen Mishpat)",
    "sama": "Sama (= Sma, Sefer Meirat Einayim)",
    "radvaz": "Radbaz responsa / on Rambam",
    "hagahotmaimoniyot": "Hagahot Maimoniyot (glosses on Mishneh Torah)",
    "rabbenuyonah": "Rabbeinu Yonah (Shaarei Teshuvah / on Avot, Berakhot)",
    "rashbaresponsa": "Teshuvot HaRashba",
    "ravyah": "Ra'avyah",
    "hagahotashri": "Hagahot Asheri",
    "rabbenuyerucham": "Rabbeinu Yerucham (Toldot Adam v'Chavah)",
    "eliyarabba": "Eliyah Rabbah (on Orach Chaim)",
    "tureievenroshhashana": "Turei Even (on Rosh Hashanah)",
    "ravpealim": "Rav Pe'alim (Ben Ish Chai responsa)",
    "maamarmordechai": "Maamar Mordechai (on Orach Chaim)",
    "knessethagedola": "Knesset HaGedolah",
    "hatrumah": "Sefer HaTerumah",
    "rambamseferhamitzvot": "Rambam, Sefer HaMitzvot (definitely on Sefaria)",
    "rambamhilchosmachalasasuros": "Rambam, Ma'achalot Assurot (definitely on Sefaria)",
    "rambammishnehtorahhilchottefillahubirkatcohanimchapter":
        "Rambam, Hilchot Tefillah (definitely on Sefaria)",
}

# Not Sefaria source texts at all: kashrus orgs, English handbooks, and topic /
# section headings the extractor mistook for work titles. Excluded from tiers.
NONSOURCE = {
    "stark": "Star-K (kashrus organization)",
    "childreninhalacha": "English handbook",
    "shabboskitchen": "English handbook (ArtScroll)",
    "bishulyisroel": "topic heading (laws of bishul akum), not a titled work",
    "bishulyisroelpages": "extraction noise",
}


absent = []
present_variant = []

if OFFLINE:
    if not os.path.exists(MW_PATH):
        sys.exit("--offline needs a prior data/sefaria_most_wanted.json to reuse; none found.")
    prev = json.load(open(MW_PATH))
    absent = [(d["work"], d["citations"]) for d in prev.get("absent_ranked", [])]
    present_variant = [tuple(x) for x in prev.get("present_under_variant_spelling", [])]
    absent.sort(key=lambda x: -x[1])
    print(f"[offline] reusing {len(absent)} absent works from committed dataset "
          f"(no /api/name calls)\n")
else:
    for name, n, linked in ranked[:TOP]:
        k = normkey(name)
        if linked or k in VERIFIED_PRESENT:
            continue
        if ENGLISH.search(name):
            continue  # english handbooks tracked separately
        r = presence.check(name, cache=cache)
        if r["present"]:
            present_variant.append((name, n, r["match"]))
        elif r["present"] is False:
            if is_present(name, cache):        # second-chance normalized/stripped forms
                present_variant.append((name, n, "(via normalization)"))
            else:
                absent.append((name, n))
    json.dump(cache, open(cache_path, "w"), ensure_ascii=False)

    # merge spelling-variant duplicates, incl. fuzzy (Chazon Ovadyah / Chazon Ovadia)
    import difflib

    def canon(k):  # collapse common transliteration twins before comparing
        k = k.replace("y", "i").replace("w", "v")
        k = re.sub(r"(.)\1+", r"\1", k)   # doubled letters
        return k.rstrip("h")

    absent.sort(key=lambda x: -x[1])
    clusters = []  # [canonical_name, total_n, canon_key]
    for name, n in absent:
        ck = canon(normkey(name))
        for c in clusters:
            if ck == c[2] or difflib.SequenceMatcher(None, ck, c[2]).ratio() >= 0.9:
                c[1] += n
                break
        else:
            clusters.append([name, n, ck])
    absent = sorted(((c[0], c[1]) for c in clusters), key=lambda x: -x[1])

import difflib


def era(nm):  # exact, then fuzzy, ERA lookup so spelling variants inherit the tier
    k = normkey(nm)
    if k in ERA:
        return ERA[k]
    for ek, val in ERA.items():
        if difflib.SequenceMatcher(None, k, ek).ratio() >= 0.9:
            return val
    return ("", "?")


# Pull the suspected-present and non-source works out of the absent set before
# tiering, so nothing unverified is asserted as a genuine gap.
def bucketed(nm, table):
    return table.get(normkey(nm))


verify = [(nm, n, VERIFY_PRESENCE[normkey(nm)]) for nm, n in absent if bucketed(nm, VERIFY_PRESENCE)]
nonsrc = [(nm, n, NONSOURCE[normkey(nm)]) for nm, n in absent if bucketed(nm, NONSOURCE)]
tiered = [(nm, n) for nm, n in absent
          if not bucketed(nm, VERIFY_PRESENCE) and not bucketed(nm, NONSOURCE)]

pd = [(nm, n) for nm, n in tiered if era(nm)[1] == "PD"]
mod = [(nm, n) for nm, n in tiered if era(nm)[1] == "MOD"]
unk = [(nm, n) for nm, n in tiered if era(nm)[1] == "?"]

out = {"absent_ranked": [{"work": nm, "citations": n,
        "author": era(nm)[0], "tier": era(nm)[1]}
        for nm, n in tiered],
       "pending_presence_verification": [{"work": nm, "citations": n, "likely": why}
        for nm, n, why in sorted(verify, key=lambda x: -x[1])],
       "non_source_excluded": [{"work": nm, "citations": n, "reason": why}
        for nm, n, why in sorted(nonsrc, key=lambda x: -x[1])],
       "present_under_variant_spelling": present_variant,
       "total_absent_citations": sum(n for _, n in tiered),
       "note": "Ranked by citation frequency across a 250-page Halachipedia sample. "
               "Tier-3 tail hand-classified by author era; suspected false-absents "
               "moved to pending_presence_verification."}
json.dump(out, open(MW_PATH, "w"), ensure_ascii=False, indent=1)

def clean(nm):  # strip extraction noise: trailing lone letters / volume markers
    return re.sub(r"\s+[a-zA-Z]$", "", nm).strip()


# ---- markdown brief ----
md = []
md.append("# Halachipedia's most-cited works that Sefaria doesn't have\n")
md.append("_A candidate priority list for Sefaria's library team._\n")
md.append(f"**Method.** From a {TOP}-page sample of Halachipedia, we extracted the "
          f"footnote citations, ran each through Sefaria's own `find-refs` linker, and kept "
          f"what it detected as a citation but couldn't resolve to a text. We reduced each to "
          f"its base work, counted how often it's cited, and confirmed absence via `/api/name` "
          f"(a work is 'present' if any real ref title matches, allowing for transliteration). "
          f"Works present under a variant spelling were excluded — see the tail. The Tier-3 "
          f"tail was then hand-classified by author era; entries whose absence looked doubtful "
          f"(classic rishonim/acharonim, Rambam sections) were pulled into a separate "
          f"'pending verification' list rather than asserted as gaps.\n")
md.append(f"**Result.** {len(tiered)} works confidently absent ({sum(n for _,n in tiered)} "
          f"citations), split by why they're missing. A further {len(verify)} works "
          f"({sum(n for _,n,_ in verify)} citations) await a live presence check, and "
          f"{len(nonsrc)} non-source pages are excluded.\n")

md.append("## Tier 1 — Public domain, not yet digitized\n")
md.append("_Author died >70 years ago; Sefaria can add these without licensing._\n")
md.append("| Citations | Work | Author |\n|---:|---|---|")
for nm, n in pd:
    md.append(f"| {n} | {clean(nm)} | {era(nm)[0]} |")

md.append("\n## Tier 2 — Modern / in-copyright\n")
md.append("_Recent authorities; would require a licensing arrangement. Ranked by demand._\n")
md.append("| Citations | Work | Author |\n|---:|---|---|")
for nm, n in mod:
    md.append(f"| {n} | {clean(nm)} | {era(nm)[0]} |")

md.append("\n## Tier 3 — Absent, era still uncertain\n")
md.append("_Detected as absent but author/edition ambiguous; needs a hand-check._\n")
md.append("| Citations | Work |\n|---:|---|")
for nm, n in unk:
    md.append(f"| {n} | {clean(nm)} |")

md.append("\n## Pending presence verification — likely already on Sefaria\n")
md.append("_Flagged absent by the miner, but these are classic works (or Rambam sections) "
          "Sefaria very probably already has under an embedded or abbreviated form. Queued for "
          "a live `/api/name` spot-check before any are counted as gaps — NOT asserted as "
          "wanted._\n")
md.append("| Citations | Cited-as | Likely the present work |\n|---:|---|---|")
for nm, n, why in sorted(verify, key=lambda x: -x[1]):
    md.append(f"| {n} | {clean(nm)} | {why} |")

md.append("\n## Excluded: not a Sefaria source text\n")
md.append("_Kashrus organizations, English handbooks, and topic headings the extractor "
          "mistook for work titles._\n")
md.append("| Citations | Item | What it is |\n|---:|---|---|")
for nm, n, why in sorted(nonsrc, key=lambda x: -x[1]):
    md.append(f"| {n} | {clean(nm)} | {why} |")

md.append("\n## Excluded: present under a variant spelling\n")
md.append("_Flagged absent by exact match but found on Sefaria after normalization — NOT wanted._\n")
md.append("| Cited-as | Actually on Sefaria as |\n|---|---|")
for nm, n, match in sorted(present_variant, key=lambda x: -x[1])[:40]:
    md.append(f"| {nm} | {match} |")

md.append("\n---\n_Caveats: 250-page sample (not all of Halachipedia); work-name extraction "
          "is heuristic; frequency reflects Halachipedia's Anglo-Orthodox canon, not Sefaria's "
          "whole user base. Counts are lower bounds — a work also present under one spelling and "
          "absent under another is undercounted here. Era classification of the tail is by hand "
          "from author death dates (life+70, as of 2026); entries marked 'unverified' or in the "
          "pending-verification list still need a live check._\n")
open(os.path.join(HERE, "..", "data", "SEFARIA-MOST-WANTED.md"), "w").write("\n".join(md))

print(f"{len(tiered)} genuinely-absent works, {sum(n for _,n in tiered)} citations")
print(f"  Tier1 public-domain: {len(pd)}   Tier2 modern: {len(mod)}   Tier3 uncertain: {len(unk)}")
print(f"  {len(verify)} pending presence verification ({sum(n for _,n,_ in verify)} citations)")
print(f"  {len(nonsrc)} non-source excluded; {len(present_variant)} present-under-variant")
print(f"  -> data/SEFARIA-MOST-WANTED.md, data/sefaria_most_wanted.json\n")
print("TIER 1 (public domain):")
for nm, n in pd:
    print(f"  {n:4}  {clean(nm):30} {era(nm)[0]}")
print("\nPENDING VERIFICATION (suspected false-absents):")
for nm, n, why in sorted(verify, key=lambda x: -x[1]):
    print(f"  {n:4}  {clean(nm):30} -> {why}")
