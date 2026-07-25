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
after LLM labeling and Sefaria verification, **137 verified `raw → ref` pairs**
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

## A denser corpus: Halachipedia, and a gift for Sefaria

Source sheets saturated (~85% noise). The pipeline was re-pointed at
[Halachipedia](https://www.halachipedia.com), whose footnotes are dense, nearly
pure halachic citations. Mining the **full site (640 substantial pages)** yielded
**38,195 citation detections → 7,878 distinct works**. Two findings:

1. The deterministic rules generalize **poorly** across genre — ~2% hit on this
   acharonim/responsa corpus vs ~43% on the sheet Talmud/Tanakh. Honest evidence
   that citation normalization overfits not just to dialect but to *canon*.
2. The reason most don't resolve is that **Sefaria doesn't have the work** — not
   a normalization failure (only ~40% of detections link). Ranking the
   genuinely-absent works by how often Halachipedia cites them produces a
   **licensing-priority list for Sefaria**:
   [`data/SEFARIA-MOST-WANTED.md`](data/SEFARIA-MOST-WANTED.md) — 71 works,
   6,771 citations, tiered into public-domain (digitize) vs modern (license).
   R. Ovadia Yosef's corpus (Yalkut Yosef, Chazon Ovadyah, Yabia Omer, Yechave
   Daat, Halacha Brurah) is the single biggest gap (~⅓ of all demand). Built with
   the same propose→verify discipline: each "absent" work is re-checked through
   the normalizer's own candidate spellings so present-but-transliterated works
   aren't falsely listed. See `CORPUS-COMPARISON.md` for the full-vs-250-page diff.

## Layout

- `normalizer/rules.py` — candidate generators (the general families).
- `normalizer/resolve.py` — propose → `/api/name` → cache.
- `data/citation_dataset.json` — verified `raw → Sefaria ref` pairs.
- `pipeline/` — the corpus miner (`find-refs` failures) and verify/cluster tools.
- `benchmark.py` — coverage of the rules against the dataset (tracks the ~43%).

## Provenance & scope

Public data only (Sefaria source sheets). Deliberately not derived from any
single author, to avoid the overfitting that a one-author rule set produces.
