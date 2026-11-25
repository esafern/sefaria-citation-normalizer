# citenorm: Torah citations to Sefaria links

[![tests](https://github.com/esafern/sefaria-citation-normalizer/actions/workflows/tests.yml/badge.svg)](https://github.com/esafern/sefaria-citation-normalizer/actions/workflows/tests.yml)

Turns citations of Jewish texts, as people actually write them in English, into links to
[Sefaria](https://www.sefaria.org). When it can't be sure, it leaves the citation unlinked
rather than guessing.

```
Berachos 5a                          -> https://www.sefaria.org/Berakhot.5a
Hilchos Eidus 4:1                    -> https://www.sefaria.org/Mishneh_Torah,_Testimony.4.1
Ohr HaChaim to Shemot 23:2           -> https://www.sefaria.org/Or_HaChaim_on_Exodus.23.2
Pirke De-Rabbi Eliezer, chapter 24   -> https://www.sefaria.org/Pirkei_DeRabbi_Eliezer.24
Shmuel A 9:2                         -> https://www.sefaria.org/I_Samuel.9.2
Shmuel 23:8                          -> (unlinked: I or II Samuel?)
Kaf HaHayim 92:8                     -> (unlinked: Orach Chayim or Yoreh De'ah?)
```

It's aimed at the shorthand of English Torah writing (Ashkenazi and academic
transliterations, abbreviations like `S"A O"C`, `B"M`, `Hil.`, Hebrew book names,
"chapter 2, ¶ 3") that Sefaria's own linker often detects but can't resolve. It complements
that linker; it doesn't replace it.

*Not developed by or affiliated with Sefaria. It uses Sefaria's public API.*

## How it works: propose, then verify

```
citation -> rules propose many plausible normalized forms
         -> Sefaria's /api/name says which one is a real reference
         -> checks reject any answer that changed the meaning
         -> cache (so reruns are offline and deterministic)
```

The rules don't need to know Sefaria's canonical titles (which are sometimes
transliterations, sometimes English translations); they over-generate, and Sefaria
confirms. A bad candidate simply doesn't resolve. The risky part is **choosing**, so
every answer that came from Sefaria's suggestions or title list passes checks that reject:

- dropped words (`Kaf Hachaim Palagi` is not *Kaf HaChayim on Shulchan Arukh*)
- added words (`Moreh Nevuchim` is not *Guide for the Perplexed, Prefatory Remarks*)
- reordered words (*Arukh HaShulchan* is not *Shulchan Arukh*)
- an added number or part (`Noda B'Yehuda, YD 81`: which edition?)
- a Talmud side (a or b) or a Shulchan Arukh section Sefaria filled in on its own
- look-alike spellings that are different words (`Challah` is not `Kallah`, `Deot` is not
  `Deut`, `Kilayim` is not `Kelim`)

## Install and use

Python 3.10+, standard library only.

```bash
pip install git+https://github.com/esafern/sefaria-citation-normalizer
citenorm "Berachos 5a" "SA OC 271:1"
citenorm < citations.txt              # one per line; prints citation<TAB>url (or -)
citenorm --json --conventions strict "YD 289"
```

```python
from citenorm.resolve import resolve, Cache

cache = Cache("cache.json")
resolve("ArtScroll Berachos 57b, note 38", cache=cache)   # 'https://www.sefaria.org/Berakhot.57b'
resolve("Shmuel 23:8", cache=cache)                       # None (ambiguous)
cache.save()
```

### Conventions: `common` (default) or `strict`

Three citation patterns are ambiguous, and Sefaria resolves them by convention:

| Pattern | Sefaria's reading | Measured on ~19,000 real citations |
|---|---|---|
| A Shulchan Arukh section with no work named (`YD 289`) | the Shulchan Arukh | 87% of writers meant that; 13% meant the Tur, Arukh HaShulchan, Mishnah Berurah, Beit Yosef or a responsum |
| A tractate with chapter:mishnah (`Kilayim 9:3`) | the Mishnah | some writers meant the Yerushalmi or a Mishneh Torah section |
| A 2-3 letter abbreviation (`Ber 9`) | Sefaria's alias (Berakhot) | `Ber.` also means Bereshit in academic writing |

`conventions="common"` follows Sefaria; `"strict"` leaves these unlinked.

### Being polite to Sefaria

Requests identify themselves (`User-Agent: citenorm/<version> (+this repo)`), wait 0.2 s
between calls by default (0.3 s on the command line), and every answer is cached; Sefaria's
title list is downloaded once to `~/.cache/citenorm/` (override with `CITENORM_CACHE`). For
large batches, keep the default pacing and keep the cache.

## How accurate is it?

Measured against citations whose correct answer was chosen by their writers: about 19,000
links to Sefaria collected from Mi Yodeya, English Wikipedia and other Stack Exchange sites
([the dataset](docs/DATASET.md); method and numbers in [docs/EVALUATION.md](docs/EVALUATION.md)).
On a 1,588-pair sample, for the 616 citations Sefaria does **not** resolve as written:

| correct | coarser (e.g. the chapter, not the verse) | wrong | unlinked |
|---|---|---|---|
| 256 (42%) | 156 (25%) | 7 (1.1%) | 179 (29%) |

(+18 where the writer's link disagrees with their own text.) Of the 7 wrong: 3 follow one of
the conventions above, 4 are writer-side typos or link mismatches. The original 139-citation
benchmark (`benchmark.py`): 97 correct, 3 coarser or finer, **0 wrong**.

What stays unlinked is mostly genuinely ambiguous (no work named, `Shmuel` without I/II), or
needs knowledge the rules don't have (English translations of titles, rare works).

## Also in this repo

- **[What Sefaria is missing](data/SEFARIA-MOST-WANTED.md):** 71 works Halachipedia cites
  that Sefaria doesn't have, ranked by 6,771 citations from 640 Halachipedia pages and split
  into public-domain (digitize) vs modern (license). R. Ovadia Yosef's works are the single
  biggest gap.
- **Upstream bug reports** found along the way ([docs/upstream/](docs/upstream/)): `Ref()`
  title matching is case-sensitive (Sefaria-Project
  [#1016](https://github.com/Sefaria/Sefaria-Project/issues/1016)); titles containing a hyphen
  can never resolve ([#4150](https://github.com/Sefaria/Sefaria-Project/issues/4150)); and some
  title-data errors.
- **Research notes:** [docs/FINDINGS.md](docs/FINDINGS.md) (cross-corpus findings),
  [docs/notes/LESSONS.md](docs/notes/LESSONS.md) (what building this taught), and the working
  notes in `docs/notes/`.

## Layout

```
citenorm/            the package: rules.py (candidates), resolve.py (verify + checks), cli.py
benchmark.py         scores the original 139-citation set (--strict fails on any wrong link)
test_rules_offline.py  100 offline regression cases, each from a real failure (run in CI)
pipeline/            mining and evaluation: web_pairs.py (collect, verify, score), export_dataset.py,
                     the Halachipedia and source-sheet miners
data/                the datasets and analyses (see data/README.md for sources and licenses)
docs/                evaluation, dataset card, licensing, upstream reports, notes
```

## Development

```bash
python3 test_rules_offline.py         # offline, fast; must pass
python3 benchmark.py --strict         # networked; must show WRONG 0
python3 pipeline/web_pairs.py eval    # networked; scores data/web_pairs.json
```

Every rule should be checked against the whole evaluation set, not just the case that
prompted it: three of our own fixes caused new wrong links that only the broad data caught
([LESSONS.md](docs/notes/LESSONS.md)).

## License

Code: [MIT](LICENSE). Data: CC BY-SA 4.0 where it comes from CC BY-SA sources (see
[data/README.md](data/README.md)). Why MIT: [docs/LICENSING.md](docs/LICENSING.md).

Sefaria is a trademark of Sefaria. This project is not developed by Sefaria.
