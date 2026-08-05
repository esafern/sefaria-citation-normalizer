# Integration Plan: Shared Dialect Layer (B+E)

_Start here if you're picking up the "integrate the blog's linker with this repo" task.
Read this file first, then `HANDOFF.md`, then look at the two live codebases below
before writing anything — they've moved since this was written._

## Why this exists

Two independently-maintained citation linkers exist:

1. **This repo** (`sefaria-citation-normalizer/normalizer/rules.py` + `resolve.py`) —
   propose-candidates-then-verify-via-Sefaria's-`/api/name`. Never constructs a URL
   itself; needs network or cache to produce a link. General-purpose, no per-work
   whitelist, the intended eventual Sefaria contribution.
2. **The blog repo** (`~/work/rav-shvat-blog/pipeline/sefaria_linker/`) — a private repo
   building Rav Ari Shvat's Torah blog. Contains **two different designs**:
   - `offline.py` — hardcoded per-work regex → URL construction (`TALMUD`, `TANACH`,
     `RAMBAM` dicts, qualified-tractate handling, dual commentary+base linking). No
     network, ever. **This is what actually runs** — `pipeline/sefaria.py` calls only
     this file.
   - `dialect.py` + `resolver.py` — same propose→verify philosophy as this repo's
     `rules.py`/`resolve.py`, independently evolved. **Currently dead code** — only
     exercised by `pipeline/test_linker.py`, never wired into the live CLI.

On 2026-08-05, a real citation (`"Tosefta, Av.Z. 5, 2"`, from Rav Shvat's own writing)
exposed the cost of this duplication: the fix — expanding the `Av.Z.` abbreviation, and
discovering Sefaria's trie rejects `"Tosefta, X"` but accepts `"Tosefta X"` (a general,
not citation-specific, finding) — had to be made **twice**, by hand, in two different
rule syntaxes, because there is no shared code path. It only reached both repos because
the user caught it and asked; nothing structural prevents this drift recurring.

## Decision: B + E

**B — Extract just the dialect/abbreviation layer as shared.** Not the whole linker.
Specifically: abbreviation maps (`Av.Z.` → `Avodah Zarah`, `O.Ch.` → `Orach Chayim`,
etc.), structural corpus prefixes (`Tosefta,? ` comma-handling, `Yerushalmi,? `,
`Tanchuma,? `), and the Rambam-section name map. This is genuinely general Anglo-Orthodox
dialect knowledge, not work-specific mislink-avoidance logic — it belongs in one place.

**Stays local to the blog, NOT shared:** `offline.py`'s per-work URL-construction dicts
(`TALMUD`, `TANACH`, `RAMBAM`, `BOOK_LEVEL`) and its hand-tuned precision logic —
qualified-tractate shielding (Yerushalmi/Mishnah vs Bavli), dual commentary+base
linking, the "trim to first ref" jammed-citation handling. These emerged from real
user feedback fixing actual mislinks on the live blog and are legitimately specific to
guaranteeing safe, deterministic, no-network builds — a design requirement the blog's
README explicitly commits to ("offline builds never fail if Sefaria is unreachable").
Porting this into the propose→verify model is a bigger, separate, deliberate project
(that would be "C" from the options considered) — not this task.

