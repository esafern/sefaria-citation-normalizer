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

## Current status (2026-11-24) — start here

Everything below this section is history, newest first further down. For *why* things
are the way they are, also read [`LESSONS.md`](LESSONS.md).

### Where it stands

| Measure | Result |
|---|---|
| Benchmark (`python3 benchmark.py --strict`, 139 rows) | 95 correct, 5 coarser, **0 wrong**, 39 unresolved |
| Web test set, mangled (`data/web_pairs.json`, n=616) | 225 correct, 148 coarser, 1 finer, 15 label noise, **5 wrong**, 222 unresolved |
| Web test set, clean (n=972) | Sefaria already handles them as written; 16 links disagree with Sefaria's reading (writer context) |

The 5 mangled "wrong": 2 are bare-section citations (decision 1 below), 3 are cases where
the writer's text and link disagree (typo'd verse, "with Rashi", English vs Hebrew verse
numbering). None is a resolver error. **Treat the web test set as the primary
correctness test**; the benchmark has 32 circular rule-labeled rows (loose end 8).

### What exists now (built 2026-11-23/24)

- `benchmark.py`: scores correct / coarser / finer / WRONG / unresolved; `--strict` exits 1
  on any WRONG. A daf covers its amudim; a range covers points in it.
- `pipeline/web_pairs.py`: free labeled test data from link text -> Sefaria href.
  Subcommands `miyodeya`, `miyodeya_api`, `stackexchange <sites>`, `wikipedia`, `verify N`,
  `eval`. ~35k raw pairs, ~20k usable after the consistency filter; 1,588-pair sample
  committed (`data/web_pairs.json`, scored copy `data/web_pairs_scored.json`). CC BY-SA,
  `where` URL per row for attribution.
- `normalizer/resolve.py`: `_keeps_all_words` guard on the canonicalization passes (no
  dropped/added meaningful words, same order, no added numbers), `_adds_part_numeral`,
  `_hilchot_is_ambiguous`, consonant-skeleton spelling match.
- `normalizer/rules.py`: ~15 new dialect rules (book names, abbreviations, locators,
  Hilchot -> Rambam, ...), each traced to failures in the web data. **Not yet in
  `shared_dialect.py`**, so the blog repo doesn't have them (loose end 5).
- Sefaria case-sensitivity research: full 1,097-group check (0 divergent; 1,093/1,093
  miscasings fail; 18 lowercase + 24 hyphenated alt titles unreachable). Comment for issue
  #1016: `docs/upstream/issue-1016-comment.md`; draft PR: `docs/upstream/SEFARIA-CASE-SENSITIVITY-PR.md`.
  **Neither posted.**
- Branches: `0ctxcz` merged, `pd-index-submissions` updated and merged, `lw5947` deleted.

### Update, 2026-11-24 evening

- **Vocabulary-anchored pass ("tier 1.5") landed** (`_resolve_via_vocabulary` in
  `normalizer/resolve.py`). It matches the work name against Sefaria's full 67k title list
  (`normalizer/.titles_cache.json`, fetched once, gitignored) with the same guard, then
  verifies live. Sefaria's autocomplete ranking often omits the right title
  (`Rambam, Hilchot Eidus` never surfaced `Rambam, Hilchot Edut`).
- **Latent mislink fixed:** "hilchot"/"laws" were droppable, so `Hilchot Shabbat 2:3`
  could have become `Shabbat 2:3`, which Sefaria reads as *Mishnah* Shabbat 2:3.
- More rules: I/II markers (`Shmuel A`, `Melachim B`, `Samuel 1 13:1`); `X on Torah,
  Book` and `X, Book` commentary titles; dropping `OC` after Orach-Chayim-only
  commentaries; Gemara spelling variants; leading `in`/`See`; `MT,`; v/b in spelling
  comparison; verse-part letters (`9:20f`); two-level truncation before one-level;
  precise-first candidate order; bracket cleanup.
- The Hilchot -> Rambam ambiguity check now resolves each same-name title and only
  abstains if one lands outside the Mishneh Torah.
