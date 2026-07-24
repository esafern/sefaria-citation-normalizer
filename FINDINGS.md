# Findings — why citation linking fails, and what to do about it

_Distilled from two mined corpora: `find-refs` failures over 289 Sefaria source
sheets (137 hand-verified `raw → ref` pairs) and a 250-page Halachipedia sample
(14,268 citation detections → 3,520 distinct works). Numbers below are from
those datasets; see `data/citation_dataset.json` and `pipeline/work_frequency.json`._

## The central finding: two failure modes, split by genre

A citation that Sefaria's linker can't resolve fails for one of two reasons, and
which one dominates depends entirely on the **genre** of the text:

| | **Mode A — surface form** | **Mode B — coverage** |
|---|---|---|
| What's wrong | The work *is* on Sefaria; the citation string didn't match | The work is *not* in Sefaria's library |
| Dominant in | Talmud / Tanakh (source sheets) | Acharonim / responsa (Halachipedia) |
| Fixable by | Normalization (rules + a knowledge tier) | Only by acquiring the text |
| Ceiling | high — most strings are recoverable | zero — no string edit conjures a missing book |

On canonical text the linker trips on **spelling**; on lived halacha it trips on
**absence**. Conflating the two is the trap — most "linker failures" in a real
halachic corpus are not normalization problems at all.

## Mode A — surface-form failures (source-sheet corpus, n=137)

Every one of these 137 is *resolvable* (a real Sefaria ref exists), so each is a
pure normalization miss. Cause breakdown:

| cause | ~share | example |
|---|---:|---|
| spelling / transliteration choice | 42% | `Derech Chaim → Derekh Chayyim` |
| trailing note / s.v. / page cruft | 20% | `ArtScroll Berachos 57b, note 38` |
| Ashkenazi endings (`-os/-oth → -ot`) | 15% | `Berachos → Berakhot` |
| structural words (`Gemara`, `Meseches`) | 12% | `30a Gemara Rosh Hashana` |
| edition / publisher prefix | 7% | `ArtScroll…`, `Soncino…` |
| Rambam section names | 3% | `Hil. M'lachim → Kings and Wars` |

**The key wrinkle: in 26 of 137 (19%) the canonical name cannot be computed.**
Sefaria's title is sometimes a transliteration and sometimes an English
translation, unpredictably:

- `Chovot HaLevavot → Duties of the Heart`
- `The Book of Beliefs and Opinions → HaEmunot veHaDeot`
- `Mekhilta d'Rabbi Yishmael → Mekhilta DeRabbi Yishmael`

You cannot deterministically produce the target string. This is the entire
justification for **propose → verify**: generate many plausible candidates and
let `/api/name` say which is real. Over-generation is cheap; a wrong candidate
just doesn't resolve, so the system fails safe (unlinked, never mislinked).

The deterministic rules recover **~43%** of this corpus. The remaining ~57% is
knowledge-bound (English titles, alternate names, Hebrew) — a model's job.

## Mode B — coverage failures (Halachipedia corpus)

Halachipedia footnotes are dense, near-pure halachic citations. Of **14,268
detections**, `find-refs` links only **39%** (5,668); the other **60%** go
unlinked — and the dominant reason is that **Sefaria doesn't have the work.**
The deterministic rules that recover 43% of the source-sheet corpus recover only
**~2%** here: normalization overfits not just to dialect but to *canon*.

Ranking the genuinely-absent works by citation frequency is therefore not a
linker problem but a **library-acquisition** signal — the output is
`data/SEFARIA-MOST-WANTED.md` (72 works, 2,758 citations). The demand is
concentrated: R. Ovadia Yosef's Sephardi psak ecosystem (Yalkut Yosef 428,
Chazon Ovadyah 268, Yabia Omer, Yechave Daat, Halacha Brurah, …) is the single
biggest gap, followed by modern Ashkenazi responsa (Igrot Moshe, Shemirat
Shabbat KeHilchata, Tzitz Eliezer). A 22-work public-domain tier (Chida's Birkei
Yosef, Pri Chadash, Chavot Daat, …) is the cheapest win — no rights to clear.

Cross-cutting complications inside Mode B that also bit the *presence* test:
- **Abbreviations** (~240 hits: `Maharsham`, `Sma`, `Radvaz`) — a one-letter
  difference marks a *different* work (`Maharsham` ≠ `Maharshal` ≠ `Maharshag`).
- **Responsa / shu"t prefix forms** (~670) — the work lives under `Teshuvot X` /
  `Responsa X`, which a prefix-only match can't see.
- **Severed section-markers** — `Chazon Ovadia · Purim` extracted as bare
  `Purim`; `Ben Ish Chai · Vezot Habracha` as bare `Vezot Habracha`. These
  aren't works and aren't the parsha text — they're fragments of a parent work.

## How each is fixed

- **Mode A, mechanical (~43%)** → the deterministic normalizer (`normalizer/`):
  strip prefixes/tails, rewrite endings, map Rambam sections. Offline, no model.
- **Mode A, unpredictable name (~19%)** → a knowledge tier: an LLM/SLM proposes
  English-translation and alternate-name candidates; `/api/name` verifies. The
  137-pair dataset is its train/eval seed.
- **Abbreviations & responsa forms** → curated abbreviation→work map + the
  presence-matcher hardening already landed (strip `Teshuvot`/`Responsa` title
  prefixes; reject equal-length single-token substitutions). That alone flipped
  `Maharsham` / `Maharil` / `Rav Pealim` from wrong to right.
- **Severed section-markers** → fix at extraction: keep the parent attached so
  demand credits the real work instead of fragmenting.
- **Mode B (coverage)** → acquisition, not normalization. The most-wanted list is
  the deliverable: public-domain tier to digitize, modern tier to license.

## The strategic takeaway

Normalization has a hard ceiling — ~43% deterministic, ~62% with a knowledge
tier — because the majority of real-world halachic citation failures are
**coverage, not spelling.** The highest-leverage output of this project may be
the licensing-priority list, not the linker itself.

---
_Method caveats: the 250-page Halachipedia sample is not the whole site;
work-name extraction is heuristic; frequency reflects Halachipedia's
Anglo-Orthodox canon, not Sefaria's whole user base. All data is public (Sefaria
API, public Halachipedia via its MediaWiki API); access is paced and cached._
