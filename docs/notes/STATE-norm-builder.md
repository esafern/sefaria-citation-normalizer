# State: norm-builder

_Updated 2026-11-27. Branch `norm-builder` at main's 165f8dc plus this note; nothing of
norm-builder's merged yet._

## Where things stand

- Released: v0.1.0 (MIT, default conventions `common`, `strict` available). Dataset published
  on Hugging Face, tagged `dataset-v1`.
- Since 0.1.0, unreleased on main: `--explain` / `explain()`, `ResolverUnavailable` (outages
  never cached), `python3 -m citenorm`, REST API v1 (`citenorm/api.py`, `docs/API.md`, built,
  not deployed), Mishmeret's role guard.
- Offline tests pass here: rules 108/108, cache 8/8, API PASS, demo PASS.
- Accuracy (README, 1,588-pair web sample, 616 mangled): 257 correct, 157 coarser, 7 wrong
  (none a resolver error), 177 unlinked. Benchmark: 97 correct, 3 coarser/finer, 0 wrong.
- The full-run scores (`pipeline/web_pairs_raw/web_pairs_full_scored.json`, 19,227 pairs) were
  made with 2026-11-24-evening code. `pipeline/web_pairs_raw/` and the caches are gitignored and
  live only in the main clone, not in this worktree.
- With the owner or other roles (not norm-builder's): demo deploy (girsa-demo-operator), Powered
  by Sefaria form, replies to the 2026-11-25 emails, where to deploy the API, posting the #1016
  comment / PR, Sefaria and Aruch HaShulchan outreach.

## Next work, in order

From HANDOFF "Next steps" and ROADMAP "Planned".

1. **Re-measure on current code.** Rerun `web_pairs.py eval` over the full 19,227 pairs (own
   cache, own output) so later changes have a current baseline. Tier 1.5 (HANDOFF 1a) landed
   2026-11-24; this is its "re-measure the residue". Needs the raw pairs from the main clone.
2. **Absent-works mislink trap** (HANDOFF 1b, the missing part of the harness): citations of
   works Sefaria lacks (`data/sefaria_most_wanted.json`) that must stay unlinked, as a test that
   fails on any link.
3. **Offline mode** (ROADMAP, command line): `--offline` answers from the cache only, no network.
4. **Cache commands** (ROADMAP): `citenorm cache info` and `citenorm cache clear [pattern]`.
5. **Batch CSV/TSV** (ROADMAP): resolve one column, write back `url`, `ref`, `status` (and
   optionally the reason).
6. **Multi-part works** (ROADMAP, resolver): `Moreh Nevuchim 3:53:2` -> Guide, Part 3.
7. **Halachipedia triage** (HANDOFF 1, loose end 13): re-resolve `pipeline/hp_unresolved.json`
   with today's resolver first; then head extraction (merge spelling twins with
   `pipeline/presence.py`), `pipeline/build_hp_triage.py`, and the review server and page in the
   yad-malachi style.
8. **Bare tractate names that need a spelling correction** (`Kesubos`, `Mesechtas Berochos`,
   `Mesechtas Menochos`): measure what current code does; any change is a mislink-risk decision
   for the owner, not a guess.
9. **Running text** (ROADMAP) and then the API's `/v1/link-text`: a detector (Sefaria's
   `find-refs` spans, or our own) in front of the resolver.
10. **Hebrew-script citations** (ROADMAP), using the collected Hebrew Wikipedia pairs.
11. **Demo: show the reason for unlinked citations** (ROADMAP). Prepare only; a visible change
    needs the reviewer's go through girsa-demo-operator.

## Not norm-builder's now

- Tier 2 (HANDOFF 1c): waits on the owner's decision whether "never mislinked" stays inviolable.
- Blog-repo port and its 43-citation coverage regression (HANDOFF 1d, ROADMAP): on hold, and
  `~/work/rav-shvat-blog` is foreign to this role.
- API deployment, demo deployment, tags, pushes: norm-operator / girsa-demo-operator / owner.
- Most-wanted list (HANDOFF 2): done; the Wikidata death-date check is worth rerunning
  periodically, no date set.
- Contributions to Sefaria (HANDOFF 3): held for the owner's call.
