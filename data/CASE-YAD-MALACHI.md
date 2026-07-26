# A case for digitizing Yad Malachi

_A proposal to scan, OCR, and structure one foundational, public-domain work of
Torah that is heavily relied upon but not yet available as clean digital text._

## The work

**Yad Malachi** (יד מלאכי), by **R. Malachi ben Jacob HaKohen of Livorno**
(d. 1772), first printed Livorno 1766–7 (later Berlin 1857). It is a three-part
masterwork of *methodology* — the rules by which the Talmud is learned and halacha
is decided:

1. **Klalei HaTalmud** — an alphabetical index of the rules and technical terms of
   the Talmud, with explanations.
2. **Klalei HaPoskim** — the rules governing the codifiers (Rif, Rambam, Rosh, Tur,
   Shulchan Aruch…).
3. **Klalei HaDinim** — the principles of halachic decision-making and responsa.

It is, in short, the *grammar* of the tradition: not a text read once, but a
reference reached for whenever a question of method arises.

## Why it matters

Its standing is not a matter of opinion — and it is not a historical curiosity.

**Across the centuries.** The author was "quoted **frequently by major halakhic
authorities of the 18th and 19th centuries**," and the Chida praised Yad Malachi
effusively (English Wikipedia, "Malachi ben Jacob ha-Kohen"). That reliance is
measurable inside the digital library today: **287 places in Sefaria's existing
texts cite יד מלאכי** — and every one is a **dead end**, because the work itself is
not in the library. A reader who reaches "Yad Malachi, Klal …" inside a work Sefaria
*does* have cannot follow the reference. The citing works span three centuries:

| Mentions | Citing work |
|---:|---|
| 118 | Ayin Zokher |
| 17 | Petach Einayim (Chida) |
| 13 | Shem HaGedolim (Chida) |
| 11 | Pardes Yosef |
| 9 | Kaf HaChayim (d. 1939) |
| 8 | Rosh David (Chida) |
| — | + Mishnah Berurah / Biur Halacha, Torah Temimah, Minchat Chinukh, Even Ha'azel, and living responsa (Benei Banim) |

**And in active use today.** Yad Malachi is a living reference, not a shelved
classic:

- It is **continuously republished**: again in the late 20th century, a new Israeli
  edition in 2001, a **Machon Yerushalayim critical edition in 2016** (freshly
  typeset, cross-referencing parallel *Klalim* works), and a third volume in 2018
  (Wikipedia). A work the contemporary Torah-publishing world keeps re-typesetting
  is a work in active use — and the subject of modern scholarship (Benjamin Brown,
  *"Some Say This, Some Say That": … Interpretation Rules in Yad Malachi*).
- In a large **contemporary English-language halachic reference** (Halachipedia),
  Yad Malachi is cited **243 times** — directly, by its numbered klalim — putting it
  among the most-cited works that reference lacks a link for. That is present-day
  halachic writing reaching for it, hundreds of times, right now.
- Modern authorities cite it directly: Kaf HaChaim (d. 1939) and the contemporary
  responsa Benei Banim appear among the 287 above.

## The gap this closes

Yad Malachi is **public domain** — no rights, no license, no permission needed. Yet
there is no clean digital text of it. So every one of those 287 references is
unlinkable, and anyone quoting the work must **hand-transcribe the Hebrew** from a
scan. Digitizing it once turns 287 dead references into live links and ends the
re-keying — permanently.

## Why it is an ideal candidate

- **Public domain** — free to reproduce.
- **A scan already exists** — the Livorno 1766–7 and Berlin 1857 printings are on
  HebrewBooks.org / Otzar HaChochma. No physical scanning needed.
- **Cleanly structured** — its native form (numbered *klalim* within three parts)
  maps directly onto a digital schema, so each reference becomes individually
  linkable.

## Process

1. **Acquire the scan** (free) — pick the cleanest of the Livorno 1766–7 or Berlin
   1857 printings.
2. **OCR (Hebrew)** — Jochre (purpose-built for rabbinic Hebrew), Google Cloud
   Vision, or Tesseract `heb`. Expect a high error rate: dense rabbinic Hebrew,
   heavy abbreviation (ר"ת), older type.
3. **Structure** into the three parts and their numbered klalim.
4. **Hand-proof against the scan** — a Hebrew-literate proofreader corrects the OCR
   line by line, expands abbreviations, and fixes letter confusions (ד/ר, ב/כ,
   ן/ו). This is the real work.
5. **QA and ingest**, wiring up the reference structure.

## Cost

Hand-proofing is the only material cost. Yad Malachi runs across three parts —
estimated **~700–1,000 pages** (confirm from the scan; an exact count wasn't
obtainable here). Careful proofing of OCR'd rabbinic Hebrew runs ~10–20 pages/hour:

| | low | high |
|---|---:|---:|
| Pages | 700 | 1,000 |
| Proofing rate (pp/hr) | 20 | 10 |
| Hours | 35 | 100 |
| Rate (Hebrew-literate proofer) | $20 | $35 |
| Proofing | ~$700 | ~$3,500 |
| + structuring / QA / ingest | +$400 | +$1,000 |
| **Total** | **~$1,100** | **~$4,500** |

**~$2–5k, one-time**, to bring a foundational work of Torah — cited 287 times
within the very library that currently lacks it — permanently online.

_Sources: Sefaria search API (the 287 in-corpus references and citing-work
breakdown); a citation survey of Halachipedia, a large contemporary
English-language halachic reference (243 direct citations); English Wikipedia,
"Malachi ben Jacob ha-Kohen" (three-part structure; d. 1772; standing among later
authorities; the Chida's praise; republication history — 2001, Machon Yerushalayim
2016, 2018 — and modern scholarship). Page count and cost are estimates pending the
actual scan._
