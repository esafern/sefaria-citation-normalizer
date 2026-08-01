# Findings — why citation linking fails, and what to do about it

_Distilled from four mined corpora: `find-refs` failures over 289 Sefaria source
sheets (137 hand-verified `raw → ref` pairs), the full 640-page Halachipedia corpus
(38,195 citation detections → 7,878 distinct works), Mi Yodeya (Judaism Stack
Exchange), and a bounded Hebrew Wikisource trawl. Numbers below are from those
datasets; see `data/citation_dataset.json`, `pipeline/work_frequency.json`,
`data/miyodeya_pairs.json`, and `pipeline/wiki_freq.json`._

## The central finding: two failure modes, split by genre

A citation that Sefaria's linker can't resolve fails for one of two reasons, and
which one dominates depends entirely on the **genre** of the text:

| | **Mode A — surface form** | **Mode B — coverage** |
|---|---|---|
| What's wrong | The work *is* on Sefaria; the citation string didn't match | The work is *not* in Sefaria's library |
| Dominant in | Talmud / Tanakh (source sheets); classic Hebrew halacha (Wikisource) | Acharonim / responsa (Halachipedia) |
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

Halachipedia footnotes are dense, near-pure halachic citations. Of **38,195
detections** (the whole site), `find-refs` links only **40%**; the other **59%** go
unlinked — and the dominant reason is that **Sefaria doesn't have the work.**
The deterministic rules that recover 43% of the source-sheet corpus recover only
**~2%** here: normalization overfits not just to dialect but to *canon*.

Ranking the genuinely-absent works by citation frequency is therefore not a
linker problem but a **library-acquisition** signal — the output is
`data/SEFARIA-MOST-WANTED.md` (71 works, 6,771 citations). The demand is
concentrated: R. Ovadia Yosef's Sephardi psak ecosystem (Yalkut Yosef 945,
Chazon Ovadyah 573, Yabia Omer, Yechave Daat, Halacha Brurah, …) is the single
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

## A third corpus: Mi Yodeya (free-prose Q&A) — a dataset source, not a coverage one

Sampled 800 answers from the Mi Yodeya (Judaism Stack Exchange) dump and ran them
through find-refs: 1,966 detections, 1,168 distinct unresolved. Unlike the two
structured corpora, this is free prose, and it behaves like a **third mode**:

- **Noisy.** ~40% of "detections" aren't citations at all — page numbers,
  addresses (`8 West 70th Street`), percentages, English phrases, academic
  references (`Antiquities of the Jews`, `Anchor Bible`). Free prose defeats a
  citation detector tuned for footnotes.
- **No new coverage.** Its real citations are overwhelmingly to works Sefaria
  *already has* — almost nothing genuinely absent surfaced that the Halachipedia
  list didn't already have. As a most-wanted source it's a dead end.
- **But a dialect goldmine.** The real citations show the widest transliteration
  variety of any corpus — exactly the Mode-A knowledge the rules overfit to. One
  work, `Avot DeRabbi Natan`, appears as `Avos DeRabbi Nasan`, `Avot D'Rabbi
  Natan`, and `Avot De-Rabbi Natan`; `-os/-as` Ashkenazi endings are everywhere
  (`Toras HaShabbos`, `Kesubos`, `Hilchos De'os`, `Asarah B'Teves`).

So Mi Yodeya confirms the genre thesis from the other direction: it's useless for
**coverage** (Mode B) but ideal raw material for the **normalization dataset**
(Mode A) — the tier-2 train/eval set that teaches the spelling/alternate-name
variety no rule captures.

**Dataset built** (`data/miyodeya_pairs.json`, 121 verified `raw → ref` pairs):
the 1,168 failures were filtered to 957 plausible citations, auto-resolved (only
~3% — rules don't generalize), then the unresolved set was triaged (142 labelable
present-on-Sefaria works vs 664 coverage gaps) and the labelable ones hand-labeled
and `/api/name`-verified. It captures exactly the knowledge rules can't compute —
`Chovot Halevavot → Duties of the Heart`, `Moreh Nevuchim → Guide for the
Perplexed`, `Semag → Sefer Mitzvot Gadol`, Rambam section maps, and pervasive
`-os/-as` dialect. Kept as separate provenance from the 137 source-sheet pairs in
`citation_dataset.json`; together they seed the tier-2 model. Raw strings:
`pipeline/miyodeya_failures.json` (CC-BY-SA, from the public dump).

## A fourth corpus: Hebrew Wikisource — classic Hebrew, a pure Mode-A frontier

Mined 112 leaf pages from eight citation-dense classic works (the responsa of the
Rosh, Rashba, Noda BiYehuda and Chatam Sofer; Aruch HaShulchan, Ben Ish Chai, Mateh
Efraim, Shulchan Aruch HaRav) through `find-refs` (`pipeline/mine_wikisource.py`). It
is the most one-sided corpus yet, and sits entirely on the **Mode-A** side:

- **17% resolve rate.** Of 1,793 detected citations, only 299 linked. But the 83% that
  failed are **not absent works** (`MOST-CITED-ABSENT-BY-CORPUS.md` shows no coverage
  signal) — they are citations to works Sefaria *already has*, in a classic Hebrew
  style the linker can't parse.
- **A new normalization class the English-facing rules never touch — allusive Hebrew
  references:**
  - *chapter-of + daf*: `בפ"ק דקידושין (לו:)` → Kiddushin 36b; `דפ"ק דביצה (דף ג:)` → Beitzah 3b.
  - *bare work name, siman in the section header*: `ובשולחן ערוך` (no siman inline —
    the running section *is* the siman).
  - *named-perek references*: `בפרק במה בהמה` → the tractate + daf that perek names.
  - *Hebrew abbreviations & bare part-names*: `אה"ע` / `ח"מ`, `אורח חיים` as a section label.

This is the "findings go back to the normalizer" point. The excursion was launched to
hunt absent works; it instead mapped a large **Hebrew normalization frontier**. Today's
deterministic rules are English-facing (`-os/-as`, ArtScroll tails); classic Hebrew
halacha needs a parallel Hebrew tier — chapter-name→daf and perek-name→masechet maps,
and bare-work-name + surrounding-siman resolution. The project's **link-readiness demo
already prototypes exactly this** (`pipeline/link_readiness.py`: `רש"י ז"ל בפ"ב דנדרים`
→ *Rashi on Nedarim 19b*, verified against the linker); Wikisource shows the scale of
text — the entire classic-Hebrew corpus — that such a tier would light up.

## The strategic takeaway

Normalization has a hard ceiling on *contemporary* halacha — ~43% deterministic,
~62% with a knowledge tier — because there the majority of real-world citation
failures are **coverage, not spelling**, so the highest-leverage output may be the
licensing-priority list, not the linker itself. But the picture **inverts on classic
Hebrew text** (Wikisource): there almost every failure is surface form, and the
linker resolves only ~17% — a large, *recoverable* normalization gap that a Hebrew
tier (chapter→daf, perek→masechet, bare-name+siman) would close. Two frontiers, then:
**acquisition** for lived halacha, **Hebrew normalization** for the classical corpus.

---
_Method caveats: the corpus is the whole mineable site (640 substantial pages; stubs excluded);
work-name extraction is heuristic; frequency reflects Halachipedia's
Anglo-Orthodox canon, not Sefaria's whole user base. All data is public (Sefaria
API, public Halachipedia via its MediaWiki API); access is paced and cached._