- **Benchmark relabel (loose end 8, mostly done):** 8 coarse rule-derived labels now say
  what the raw text says (`Genesis 1:1 (SP)` -> Genesis 1:1, not Genesis 1). All 32
  rule-verified rows are marked hand-reviewed. Benchmark against the honest labels:
  **101 correct, 1 coarser, 0 wrong, 37 unresolved**.
- **Cache race fixed:** each eval output now gets its own resolver cache
  (`resolve_cache_<output>.json`). The earlier shared `resolve_cache.json` (renamed
  `resolve_cache_OLD_shared.json`) was written by concurrent runs on different code, so
  sample numbers reported between the full run's eval start and this fix may be off.
  Fresh runs on current code are in progress.
- **Mistake:** a `pkill -f "web_pairs.py eval$"` meant for the sample run also killed the
  full run's eval (same command line). The full run was restarted on current code and
  now also covers the Mi Yodeya 2024+ and SE pairs (loose end 7). Stop background jobs
  by PID only.

### Full run results + third mislink pass (2026-11-25)

The full run finished overnight: **19,227 verified pairs** (7,250 mangled, 11,977 clean)
from all sources. Mangled: 2,752 correct, 1,736 coarser, 11 finer, 255 label noise,
**156 WRONG**, 2,340 unresolved. Reading the 156 exposed real mislinks the 616-pair sample
was too small to show:
- **The spelling match was too loose.** Dropping all vowels and merging ch with k made
  Challah = Kallah (x10), Deot = Deut(eronomy) (x6), Kilayim = Kelim, Edus = Eduyot,
  Vaera = Vayera; a 0.8 ratio fallback matched Megillah/Me'ilah and Orlah/Torah.
  Replaced by `_translit` + `_vowel_groups`: real transliteration variants only (tav s/t,
  ch/kh, non-initial k, v/b, academic h for chet), vowels compared by class (kamatz a/o
  merged, tzere/segol/sheva dropped), exact match for short words, ratio fallback only
  when consonants are identical.
- **Sefaria filled in what the text didn't say:** an amud (`Brakhot 11:13` -> Berakhot
  11a:13) or a Shulchan Arukh section via an alias (`Kaf HaHayim 92:8` -> the OC volume;
  Kaf HaChayim also covers YD). `_guessed_something` now rejects both.
- Also fixed: "Yad." (tractate Yadayim) satisfying "Rambam"; `Melachim 1:5` read as I
  Kings 5; a footnote marker spliced into a locator (`11:1][1` -> 11:11); `note 48` promoted
  to siman 48; "Talmud" added mid-title (`Hilchos Torah` -> *Hilchos Talmud Torah*); the
  Hilchot ambiguity check now works both ways.
- Rescored with current code, the 156 become: 56 unresolved, 5 correct, 95 still WRONG,
  none of them a resolver error we can fix without context: 18 bare section (decision 1),
  15 tractate + chapter:mishnah -> Mishnah (decision 5 below), 2 `Ber` alias, 29
  commentary-layer label noise, ~28 text-vs-link disagreement, 3 Sefaria-side (see below).
- Accepted loss: `Kav HaYosher` no longer matches *Kav HaYashar* (different vowel pattern;
  the looser rule that allowed it also made Deot = Deut).
- **Sefaria data error found:** the alt title `Rambam, Hilchot Malveh veLoveh` (Creditor and
  Debtor) is attached to *Mishneh Torah, Inheritances*. Worth reporting.
- **New decision 5:** a bare tractate + chapter:mishnah (`Kilayim 9:3`, `B'rachot 2:4-5`)
  resolves to the **Mishnah** by Sefaria's own convention (its Bavli refs check the Mishnah
  pattern first). In the full run, 15 such links went to the Yerushalmi or Mishneh Torah
  instead. Same shape as decision 1: keep the convention or abstain.
- **New decision 6:** short Sefaria aliases (`Ber` = Berakhot) collide with common
  abbreviations (`Ber.` = Bereshit in academic writing). Keep or abstain on 2-3 letter
  work names.
