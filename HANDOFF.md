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

1. **The normalizer** (`normalizer/`) — the tier-1 deterministic layer. Resolves 116/139
   (83%) of the verified corpus as of 2026-08-18 (`python3 benchmark.py`; up from ~43% at
   this file's last full rewrite — see "Progress so far" below for what moved it). The
   remainder is irreducibly knowledge-based (English-translated titles, alternate names,
   Hebrew) and is the job of an LLM/SLM — that's tier 2, and the dataset feeds it.
2. **A licensing-priority list for Sefaria** (`data/SEFARIA-MOST-WANTED.md`) — a byproduct
   that turned out to be independently valuable. See below.

## Progress so far (as of 2026-07-24, with 2026-08-05 and 2026-08-18 updates below)

- **2026-08-18**: rule coverage moved from 101/139 to **107/139 (72% -> 76%)**, fresh and
  live-verified (not a cache artifact — the prior number partly rested on stale local cache;
  clearing it exposed one masked gap, see below). Four fixes in `normalizer/rules.py` /
  `shared_dialect.py`: bare `"Talmud"` was missing from the prefix-strip list; wrapping
  parens around a whole citation (`"Talmud (Chagiga 13b:14)"`, `"Rambam (Hilkhot Brakhot
  1:16)"`) broke every downstream rule (now unwrapped-and-recursed through the full rule
  set); `/api/name`'s `is_ref` path is case-sensitive beyond the first letter of the whole
  string with no fuzzy fallback (`"Chovot Halevavot"` misses, `"Chovot HaLevavot"` resolves
  to *Duties of the Heart*) and tier 1 never generated case variants (now does); and
  `RAMBAM_SECTIONS` (shared with the blog repo) was missing the `brakhot` spelling of
  Blessings. Also fixed a real cross-process cache-key bug in `pipeline/halachipedia_mine.py`
  (`hash()` is per-process randomized; switched to `hashlib.md5`, matching `mine_wide.py`).
  **Open gap exposed by the fresh run** (since mostly fixed — see "Bare-tractate-name
  fallback" below): bare tractate names with no locator (`"Kesubos"`,
  `"Rosh Ha-Shanah"` alone) don't resolve — the live-canonicalization fallback in
  `resolve.py`'s `_resolve_via_canonicalization` only triggers on candidates that end in a
  numeric locator, so a bare mis-spelled tractate name never reaches it. `/api/name`'s
  completions for these *do* contain the right target but wrapped in unrelated prefixes
  (`"Tos. Kesuvos"`, `"Yerushalmi Kesuvos"` for `"Kesubos"`) — filtering those down to a bare
  match safely (without risking a mislink) needs more care than the fixes above; not
  attempted yet, flagged for a decision rather than guessed at.
  - **Sefaria's own architecture, read directly from their public repo**: the trie-based
    fuzzy system (`sefaria/model/autospell.py` — `AutoCompleter`/`TitleTrie`/Norvig
    spell-checker/n-gram TF-IDF) only powers `/api/name`'s `completions` suggestion list. It
    is **never consulted for `is_ref`/`url`** — those come from `Ref.__init__` in
    `sefaria/model/text.py`, an exact-string dict lookup (`library.get_title_node_dict`)
    that only capitalizes the very first letter of the whole input and does no other
    normalization. Confirmed live: `"rosh Hashanah 30a"` resolves (leading letter forced
    upper), `"Rosh hashanah 30a"` does not (mid-string casing untouched), even though that
    same query's `completions` list has `"Rosh Hashanah"` as its first suggestion. This means
    contributing our alias data to their fuzzy matcher would not fix anything we depend on —
    it's not in the decision path. A bug report against the exact-match path is drafted at
    `SEFARIA-CASE-SENSITIVITY-BUG.md` (this repo), not yet posted (see "Contribute to
    Sefaria" below).
  - **Tier-2 design plan** (dispatched to an Opus-backed planning pass): recommends *not*
    building tier 2 yet — land "tier 1.5" first (case/whitespace candidates, done above in
    part; vocabulary-anchored span extraction against Sefaria's own 65k-title list, vendored
    in the blog repo as `sefaria_titles.txt.gz`, not yet ported here) and re-measure, since
    several "knowledge-tier" misses are actually reachable without a model. For tier 2 itself
    when the residue is re-scoped: RAG-constrained *selection* (retrieve candidates from
    Sefaria's own title vocabulary, model picks/recomposes, never free-generates a title) over
    fine-tuning (too little labeled data, ~200 works) or free-generation prompting (the
    existing `titles.py` docstring in the blog repo already recorded `/api/name` returning
    "confident nonsense" for junk input — free generation would be a *better* junk generator
    than that). Small model (Haiku) with Opus escalation on disagreement; cost is not a
    binding constraint at any scale measured here (~$40 for a full frontier pass over the
    entire unresolved Halachipedia corpus). **The load-bearing risk**: `/api/name` cannot
    adjudicate section-inference (`Shulchan Aruch 294:2` -> Orach Chayim vs. Yoreh De'ah 294:2
    are both real refs), so an LLM proposer can break the "unlinked, never mislinked" property
    that rule-based over-generation gets for free — this needs an explicit decision (accept a
    bounded mislink rate behind confidence gates, or permanently abstain on section-inference).
    Also caught in passing: **`benchmark.py` scores truthiness, not correctness** — it never
    checks the resolved ref matches `sefaria_ref`, which was fine for rule-based
    over-generation (a wrong candidate just doesn't resolve) but is the wrong shape once an
    LLM can resolve to a wrong-but-real ref. A 4-part harness upgrade (three-outcome
    correct/wrong/abstain scoring, an absent-works mislink-trap fixture from
    `data/sefaria_most_wanted.json`, a specificity check, and a held-out eval on the separate
    121-pair Mi Yodeya corpus) is recommended as the go/no-go instrument to build *before* any
    tier-2 code — not yet implemented, flagged for a scoping decision rather than built
    speculatively. ~23% of the ~8,748 unresolved Halachipedia strings name a work on the
    71-work absent list — a free, zero-labeling mislink-risk measurement once that trap exists.
- **2026-08-05**: rule coverage jumped from 79/139 to 101/139 (56% -> 72%) after replacing
  a hand-typed tractate-spelling list with a resolver pass that canonicalizes tractate
  names live via Sefaria's own `/api/name` completions. Details in "Relationship to the
  blog repo" below and in `INTEGRATION-PLAN.md`.
- **`data/citation_dataset.json`** — 139 verified `raw → Sefaria ref` pairs, mined from
  `find-refs` failures over 289 source sheets, LLM-labeled, Sefaria-verified. `my_canonical`
  is the labeler's guess; `sefaria_ref` is Sefaria's authoritative answer (they differ in
  ~14 cases — that gap is exactly why propose→verify beats compute-the-name).
- **Normalizer + benchmark** — `benchmark.py` tracks rule coverage (originally ~43%, now 83%). Rule
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

**Step 6 done, mixed result (2026-08-18)**: the literal before/after diff (baseline
`9d98ada` vs. current HEAD, offline linker over all 138 real letter/Q&A drafts, same
committed cache both runs — this is the actual default non-`--online` build path, so
Cache.set()'s known-miss fix landing after baseline doesn't confound the comparison)
found **638 -> 521 citations resolved, 195 changed**: 115 an intentional specificity guard
now correctly *not* auto-linking bare/generic citations ("12", "Bo", "ibid") — working as
designed; 35 new links gained from the integration's new rules; 2 real bug fixes (a
corrupted nested-link URL from a context-blind cache splice, now clean); and **43 a genuine
coverage regression** — citations currently linked live that the new code fails to resolve
(mostly non-Yalkut-remez cases: Shulchan Aruch, Sefer HaChinuch, Tosfot, Bava Batra,
Mesilat Yesharim, Yechezkel, plus Yalkut spelling variants like "Zechariya"/"Zecharia" the
new vocab doesn't cover). **Zero cases of a wrong new URL replacing a correct old one** —
the fail-safe property held throughout. This closes the "did the integration silently
mislink anything" question (no). It does **not** close the coverage question — the
43-citation regression is real and unaddressed; a follow-up pass on the non-Yalkut offline
rules and the Yalkut spelling vocab is needed before calling the integration fully settled.
Full data/script: `/tmp/step6-diff/` (untracked, not committed — recreate the diff run if
needed rather than relying on that path surviving).

Earlier, partial de-risking (2026-08-16): a full content-integrity + link-validity audit of
all 253 live posts (`check_site.py`, plus a targeted cross-check of every "context-risky"
cache key against live links) found zero broken or invalid Sefaria links anywhere in the
corpus. It also found one unrelated, pre-existing defect (a context-blind cache mislink
predating the Aug 6 dialect work, in "Ya'akov Dons Esav's Arms" — fixed). Full detail in
the blog repo's `HANDOFF.md`, "Correction (2026-08-16)" note.

## Latest work (2026-08-18)

- **Bare-tractate-name fallback: done, verified, committed (`2dbf999`).** Fresh
  full-corpus benchmark confirmed **116/139 (83%)**, up from 107/139 — miss
  list strictly shrank (32 -> 22), no regressions. The fallback generalized
  well beyond its 3 target cases (6 bonus resolves: *Eternal Victory Netzach
  Yisrael*, *Guide for the Perplexed Introduction*, *Midrash Sh'muel*,
  *Midrash of Ben Sira*, *Mishnah Bikkurim Rabbi Arthur Green*, *Tzava'at
  Harivash*). Added
  `_resolve_bare_via_canonicalization` to `normalizer/resolve.py` (third
  fallback pass, after the locator-bearing canonicalization): for a candidate
  with no numeric locator, ask `/api/name` for ref completions and accept one
  only if every word of its canonical `key` is already a normalized whole-word
  match somewhere in the original raw citation (safe, provenance-based — never
  a spelling guess). Confirmed working on the 3 target cases (`"Mesechet Rosh
  Hashanah"`, `"Rosh Ha-Shanah"`, `"Tosefta to Tractate Chagigah"` all now
  resolve) and correctly still rejects the 3 cases that need a real spelling
  correction, not just reformatting (`"Kesubos"`, `"Mesechtas Berochos"`,
  `"Mesechtas Menochos"` — disclosed gap, not fixed, see code comment). Also
  added `"Mesechet"` (no final s) to `_STRIP_PREFIX` in `rules.py`. Verified
  with a cache-cleared full-corpus run before committing; re-confirmed
  116/139 on 2026-08-18 after the session resumed.
- **HP triage review dashboard — scope decided, not built.** Owner confirmed
  (2026-08-18): review target is the Halachipedia unresolved-citation triage
  queue (the tier-2 design plan's "~200 top-frequency heads cover 40%"
  concrete next task), styled after `~/work/yad-malachi/yad-malachi-pipeline`'s
  review dashboard pattern — explicitly "don't reinvent the wheel, use a
  familiar look and feel". That pattern, read directly from the source: a
  stdlib-only local HTTP server (`review_server.py`, `ThreadingHTTPServer`, no
  framework) that re-reads its JSON data fresh off disk every request and
  merges in human decisions at serve time; decisions are an **append-only
  JSONL log** (`review_decisions.py` — one line per decision, "current" =
  last matching line for a key, full history always recoverable, and a
  promote-to-corpus step is a separate, deliberately manual script so a
  rebuild can never clobber a human decision); a vanilla static JS/CSS
  frontend (`review_frontend/`, no build step) with a fixed design system
  worth reusing verbatim (`--ink`/`--paper`/`--wash`/`--accent`/`--danger`
  CSS custom properties, Frank Ruhl Libre serif for content + Inter for UI
  chrome, a left nav-pane of items with red=open/green=decided count badges,
  a sliding side-panel drawer for making a decision, a legend box pinned
  bottom-corner as a tri-state readout). One sharp implementation lesson
  worth carrying over: `review_decisions.py`'s `_resolve(path)` docstring
  documents a real bug they hit twice — a function default argument
  (`path=DECISIONS_PATH`) binds at *import time*, so reassigning the module
  constant later (e.g. to redirect tests at a throwaway file) silently doesn't
  work; resolve the path *inside* the function body instead.
  **Data-prep prototyped, not yet in the repo**: a head-extraction heuristic
  (strip trailing locators/volume-section qualifiers/unbalanced parens from
  each of the 8,789 raw strings in `pipeline/hp_unresolved.json`, group,
  count) was iterated on on in `/private/tmp/.../scratchpad/head_explore.py`
  (a throwaway path, not in this repo) — current state finds ~7,253 distinct
  heads with the top 200 covering only ~16% (not the ~40% the design agent's
  quick pass estimated; that estimate was informal too, so neither number
  should be trusted over the other without a proper side-by-side). The
  extraction needs another pass before it's good enough to build the real
  queue from — remaining noise: unclosed volume/page fragments like
  `"39 melachos (rabbi ribiat, vol"`, and un-merged spelling twins like
  `"chazon ovadia"` vs `"chazon ovadyah"` splitting one work's count across
  two queue rows (`pipeline/presence.py`'s already-hardened fuzzy word
  matcher is the right tool to merge these — reuse it, don't rewrite it).
  **Not started at all**: the actual `pipeline/build_hp_triage.py` (would
  call `presence.check()` per head, paced, to pre-flag likely-absent heads
  against `data/sefaria_most_wanted.json`'s 71-work list, and fetch a few
  ref-completion candidates per head for the reviewer to pick from), the
  review server, and the frontend. All next steps for whoever/whatever
  session picks this up.

## Next steps

0. ~~Integrate the shared dialect layer with the blog repo~~ — done 2026-08-05, see above.
   ~~Regression-diff step 6~~ — done 2026-08-18, see above (no mislinks; 43-citation coverage
   regression found and left open, see item 1d).
1. **Grow tier 2 — design plan done 2026-08-18, not yet built** (see "Progress so far" above
   for the full recommendation). Concrete decisions needed before writing tier-2 code:
   - **(a)** Land "tier 1.5" first (vocabulary-anchored span extraction against Sefaria's
     65k-title list) and re-measure the residue — currently un-scoped work, not yet started.
   - **(b)** Build the benchmark-harness upgrade (three-outcome scoring, absent-works
     mislink-trap, specificity check, Mi Yodeya held-out eval) as the go/no-go instrument —
     currently un-scoped work, not yet started.
   - **(c)** Decide whether "unlinked, never mislinked" stays inviolable for tier 2, or a
     bounded mislink rate is acceptable behind confidence gates — the owner's call, not made.
   - **(d)** Blog-repo coverage regression from step 6: 43 citations linked by the old
     offline rules no longer resolve (Shulchan Aruch, Sefer HaChinuch, Tosfot, Bava Batra,
     Mesilat Yesharim, Yechezkel, Yalkut spelling variants). No mislinks; coverage only.
   - Bare-tractate gap: **mostly fixed** (`2dbf999`, see "Latest work"). Still open: names
     needing a real spelling correction rather than reformatting (`"Kesubos"`,
     `"Mesechtas Berochos"`, `"Mesechtas Menochos"`) — needs a mislink-risk decision, not a
     guess.
   - Also queued from the design pass, not yet done: fix `pipeline/mine_wide.py`'s HP-corpus
     re-mine to reuse the now-fixed cache-key scheme (see "Progress so far" above) before any
     re-mine of the ~8,748 unresolved strings for tier-2 use as a triage/eval set (they're
     unlabeled — not training signal; see design plan for the triage-by-head-frequency
     approach — the design pass estimated ~200 heads cover 40% of citations; the later
     prototype measured ~16%, so treat both as unverified).
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
   - **Translation-availability pass — done 2026-08-18.** `data/ANALYSIS.md`'s "Existing
     translations to license?" section is now a real WorldCat/publisher-catalog pass (not
     Wikidata) across ~22 merged works (the 44 `english_gap.json` rows collapse to ~19-22
     distinct author/work questions once tractate/section splits are merged). Confirms the
     original assumption for nearly everything — no independently licensable English edition
     exists for Rosh, Ran, Rashba, Rif, Tosafot, Shach, Taz, Bach, Beit Yosef, Kessef Mishneh,
     Kol Bo, Havot Yair, Teshuvot HaRivash/HaRosh, Beit Shmuel, Chelkat Mechokek; Sefaria's own
     site holds the only English these have. **One real surprise, flagged in the doc**: a
     complete, free, LLM-generated English translation of the entire Aruch HaShulchan (all 4
     sections) was published May 2026 by an independent ML engineer (Joshua Broyde), sourced
     from Sefaria's own Hebrew text, code/data on GitHub — not a traditional license, quality
     self-described as AI first-pass, but a materially cheaper option than commissioning from
     scratch. Worth a direct conversation with the author — not yet reached out to, the
     owner's call on outreach per item 3 below.
3. **Contribute to Sefaria — when it's "truly real."** The strongest form isn't a repo link
   but a PR / data contribution into Sefaria's own repos: the dataset (as linker eval cases),
   the dialect map, and the most-wanted list (for their library/licensing team). Hold outreach
   until the deliverable is polished — the owner's explicit call.
   - **New, sharper candidate found 2026-08-18**: `Ref()`'s exact-match title lookup (the
     path that actually decides `/api/name`'s `is_ref`/`url` — separate from and *not*
     covered by Sefaria's fuzzy `AutoCompleter`, confirmed by reading `sefaria/model/text.py`
     and `autospell.py` directly) is case-sensitive beyond the first letter of the query, with
     no fallback to the suggestion engine that already has the right answer. Draft bug report
     at `SEFARIA-CASE-SENSITIVITY-BUG.md` (this repo) — not posted, pending the same
     "deliverable is polished" call as the dataset/dialect-map contribution. This also
     sharpens the already-drafted-but-unposted comment on their issue #577 in the blog repo's
     `archive/SEFARIA-CONTRIB-DRAFTS.md` (draft B, "the alias list is structurally
     incomplete") with a concrete root cause instead of just symptom examples.

## Provenance & privacy

**Public data only** (Sefaria API, public Halachipedia via its MediaWiki API). No private or
personal material — this repo is safe to open-source when ready. Nothing here is
author-specific, by design, to avoid one-author overfitting.

## Quick orientation

```bash
python3 benchmark.py                       # rule coverage vs the verified dataset
python3 test_shared_dialect.py             # diff-check vs the blog repo's vendored copy
python3 pipeline/build_final.py            # rebuild the most-wanted list (uses work_frequency.json)
python3 -c "import json;print(len(json.load(open('data/citation_dataset.json'))))"  # 139
```
