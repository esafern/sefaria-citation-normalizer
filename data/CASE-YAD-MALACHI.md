# The case for digitizing Yad Malachi (scan → OCR → structure)

_A worked example of the cheapest, highest-leverage move on the most-wanted list:
a public-domain foundational work, heavily cited, that Sefaria lacks. Numbers
below are measured (Sefaria search API + this project's corpus) unless flagged as
an estimate or domain judgment._

## The ask

Digitize **Yad Malachi** (R. Malachi HaKohen, Livorno 1767; author d. 1785, so
**public domain** — no licensing, no rights holder). It is a *klalim* work — the
rules of Talmudic and halachic methodology (Klalei HaTalmud, Klalei HaPoskim,
Klalei HaDinim), organized as numbered rules. Sefaria does not have it.

## Demand is documented twice over — 530 references to a text Sefaria lacks

- **287 references to "יד מלאכי" across Sefaria's *own* existing Hebrew corpus**
  (Sefaria search API). Every one is a **dead end**: a reader inside a text Sefaria
  *does* have hits "Yad Malachi, Klal …" and cannot follow it, because the target
  isn't in the library.
- **243 citations in this project's Anglo-Orthodox corpus** (640-page Halachipedia
  mine) — the **#1 public-domain absent work**, ahead of Birkei Yosef (45).

That is 530 documented pointers, from two independent corpora, to a work that
costs *nothing to license*.

## How it's used — a cross-generational methodology backbone (measured)

The 287 in-corpus mentions, by citing work:

| Mentions | Citing work |
|---:|---|
| 118 | Ayin Zokher (klalim) |
| 17 | Petach Einayim (Chida) |
| 13 | Shem HaGedolim (Chida) |
| 11 | Pardes Yosef |
| 9 | Kaf HaChayim |
| 8 | Rosh David (Chida) |
| — | + Mishnah Berurah / Biur Halacha, Torah Temimah, Minchat Chinukh, Even Ha'azel, Responsa Rav Pealim, Responsa Benei Banim (modern) |

The span is the point: it is cited from the 18th century (Chida) through **Kaf
HaChayim** and into **living responsa** (Benei Banim) — a reference work every
layer of the tradition reaches for when reasoning about *how* to pasken. It shows
up inside **Mishnah Berurah and Biur Halacha** themselves.

**Honest caveat on R. Yosef:** Yad Malachi is bedrock of the Sephardi *klalei
ha-poskim* method that R. Ovadia and R. Yitzchak Yosef build on (their Yabia Omer
and Yalkut Yosef lean heavily on exactly this genre) — but this can't be *measured*
here, because R. Yosef's works are themselves absent from Sefaria (they top the
modern most-wanted list). The measured 0 for Yabia Omer/Yalkut Yosef is a
library-gap artifact, not evidence they don't cite it. This is domain judgment.

## The digitization pain it removes

Because it's public domain **but not available as clean digital text**, every one
of those 530 references is unlinkable, and anyone quoting it — English writers,
source-sheet makers, responsa authors — must **hand-transcribe the Hebrew** off a
scan (no copy-paste from a clean source). Digitizing it once converts 530 dead
references into live links and ends the re-keying, permanently, for free.

## Why this is the *cheapest* lever on the list

Unlike the translation-gap works (which need commissioned English — tens of
thousands of dollars each), a PD Hebrew work needs only **scan → OCR → proof**.
The scan already exists (HebrewBooks/Otzar HaChochma host PD seforim), so there is
no physical scanning step — only OCR and correction.

## Process guide

1. **Acquire the scan** (free). The Livorno/standard editions are already scanned
   on HebrewBooks.org / Otzar HaChochma. Pick the cleanest print.
2. **OCR (Hebrew).** Options, best-to-worst for rabbinic type: **Jochre**
   (purpose-built for Hebrew/rabbinic), Google Cloud Vision (strong Hebrew), or
   Tesseract `heb`. Expect a meaningful error rate — dense rabbinic Hebrew,
   abbreviations (ר"ת), and older type defeat naive OCR.
3. **Structure into klalim.** The work's native structure (numbered rules within
   Klalei HaTalmud / HaPoskim / HaDinim) maps directly onto a Sefaria schema —
   this is what makes each of the 287 dead references *linkable*.
4. **Hand-proof against the scan.** The real work: a Hebrew-literate proofreader
   corrects OCR line-by-line against the image, expands abbreviations, fixes
   letter confusions (ד/ר, ב/כ, ן/ו).
5. **QA + ingest** into Sefaria's format; wire up the ref structure.

## Cost estimate (hand-proofing — the only material cost)

Yad Malachi is a single volume, **roughly 400–600 pages** of dense Hebrew
(estimate — confirm from the actual scan). Careful proofing of OCR'd rabbinic
Hebrew against the image runs ~**10–20 pages/hour**:

| | low | high |
|---|---:|---:|
| Pages | 400 | 600 |
| Proofing rate (pp/hr) | 20 | 10 |
| Hours | 20 | 60 |
| Rate (Hebrew-literate proofer) | $20 | $35 |
| **Proofing** | **~$400** | **~$2,100** |
| + structuring / QA / ingest | +$300 | +$700 |
| **Total** | **~$700** | **~$2,800** |

Call it **~$1–3k, one-time**, versus tens of thousands to translate a single
gap work. For that, the single most-cited public-domain absent text — and 530
currently-dead references across two corpora — goes live. It is the highest
return-on-cost item on the entire acquisition list.

_Sources: Sefaria search API (287 in-corpus mentions, citing-work breakdown);
`data/SEFARIA-MOST-WANTED.md` / `work_frequency.json` (243 corpus citations, PD
tier); citation forms ("Klalei HaRav HaMaggid", "Klalei HaTur") from the raw
Halachipedia mine. Page count and cost figures are estimates pending the actual
scan._
