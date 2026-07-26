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
- **Public-domain scans already exist** (verified on HebrewBooks.org): the complete
  **Livorno 1766–7 first edition** — part I (#32530, 348 pp), part II (#32532, 54
  pp), part III (#32531, 55 pp) — plus an independent **Przemyśl 1877** witness for
  the large part I (#14122, 491 pp). No physical scanning needed, and multiple
  witnesses are already in hand for the ensemble.
- **Cleanly structured** — its native form (numbered *klalim* within three parts)
  maps directly onto a digital schema, so each reference becomes individually
  linkable.

## Process — ensemble OCR with AI adjudication

High accuracy on dense rabbinic Hebrew comes not from proofreading one OCR pass but
from **consensus across many witnesses**. OCR engines make *uncorrelated* errors, so
where several agree the reading is near-certain, and disagreements are automatically
localized to specific words — turning "proofread everything" into "adjudicate the
few conflicts."

1. **Gather every public-domain witness.** The Livorno 1766–7 first edition (all
   three parts) and an 1877 Przemyśl printing are already on HebrewBooks (IDs above);
   add any further early printings (e.g. Berlin 1857) from HebrewBooks / Otzar. Each
   is an independent witness to the same PD text. (Modern critical editions are *not*
   scanned into the corpus — see the copyright note.)
2. **Multi-engine OCR, per scan.** Run several systems on each printing — Google
   Cloud Vision, Tesseract `heb`, **Jochre** (best for rabbinic/Rashi type), ABBYY,
   plus Hebrew-specialized tooling (**DICTA** post-correction; **Kraken /
   eScriptorium** with trained Hebrew models). Uncorrelated errors make agreement a
   strong signal.
3. **Align and vote — per scan.** Align the engine outputs (word/character sequence
   alignment, anchored on the numbered *klalim*) and take a per-token consensus.
   Agreed tokens — the large majority — are accepted automatically; only conflicts
   are flagged.
4. **AI adjudication — image-grounded, selection-only.** For each flagged token,
   give a multimodal model (Claude / GPT with vision) the candidate readings **plus
   the cropped scan image** of that word, and have it *select* the correct reading —
   never invent text. It must name the witness it relied on; anything not attested
   by a scan is a flagged conjecture for a human, not a silent change. This is the
   critical guardrail against the model "helpfully" emending the text to what it
   expects.
5. **Collate the editions.** With each printing reduced to a best-text, collate them
   against each other. Genuine differences between printings (a typo or correction in
   one) are recorded as variants — yielding a text potentially *better than any
   single edition*, with an apparatus.
6. **Human review — only the flagged set.** A Hebrew-literate reviewer resolves the
   remaining conflicts against the scan (and may **consult** the modern critical
   editions as a reference for hard readings — see note) and spot-checks the
   auto-accepted text. Because the human only ever touches disagreements, this is a
   fraction of full proofreading.
7. **Structure and ingest** into the three parts and their klalim; output text +
   per-token confidence map + variant apparatus.

**Copyright note.** The *base text you reproduce* comes only from fully
public-domain printings. You may **consult** modern critical editions (2001; Machon
Yerushalayim 2016) to decide a hard reading — using a work to inform judgment is not
infringement — but you may not reproduce their annotations, cross-references, or
apparatus, or OCR them into the corpus; source the actual reading from a PD printing.
(General principle, not legal advice; have counsel bless the workflow before
publication.)

## Cost

The ensemble front-loads a little engineering and collapses the human cost — which
is the expensive part of any digitization.

The work is **~457 pages** (the verified Livorno set: 348 + 54 + 55), OCR'd across
a couple of witnesses.

- **One-time harness** (OCR-ensemble + alignment + adjudication): developer time,
  ~40–80 hrs, and **reusable** for every other public-domain work — so it amortizes
  far beyond this one text.
- **Compute** (multi-engine OCR + AI adjudication over ~460 pages × 2 witnesses):
  modest — low hundreds of dollars in OCR/API credits at most.
- **Human review** — only the flagged conflict set. If the ensemble auto-accepts
  ~90% of tokens, a reviewer handles the rest in perhaps **~5–10 hours (~$150–350)**,
  versus ~25–45 hours to proofread all 457 pages single-pass.

Net: after the reusable harness exists, the **marginal cost per work is a few hundred
dollars**, and the output is *more* accurate than a single proofread pass —
potentially better than any existing edition. For that, a foundational work of Torah
— cited 287 times inside the very library that currently lacks it, and 243 times in
contemporary halachic writing — goes permanently online.

_Sources: Sefaria search API (the 287 in-corpus references and citing-work
breakdown); a citation survey of Halachipedia, a large contemporary
English-language halachic reference (243 direct citations); English Wikipedia,
"Malachi ben Jacob ha-Kohen" (three-part structure; d. 1772; standing among later
authorities; the Chida's praise; republication history — 2001, Machon Yerushalayim
2016, 2018 — and modern scholarship); HebrewBooks.org for the public-domain scans
and page counts (Livorno 1766–7: #32530 / #32532 / #32531; Przemyśl 1877: #14122).
Cost figures are estimates; page counts are from HebrewBooks._
