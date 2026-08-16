# Sefaria Citation Normalizer — Project Handoff

_A starting brief for a fresh Claude Code session. Read this, then `README.md`._

## The goal

Turn messy, transliterated Anglo-Orthodox Torah citations (`ArtScroll Berachos 57b`,
`O.Ch. 271:1`, `Hil. M'lachim`) into canonical Sefaria references — **without the
insanely long whitelists of special cases** that this normally requires. The insight
that makes it work: don't try to compute Sefaria's canonical name (it's unpredictable —
sometimes a transliteration, sometimes an English translation). Instead **propose many
plausible normalized forms and let Sefaria's `/api/name` say which is real.** Rules can be
sloppy; over-generation is cheap; a wrong candidate just doesn't resolve, so the system
fails safe (unlinked, never mislinked).

This is complementary to Sefaria's own ML linker (`find-refs`), not a replacement — it
targets the dialect shorthand the linker's training data doesn't cover, and runs
deterministically with no model at link time.

## Two things this repo produces

1. **The normalizer** (`normalizer/`) — the tier-1 deterministic layer. Resolves 101/139
   (72%) of the verified corpus as of 2026-08-05 (`python3 benchmark.py`; up from ~43% at
   this file's last full rewrite — see "Progress so far" below for what moved it). The
   remainder is irreducibly knowledge-based (English-translated titles, alternate names,
   Hebrew) and is the job of an LLM/SLM — that's tier 2, and the dataset feeds it.
2. **A licensing-priority list for Sefaria** (`data/SEFARIA-MOST-WANTED.md`) — a byproduct
   that turned out to be independently valuable. See below.

## Progress so far (as of 2026-07-24, with a 2026-08-05 update below)

- **2026-08-05**: rule coverage jumped from 79/139 to 101/139 (56% -> 72%) after replacing
  a hand-typed tractate-spelling list with a resolver pass that canonicalizes tractate
  names live via Sefaria's own `/api/name` completions. Details in "Relationship to the
  blog repo" below and in `INTEGRATION-PLAN.md`.
- **`data/citation_dataset.json`** — 137 verified `raw → Sefaria ref` pairs, mined from
  `find-refs` failures over 289 source sheets, LLM-labeled, Sefaria-verified. `my_canonical`
  is the labeler's guess; `sefaria_ref` is Sefaria's authoritative answer (they differ in
  ~14 cases — that gap is exactly why propose→verify beats compute-the-name).
- **Normalizer + benchmark** — `benchmark.py` tracks the ~43% deterministic ceiling. Rule
  families: Ashkenazi endings, edition/prefix strip, Rambam-section map, note-tail strip.
- **Halachipedia phase** — `pipeline/halachipedia_mine.py` mined a 250-page sample:
  14,511 detections → 3,520 distinct works. `hp_failures.json` (8,990 distinct unresolved),
  `hp_resolve.py` auto-resolved 200 via rules (a 2% hit rate — the honest cross-genre
  generalization finding).
- **Most-wanted list** — `pipeline/build_final.py` (+ `presence.py`, `build_mostwanted.py`,
  `classify_mostwanted.py`) → `data/SEFARIA-MOST-WANTED.md` + `sefaria_most_wanted.json`.
  Now built from the **full 640-page Halachipedia corpus** (38,195 detections): **71 absent
  works / 6,771 citations**, tiered public-domain (21) vs modern (50), fully era-classified,
  36 false-absents filtered out. See `CORPUS-COMPARISON.md` for the full-vs-250-page diff.
- **Full-corpus widening (done 2026-07)** — `mine_wide.py` mined pages 250–640 gently/serially;
  `merge_frequency.py` summed the new cache with the committed 0–250 reduction (disjoint ranges,
  no re-mining). Finding: the corpus grew 2.6× but the work count held (72→71) — the extra data
  reinforced the R. Ovadia Yosef concentration (~2,300 of 6,771 cites) rather than broadening.
- **Most-wanted pressure-test (done 2026-07)** — re-verified every candidate live against
  `/api/name`: removed 8 false-absents present under a title the prefix-trie couldn't reach
  (Sma, Rabbenu Yonah, Rambam/Mishneh-Torah wrappers, …), merged spelling twins and folded
  section-volumes into parents (Yalkut Yosef → 428, Chazon Ovadyah → 260), hand-classified the
  whole Tier-3 tail (0 left unclassified), and dropped non-texts / mis-split section markers.
  Fixed a real `presence.py` bug: the fuzzy matcher collapsed equal-length one-letter names
  (Maharshag/Maharsham/Maharshal) — now rejects same-length substitutions for single tokens and
  strips `Teshuvot`/`Responsa` title prefixes before matching.

## Key architecture notes

- **`/api/name`** is a trie autocompleter that returns `is_ref`/`completions`/
  `completion_objects`. Space must be `%20`-encoded, not `+`. A work is "present" if a
  ref-type completion's title begins with the query words (fuzzy per word, to absorb
  transliteration). This presence test lives in `pipeline/presence.py`.
