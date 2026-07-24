#!/usr/bin/env python3
"""Live presence spot-check for the 'pending_presence_verification' works.

Those 18 works are cited-as abbreviations / short-forms (Sma, Radvaz, Rambam
sections, classic rishonim) whose 'absent' flag we distrust: no transliteration
rule can bridge an abbreviation to its Sefaria title, so build_final.py parks
them pending a live check instead of asserting them as gaps. This script does
that check against /api/name — using hand-supplied probe spellings (the real
Sefaria-ish titles the short-form maps to) plus the normalizer's own candidates
— and records a verdict per work in pipeline/pending_resolved.json.

build_final.py reads that file: PRESENT works move to the 'present under a
variant spelling' exclusion; STILL-ABSENT works drop out of pending and tier by
era (a pre-seeded era is applied, so a verified-absent rishon lands in Tier 1).

Needs Sefaria egress (blocked in the web sandbox — a 403 from the proxy means
this must run from a session whose network policy allows www.sefaria.org).
Gentle: single-threaded, cached, delayed.

    python3 pipeline/verify_pending.py        # probe live, write verdicts
    python3 pipeline/build_final.py --offline  # regenerate the list from them
"""
import json, os, re, sys
import presence
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from normalizer import rules

HERE = os.path.dirname(__file__)
MW_PATH = os.path.join(HERE, "..", "data", "sefaria_most_wanted.json")
cache_path = os.path.join(HERE, "verify_pending_cache.json")
cache = json.load(open(cache_path)) if os.path.exists(cache_path) else {}


def norm(w):
    return re.sub(r"[^a-z]", "", w.lower())


# Hand-supplied probe spellings: the real Sefaria-ish titles each abbreviation or
# short-form maps to. This is the knowledge no transliteration rule encodes.
# Keyed by the normalized cited-as name.
PROBES = {
    "sma": ["Sefer Meirat Einayim", "Meirat Einayim", "Sma"],
    "sama": ["Sefer Meirat Einayim", "Meirat Einayim", "Sama"],
    "radvaz": ["Radbaz", "Teshuvot HaRadbaz", "Radvaz"],
    "hagahotmaimoniyot": ["Hagahot Maimoniyot", "Haggahot Maimoniyot", "Hagahot Maimuniyot"],
    "rabbenuyonah": ["Rabbeinu Yonah", "Shaarei Teshuvah", "Rabbeinu Yonah on Pirkei Avot",
                     "Rabbeinu Yonah on Berakhot"],
    "rashbaresponsa": ["Teshuvot HaRashba", "Responsa of the Rashba", "Rashba"],
    "ravyah": ["Raavyah", "Ra'avyah", "Ravyah", "Rabiah"],
    "hagahotashri": ["Hagahot Asheri", "Haggahot Asheri", "Hagahot Ashri"],
    "rabbenuyerucham": ["Rabbeinu Yerucham", "Toldot Adam veChavah", "Toldot Adam ve-Chavah"],
    "eliyarabba": ["Eliyah Rabbah", "Eliyahu Rabbah", "Elyah Rabbah", "Eliya Rabba"],
    "tureievenroshhashana": ["Turei Even", "Turei Even on Rosh Hashanah"],
    "ravpealim": ["Rav Pealim", "Rav Poalim", "Rav Pe'alim"],
    "maamarmordechai": ["Maamar Mordechai", "Maamar Mordekhai"],
    "knessethagedola": ["Knesset HaGedolah", "Kenesset HaGedolah", "Knesses HaGedolah"],
    "hatrumah": ["Sefer HaTerumah", "HaTerumah"],
    "rambamseferhamitzvot": ["Sefer HaMitzvot", "Rambam Sefer HaMitzvot"],
    "rambamhilchosmachalasasuros": ["Mishneh Torah, Forbidden Foods", "Maachalot Assurot"],
    "rambammishnehtorahhilchottefillahubirkatcohanimchapter":
        ["Mishneh Torah, Prayer and the Priestly Blessing", "Mishneh Torah, Prayer"],
}


def probe(work):
    """Try the raw name, the normalizer's candidates, then the hand probes.
    First title that resolves on Sefaria => present."""
    queries = [work] + rules.candidates(work) + PROBES.get(norm(work), [])
    for q in dict.fromkeys(queries):        # dedupe, preserve order
        if len(q) < 3:
            continue
        r = presence.check(q, cache=cache)
        if r["present"]:
            return {"verdict": "present", "match": r["match"], "via": q}
        if r["present"] is None:            # network/error — don't cache a false 'absent'
            return {"verdict": "error", "match": r["match"], "via": q}
    return {"verdict": "absent", "match": None, "via": None}


def main():
    if not os.path.exists(MW_PATH):
        sys.exit("no data/sefaria_most_wanted.json — run build_final.py first.")
    pending = json.load(open(MW_PATH)).get("pending_presence_verification", [])
    if not pending:
        print("nothing pending — pending_presence_verification is empty.")
        return

    resolved, report, errors = {}, [], []
    for item in pending:
        work, n = item["work"], item["citations"]
        res = probe(work)
        res.update({"work": work, "citations": n})
        if res["verdict"] == "error":
            errors.append((n, work, res))
            continue                        # leave unresolved; re-run when network is up
        resolved[norm(work)] = res
        report.append((n, work, res))

    json.dump(cache, open(cache_path, "w"), ensure_ascii=False)
    resolved_path = os.path.join(HERE, "pending_resolved.json")
    # merge with any prior verdicts so partial/repeated runs accumulate
    prior = json.load(open(resolved_path)) if os.path.exists(resolved_path) else {}
    prior.update(resolved)
    json.dump(prior, open(resolved_path, "w"), ensure_ascii=False, indent=1)

    present = sorted([r for r in report if r[2]["verdict"] == "present"], key=lambda x: -x[0])
    absent = sorted([r for r in report if r[2]["verdict"] == "absent"], key=lambda x: -x[0])

    if errors:
        print(f"!! {len(errors)} works errored (Sefaria unreachable?) — left unresolved. "
              f"First: {errors[0][1]} -> {errors[0][2]['match']}\n")
    print(f"verified {len(report)} pending works: {len(present)} PRESENT, "
          f"{len(absent)} still absent\n")
    for n, w, r in present:
        print(f"  PRESENT  {n:4}  {w:36} -> {r['match']}   (via '{r['via']}')")
    print()
    for n, w, r in absent:
        print(f"  absent   {n:4}  {w}")
    print(f"\nwrote {os.path.relpath(resolved_path)} "
          f"({len(prior)} total verdicts).")
    print("next: python3 pipeline/build_final.py --offline   (or live) to regenerate the list.")


if __name__ == "__main__":
    main()
