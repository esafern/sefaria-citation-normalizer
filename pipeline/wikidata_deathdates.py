#!/usr/bin/env python3
"""Verify most-wanted authors' death years against Wikidata, and re-check
tier (public-domain vs. modern/in-copyright) against a *current* 70-years-
since-death threshold. Gentle: single-threaded, delayed, cached.

Why this exists: SEFARIA-MOST-WANTED.md's Tier 1/Tier 2 split was hand-
classified once, anchored to whatever "today" was at the time. Time keeps
passing and the table doesn't re-check itself — an author correctly modern
when the table was written can cross the 70-year threshold years later
without anyone noticing (see the Chazon Ish finding this script surfaces).
This is a one-off verification pass, not infrastructure: 71 authors, run
once, review the output by hand. See HANDOFF.md item 2 and ANALYSIS.md's
caveat about a *different* unreliable Wikidata use (title-based translation-
availability matching for works). Turns out this is NOT immune to the same
underlying problem, contrary to what was first assumed here: Wikidata's
search is exact/prefix label-alias matching, not transliteration-fuzzy, so
abbreviated Anglo-Orthodox author names ("S.Z. Auerbach") mostly miss
entities that ARE on Wikidata under a fuller name ("Shlomo Zalman
Auerbach"). Fixed with a small, bounded, hand-verified name-override table
(NAME_OVERRIDES below) rather than by pretending the mismatch away — see
that table's own comment for why a hardcoded list is legitimate here
(~50 named people) but wasn't for tractate names (open-ended spelling tail).
"""
import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date

HERE = os.path.dirname(__file__)
UA = "sefaria-citation-normalizer-research/1.0 (one-off author death-date check)"
CURRENT_YEAR = date.today().year
PD_THRESHOLD = CURRENT_YEAR - 70  # author must have died on/before this year to be PD

cache_path = os.path.join(HERE, "wikidata_deathdate_cache.json")
cache = json.load(open(cache_path)) if os.path.exists(cache_path) else {}

RABBI_KEYWORDS = re.compile(
    r"rabbi|posek|halakh|talmudist|rosh yeshiva|yeshiva|hasidic|haredi|"
    r"orthodox|dayan|kabbalist|jewish scholar", re.I)

# --- author-string cleanup -------------------------------------------------

_DEATH_YEAR = re.compile(r"\(d\.(\d{4})\)")
_CENTURY = re.compile(r"\((\d{1,2})c\)")
_YEAR_RANGE_IN_DESC = re.compile(r"\((\d{4})[–-](\d{4})\)")   # "(1878-1953)"
_BORN_IN_DESC = re.compile(r"\bborn\s+(\d{4})\b", re.I)


def clean_author(raw):
    """Return (search_name, hand_year, hand_century, no_name_recorded).

    Handles the patterns actually present in sefaria_most_wanted.json:
    "Name (d.YYYY)", "Name (NNc)", "Name, modern", "modern (R. Name)",
    "rulings of R. Name, modern", "Name1 / Name2 (d.YYYY)",
    "X on Y, modern" (compiler on subject — the compiler is the author),
    and bare "modern"/organization descriptions with no person name at all.
    """
    s = raw.strip()

    hand_year = None
    m = _DEATH_YEAR.search(s)
    if m:
        hand_year = int(m.group(1))
        s = _DEATH_YEAR.sub("", s).strip()

    hand_century = None
    m = _CENTURY.search(s)
    if m:
        hand_century = int(m.group(1))
        s = _CENTURY.sub("", s).strip()

    # "H. Schachter on R. Soloveitchik, modern" -- the compiler is the author,
    # not the subject. Must run before the "R. Name" extraction below, or
    # that pattern (unanchored \bR\.) wrongly grabs the subject's name
    # instead, since it matches anywhere in the string.
    m = re.match(r"^([A-Za-z' .]+?)\s+on\s+", s)
    if m:
        s = m.group(1).strip()
    else:
        # "modern (R. Name)" / "rulings of R. Name, modern"
        m = re.search(r"\(R\.\s*([A-Za-z' .]+?)\)", s) or re.search(r"\bR\.\s*([A-Za-z' .]+?),\s*modern", s)
        if m:
            s = m.group(1).strip()

    # "Name1 / Name2" -- prefer the fuller (longer) alt-name
    if "/" in s:
        parts = [p.strip() for p in s.split("/")]
        s = max(parts, key=len)

    s = re.sub(r",?\s*modern\s*", "", s, flags=re.I).strip(" ,")

    # Not a person name at all: bare "modern", an organization mention in
    # parens with no "R." (rabbi) prefix ("modern (Torah VeHaaretz)"), or
    # empty after cleanup.
    no_name = (not s) or bool(re.match(
        r"^(\(|on\b|rabbinical institute|modern$)", s, re.I))

    return (s if not no_name else None), hand_year, hand_century, no_name