- `test_rules_offline.py` now has 93 cases.

### Running in the background

Full run: **finished 2026-11-25** (results above; `pipeline/web_pairs_raw/web_pairs_full_scored.json`,
scored with the code of 2026-11-24 evening). A rerun on current code is the next step.
A fresh sample eval on current code (`sample_eval.log`) is running.

### Git

`next-work` is ahead of `main`; `main` is ahead of `origin/main`. **Nothing is pushed.**

### Loose ends

**Decisions (owner):**
1. **Bare section citations** (`YD 289`, `O.C. 122:1`, no work named). Current rule: assume
   the Shulchan Arukh. Measured over ~28k mined pairs (477 cases): 87% Shulchan Arukh, 13%
   other works (Tur, Arukh HaShulchan, Mishnah Berurah, Beit Yosef, responsa). Keep the
   convention (~13% mislinks on this pattern) or leave bare sections unlinked.
2. **Reddit** as a source (r/Judaism via the Arctic Shift research archive): useful
   links, but Reddit's data terms restrict ML use.
3. **When to post** the #1016 comment (and offer the PR); also whether to file a
   separate issue for hyphenated titles being unreachable.
4. **Repo license.** There is none; the committed web pairs are CC BY-SA.

**Blocked on the blog repo (on hold by request):**
5. Port the guard + new rules to the blog's `resolver.py`; move the book-name map and
   quoted abbreviations into `shared_dialect.py` (both copies, keep them byte-identical).
6. Audit the blog's 35 step-6 gained links against correct answers; fix its
   43-citation coverage regression.

**Data / evaluation:**
7. When the full run finishes, rerun verify+eval including the 2024+ and SE pairs.
8. ~~32 rule-verified benchmark rows~~: hand-reviewed and 8 relabeled 2026-11-24. Still
   genuinely ambiguous, so kept as-is: `Vayishlach, 6`, `Proverbs 556`.
9. Common Crawl via its columnar Parquet index filtered by domain (thetorah.com,
   myjewishlearning.com, etzion.org.il, ou.org), since the CDX index server timed out.
10. ~~Shared resolver cache~~: fixed (per-output caches). `name_cache.json` (gold-ref
    lookups) is still shared; concurrent writers only waste requests there.

**Resolver:**
11. Remaining 222 unresolved mangled: parts of multi-part works (`Moreh Nevuchim
    3:53:2` -> Part 3), parasha-based Midrash, more abbreviations, Sefaria's MT section
    titles. ~20% name no work and should stay unlinked.
12. Push `main` and `next-work`; delete the two merged remote branches.

**13. Older items, not touched in the 2026-11-23/24 sessions:**
- **Halachipedia review dashboard.** Scope agreed 2026-08-18: a local review tool for the
  ~8,789 Halachipedia citations that still don't resolve (`pipeline/hp_unresolved.json`),
  grouped by work name ("head") so a reviewer labels the most-cited works first. Look and
  feel copied from `~/work/yad-malachi/yad-malachi-pipeline` (stdlib HTTP server,
  append-only JSONL decisions, vanilla JS frontend). Not built. The head-extraction
  prototype lived in a temp scratchpad and is gone, and it measured the top 200 heads
  covering ~16% of citations (not the ~40% first estimated). Why it still matters:
  Halachipedia is the target dialect but has **no** Sefaria links (1 in the whole site),
  so it can't be labeled the free way the web pairs were. Hand-labeling the top heads
  is the only route to Halachipedia-specific correctness numbers. **Do first:**
  re-resolve `hp_unresolved.json` with today's resolver. Many heads (`Kaf Hachaim`,
  `Sefer Hachinuch`, `Mishna brurah`, Hilchot X) now resolve, which shrinks the queue.
