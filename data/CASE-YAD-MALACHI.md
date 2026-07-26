# The case for digitizing Yad Malachi (scan → OCR → structure)

_A worked example of the cheapest, highest-leverage move on the most-wanted list:
a public-domain foundational work, heavily cited, that Sefaria lacks. Figures are
measured (Sefaria search API, this project's corpus) or externally sourced
(Wikipedia); size/cost are estimates, flagged as such._

## The ask

Digitize **Yad Malachi** (R. Malachi ben Jacob HaKohen of Livorno, first printed
Livorno 1766–7; author d. **1772**, so firmly **public domain** — no licensing, no
rights holder). Per Wikipedia (author's entry), it is "a methodological work and
compilation in **three parts**": (1) an alphabetical list of all the rules and
technical terms in the Talmud, (2) the rules governing the codifiers (poskim),
(3) the rules of legal decision-making (responsa principles) — i.e. the *grammar*
of how to learn and pasken. Sefaria does not have it.

## Demand is documented — 287 dead-end references inside Sefaria itself

- **287 references to "יד מלאכי" across Sefaria's *own* existing Hebrew corpus**
  (Sefaria search API). Every one is a **dead end**: a reader inside a text Sefaria
  *does* have hits "Yad Malachi, Klal …" and cannot follow it, because the target
  isn't in the library. This is the core argument — you don't need external usage
  data; Sefaria's own corpus points at the hole 287 times.
- **243 citations in this project's Anglo-Orthodox corpus** (640-page Halachipedia
  mine) — the **#1 public-domain absent work**, ahead of Birkei Yosef (45).

_(Source sheets are **not** a strong angle here: only ~3–5 sheets reference it — it
is advanced methodology, not typical sheet material. Reported for completeness, not
as support. The earlier "0 sheets" was a broken query; the corrected count is 3–5.)_

## How it's used — a cross-generational methodology backbone

**Externally sourced:** Wikipedia's entry on the author states he was "quoted
**frequently by major halakhic authorities of the 18th and 19th centuries**," and
records the Chida's effusive praise of Yad Malachi — independent confirmation that
this is a reference work the tradition leans on, not a marginal text.

**Measured** (the 287 in-corpus mentions, by citing work):

| Mentions | Citing work |
|---:|---|
| 118 | Ayin Zokher (klalim) |
| 17 | Petach Einayim (Chida) |
| 13 | Shem HaGedolim (Chida) |
| 11 | Pardes Yosef |
| 9 | Kaf HaChayim |
| 8 | Rosh David (Chida) |
| — | + Mishnah Berurah / Biur Halacha, Torah Temimah, Minchat Chinukh, Even Ha'azel, Responsa Rav Pealim, Responsa Benei Banim (modern) |

The span is the point: cited from the 18th c. (Chida) through **Kaf HaChayim** into
**living responsa** (Benei Banim), and inside **Mishnah Berurah / Biur Halacha**
themselves.

**Honest caveat on R. Yosef:** Yad Malachi is bedrock of the Sephardi *klalei
ha-poskim* method R. Ovadia and R. Yitzchak Yosef build on — but this can't be
*measured* here, because R. Yosef's works are themselves absent from Sefaria (they
top the modern most-wanted list). The measured 0 for Yabia Omer/Yalkut Yosef is a
library-gap artifact, not evidence. This is domain judgment, not a counted figure.

## The digitization pain it removes

Public domain **but with no clean digital text**: every one of those 287 in-corpus
references is an unlinkable dead-end, and anyone quoting it — English writers,
responsa authors — must **hand-transcribe the Hebrew** off a scan (no copy-paste
from a clean source). Digitizing it once converts 287 dead references into live
links and ends the re-keying, permanently, for free.

## Why this is the *cheapest* lever on the list

Unlike the translation-gap works (commissioned English, tens of thousands each), a
PD Hebrew work needs only **scan → OCR → proof**. A scan already exists
(HebrewBooks.org / Otzar HaChochma host the Livorno 1766–7 and Berlin 1857
printings), so there is no physical-scanning step — only OCR and correction.

## Process guide

1. **Acquire the scan** (free) from HebrewBooks/Otzar; pick the cleanest of the
   Livorno 1766–7 or Berlin 1857 printings.
2. **OCR (Hebrew).** Best-to-worst for this type: **Jochre** (purpose-built for
   rabbinic Hebrew), Google Cloud Vision (strong Hebrew), Tesseract `heb`. Expect a
   high error rate — dense rabbinic Hebrew, heavy abbreviation (ר"ת), older type.
3. **Structure into the three parts / klalim.** The native structure (numbered
   rules within Klalei HaTalmud / HaPoskim / HaDinim) maps onto a Sefaria schema —
   this is what makes each of the 287 dead references *linkable*.
4. **Hand-proof against the scan** — a Hebrew-literate proofreader corrects OCR
   line-by-line against the image, expands abbreviations, fixes letter confusions
   (ד/ר, ב/כ, ן/ו). This is the real work.
5. **QA + ingest** into Sefaria's format; wire up the ref structure.

## Cost estimate (hand-proofing — the only material cost)

Yad Malachi is a **three-part** work; I could not obtain an exact page count from
accessible sources (no clean scan on archive.org; HebrewBooks is the likely source
but wasn't reachable here), so this is an estimate to confirm against the actual
scan — call it **~700–1,000 pages** across the three parts. Careful proofing of
OCR'd rabbinic Hebrew runs ~**10–20 pages/hour**:

| | low | high |
|---|---:|---:|
| Pages | 700 | 1,000 |
| Proofing rate (pp/hr) | 20 | 10 |
| Hours | 35 | 100 |
| Rate (Hebrew-literate proofer) | $20 | $35 |
| **Proofing** | **~$700** | **~$3,500** |
| + structuring / QA / ingest | +$400 | +$1,000 |
| **Total** | **~$1,100** | **~$4,500** |

Call it **~$2–5k, one-time** (confirm once the scan's page count is known), versus
tens of thousands to translate a single gap work. For that, the single most-cited
public-domain absent text — and 287 currently-dead references inside Sefaria's own
corpus — goes live. Highest return-on-cost item on the acquisition list.

_Sources: Sefaria search API (287 in-corpus mentions + citing-work breakdown; ~3–5
sheets via the corrected `field:content` sheet query); `SEFARIA-MOST-WANTED.md` /
`work_frequency.json` (243 corpus citations, PD tier); English Wikipedia, "Malachi
ben Jacob ha-Kohen" (three-part structure, d. 1772, "quoted frequently by major
halakhic authorities of the 18th and 19th centuries," Chida's praise). Page count
and cost are estimates pending the actual scan._
