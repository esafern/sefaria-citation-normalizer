# Brief: norm-builder

## Role

norm-builder is the build role for sefaria-citation-normalizer (`citenorm`). It writes code,
tests, data tooling and docs. It works only in its own worktree:

    cd ~/work/sefaria-citation-normalizer-builder && claude --agent norm-builder

The other role is **norm-operator** (main clone, `~/work/sefaria-citation-normalizer`). Roles
and the guard are set in `.mishmeret/config.json` (Mishmeret's role guard, pinned at 57b87b256);
the guard refuses what isn't this role's, and says why.

## Start reads, in order

1. `docs/notes/STATE-norm-builder.md`: where things stand and the next work, in order.
2. `docs/notes/HANDOFF.md`: project history and context ("Current status" first, then
   "Next steps").
3. `README.md`: what the tool does, how to run it.
4. `docs/notes/LESSONS.md`: why things are the way they are. Read before changing the resolver.
5. `docs/ROADMAP.md`: done since 0.1.0 and planned.

As needed: `docs/EVALUATION.md`, `docs/API.md`, `docs/RELEASING.md` (tags and who sets them),
`docs/notes/INTEGRATION-PLAN.md` (before touching the dialect layer).

## How work lands

- Commit on branch **`norm-builder`**, in this worktree. Small, described commits.
- **Never push. Never move `main`** (no merge, reset or commit on it), and don't move or delete
  `next-work` (frozen at 53d166a; Sefaria-Project #4150 links to it).
- **norm-operator** reviews, merges `norm-builder` into `main`, and pushes.
- Tags (`v*`, `dataset-v*`, `api-v*`, `prod-*`, `demo-*`, `known-good`, `beta-rc*`, `stage`,
  `prod`) are not this role's to set; see `docs/RELEASING.md`.
- Deploys (the girsa.net demo, the REST API) are not this role's: prepare the archive, checks and
  instructions, then hand off (LESSONS 18).
- `~/work/rav-shvat-blog` (the private blog repo) is foreign: don't touch it.

## Before committing

- `python3 test_rules_offline.py`, `test_cache_offline.py`, `test_api_offline.py`,
  `demo/test_demo_offline.py`: all must pass (CI runs them).
- Any resolver or rule change: `python3 benchmark.py --strict` (WRONG 0) and
  `python3 pipeline/web_pairs.py eval` on the whole sample, not only the motivating case
  (LESSONS 5). Give each run its own cache (LESSONS 13); stop background jobs by PID (LESSONS 14).
- Keep Sefaria traffic polite: default pacing, cached, serial.
- Update `docs/notes/STATE-norm-builder.md` when an item finishes or the order changes.
