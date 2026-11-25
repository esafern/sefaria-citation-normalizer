# Data in this repository

What each file is, where it came from, and what you may do with it. The code's license
is separate (see the repository root). Nothing here is Sefaria's own data unless said so;
Sefaria was used to *verify* references through its public API.

## Evaluation data (citation -> Sefaria ref)

| File | What | Source | License |
|---|---|---|---|
| `web_pairs.json` | 1,588 labeled pairs: a citation as a person wrote it (`raw`), the Sefaria ref they linked to (`sefaria_ref`, verified live), whether Sefaria already resolves the raw text (`clean`), the source (`source`), and the post or article it came from (`where`). | Hyperlinks to sefaria.org in Mi Yodeya (Judaism Stack Exchange; the archive.org dump of 2024-04 and the public API since then), English Wikipedia, and the Hermeneutics, Christianity and History Stack Exchange sites. Mined by `pipeline/web_pairs.py`. | **CC BY-SA 4.0**, inherited from the sources. Attribution: the `where` URL of each row. |
| `web_pairs_scored.json` | The same rows plus this tool's answer (`ours`) and its score (`outcome`: correct / coarser / finer / label_noise / WRONG / unresolved). | Derived from `web_pairs.json`. | CC BY-SA 4.0 |
| `citation_dataset.json` | 139 pairs: the original benchmark (`benchmark.py`). `raw`, `sefaria_ref`, sometimes `my_canonical`, `source`, `label_note`. | Citations that Sefaria's linker detected but could not resolve on public Sefaria source sheets; labeled with an LLM and verified against Sefaria. 32 rows were labeled by an early version of this tool's own rules; all were hand-reviewed in 2026-11 (`source` says so). | Short bibliographic strings and our labels: CC BY-SA 4.0. |
| `miyodeya_pairs.json` | An earlier, smaller set of Mi Yodeya pairs, labeled with an LLM and verified against Sefaria. | Mi Yodeya (Judaism Stack Exchange) | CC BY-SA 4.0 |

The full mined set (about 19,000 verified pairs) is published separately as a dataset;
see `docs/DATASET.md`.

**Known noise:** some links don't match their text, e.g. a writer cites "Rashi to Devarim
21:27" but links Numbers 21:27, or links the commentary they were reading rather than the
verse they cite. `web_pairs_scored.json` marks the recognizable cases as `label_noise`;
others remain in WRONG. See `docs/EVALUATION.md`.

## The "most wanted" list (works Sefaria lacks)

| File | What | Source | License |
|---|---|---|---|
| `SEFARIA-MOST-WANTED.md`, `sefaria_most_wanted.json` | 71 works that Halachipedia cites and Sefaria doesn't have, ranked by citation count and split by copyright status (public domain vs modern). | Citation counts from 640 Halachipedia pages (`pipeline/`); presence checked against Sefaria's API; authors' death years partly from Wikidata. | Our analysis: CC BY-SA 4.0. |
| `wikidata_deathdate_findings.json` | The death-year cross-check behind the public-domain split. | Wikidata (CC0) | CC0 |
| `ANALYSIS.md`, `english_gap.json`, `MOST-CITED-ABSENT-BY-CORPUS.md` | Analyses built on the list: top works, genres, which present works lack English. | Our analysis | CC BY-SA 4.0 |
| `CASE-YAD-MALACHI.md`, `images/`, `ocr-samples/` | A worked digitization case for the most-cited public-domain absent work. Images are page scans of public-domain printings (sources cited in the document) and one screenshot illustrating a broken citation. | As cited in the document | Text: CC BY-SA 4.0. Scans: public-domain works; respect each scan provider's terms. |

## Mining by-products in `pipeline/`

`hp_*.json`, `work_frequency*.json`, `wiki_freq.json`, `sheet_work_freq.json`,
`*_failures.json`, `v3_*.json`, `unresolved_for_labeling.json`, `*auto_resolved.json`: the
intermediate outputs of the mining runs (citation strings, work-name counts). They are kept
so the analyses can be rebuilt without re-mining.

**About Halachipedia:** the site declares no content license. These files keep only short
citation strings (source references, not article text), and counts derived from them.

## Not in the repository

Raw dumps and caches (`pipeline/web_pairs_raw/`, `pipeline/hp_cache/`, `pipeline/mine_cache/`,
`*_cache.json`) are ignored by git. They can be regenerated; please do it gently (the scripts
pace and cache every request).