- **`mine_wide.py` cache-key item: the code part is done.** Python's built-in
  `hash()` is randomized per process, so cache files keyed by it can't be found on a later
  run. `mine_wide.py` always used md5; `halachipedia_mine.py` was switched to md5 on
  2026-08-18. What remains: 439 old `pipeline/hp_cache/fr_<int>.json` files written under
  the old keys are unreachable. They don't store the text they were computed from, so they
  can't be re-keyed; a re-mine would re-fetch those find-refs results (and should, gently).
  **Deleted 2026-11-24.** The same bug was still live in four more miners
  (`mine_v2.py`, `trawl_big.py`, `mine_sheets_freq.py`, `mine_wikisource.py`): **fixed
  2026-11-24** (md5 keys), and the 1,259 unreachable `fr_` files in `pipeline/mine_cache/`
  were deleted. Its 1,506 URL/name-keyed files (`sheet_`, `tag_`, `nm_`) are stable and were
  kept. No `hash()`-keyed caches remain in `pipeline/`.
- **Aruch HaShulchan translation outreach.** The translation-availability pass
  (`data/ANALYSIS.md`) found that Joshua Broyde, an independent ML engineer, published a
  complete, free, LLM-generated English translation of all four sections of the Aruch
  HaShulchan in May 2026, made from Sefaria's own Hebrew, with code and data on GitHub. The
  Aruch HaShulchan is cited heavily and has no Sefaria English. That makes it a much
  cheaper path than commissioning a translation, though it's an AI first draft, not a
  licensed edition. The open item is a conversation, with him and/or Sefaria, about
  license, quality review and hosting. Owner's call, held with the other "contribute
  when polished" outreach.
- **Tier 2 (an LLM layer for the knowledge-heavy misses).** The 2026-08-18 design plan
  said: build the evaluation harness first, try "tier 1.5" (matching against Sefaria's
  65k-title list) next, and decide on mislink tolerance before writing any model code.
  **The harness now largely exists** (correctness scoring, label-noise handling, ~20k
  labeled web pairs; the 222 unresolved mangled web pairs are a ready-made tier-2 eval
  set). Still missing: an absent-works mislink trap (citations of works Sefaria doesn't
  have, from `data/sefaria_most_wanted.json`, which must stay unlinked) and decision 1's
  sibling: whether tier 2 may ever pick a section the text doesn't name. Recommended
  shape is unchanged: the model *selects* from Sefaria's own title candidates, never
  free-generates a title, and every pick goes through the same `_keeps_all_words` guard.

## Two things this repo produces

