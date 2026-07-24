# Sefaria Citation Normalizer — Project Handoff

_A starting brief for a fresh Claude Code session. Read this, then `README.md`._

**Active branch / PR:** work is on `claude/project-onboarding-status-lw5947`, open as
[PR #1](https://github.com/esafern/sefaria-citation-normalizer/pull/1). Pushing more commits to
that branch updates the PR — don't open a new one. (The repo has no CI configured.)

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
  103 absent works / ~2,900 citations, tiered public-domain vs modern, with 33 false-absents
  (present under a variant spelling) filtered out via the normalizer's own candidates.
- **Tier-3 era pass (2026-07)** — the ~75-work "era not classified" tail was hand-classified
  from author death dates (life+70): now 11 PD / 66 MOD / 3 genuinely-uncertain. 18 suspected
  false-absents (classic rishonim/acharonim + Rambam sections + the flagged abbreviations Sma,
  Radvaz) were pulled into a new `pending_presence_verification` bucket — **not** asserted as
  gaps, queued for the live `/api/name` spot-check. 5 non-source items (Star-K, English
  handbooks, topic headings) excluded. `build_final.py` gained an `--offline` mode that reuses
  the committed absent-set so the tiering can be regenerated with no network (Sefaria egress is
  policy-blocked in the web sandbox). This was done offline; the presence spot-check still needs
  a session with Sefaria access.

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
2. **Finish and pressure-test the most-wanted list** before sharing. Tier-3 era classification
   is now done (see above). Remaining work both needs Sefaria/Halachipedia egress.

   **First, enable network access** (the web sandbox blocks it — the egress proxy returns a 403
   policy-denial on `www.sefaria.org`, so `verify_pending.py`/the mine can't reach the API; don't
   try to route around it). This is per-environment config chosen at environment creation, not
   something a session can toggle from inside:
   1. Go to **claude.ai/code** → the **environment settings** for the environment this session
      runs in (same place sources, env vars, and setup scripts live).
   2. Find the **network access** (egress/allowlist) setting.
   3. Switch to a **custom allowlist** and add `www.sefaria.org` and `www.halachipedia.com`
      (or pick full access), then save.
   4. Start a **fresh session** on the updated environment — the policy binds at session start,
      so the current session won't pick up the change.
   Docs (exact policy names + UI): <https://code.claude.com/docs/en/claude-code-on-the-web>
   (network access section). Verify from the session with
   `curl -sS "$HTTPS_PROXY/__agentproxy/status"` — a `connect_rejected` 403 for `www.sefaria.org`
   in `recentRelayFailures` means it's still blocked.

   With egress open, two tasks remain:
   - **Run the presence spot-check (ready, one command):** `python3 pipeline/verify_pending.py`
     probes the 18 `pending_presence_verification` works live (hand-supplied Sefaria spellings +
     normalizer candidates), writes verdicts to `pipeline/pending_resolved.json`, and prints a
     PRESENT/ABSENT report. Then `python3 pipeline/build_final.py --offline` regenerates the list:
     confirmed-present works move to the variant-spelling exclusion; confirmed-absent ones drop
     out of pending and tier automatically (era pre-seeded in `build_final.py`'s `VERIFY_ERA`, so
     rishonim land in Tier 1). Commit `pending_resolved.json` — it's the verification record.
   - **Widen beyond the 250-page sample** — the larger, gentler re-mine (see `mine_v2.py`,
     `trawl_big.py`); keep it paced.
   With network up you can also run `python3 pipeline/build_final.py` (no `--offline`) to
   re-verify the whole absent-set live rather than reuse the committed one.
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
python3 benchmark.py                       # rule coverage vs the verified dataset (online)
python3 pipeline/build_final.py            # rebuild most-wanted, live /api/name (needs Sefaria egress)
python3 pipeline/build_final.py --offline  # rebuild from the committed absent-set, no network
python3 pipeline/verify_pending.py         # spot-check the 18 pending works (needs Sefaria egress)
python3 -c "import json;print(len(json.load(open('data/citation_dataset.json'))))"  # 137
```
