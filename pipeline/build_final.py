#!/usr/bin/env python3
"""Final most-wanted builder: robust presence test + curated annotation.

Uses presence.check (prefix/fuzzy match against ref completions) over the most-
cited works, minus a small set of works I verified present under an abbreviation
or embedded layer that the trie can't reach by prefix. Emits JSON + a readable
markdown brief for Sefaria, tiered into public-domain (digitize) vs modern
(license).
"""
import json, os, re, sys
import presence
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from normalizer import rules

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

TOP = 250
ENGLISH = re.compile(r"\bHalachos of\b|\bLaws of\b|Handbook|by Rabbi|\bThe \b|Melachos|Guide", re.I)

# Verified present by hand (trie can't reach them by prefix): abbreviations and
# layers embedded in a parent work. Checked live against /api/name.
VERIFIED_PRESENT = {"benishchai", "gra", "shaarhatziyun", "shaarhatzion",
                    "nodehbeyehuda", "nodabeyehuda", "maggidmishna", "chokyaakov"}

# Re-verified live against /api/name (2026-07): present on Sefaria under a title
# the presence trie can't reach by prefix (an abbreviation, a reordered/embedded
# form, or a "Responsa/Teshuvot..." prefix). Routed to the present-under-variant
# section, never listed as absent. Value = the authoritative Sefaria title.
KNOWN_PRESENT = {
    "sma": "Me'irat Einayim on Shulchan Arukh, Choshen Mishpat",
    "sama": "Me'irat Einayim on Shulchan Arukh, Choshen Mishpat",
    "rabbenuyonah": "Rabbeinu Yonah on Berakhot; Sha'arei Teshuvah",
    "rashbaresponsa": "Teshuvot haRashba (parts I-VII)",
    "rambamseferhamitzvot": "Sefer HaMitzvot",
    "rambamhilchosmachalasasuros": "Mishneh Torah, Forbidden Foods",
    "rambammishnehtorahhilchottefillahubirkatcohanimchapter":
        "Mishneh Torah, Prayer and the Priestly Blessing",
}

# Not Hebrew seforim Sefaria would license — English practical guides or a
# kashrut agency, not a text. Dropped from the list entirely.
NON_TEXT = {"stark", "shabboskitchen", "childreninhalacha",
            "bishulyisroel", "bishulyisroelpages"}

# Section markers severed from a parent work by the extractor, not works
# themselves: "Vezot Habracha" is a parsha section of Ben Ish Chai / Maharam Shik
# / etc.; "Purim" is the Purim volume of Chazon Ovadia. (Confirmed in the raw
# Halachipedia citations.) The parent-attributed variants are folded elsewhere;
# these bare fragments can't be attributed, so they're dropped.
NOISE = {"purim", "vezothabracha", "vezothabrachap"}

# Spelling twins / abbreviations the fuzzy collapse missed -> canonical display.
ALIAS = {
    "yachavadaat": "Yechave Daat", "chelkesbinyomin": "Chelkat Binyamin",
    "shtigrotmoshe": "Igrot Moshe", "shtshevethalevi": "Shevet Halevi",
    "rivivotephraim": "Rivevot Efraim",
    "vehanhagot": "Teshuvot VeHanhagot", "vihanhagot": "Teshuvot VeHanhagot",
    "teshuvosvhanhagos": "Teshuvot VeHanhagot",
}
# Section-volumes that fold into their parent work (one work to license/digitize).
# Prefix-keyed so every spelling variant of the parent collapses too.
FOLD = {"yalkutyosef": "Yalkut Yosef", "chazonovad": "Chazon Ovadyah",
        "hazonovad": "Chazon Ovadyah"}


def remap(name):
    """Collapse spelling twins and section-volumes to one canonical work name
    before clustering, so the count and citation totals aren't fragmented."""
    k = normkey(name)
    if k in ALIAS:
        return ALIAS[k]
    for pk, disp in FOLD.items():
        if k.startswith(pk):
            return disp
    return name