**E — No live cross-repo dependency.** The other session actively evolving this repo
(Yad Malachi, Mi Yodeya, most-wanted rebuilds — see git log) makes a live import/submodule
dependency risky: the blog's Sefaria links could destabilize from unrelated changes here.
Instead: the shared dialect module is **vendored** — a byte-identical copy lives in both
repos — with a **diff-check test in each repo's test suite** that fails loudly the moment
the two copies diverge. Drift becomes impossible to miss, even though it's still possible
to happen (a deliberate trade against A's instability risk, revisit if that calculus
changes — e.g. once the other session's work stabilizes).

## Concrete steps

1. **Design the shared module's shape.** Candidate name: `dialect.py` (matches the
   blog's existing naming) or `shared_dialect.py`, exporting:
   - `SECTIONS` (Shulchan Aruch section abbreviations)
   - `RAMBAM_SECTIONS` (already exists in both repos, compare carefully — the two
     current versions have *different* entries, e.g. this repo's `rules.py` has
     `"issureibiah"`/`"mezuza"`/`"avel"` that the blog's `dialect.py` lacks, and the
     blog has some the normalizer lacks — reconcile into one superset)
   - `STRUCTURAL_PREFIX` / `PREFIXES` (Tosefta/Yerushalmi/Mishnah/Tanchuma comma
     handling — note this repo's version and the blog's `PREFIXES` list aren't
     identical either, same reconciliation needed)
   - abbreviation expansion including the `Av.Z.` fix and its regex-`\b` lesson
     (see "Bugs already fixed" below — don't reintroduce them)
2. **Reconcile, don't just pick one.** Read both current files in full:
   - `~/work/sefaria-citation-normalizer/normalizer/rules.py`
   - `~/work/rav-shvat-blog/pipeline/sefaria_linker/dialect.py`
   They've diverged in real, non-trivial ways (different RAMBAM_SECTIONS entries,
   different structural-prefix lists, different composition strategies for how
   abbreviation expansion combines with other rules). Merge into one correct superset;
   don't silently drop either side's coverage.
3. **Extract to the shared file, place a copy in each repo**, at whatever path each
   repo's import structure expects (blog: `pipeline/sefaria_linker/`; here:
   `normalizer/`). Each repo's existing code imports its own local copy — no new
   cross-repo dependency mechanics needed.
4. **Add the diff-check test.** Simplest form: a test that reads both files (paths
   will need to be repo-relative or configured) and asserts byte-equality, or hashes
   both and compares. Needs to work from either repo's test runner without requiring
   the other repo to be checked out at a known relative path — consider whether the
   check lives in one repo only (simpler, but only catches drift when *that* repo's
   tests run) or a small script in both (more robust, more to maintain). Decide and
   document the choice.
5. **Wire the blog's live path to use it correctly.** Right now `offline.py` doesn't
   call `dialect.py` at all (that's *why* today's fix needed a second hand-copy).
   Decide: does `offline.py` call into the shared module's abbreviation-expansion
   before running its own per-work regexes? (Likely yes — pre-expand `Av.Z.` etc.
   before the TALMUD/TANACH pattern matching runs.) Get this actually wired in and
   tested against `pipeline/test_linker.py`'s existing regression suite (38-citation
   offline snapshot) — must not regress.
6. **Verify against real content.** Re-run the blog's linker over all 118 letters +
   the Q&A posts after wiring, confirm no citation that previously resolved now
   fails, and check whether previously-unresolved citations newly resolve (bonus,
   not required).

## Bugs already fixed today — don't reintroduce them

If reconciling by hand rather than starting from the current `rules.py`/`dialect.py`,
preserve these (both already fixed and pushed in this repo's `normalizer/rules.py` as
of commit `413770c`, and in the blog's `offline.py`/`dialect.py` as of commit `9d98ada`):

- **Regex `\b`-after-optional-char bug**: `r"\bAv\.?\s*Z\.?\b"` backtracks
  unpredictably and silently drops the trailing period when both the optional char and
  what follows are non-word — producing `"Avodah Zarah."` (stray period) instead of
  cleanly consuming it. Fix: put `\b` right after the *required* literal character
  (`Z`), not after an optional one: `r"\bAv\.?\s*Z\b\.?"`.
- **Ordering bug**: comma→colon conversion (`"5, 2"` → `"5:2"`) must happen **before**
  trailing-footnote-number stripping, not after — otherwise the tail-strip rule can't
  distinguish a legitimate `chapter, verse` pair from a stray trailing footnote number
  and truncates the verse off entirely (`Tosefta_Avodah_Zarah.5` instead of `.5.2`).
- **Structural-prefix candidates must be generated early**, before any rule that might
  truncate the citation (e.g. a "trim to first ref when several are jammed together"
  rule) — otherwise the comma-stripped candidate inherits the truncation.

## Current repo state (as of this writing, both pushed)

- Blog: `rav-shvat-blog` @ `9d98ada` — clean, nothing pending.
- Normalizer: `sefaria-citation-normalizer` @ `413770c` — clean except a gitignored
  `.DS_Store`. **Note**: another session is actively working in this repo (see git log
  for `claude/pd-index-submissions`, `claude/project-onboarding-*` branches and recent
  large commits on `main` — Yad Malachi case study, Mi Yodeya corpus, most-wanted
  rebuild). Pull before starting; expect more drift-in-the-other-direction (i.e. new
  normalizer work you haven't seen) by the time you read this.