1. **The normalizer** (`normalizer/`) — the tier-1 deterministic layer. As of 2026-11-24:
   benchmark **95/139 correct, 5 coarser, 0 wrong, 39 unresolved**; web test set (616
   mangled real-world citations) **225 correct, 149 coarser/finer, 5 wrong (none a resolver
   error), 222 unresolved**. See "Current status" just below. Before 2026-11-23 the
   benchmark reported 116/139 "resolved", 7 of which were wrong links. Up from ~43% at
   this file's last full rewrite. The
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
    `docs/upstream/SEFARIA-CASE-SENSITIVITY-BUG.md` (this repo), not yet posted (see "Contribute to
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
- **Normalizer + benchmark** — `benchmark.py` scores correctness against `sefaria_ref` (correct / coarser / finer / WRONG / unresolved; `--strict` exits 1 on any WRONG). Rule
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

This work spun out of `~/work/the private blog repo`, which has its own embedded copy of the linker
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

## Mislinks found and fixed (2026-11-23)

A correctness check of the 116 benchmark resolves against each row's `sefaria_ref`
(this is not what `benchmark.py` measures; it only checks that *something* resolved):
**100 exact, 6 coarser (parent section, acceptable), 3 where we're more specific than
the label, 7 real mislinks** (~6%):

- `Seifer Chofeitz Chayim … 4:12` -> *Mishneh Torah, Repentance 4:12*
- `Rambam, Sefer HaMitzvot, Prohibition 51` -> *Shorashim 51* (should be Negative Commandments)
- `… Rambam, Laws of Kings 8:10-11` -> *Heave Offerings 8:10-11*
- `Laws of Foundations of Torah 5 Rambam 1.` -> chapter 1 (should be 5)
- `Mishnah of Tractate Chagigah` -> Bavli Chagigah (dropped "Mishnah")
- `Tosfot Avodah Zarah 11a`, `Tosafos (Kesubos 30b)` -> the Gemara daf (dropped "Tosafot")

The Halachipedia sample has more of the same: `Kaf Hachaim Palagi` -> Kaf HaChayim (Sofer);
`Kaf Hachaim YD` -> the OC volume; `Kaf Hachaim. Radvaz 1:489` -> Kaf HaChayim 1:489;
`Sefer HaMitzvot Hakatzar of the Chofetz Chaim 77` -> *Sefer Etz Chaim 77*;
`Sefer Hamitzvot of Rambam (Lavin 232)` -> *Rasag's* Sefer HaMitzvot.

**Root cause (most cases): `_resolve_via_canonicalization` (pass 2, added 2026-08-05)**
accepts any `/api/name` completion for the work name, even when the completion
**drops words the citation contains** (Palagi, YD, Radvaz, of Rambam, Lav, Tosfot). Pass 3
has the opposite check (every title word must appear in the citation); pass 2 has no
check that no citation word is dropped. Fix: an "every distinctive word of the head must
appear in the canonical title" check in pass 2, and the same check added to pass 3.
The Rambam-section and wrong-locator cases are separate rule bugs.
**Fixed 2026-11-23 (benchmark WRONG 7 -> 0, fresh cache-cleared run):**
- `resolve.py`: `_keeps_all_words` guard on pass 2 and pass 3. A canonical title must
  keep every distinctive word of the citation, and must not put a new work name in
  front of it ("German Commentary on Pirkei Avot"). Generic, numbering and connector words
  (`_DROPPABLE`) may be dropped; Rambam / Maimonides / Yad / Mishneh are treated as one
  name; spelling is compared by a consonant skeleton (Kesubos=Ketubot,
  HaYosher=HaYashar, but Bekhorot != Berakhot). Pass 2 also skips heads containing a
  digit (a split locator).
- `rules.py`: `Mishnah of (Tractate) X` -> `Mishnah X` instead of stripping "Mishnah";
  `X (inner)` emits bare `inner` only when X is generic (Talmud, Gemara, ...), so
  `Tosafos (Kesubos 30b)` no longer becomes `Kesubos 30b`.
- Cost: 8 previously-correct links are now unresolved, because each depended on
  dropping words that happened to be noise (`Eternal Victory`, `Rabbi Arthur Green`,
  `Isaiah's Vineyard`, `Torah Babylonian Talmud`, `Midrash of Ben Sira`, two
  `Pirke Avot, Commentary on`). That is the intended trade.
- Halachipedia mislinks above: all now unresolved, except `Kaf Hachaim YD 116:12`,
  which now resolves to the correct Yoreh De'ah volume.
- **Not yet ported to the blog repo**, whose `resolver.py` has the same pass-2 logic.
  The blog's 35 newly gained links from step 6 also still need auditing against
  the right answer.


## Web-mined test set + second mislink pass (2026-11-24)

**New labeled data, no hand labeling:** `pipeline/web_pairs.py` mines link-text -> href
pairs wherever a writer hyperlinked a citation to Sefaria (link text = the citation as
written, href = the right answer). Sources (all CC BY-SA, bulk/API, no crawling):
- Mi Yodeya data dump (archive.org, 2024-04): 19,406 pairs from 10,938 posts
- English Wikipedia (1,506 articles): 8,420 pairs; Hebrew Wikipedia (714): 495 (Hebrew, kept for later)
- Halachipedia: 1 link only, so it stays unlabeled.
A consistency filter keeps a pair only if every number in the link text appears in the
href (drops `writes` -> a verse, `Shabbat 105b` -> Joshua 24:31) and it names more than a
generic word. ~15.7k pairs pass; `verify 500` sampled 500 per source, checked each gold
ref live -> `data/web_pairs.json` (1,000 pairs: 371 mangled, 629 clean, `where` URL per
row for attribution). Raw dumps and caches are in `pipeline/web_pairs_raw/` (gitignored).

**What it found:** the 2026-11-23 guard still let Sefaria's suggestions *add* words:
`Moreh Nevuchim` -> *Guide, Prefatory Remarks*; `Aruch Hashulchan 529:4` -> the Yoreh De'ah
volume; `Shmuel` -> *I* Samuel; `Samuel 1 13:1` -> *Rashbam on Exodus*. Fixed:
- `_keeps_all_words` is now two-way: a suggestion may change spelling/casing but may
  not add a meaningful word (only connectors and `Sefer`, per `_CANON_MAY_ADD`).
- `_adds_part_numeral`: reject a result whose title gained an I/II/III the citation
  didn't write (`Noda B'Yehuda, YD` -> Noda BiYehudah **I**).
- rules: strip a trailing number only if another number survives (`Yalkut Shimoni 1046`
  no longer becomes bare `Yalkut Shimoni` -> *on Torah*); strip trailing Hebrew years.
- `benchmark.classify` now treats a daf as covering its amudim and a range as covering
  points inside it (`Shabbat 88a-b` -> *Shabbat 88* vs a link to 88a is "coarser").
- `web_pairs.py eval` adds `label_noise`: same place, differing only by a commentary
  layer the writer never named (`Kidushin 81a` linked to *Ritva on Kiddushin*).

**Results (2026-11-24):**
- web mangled (n=371): **0 WRONG** (was 29 at first run), 122 correct, 71 coarser,
  5 label noise, 173 unresolved.
- web clean (n=629): 10 WRONG, all Sefaria's own reading of already-valid text where
  the writer linked something else (`OC 426` linked to the Tur/Bach; `Bereshit 26:5`
  linked to Chizkuni). These are label disagreements, not normalization errors.
- benchmark: 93 correct, 5 coarser, **0 WRONG**, 41 unresolved (`--strict` passes).

**Benchmark caveat:** 32 of the 139 rows are `source: rule-verified`, labeled by our own
rules, so they are circular: the benchmark rewards a rule for agreeing with itself. One
was wrong (`Sh'mot 19` was labeled the Shemot parasha; corrected to Exodus 19).
**Treat `data/web_pairs.json` as the primary correctness test from now on.** The
rule-verified rows should be re-labeled from an independent source or dropped.

## Mi Yodeya 2024+ via API, more fixes, source status (2026-11-24, later)

- `web_pairs.py miyodeya_api`: Mi Yodeya posts after the dump via the keyless SE API
  (sliding date window; pages stop at 25 without a key). 11,700 posts, 2,825 with Sefaria
  links (~24%, vs far fewer in the dump era), 6,732 pairs, **3,824 new usable pairs**.
  Source label `miyodeya_2024on`, so the committed sample stays stable.
- Web sample now **1,588 pairs** (616 mangled). Mangled: correct 225, coarser 148,
  finer 1, label noise 15, WRONG 5, unresolved 222. The 5 WRONG: 2 bare-section (decision
  c), 3 label disagreements (writer's text vs link: "with Rashi", a typo'd verse, Hebrew
  vs Christian verse numbering). **No resolver errors outside the bare-section policy.**
- Fixed: `Sefer` may no longer be added by a suggestion (*Sefer Yesodei HaTorah* is a
  different book); `Hilchot X` -> Rambam is skipped when another work in Sefaria is also
  called "Hilchot X" (`Hilchot Talmud Torah` = the Baal HaTanya's; also `Hilchot Shabbat`).
  Scoring: a cited point at one end of a linked range counts as coarser.
- **Source status:** Stack Exchange dumps done (small); Mi Yodeya API done; Common Crawl
  index currently timing out (plan: query the columnar Parquet index by domain instead,
  e.g. thetorah.com, myjewishlearning.com, etzion.org.il, ou.org, then fetch only those
  WARC records from data.commoncrawl.org); Usenet soc.culture.jewish available but
  unlabeled; Reddit pending your call; Quora excluded.
- The background full run started before these sources existed, so it covers only the
  dump + Wikipedia pairs. Rerun `verify`/`eval` with WEB_PAIRS_OUT afterwards to include
  the new ones.

## Second gap pass + Stack Exchange (2026-11-24)

- Added Hermeneutics / Christianity / History SE dumps: only 104 usable pairs (93 kept),
  but an academic citation register (`BT Yoma 35b`, `Genesis (or Bereshit) Rabbah 80:11`).
  The sample stays order-stable: existing sources keep their exact 1,000 pairs.
- Gap fixes (local `rules.py`/`resolve.py`; port to `shared_dialect.py` with the blog):
  a bounded Tanakh book-name map (Hebrew -> English, only in book position before a
  number; Shoftim/Shmuel/Melachim/Divrei HaYamim deliberately excluded), "X to Y" -> "X on
  Y", quoted abbreviations (`B"M`, `B"R`, `O"C`, `Yo"D`, `Rash"i`, ...), BT/B./JT/`Sefaria:`
  prefixes, Tanchuma-by-parasha comma form, and a trailing "and ..." clause allowed for
  Sefaria's `Rambam, Hilchot ...` compound titles.
- Web sample now 1,093 pairs. Mangled (n=399): correct 158, coarser 103, label noise 9,
  WRONG 2, unresolved 127. Benchmark unchanged at 0 WRONG.
- The 2 mangled WRONG: `Sefaria Radak on Genesis 32:32` (Christian vs Hebrew verse
  numbering; we followed the writer) and `Y"D 289` -> Shulchan Arukh (link went to the Tur).
- **Decision needed, bare section citations** (`YD 289`, `O.C. 122:1`, no work named).
  The pre-existing rule maps them to the Shulchan Arukh. Measured over all ~28k mined
  pairs: 477 bare section citations, **87% Shulchan Arukh, 13% other works** (Tur 3%,
  Arukh HaShulchan 2%, Mishnah Berurah 1%, Beit Yosef 1%, responsa, ...). Keep the
  convention (accept ~13% mislinks on this pattern) or abstain on bare sections. This is
  decision (c) in concrete form.

## Gap analysis + more sources (2026-11-24)

**Full web run in the background** (`pipeline/web_pairs_raw/full_run.sh`, log
`full_run.log`): verifies every consistent pair (~15.5k), then scores the resolver,
writing `pipeline/web_pairs_raw/web_pairs_full.json` and `..._scored.json`. Polite
serial pace, about a day in total; resumable from caches if interrupted.

**Gap fixes landed** (sample, mangled n=371): correct 122 -> 151, coarser 71 -> 86,
unresolved 173 -> 129, WRONG 0. Unclosed parens, chapter/paragraph/section-sign
locators, final s->t (Koheles), `SA`+section, `Hilchot X` -> Sefaria's own
`Rambam, Hilchot X` alt titles, tz/ts and final-h in the spelling skeleton, retrying the
full head (Mishna Brura). The guard now also rejects reordered words (`Aruch Hashulchan`
-> `Shulchan Aruch`) and added numbers (`..., part` -> `..., Part 1`).

**Remaining 129 unresolved, by kind (rough):** 21 name no work (context-only: `Nasso
16:1`, `Mitzvah # 594`), correct to leave; ~20 ambiguous or label disagrees (`Shmuel
23:8`); 20 commentator `X to/on/in Y` with Hebrew book names (`Ohr HaChaim to Shemot
23:2`), fixable with "to"->"on" + a bounded Hebrew->English book-name map; 11 parts of
multi-part works (`Moreh Nevuchim 3:53:2`); 10 abbreviations with quotes (`B"M`, `B"R`,
`O"C`, `Yo"D`); 3 Tanchuma by parasha; ~44 knowledge-heavy. Also: Sefaria's only title
for some Rambam sections is the full compound (`Hilchot Tefilah and Birkat Kohanim`), so
`Hilchot Tfila` is rejected as "adds words"; allowing a trailing `and ...` clause for
those would recover several.

**Source survey (for more test data):**
- *Other Stack Exchange dumps*, same format and code as Mi Yodeya (CC BY-SA, one
  download each): Hermeneutics (121 MB), Christianity (125 MB), History (93 MB). They
  cite Talmud/Midrash with Sefaria links in a non-yeshivish register. **Cheapest next win.**
- *Usenet soc.culture.jewish* (archive.org `usenet-soc.culture`: 750 MB mbox, plus
  soc.culture.jewish.moderated 666 MB). 1990s-2010s, mostly pre-Sefaria, so **unlabeled**.
  Good as a mangling stress set and for abstain-rate checks, not for correctness.
  (`soc.culture.judaism` doesn't exist; it's soc.culture.jewish.)
- *Reddit* (r/Judaism, r/Jewish via the Arctic Shift research API): links do appear,
  but Reddit's data terms restrict ML use and the archive is third-party. Gray; ask first.
- *Quora*: robots.txt explicitly forbids use for ML/AI systems without a license. **Skip.**
- *Sefaria's Hugging Face datasets*: `Sefaria/en_linker_gold_dataset` (GPL-3.0, 887
  examples, includes Halachipedia text) marks citation **spans** but not their refs, so it
  tests span detection (tier 1.5), not resolution. `Sefaria/links` and `database_export`
  are ref-to-ref links, not citations.
- *Not yet probed*: Common Crawl WAT outlinks to sefaria.org (labeled pairs at web scale,
  heavy processing); Sefaria source-sheet outside-text links (many are linker output,
  so biased); Mi Yodeya posts after the 2024-04 dump (SE API).

## Remote branch review (2026-11-23), resolved

- `claude/project-onboarding-status-lw5947`: superseded by PR #2 (its PR #1 was closed). **Remote branch deleted.**
- `claude/project-onboarding-plan-0ctxcz`: 6 docs-only commits (Yad Malachi case trimmed,
  Hebrew forum findings in `FINDINGS.md`). **Merged to `main`.**
- `claude/pd-index-submissions`: `docs/pd_index_submissions.md` synced with `main`'s
  list (added Chazon Ish as F4, dropped Teshuvot HaRadbaz since it's present, corrected
  Rokeach d.1238 and Yad Malachi d.1772). **Merged to `main`.**
- The two merged remote branches can be deleted once `main` is pushed.

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
     **largely done 2026-11-23/24** (correctness scoring + web pairs); the absent-works trap is
     still missing. See "Current status", loose end 13.
   - **(c)** Decide whether "unlinked, never mislinked" stays inviolable for tier 2, or a
     bounded mislink rate is acceptable behind confidence gates — the owner's call, not made.
   - **(d)** Blog-repo coverage regression from step 6: 43 citations linked by the old
     offline rules no longer resolve (Shulchan Aruch, Sefer HaChinuch, Tosfot, Bava Batra,
     Mesilat Yesharim, Yechezkel, Yalkut spelling variants). No mislinks; coverage only.
   - Bare-tractate gap: **mostly fixed** (`2dbf999`, see "Latest work"). Still open: names
     needing a real spelling correction rather than reformatting (`"Kesubos"`,
     `"Mesechtas Berochos"`, `"Mesechtas Menochos"`) — needs a mislink-risk decision, not a
     guess.
   - (2026-11-24: the code half of this is done; see "Current status", loose end 13.)
     Also queued from the design pass, not yet done: fix `pipeline/mine_wide.py`'s HP-corpus
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
     at `docs/upstream/SEFARIA-CASE-SENSITIVITY-BUG.md` (this repo) — not posted, pending the same
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
python3 test_rules_offline.py              # 67 offline regression cases (no network); must pass
python3 benchmark.py --strict              # correctness vs the verified dataset; must show WRONG 0
python3 test_shared_dialect.py             # diff-check vs the blog repo's vendored copy
python3 pipeline/build_final.py            # rebuild the most-wanted list (uses work_frequency.json)
python3 -c "import json;print(len(json.load(open('data/citation_dataset.json'))))"  # 139
```