# Author era for the top works -> tier. PD = public domain (digitize); MOD =
# modern/in-copyright (license). Keyed by normalized work name.
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
    # ---- Tier-3 tail hand-classified 2026-07 (era by author death year) ----
    # Public domain (author d. >70y ago):
    "eliyarabba": ("Eliyahu Shapira (d.1712)", "PD"),
    "radvaz": ("David ibn Zimra (d.1573); responsa absent, MT commentary present", "PD"),
    "hagahotmaimoniyot": ("Meir HaKohen (13c)", "PD"),
    "betefraim": ("E.Z. Margolis (d.1828)", "PD"),
    "knessethagedola": ("Chaim Benveniste (d.1673)", "PD"),
    "maamarmordechai": ("Mordechai Carmi (d.1825)", "PD"),
    "darkeiteshuva": ("Tzvi Hirsch Shapira (d.1913)", "PD"),
    "ravyah": ("Eliezer b. Yoel HaLevi (d.1225)", "PD"),
    "hagahotashri": ("Israel of Krems (14c)", "PD"),
    "avneinezer": ("Avraham Bornsztain (d.1910)", "PD"),
    "sidreitahara": ("Elchanan Ashkenazi (d.1780)", "PD"),
    "tureievenroshhashana": ("Aryeh Leib Ginzburg (d.1785)", "PD"),
    "rabbenuyerucham": ("Yerucham b. Meshullam (14c)", "PD"),
    "maharamshik": ("Moshe Schick (d.1879)", "PD"),
    "mishkenotyakov": ("Yaakov of Karlin (d.1844)", "PD"),
    "gesherhachaim": ("Y.M. Tucazinsky (d.1955)", "PD"),
    "hatrumah": ("Baruch b. Isaac of Worms (13c)", "PD"),
    "daattorah": ("Maharsham / S. Schwadron (d.1911)", "PD"),
    # Modern / in-copyright:
    "rivevotefraim": ("Efraim Greenblatt (d.2014)", "MOD"),
    "beermoshe": ("Moshe Stern (d.1997)", "MOD"),
    "orchotshabbatv": ("modern", "MOD"),
    "minchatasher": ("Asher Weiss, modern", "MOD"),
    "teshuvotvehanhagot": ("Moshe Sternbuch, modern", "MOD"),
    "mishnehhalachot": ("Menashe Klein (d.2011)", "MOD"),
    "birkathashem": ("modern", "MOD"),
    "ashreihaish": ("rulings of R. Elyashiv, modern", "MOD"),
    "chutshani": ("Nissim Karelitz (d.2019)", "MOD"),
    "shalmeiyehuda": ("modern (R. Elyashiv)", "MOD"),
    "hartzvi": ("Tzvi Pesach Frank (d.1960)", "MOD"),
    "chelkatyakov": ("Mordechai Y. Breisch (d.1976)", "MOD"),
    "horahbrurah": ("modern", "MOD"),
    "ateretpaz": ("Pinchas Zvichi, modern", "MOD"),
    "isheiyisrael": ("A.Y. Pfoifer, modern", "MOD"),
    "shevethakehati": ("Shammai Gross, modern", "MOD"),
    "milvehhashem": ("modern", "MOD"),
    "tiltuleishabbat": ("modern", "MOD"),
    "nishmatavraham": ("A.S. Abraham (d.2010)", "MOD"),
    "shulchanshlomo": ("S.Z. Auerbach (d.1995)", "MOD"),
    "divreiyatziv": ("Y.Y. Halberstam (d.1994)", "MOD"),
    "dorhamelaktimv": ("modern", "MOD"),
    "aznidbaru": ("Binyamin Zilber (d.2008)", "MOD"),
    "agurbohalecha": ("modern", "MOD"),
    "yaskilavdi": ("Ovadia Hedaya (d.1969)", "MOD"),
    "maharshag": ("Shmuel Engel (d.1935)", "PD"),
    # Disambiguated from the raw Halachipedia citation context:
    "mekorchaim": ("Chavot Yair / Yair Bacharach (d.1702)", "PD"),  # cited by OC siman
    "halichotolam": ("Yitzchak Yosef, modern", "MOD"),  # parsha-ordered, multi-volume
}


