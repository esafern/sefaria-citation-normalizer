# Most-cited public-domain works Sefaria lacks — by corpus

_Three corpora, and only one gives an answer. This documents the most-cited
**public-domain works absent from Sefaria**, measured separately in (a) Halachipedia,
(b) Sefaria's own source sheets, and (c) Hebrew Wikisource — and why they diverge.
Companion to `SEFARIA-MOST-WANTED.md`, `CORPUS-COMPARISON.md`, and `FINDINGS.md`._

## Halachipedia — a clear public-domain acquisition signal

From the full 640-page Halachipedia corpus (38,195 citation detections; method in
`SEFARIA-MOST-WANTED.md`), the public-domain works Sefaria lacks, ranked by how often
Halachipedia cites them:

| Rank | Citations | Work | Author |
|---:|---:|---|---|
| **1** | **243** | **Yad Malachi** | Malachi HaKohen (d. 1772) |
| **2** | **129** | **Birkei Yosef** | Chida (d. 1806) |
| 3 | 114 | Pri Chadash | H. da Silva (d. 1698) |
| 4 | 54 | Chavot Daat | Y. Lorberbaum (d. 1832) |
| 5 | 32 | Sdei Chemed | C. C. Medini (d. 1904) |
| 5 | 32 | Avnei Nezer | A. Bornsztain (d. 1910) |

**The most-cited public-domain work Sefaria lacks is Yad Malachi (243); the next is
Birkei Yosef (129).** The signal is strong and clean.

## Sefaria source sheets — essentially no public-domain-absent signal

Method: a fresh trawl of **750 public source sheets** across 40 tags
(`pipeline/mine_sheets_freq.py`), running each sheet's free-text through Sefaria's
`find-refs` linker and counting, per work, the citations it detects but cannot
resolve. The raw counts are in `pipeline/sheet_work_freq.json`.

The result is dominated by two things that are **not** public-domain acquisition
targets:

- **Surface-form misses of works Sefaria already has** — the linker failed on a
  spelling/umbrella surface, but the work is present: *Shulchan Aruch* (29),
  *Babylonian Talmud* (22), *Rambam's Commentary on the Mishnah* (4), *Tzitz Eliezer*,
  *Zohar*, *Or HaChaim*, *Pirkei Avot*. These are a **normalization** problem, not a
  missing text.
- **Noise and non-canonical / modern works** — *The Observant Life*, *JPS Torah
  Commentary*, *CCAR Press*, *NRSV*, *Quran*, *Samaritan Pentateuch*, "*Wall Street*",
  "*Why?*", website names.

After removing those, the strongest genuinely-absent items are **modern, in-copyright**
works — *Tzitz Eliezer* (~5, d. 2006), *Tosefta Kepshutah* (~3, Lieberman d. 1983),
*Mishnas Eretz Yisroel* (~4) — each cited only a handful of times, and **none public
domain**. There is no public-domain absent work with a meaningful count, so neither a
"#1" nor a "next" public-domain target emerges from source sheets.

**And Yad Malachi itself?** It appears **0 times** in the 750-sheet sample (a search of
*all* Sefaria sheets finds only ~2). A Talmudic-methodology reference simply is not
crowd-sheet material.

## Hebrew Wikisource — also no acquisition signal (a normalization corpus)

Method: a bounded trawl of **112 leaf pages** from eight citation-dense classic works
(the responsa of the Rosh, Rashba, Noda BiYehuda and Chatam Sofer; Aruch HaShulchan,
Ben Ish Chai, Mateh Efraim, Shulchan Aruch HaRav), each run through `find-refs`
(`pipeline/mine_wikisource.py`, `wiki_freq.json`).

The result is even more lopsided than the source sheets, and for the same reason. Of
**1,793 citations detected, only 299 (17%) resolved.** But the 83% that failed are
**not** absent works — they are:

- **Allusive citations to works Sefaria already has**, in a classic Hebrew style the
  linker can't parse — *"בפ"ק דקידושין (לו:)"* (Kiddushin 36b), *"ובשולחן ערוך"*
  (Shulchan Aruch with no siman inline, because the siman is the section header),
  Rema, Beit Shmuel, Chelkat Mechokek, Maggid Mishneh, Shaar HaKavanot.
- **Structure and location fragments** — section headers, Shulchan Aruch part-names
  (Orach Chaim, Yoreh De'ah…), *"בסימן קט"ו"*, dates.

After filtering those, the genuinely-absent residue is a handful of **responsa cited
once** (e.g. *Shav Yaakov*, *Maharam Padua*) — statistically nil. No public-domain
acquisition target emerges. Classic Hebrew texts cite the canonical corpus Sefaria
already holds; their unresolved links are a **normalization** problem (poor linking of
allusive Hebrew references), not a coverage one.

## Why the corpora diverge (the two-mode split)

This is the central finding of `FINDINGS.md`, seen from the acquisition angle. A
citation the linker can't resolve fails for one of two reasons, and genre decides which
dominates:

| | Source sheets | Hebrew Wikisource | Halachipedia |
|---|---|---|---|
| Typical citation | canonical Talmud / Tanakh / codes | classic Talmud / Rishonim, allusive | dense acharonic responsa & klalim |
| Linker resolve rate | low | **17%** | high (clean footnotes) |
| Why links fail | **surface form** — work *present*, misspelled | **surface form** — allusive Hebrew | **coverage** — work *absent* |
| Actionable as | normalization | normalization | **acquisition** (digitize) |
| Most-cited PD absent work | *none of weight* | *none of weight* | **Yad Malachi (243)** |

So "the most-cited public-domain work Sefaria lacks" is a **Halachipedia** phenomenon.
Both source sheets and classic Wikisource texts cite what Sefaria already has — their
failures are normalization problems; the acquisition-priority signal, including Yad
Malachi, comes from **lived, explicitly-footnoted halachic writing** like Halachipedia.
That is what makes Halachipedia special: its modern *title + number* footnotes resolve
cleanly, so what's left over is genuine absence.

## Bottom line

- **Halachipedia:** #1 **Yad Malachi (243)**, #2 **Birkei Yosef (129)**.
- **Source sheets:** no public-domain absent work of weight; top genuinely-absent items
  are modern/in-copyright, cited ~3–5×; Yad Malachi appears **0×**.
- **Hebrew Wikisource:** no public-domain absent work of weight; 17% resolve rate, the
  rest surface-form/normalization noise; genuine absences are one-off responsa.

_Caveats: source-sheet (750) and Wikisource (112-page) counts are bounded samples and
inherently noisy; the presence classifier misflags umbrella terms (e.g. "Babylonian
Talmud") as absent — those are treated as present here. The Wikisource pass reads a
~3,800-char slice per page, so it samples rather than exhausts each text. Halachipedia
figures are from the committed full-corpus analysis. Author death dates from
`SEFARIA-MOST-WANTED.md`._
