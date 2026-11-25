# Releasing, deploying and tagging

## Protected tags

A GitHub ruleset ("Protected release and deploy tags") lets only the repository admin create,
move or delete these tags. Admins bypass it, and so does anything run with the admin's
credentials, so it stops collaborators and accidents, not the owner's own tools; this document
is what keeps those disciplined.

| Tag | Marks | Moves? | Who tags |
|---|---|---|---|
| `v<major>.<minor>.<patch>` (pattern `v[0-9]*`) | A package release: `citenorm/__init__.py`'s `__version__`, a `CHANGELOG.md` entry, a GitHub release. `v[0-9]*` rather than `v*`, so a tag like `vendor-x` isn't caught. | Never | The operator, after the full check passes |
| `dataset-v<n>` | The commit whose `pipeline/export_dataset.py` produced a published Hugging Face dataset. The tag message records the Hugging Face repository and its revision hash. | Never | The operator, after the upload |
| `api-v<n>` | A version of the REST API (planned). A consumer pins it; never move what a customer depends on. | Never | The operator, when an API version ships |
| `prod-YYYY-MM-DD[.n]` | The commit deployed as the REST API's production service, one per deploy (`.2` for a second deploy that day): the history and the way back. | Never | The operator, when a deploy is confirmed |
| `demo-YYYY-MM-DD[.n]` | The commit whose demo archive (`dist/citenorm-demo-<commit>.tar.gz`) is live at girsa.net/cite/. girsa-demo-operator deploys it but can't push here, so this repository's operator tags it when girsa-demo-operator confirms the deploy. (Girsa's own `demo-good` tag marks its side.) | Never | The operator |
| `known-good` | The last commit whose full check passed: the commit to roll back to. | Yes, forward, only by `release_check.py --tag` | The operator |

## The full check

`python3 release_check.py` (exit 0 means HEAD may become `known-good`):

1. Offline suites: `test_rules_offline.py` (102 rule and guard cases), `test_cache_offline.py`
   (non-UTF-8 locale, stub files, outages), `demo/test_demo_offline.py` (limits, headers).
   CI runs these on every push.
2. `benchmark.py --strict`: 0 WRONG on the 139-citation benchmark.
3. The web sample (`data/web_pairs.json`) scored **at HEAD's code**
   (`python3 pipeline/web_pairs.py eval`; the output records the code fingerprint): no mangled
   WRONG outside the reviewed list in `docs/known_wrong.json`, and no request errors.

Answer caches are named after a fingerprint of the resolver code
(`citenorm.code_fingerprint()`), so a code change always starts a fresh cache: no check ever
reads answers computed by older code.

The full 19,000-pair run (`pipeline/web_pairs_raw/full_run.sh`) takes about a day. It is run
before a release, not for every `known-good`.

## A release

1. Full check passes; also run the full set, and review any new WRONG (add to
   `docs/known_wrong.json` only if it's a convention or writer-side noise; otherwise fix it).
2. Bump `__version__`, add the `CHANGELOG.md` entry, commit.
3. `git tag -a v<version> -m "..."`, push the tag, `gh release create v<version>`.
4. `python3 release_check.py --tag` to move `known-good` to the release.

## A demo deploy (girsa.net/cite/)

1. Full check passes on the commit.
2. `python3 demo/build.py` gives `dist/citenorm-demo-<commit>.tar.gz`; update its "Changes since the
   last deployed archive" note in `demo/DEPLOY.md` first.
3. Hand the archive to girsa-demo-operator (a REQUEST in its pane, via the reviewer); it checks it
   on a copy, then live, under its own rules.
4. When it confirms the deploy, tag the commit `demo-YYYY-MM-DD`.