- **`find-refs`** is the async ML linker: POST → `task_id` → poll `GET /api/async/{id}`.
- **Be a polite guest.** All API access is paced (delays, low concurrency) and cached. The
  raw caches (`hp_cache/` 7 MB, `*_cache.json`) are **gitignored but regenerable** — if you
  reproduce the mining, keep it gentle; don't hammer Sefaria's find-refs.

## Relationship to the blog repo

This work spun out of `~/work/rav-shvat-blog`, which has its own embedded copy of the linker
(`pipeline/sefaria_linker/`) that the blog build actually uses. R&D happens here; keep the
two from drifting. `SEFARIA-API-BUG.md` / `SEFARIA-CONTRIB-DRAFTS.md` currently live in the
blog repo but document Sefaria issues — candidates to move here.

**They had drifted** (found 2026-08-05: an abbreviation fix had to be made twice by hand,
in two different rule syntaxes, because nothing shared code between the repos). **Fixed
2026-08-05**: `normalizer/shared_dialect.py` is now vendored byte-identically into both
repos (`SECTIONS`, `RAMBAM_SECTIONS`, `PREFIXES`, `TRACTATES`, `TRACTATE_ALIASES`), each
repo's local candidate-generation/URL-construction logic delegates to it, and
`test_shared_dialect.py` in each repo fails loudly the moment the two copies diverge
(skips, doesn't fail, if the sibling repo isn't checked out).

Tractate-name spelling (Brachot/Berakhot, Psachim/Pesachim, ...) is deliberately **not**
handled by a hand-typed list in the propose-verify path (`normalizer/resolve.py` here, the
blog's `resolver.py`) — such a list can never keep up with every transliteration. Both now
canonicalize the bare tractate word live via Sefaria's own `/api/name` completions instead.
`benchmark.py` went from 79/139 to **101/139** as a result. `TRACTATE_ALIASES` still exists
in the shared file only for `offline.py`'s no-network path, which has no oracle to call.
Full history is in **[`INTEGRATION-PLAN.md`](INTEGRATION-PLAN.md)** — worth reading before
touching either linker's dialect layer, since it explains the boundary and a bug (silently
excluding Tosefta/Mishnah from canonicalization) that was found and fixed along the way.

**Still open, partially de-risked (2026-08-16)**: re-running the linker over the real
118-letter + 6-Q&A corpus to confirm nothing regressed post-integration (plan step 6) has
still not been done in its literal form (rebuild from source, diff old vs. new resolution)
— that content lives in the blog's `content.db` / live WordPress site, not files, so a true
regression diff still needs a deliberate pass. What *did* happen 2026-08-16: a full
content-integrity + link-validity audit of all 253 live posts (`check_site.py`, plus a
targeted cross-check of every "context-risky" cache key against live links) found zero
broken or invalid Sefaria links anywhere in the corpus — indirect evidence against a
resolution regression, though not the rigorous before/after diff step 6 asks for. It did
find one unrelated, pre-existing defect (a context-blind cache mislink predating the
Aug 6 dialect work, in "Ya'akov Dons Esav's Arms" — fixed). Full detail in the blog repo's
`HANDOFF.md`, "Correction (2026-08-16)" note.