def normkey(w):
    return re.sub(r"[^a-z]", "", w.lower())


absent = []
present_variant = []
for name, n, linked in ranked[:TOP]:
    k = normkey(name)
    if linked or k in VERIFIED_PRESENT:
        continue
    if k in NON_TEXT or k in NOISE:
        continue  # English guide / non-text source, or mis-detected holiday/parsha
    if k in KNOWN_PRESENT:                  # re-verified live: present under a variant title
        present_variant.append((name, n, KNOWN_PRESENT[k]))
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
            absent.append((remap(name), n))  # fold twins/section-volumes before clustering
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

def era(nm):  # exact, then fuzzy, ERA lookup so spelling variants inherit the tier
    k = normkey(nm)
    if k in ERA:
        return ERA[k]
    for ek, val in ERA.items():
        if difflib.SequenceMatcher(None, k, ek).ratio() >= 0.9:
            return val
    return ("", "?")

pd = [(nm, n) for nm, n in absent if era(nm)[1] == "PD"]
mod = [(nm, n) for nm, n in absent if era(nm)[1] == "MOD"]
unk = [(nm, n) for nm, n in absent if era(nm)[1] == "?"]

out = {"absent_ranked": [{"work": nm, "citations": n,
        "author": era(nm)[0], "tier": era(nm)[1]}
        for nm, n in absent],
       "present_under_variant_spelling": present_variant,
       "total_absent_citations": sum(n for _, n in absent),
       "note": "Ranked by citation frequency across a 250-page Halachipedia sample."}
json.dump(out, open(os.path.join(HERE, "..", "data", "sefaria_most_wanted.json"), "w"),
          ensure_ascii=False, indent=1)

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
          f"(a work is 'present' if any real ref title matches, allowing for transliteration and "
          f"for titles stored under a `Teshuvot`/`Responsa` prefix). Every candidate was "
          f"re-verified live against `/api/name` (2026-07): works present under a variant or "
          f"abbreviated spelling were excluded (see the tail), spelling twins and section-volumes "
          f"were merged into one work, and mis-detected non-texts were dropped.\n")
md.append(f"**Result.** {len(absent)} works, {sum(n for _,n in absent)} citations. Split by why "
          f"they're missing:\n")

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

if unk:
    md.append("\n## Tier 3 — Absent, era not yet classified\n")
    md.append("_Detected as absent; author/copyright status not hand-checked. Longer tail._\n")
    md.append("| Citations | Work |\n|---:|---|")
    for nm, n in unk:
        md.append(f"| {n} | {clean(nm)} |")

md.append("\n## Excluded: present under a variant spelling\n")
md.append("_Flagged absent by exact match but found on Sefaria after normalization — NOT wanted._\n")
md.append("| Cited-as | Actually on Sefaria as |\n|---|---|")
for nm, n, match in sorted(present_variant, key=lambda x: -x[1])[:40]:
    md.append(f"| {nm} | {match} |")

md.append("\n---\n_Caveats: 250-page sample (not all of Halachipedia); work-name extraction "
          "is heuristic; frequency reflects Halachipedia's Anglo-Orthodox canon, not Sefaria's "
          "whole user base. Counts are lower bounds — a work also present under one spelling and "
          "absent under another is undercounted here. Era is classified by author death year "
          "(work-level, from the citation context where the title alone is ambiguous)._\n")
open(os.path.join(HERE, "..", "data", "SEFARIA-MOST-WANTED.md"), "w").write("\n".join(md))

print(f"{len(absent)} genuinely-absent works, {sum(n for _,n in absent)} citations")
print(f"  Tier1 public-domain: {len(pd)}   Tier2 modern: {len(mod)}   Tier3 unclassified: {len(unk)}")
print(f"  {len(present_variant)} excluded (present under variant spelling)")
print(f"  -> data/SEFARIA-MOST-WANTED.md, data/sefaria_most_wanted.json\n")
print("TOP 25 ABSENT:")
for nm, n in absent[:25]:
    a, t = era(nm)
    print(f"  {n:4}  [{t:3}]  {clean(nm):30} {a}")
