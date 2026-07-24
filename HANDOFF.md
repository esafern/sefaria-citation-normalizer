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

1. **The normalizer** (`normalizer/`) — the tier-1 deterministic layer. Resolves ~43% of
   the sheet corpus; the other ~57% is irreducibly knowledge-based (English-translated
   titles, alternate names, Hebrew) and is the job of an LLM/SLM — that's tier 2, and the
   dataset feeds it.
2. **A licensing-priority list for Sefaria** (`data/SEFARIA-MOST-WANTED.md`) — a byproduct
   that turned out to be independently valuable. See below.

## Progress so far (as of 2026-07-24)

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
  `classify_mostwanted.py`) → `data/SEFARIA-MOST-WANTED.md` + `sefaria_most_wanted.json`:
  **72 absent works / 2,750 citations**, tiered public-domain (22) vs modern (50), fully
  era-classified, with 40 false-absents (present under a variant spelling) filtered out.
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

## Next steps

1. **Grow tier 2.** The 137-pair dataset + the ~8,800 unresolved Halachipedia citations are
   raw material for an LLM/SLM that surfaces citations and generalizes transform rules. The
   dataset is the training/eval seed.
2. **Most-wanted list — pressure-test done** (see above; Tier-3 fully classified, false-absents
   and ambiguous abbreviations resolved). Remaining: widen beyond the 250-page sample to firm up
   the frequency ranking, and re-check the acharonim tier's copyright dates before outreach.
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
python3 pipeline/build_final.py            # rebuild the most-wanted list (uses work_frequency.json)
python3 -c "import json;print(len(json.load(open('data/citation_dataset.json'))))"  # 137
```
