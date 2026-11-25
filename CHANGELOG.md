# Changelog

## 0.1.0 (2026-11-25)

First public release as a package.

- `citenorm` package and command-line tool (Python 3.10+, standard library only).
- Propose-then-verify resolution against Sefaria's `/api/name`, with checks that reject any
  answer that drops, adds or reorders words, adds a number or part, relies on a Talmud side or
  Shulchan Arukh section Sefaria filled in, or confuses look-alike transliterations.
- A pass over Sefaria's full title list when its autocomplete ranking misses the right title.
- `conventions="common"|"strict"` for the three ambiguous patterns (bare Shulchan Arukh
  sections, tractate + chapter:mishnah, 2-3 letter aliases).
- Polite API use: identifying User-Agent, pacing, caching; data cached in `~/.cache/citenorm/`.
- Evaluation: correctness-based scoring; a 1,588-pair sample of writer-labeled web citations;
  100 offline regression tests in CI.
- Datasets: web-mined citation pairs (CC BY-SA 4.0); "most wanted" list of works Sefaria lacks.