## Next steps

0. ~~Integrate the shared dialect layer with the blog repo~~ — done 2026-08-05, see above.
1. **Grow tier 2.** The 137-pair dataset + the ~8,800 unresolved Halachipedia citations are
   raw material for an LLM/SLM that surfaces citations and generalizes transform rules. The
   dataset is the training/eval seed.
2. **Most-wanted list — pressure-test + full-corpus rebuild done** (see above; whole 640-page
   site mined, Tier-3 fully classified, false-absents and ambiguous abbreviations resolved).
   **Copyright-date re-check done (2026-08-05)** — `pipeline/wikidata_deathdates.py` cross-checked
   Tier 1/2 authors' death years against Wikidata. Found and fixed a real, live case: **Chazon
   Ish** (d.1953) had quietly aged past the 70-years-since-death public-domain threshold since
   this list was first classified and is now correctly Tier 1, not Tier 2 — the concrete proof
   that these tables need *periodic* re-checking, not a one-time classification. Also corrected
   Rokeach's death year (1230 -> 1238). 38/55 checkable authors confirmed; 16 had no confident
   Wikidata match (mostly obscure/century-only figures, not in doubt); 15 have no individual
   author name recorded at all. Full detail in `data/SEFARIA-MOST-WANTED.md`'s "Copyright-date
   re-check" note and `data/wikidata_deathdate_findings.json`. Worth re-running periodically.
   - Correction to what this item originally assumed: death-year lookup by author name was
     expected to sidestep the entity-matching brittleness `ANALYSIS.md`'s translation-
     availability check ran into (see below) — that assumption was wrong. Wikidata's search is
     exact/prefix label-alias matching, not transliteration-fuzzy, so abbreviated Anglo-Orthodox
     names ("S.Z. Auerbach") mostly missed entities that ARE on Wikidata under a fuller name
     ("Shlomo Zalman Auerbach"), and one very-online figure ("Ovadia Yosef") collided with a
     living namesake. Worked around with a small, bounded, hand-verified name-override table in
     the script (~20 entries) — legitimate there because it's a finite set of named people, not
     an open-ended spelling tail like the tractate-name problem earlier in this file.
   - **Open issue, not the same task**: `data/ANALYSIS.md`'s "Existing translations to
     license?" section (the *translation-availability* judgment, not copyright dates) is a
     domain assessment, not machine-verified — an automated Wikipedia/Wikidata check was
     tried there and found unreliable (thin coverage, poor title matching for these works).
     Getting a definitive answer needs a library-catalog (WorldCat/publisher) pass instead.
3. **Contribute to Sefaria — when it's "truly real."** The strongest form isn't a repo link
   but a PR / data contribution into Sefaria's own repos: the dataset (as linker eval cases),
   the dialect map, and the most-wanted list (for their library/licensing team). Hold outreach
   until the deliverable is polished — the owner's explicit call.

## Provenance & privacy

**Public data only** (Sefaria API, public Halachipedia via its MediaWiki API). No private or
personal material — this repo is safe to open-source when ready. Nothing here is
author-specific, by design, to avoid one-author overfitting.

## Quick orientation

```bash
python3 benchmark.py                       # rule coverage vs the verified dataset
python3 test_shared_dialect.py             # diff-check vs the blog repo's vendored copy
python3 pipeline/build_final.py            # rebuild the most-wanted list (uses work_frequency.json)
python3 -c "import json;print(len(json.load(open('data/citation_dataset.json'))))"  # 137
```