# Wikidata's search is exact/prefix label-alias matching, not transliteration-
# fuzzy -- abbreviated Anglo-Orthodox forms ("S.Z. Auerbach", "Yitzchak
# Yosef") mostly miss entities that ARE on Wikidata under a fuller or
# differently-transliterated name ("Shlomo Zalman Auerbach", "Yitzhak
# Yosef"). This is the same underlying limitation ANALYSIS.md already found
# for title-based translation-availability matching -- entity-name matching
# against Wikidata's labels is generally this brittle, not a property
# specific to that earlier check. Bounded, hand-verified override list
# (biographical knowledge, each confirmed against Wikidata below, not
# assumed) — legitimate here because it's a *finite set of ~50 named
# people*, unlike the open-ended tractate/work-name problem this project
# deliberately avoids hardcoding. Prefix a value with "qid:" to bypass
# search entirely for a name disambiguation search can't resolve (e.g.
# "Ovadia Yosef" collides with a living namesake also described as
# "Israeli rabbi").
NAME_OVERRIDES = {
    "Yitzchak Yosef": "Yitzhak Yosef",
    "Yitzchak Yosef, modern": "Yitzhak Yosef",
    "Ovadia Yosef (d.2013)": "qid:Q467172",  # disambiguates from a living namesake
    "Y.Y. Neuwirth (d.2013)": "Yehoshua Neuwirth",
    "Malachi HaKohen (d.1772)": "Malachi HaKohen Yad Malachi",
    "S.H. Wosner (d.2015)": "Shmuel Wosner",
    "A.Y. Karelitz (d.1953)": "qid:Q543442",  # Chazon Ish
    "E. Waldenberg (d.2006)": "Eliezer Waldenberg",
    "Chida (d.1806)": "Chaim Yosef David Azulai",
    "H. da Silva (d.1698)": "Hezekiah da Silva",
    "S.Z. Auerbach (d.1995)": "Shlomo Zalman Auerbach",
    "Y.Y. Weiss (d.1989)": "Yitzchok Yaakov Weiss",
    "Y. Lorberbaum (d.1832)": "Yaakov Lorberbaum",
    "modern (R. Elyashiv)": "Yosef Shalom Elyashiv",
    "rulings of R. Elyashiv, modern": "Yosef Shalom Elyashiv",
    "Mordechai Y. Breisch (d.1976)": "Mordechai Yaakov Breisch",
    "Chavot Yair / Yair Bacharach (d.1702)": "Yair Chaim Bacharach",
    "Y.M. Tucazinsky (d.1955)": "Yechiel Michel Tucazinsky",
    "Maharsham / S. Schwadron (d.1911)": "Sholom Mordechai Schwadron",
    "A.S. Abraham (d.2010)": "Avraham Sofer Abraham",
    "H. Schachter on R. Soloveitchik, modern": "Hershel Schachter",
    "Eliezer b. Yoel HaLevi (d.1225)": "Eliezer ben Joel HaLevi",
}


