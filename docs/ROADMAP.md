# Roadmap

## Done since 0.1.0 (unreleased)

- **`--explain`** (CLI) and **`citenorm.resolve.explain()`** (Python): for each citation, the
  spellings tried, every suggestion from Sefaria accepted or rejected and why ("drops
  'Palagi'", "adds 'I'", "changes the word order", "picks a section of the Shulchan Arukh the
  citation doesn't name"), and the convention a reading relies on. The text view is a summary;
  `--json` has every step. The trace is per call (a context variable), so it is safe for the API
  server below.
- Failure handling: an unreachable Sefaria raises `ResolverUnavailable` and is never cached;
  the CLI prints `?` and exits 1.

## Planned

### A REST API: v1 built (not deployed)

`citenorm/api.py`, documented in `docs/API.md`: `/v1/resolve` (GET one, POST up to 50),
`/v1/explain`, `/v1/health`, `/v1/openapi.json`; per-client and global limits, optional API keys,
CORS, answers cached per code version, outages reported as `unavailable` and never cached.
`citenorm-api` serves it locally. **Open:** where to deploy it, and `/v1/link-text`.

The original plan, for reference: a small HTTP service in front of the resolver, for sites and tools that can't run Python.
Versioned from the start; tags `api-v<n>` mark versions and `prod-YYYY-MM-DD` marks deploys
(`docs/RELEASING.md`). A consumer pins an API version, so a version never changes once tagged.
Sketch:

- `GET /v1/resolve?q=...&conventions=common|strict` -> `{citation, status, url, ref, convention}`
- `POST /v1/resolve` with a list (batch)
- `GET /v1/explain?q=...` -> the `explain()` trace
- `POST /v1/link-text` -> running text with citations linked (see below)
- Same politeness as the library (identifying User-Agent, pacing, shared answer cache), plus
  per-client rate limits and keys. The demo's app (`demo/app.py`) is a starting point.

### Command line

- **Batch files:** read a CSV/TSV, resolve one column, write it back with `url`, `ref`,
  `status` (and optionally the reason) columns, for fixing a spreadsheet of citations.
- **Running text:** take an article or footnotes and return them with citations linked. Needs a
  detector: either Sefaria's `find-refs` (its ML linker finds spans; citenorm resolves the ones it
  can't), or a detector of our own trained on the web-pairs data.
- **Offline mode:** answer from the cache only, no network (`--offline`), e.g. for a build
  pipeline that must not call out.
- **Cache commands:** `citenorm cache info` (size, code version, entries) and `citenorm cache
  clear` (all, or entries matching a pattern).

### The demo (girsa.net/cite/)

- Show the reason for each unlinked citation, from `explain()`. A visible change, so it needs
  the reviewer's go under the demo's stability-first rule.

### Resolver

- Multi-part works where the first number is the part (`Moreh Nevuchim 3:53:2` -> Guide, Part 3).
- Hebrew-script citations (the Hebrew Wikipedia pairs are collected, not yet used).
- The private blog's port of the guards and rules (on hold).
