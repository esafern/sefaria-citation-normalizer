# Getting listed on Powered by Sefaria: process and polish plan (2026-11-25)

## The process

Sources: developers.sefaria.org ("Projects Powered By Sefaria", "Project Acceptance Criteria",
"Copyright and Data Use", "Public Contributions"), and the Sefaria-Project code for the new form
(`powered_by/models.py`, PRs #4042, #4100, #4101, merged November 2026).

1. **Showcase:** https://powered-by.sefaria.org (about 180 projects). It's curated: "Use of
   Sefaria's API or data does not automatically result in inclusion."
2. **How to apply (new this month):** sefaria.org account -> Settings -> **Developer Settings** ->
   create a project (this is also where API keys now live) -> **"Publish your project"**. The old
   Formstack form is being retired; existing listings were migrated on 2026-11-19.
3. **What the form asks** (from the data model): project name, **live link**, source-code URL,
   description, why you built it, category, which Sefaria tools you used (Sefaria API, Linker, MCP,
   ...), reach (number of users, or "proof of concept"), an image, whether you show the Powered-by
   badge, organization, your technical experience, **whether it was vibe-coded**, purpose (personal /
   research / community / ...), and "anything else".
4. **Categories:** Learning & Study Tools; AI Projects, Apps, & Other Tools; Visualization & Data
   Analysis; Community, Interaction, & Social; **Extensions, API Integrations, & GitHub Code**; Other.
   This project fits "Extensions, API Integrations, & GitHub Code", and arguably "Visualization &
   Data Analysis" for the most-wanted list.
5. **Review:** case by case, at Sefaria's discretion. They look for projects that deepen engagement
   with Jewish texts, use sources respectfully, and show creativity, scholarship or accessibility.
   Staff also track whether a listed project is live or dead, and whether it's buggy.
6. **Name and logo:** "Sefaria" is a trademark. Projects may use the official Powered-by badges, and
   must make clear they are *not* developed by Sefaria.

## Where the repo stands today (it is already public)

Strong: a clear idea (propose -> verify), measured correctness with 0 known resolver mislinks, a
~19k-pair labeled dataset, an offline test suite, real bug reports upstream, the most-wanted list.

Gaps a reviewer or a first-time visitor would hit:
- **No LICENSE.** Nobody may legally reuse the code. The web-pairs data is CC BY-SA, which requires
  the derived dataset to be CC BY-SA too.
- **`main` is stale.** All work since 2026-11-23 (29 commits) is on `next-work`, and `main`'s README
  still claims "107/139 (76%)" from before the correctness work.
- **The README is out of date and has no install or usage section** beyond one snippet.
- **The root is cluttered with internal working docs**: HANDOFF, INTEGRATION-PLAN, LESSONS,
  CORPUS-COMPARISON, the bug and PR drafts. `contribution/` holds unsent email drafts, and they're
  public now.
- **Private references:** INTEGRATION-PLAN.md and HANDOFF.md name the private blog repo and "Rav
  Shvat's own writing". `citenorm/resolve.py`, `shared_dialect.py` and `test_shared_dialect.py`
  refer to that repo. `pipeline/mine_miyodeya.py` has a hard-coded scratch path from an old session.
- **No live link.** The form wants one, and staff check whether it's live.
- **API etiquette:** requests go out with Python's default user agent. Polite pacing and caching
  exist but aren't documented.
- **Data provenance isn't documented per file.** Halachipedia declares no license (its siteinfo
  rights field is empty); we keep only short citation strings from it, and the README should say so.
- **Open policy decisions 1, 5 and 6** (bare sections, Mishnah convention, short aliases) are
  currently hard-wired.

## Polish plan, in priority order

**Before listing (must):**
1. **Merge `next-work` into `main`.**
2. **Licenses:** code under MIT, or GPL-3.0 to match Sefaria's; `data/web_pairs*.json` under CC BY-SA
   4.0 with attribution; a short `data/README.md` giving each file's source, license, fields and
   size. Note Halachipedia's missing license and what we keep.
3. **README rewrite:**
   - what it does, with 3-4 before/after examples
   - install (stdlib only at runtime) and usage (Python API + a small CLI)
   - accuracy, honestly stated, with the method (correct/coarser/WRONG on ~19k real citations;
     abstains rather than guesses)
   - limits
   - data and licenses
   - API etiquette
   - the Powered-by badge and a "not affiliated with or developed by Sefaria" line
   - links to the upstream issues (#1016, #4150)
4. **Clean up the tree:** move internal docs to `docs/notes/` (or drop them from the public branch);
   move the unsent emails out of the public repo until they're sent; remove the private-repo
   references and the hard-coded scratch path. Decide whether the Yad Malachi case and images belong
   here or in their own repo.
5. **Identify ourselves to the API:** a User-Agent like `sefaria-citation-normalizer/0.x
   (+repo URL)`, default pacing, and the cache, all documented.
6. **A live link:**
   - Option A, cheapest: the GitHub repo as the link, category "GitHub Code", reach "proof of
     concept".
   - Option B, better: a small free demo (a Hugging Face Space or a static page) where you paste a
     citation and get the link, plus the most-wanted list rendered as a page.

**Strongly recommended:**
7. **Packaging and CI:** `pyproject.toml` (installable), a `sefaria-normalize` CLI, and GitHub
   Actions running `test_rules_offline.py` on every push (no network). Run the networked benchmark
   only on a schedule, gently.
8. **Make decisions 1, 5 and 6 options rather than hard-wired:** e.g. `strict=True` (abstain on
   conventions) vs `conventional` (bare section -> Shulchan Arukh, chapter:mishnah -> Mishnah). It's
   useful either way, and ships before the decisions are final.
9. **Publish the evaluation set:** the ~19k web pairs as a Hugging Face dataset with a dataset card
   (Sefaria publishes its own datasets there, e.g. `Sefaria/en_linker_gold_dataset`). A
   citation -> ref resolution benchmark doesn't exist publicly yet; it's useful to Sefaria's linker
   team and to researchers.
10. **A version and changelog** (`v0.1.0`), so the listing points at something stable.

**Nice to have:**
11. A one-page writeup (blog post or `docs/`) of the method and findings: propose -> verify, the
    mislink taxonomy, the Sefaria bugs found. It doubles as the "why you built it" answer.
12. Later: offer the normalizer as a Sefaria MCP-compatible tool, or as a pre-pass in front of
    Sefaria's linker.

## Form answers (draft)

- **Name:** Sefaria Citation Normalizer. Consider a name that doesn't lead with "Sefaria", for the
  trademark reason above (e.g. "Citation Normalizer for Sefaria").
- **Category:** Extensions, API Integrations, & GitHub Code (+ Visualization & Data Analysis)
- **Tools used:** Sefaria API (`/api/name`, `/api/index/titles`, find-refs for mining)
- **Reach:** proof of concept (or the blog's readership, if it ships there)
- **Purpose:** research / community
- **Vibe-coded:** answer honestly. Built with an AI coding agent, with human direction and review.
- **Why:** English-language Torah writing (Halachipedia, Q&A sites, blogs) cites sources in
  Ashkenazi and academic shorthand that Sefaria's linker often can't resolve. This turns those
  citations into correct links, or leaves them unlinked rather than guessing.