# --- Wikidata -----------------------------------------------------------

def _get(url, retries=4):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    for attempt in range(retries):
        try:
            return json.loads(urllib.request.urlopen(req, timeout=15).read())
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < retries - 1:
                time.sleep(3 * (attempt + 1))  # backoff: 3s, 6s, 9s
                continue
            raise


def wikidata_search(name, limit=5):
    url = "https://www.wikidata.org/w/api.php?" + urllib.parse.urlencode({
        "action": "wbsearchentities", "search": name, "language": "en",
        "format": "json", "type": "item", "limit": limit})
    return _get(url).get("search", [])


def _entity_year(qid, prop):
    d = _get(f"https://www.wikidata.org/wiki/Special:EntityData/{qid}.json")
    claims = d.get("entities", {}).get(qid, {}).get("claims", {}).get(prop)
    if not claims:
        return None
    val = claims[0].get("mainsnak", {}).get("datavalue", {}).get("value", {})
    t = val.get("time")
    m = re.match(r"[+-](\d+)-", t or "")
    return int(m.group(1)) if m else None


def _entity_label_description(qid):
    d = _get(f"https://www.wikidata.org/wiki/Special:EntityData/{qid}.json")
    ent = d.get("entities", {}).get(qid, {})
    label = ent.get("labels", {}).get("en", {}).get("value", qid)
    desc = ent.get("descriptions", {}).get("en", {}).get("value", "")
    return label, desc


def lookup(name):
    """Return {qid, label, description, death_year, birth_year, confident} or None.
    `name` may be "qid:Q123" to fetch a known entity directly, bypassing
    search (for cases search can't disambiguate)."""
    if name in cache:
        return cache[name]
    result = None
    if name.startswith("qid:"):
        qid = name[len("qid:"):]
        try:
            label, desc = _entity_label_description(qid)
            time.sleep(0.6)
            death_year = _entity_year(qid, "P570")
            time.sleep(0.6)
            birth_year = _entity_year(qid, "P569")
            time.sleep(0.6)
            result = {"qid": qid, "label": label, "description": desc,
                      "death_year": death_year, "birth_year": birth_year, "confident": True}
        except Exception as e:
            # Don't cache transient failures (rate limits, timeouts) as if
            # permanent -- a re-run should retry these, not replay the error
            # forever the way it would if this were written to `cache`.
            return {"error": str(e)}
        cache[name] = result
        json.dump(cache, open(cache_path, "w"), ensure_ascii=False, indent=1)
        return result
    try:
        candidates = wikidata_search(name)
        time.sleep(0.6)
        ranked = sorted(candidates, key=lambda c: bool(RABBI_KEYWORDS.search(
            c.get("display", {}).get("description", {}).get("value", ""))), reverse=True)
        if ranked:
            top = ranked[0]
            desc = top.get("display", {}).get("description", {}).get("value", "")
            qid = top["id"]
            confident = bool(RABBI_KEYWORDS.search(desc))
            m = _YEAR_RANGE_IN_DESC.search(desc)
            if m:
                birth_year, death_year = int(m.group(1)), int(m.group(2))
            else:
                birth_year = None
                death_year = _entity_year(qid, "P570")
                time.sleep(0.6)
                if birth_year is None:
                    birth_year = _entity_year(qid, "P569")
                    time.sleep(0.6)
                bm = _BORN_IN_DESC.search(desc)
                if birth_year is None and bm:
                    birth_year = int(bm.group(1))
            result = {"qid": qid, "label": top.get("label"), "description": desc,
                      "death_year": death_year, "birth_year": birth_year,
                      "confident": confident}
    except Exception as e:
        return {"error": str(e)}
    cache[name] = result
    json.dump(cache, open(cache_path, "w"), ensure_ascii=False, indent=1)
    return result


