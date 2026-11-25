# How citenorm is evaluated

## The test sets

1. **Web pairs** (primary). Citations that people hyperlinked to Sefaria, so each one's
   correct answer was chosen by its writer, not by us. Collected by `pipeline/web_pairs.py` from
   Mi Yodeya, English Wikipedia and three other Stack Exchange sites; filtered so the link text
   names a work and every number in it appears in the link; each target verified live.
   About 19,000 pairs in total ([DATASET.md](DATASET.md)); a fixed 1,588-pair sample is
   committed as `data/web_pairs.json`. The sample stays stable when sources are added.
2. **Benchmark** (`benchmark.py`, `data/citation_dataset.json`). 139 citations from Sefaria
   source sheets that Sefaria's linker detected but couldn't resolve. Smaller and older; 32
   labels were originally derived from early rules and were hand-reviewed in 2026-11.
3. **Offline regression cases** (`test_rules_offline.py`). 100 cases, each from a real failure
   (a mislink caught, or a correct link lost). No network; run in CI.

## How an answer is scored

Each answer is compared with the label as a reference, and gets one outcome:

| Outcome | Meaning |
|---|---|
| correct | the same reference |
| coarser | contains the label (the chapter for a verse; the whole daf for one side; a range that includes the point). Not a mislink. |
| finer | inside the label (the label was less specific than the text) |
| label_noise | same location, but writer and link disagree about a commentary layer the writer did or didn't name ("Kidushin 81a" linked to Ritva on Kiddushin; "Rashi in Breishit 29:25" linked to the verse) |
| **WRONG** | anything else: the number that must stay at zero |
| unresolved | left unlinked (the safe failure) |

`clean` rows are those Sefaria's `/api/name` already resolves as written; `mangled` rows need
normalizing and are the real test. Clean-row WRONGs are Sefaria's own reading of text that
already resolves, where the writer linked something else (e.g. `OC 426` linked to the Tur).

## Current results (2026-11-25)

Sample (`data/web_pairs.json`, 1,588 pairs), current code:

| | n | correct | coarser | finer | label noise | WRONG | unresolved |
|---|---|---|---|---|---|---|---|
| mangled | 616 | 257 | 156 | 1 | 18 | 7 | 177 |
| clean | 972 | 675 | 250 | 0 | 31 | 15 | 1 |

The 7 mangled WRONG: 2 bare Shulchan Arukh sections and 1 Mishnah-by-default (the
"conventions"; `strict` mode leaves them unlinked), and 4 where the writer's link disagrees with
their own text (a typo'd verse, Christian verse numbering, "with Rashi", a commentary named but
the verse linked).

Benchmark (139): 97 correct, 1 coarser, 2 finer, **0 WRONG**, 39 unresolved.

Full set: a full run (19,227 pairs) on the code of 2026-11-24 found 156 mangled WRONG; every
one was reviewed, the resolver causes were fixed (the transliteration matcher, inferred Talmud
sides and Shulchan Arukh sections, and others; see `docs/notes/HANDOFF.md`), and the remaining
95 are conventions, label noise and Sefaria-side data errors. A full rerun on current code is
the next measurement.

## Running it

```bash
python3 test_rules_offline.py                        # offline
python3 benchmark.py --strict                        # networked, ~minutes with a warm cache
python3 pipeline/web_pairs.py eval                   # networked; per-output cache in pipeline/web_pairs_raw/
WEB_PAIRS_OUT=$PWD/pipeline/web_pairs_raw/web_pairs_full.json python3 pipeline/web_pairs.py eval   # the full set; hours
```

Caches must be cleared when the code they cache changes (each eval output has its own resolver
cache, so concurrent runs don't overwrite each other).
