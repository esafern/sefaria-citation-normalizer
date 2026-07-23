# sefaria-citation-normalizer

Normalize messy, transliterated **Anglo-Orthodox Torah citations** to canonical
Sefaria references. Complementary to Sefaria's own ML linker (find-refs): it
targets the shorthand and dialect variation that the linker's data doesn't
resolve, and it runs deterministically with no model at link-time.

## How it works: propose → verify → cache

```
raw citation → rules.candidates()  (generate plausible normalized forms)
            → Sefaria /api/name     (which candidate is a real reference?)
            → cache                 (deterministic, offline-replayable)
```

The rules never have to be exactly right. Over-generation is cheap and Sefaria
is the authority — a wrong candidate simply doesn't resolve, so the system fails
safe (unlinked, never mislinked). This also sidesteps the fact that Sefaria's
canonical naming is unpredictable (sometimes transliteration `HaEmunot veHaDeot`,
sometimes the English translation `Duties of the Heart`): you can't compute the
target, so you propose and let Sefaria confirm.

```python
from normalizer.resolve import resolve, Cache
resolve("ArtScroll Berachos 57b, note 38", cache=Cache("cache.json"))
# -> https://www.sefaria.org/Berakhot.57b
```

## What the rules cover — and don't (measured, not guessed)

Built from a corpus mined off Sefaria source sheets: `find-refs` over 289 sheets
surfaced ~1,100 distinct English citations it *detected but could not resolve*;
after LLM labeling and Sefaria verification, **107 verified `raw → ref` pairs**
(`data/citation_dataset.json`).

The deterministic general rules resolve **~43%** of that corpus. The families:

| family | rule-able |
|---|---|
| Ashkenazi / academic endings (`-os/-oth → -ot`, `Shabbos → Shabbat`) | yes |
| edition / structural prefix strip (`ArtScroll`, `Meseches`, `Gemara`) | yes |
| Rambam section → Mishneh Torah English (bounded ~40-section map) | yes |
| `Pirke → Pirkei`, `d'Rebbi → DeRabbi`, roman numerals, note-tail strip | yes |

The other **~57%** is irreducibly knowledge-based and no rule captures it:
English-translated titles (`Chovot Halevavot → Duties of the Heart`), alternate
names (`Book of Jasher → Sefer HaYashar`), Hebrew, and a long tail of one-off
spellings. That half is the job of an LLM (at small scale) or a fine-tuned SLM /
Sefaria's find-refs (at large scale).

So this repo is deliberately **tier 1** — the deterministic ceiling — and the
dataset is what feeds tier 2.

## Layout

- `normalizer/rules.py` — candidate generators (the general families).
- `normalizer/resolve.py` — propose → `/api/name` → cache.
- `data/citation_dataset.json` — verified `raw → Sefaria ref` pairs.
- `pipeline/` — the corpus miner (`find-refs` failures) and verify/cluster tools.
- `benchmark.py` — coverage of the rules against the dataset (tracks the ~43%).

## Provenance & scope

Public data only (Sefaria source sheets). Deliberately not derived from any
single author, to avoid the overfitting that a one-author rule set produces.