# --- main -----------------------------------------------------------------

def main():
    mw = json.load(open(os.path.join(HERE, "..", "data", "sefaria_most_wanted.json")))
    findings = {"tier_flips": [], "year_mismatches": [], "no_name_recorded": [],
                "no_wikidata_match": [], "low_confidence": [], "confirmed": []}

    for entry in mw["absent_ranked"]:
        work, tier, author_raw = entry["work"], entry["tier"], entry["author"]
        name, hand_year, hand_century, no_name = clean_author(author_raw)
        name = NAME_OVERRIDES.get(author_raw, name)

        if no_name:
            findings["no_name_recorded"].append({"work": work, "author": author_raw})
            continue

        wd = lookup(name)
        if not wd or wd.get("error") or not wd.get("qid"):
            findings["no_wikidata_match"].append({"work": work, "author": author_raw, "searched": name})
            continue

        wd_year = wd.get("death_year")
        row = {"work": work, "tier": tier, "author": author_raw, "searched": name,
               "wikidata_label": wd.get("label"), "wikidata_description": wd.get("description"),
               "wikidata_death_year": wd_year, "hand_year": hand_year, "hand_century": hand_century,
               "confident": wd.get("confident")}

        if not wd.get("confident"):
            findings["low_confidence"].append(row)
            continue

        if wd_year is None:
            # No death date on Wikidata at all -> presumed living, consistent with "modern"
            findings["confirmed"].append(row)
            continue

        correct_tier = "PD" if wd_year <= PD_THRESHOLD else "MOD"
        if correct_tier != tier:
            row["correct_tier"] = correct_tier
            row["years_since_death"] = CURRENT_YEAR - wd_year
            findings["tier_flips"].append(row)
        elif hand_year is not None and hand_year != wd_year:
            findings["year_mismatches"].append(row)
        else:
            findings["confirmed"].append(row)

    out_path = os.path.join(HERE, "..", "data", "wikidata_deathdate_findings.json")
    json.dump(findings, open(out_path, "w"), ensure_ascii=False, indent=1)

    print(f"=== Wikidata author death-date check (PD threshold: died <= {PD_THRESHOLD}, "
          f"i.e. 70+ years before {CURRENT_YEAR}) ===\n")
    print(f"TIER FLIPS (currently misclassified) — {len(findings['tier_flips'])}:")
    for r in findings["tier_flips"]:
        print(f"  {r['work']}: {r['author']!r} -> Wikidata death {r['wikidata_death_year']} "
              f"({r['years_since_death']} yrs ago) -> should be {r['correct_tier']}, currently {r['tier']}")
    print(f"\nYEAR MISMATCHES (hand-entered vs. Wikidata, same tier either way) — {len(findings['year_mismatches'])}:")
    for r in findings["year_mismatches"]:
        print(f"  {r['work']}: hand={r['hand_year']} vs Wikidata={r['wikidata_death_year']} ({r['wikidata_label']})")
    print(f"\nNO AUTHOR NAME RECORDED (can't check) — {len(findings['no_name_recorded'])}:")
    for r in findings["no_name_recorded"]:
        print(f"  {r['work']}: {r['author']!r}")
    print(f"\nNO WIKIDATA MATCH — {len(findings['no_wikidata_match'])}:")
    for r in findings["no_wikidata_match"]:
        print(f"  {r['work']}: searched {r['searched']!r}")
    print(f"\nLOW CONFIDENCE (top match not clearly a rabbi/scholar) — {len(findings['low_confidence'])}:")
    for r in findings["low_confidence"]:
        print(f"  {r['work']}: {r['searched']!r} -> {r['wikidata_label']} ({r['wikidata_description']})")
    print(f"\nCONFIRMED (matches hand-entry or correctly no death date) — {len(findings['confirmed'])}")
    print(f"\nFull detail written to {out_path}")


if __name__ == "__main__":
    main()
