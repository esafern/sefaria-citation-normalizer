# Most-cited public-domain works Sefaria lacks — by corpus

_Two corpora, two very different answers. This documents the most-cited **public-domain
works absent from Sefaria**, measured separately in (a) Halachipedia and (b) Sefaria's
own source sheets — and why they diverge. Companion to `SEFARIA-MOST-WANTED.md`,
`CORPUS-COMPARISON.md`, and `FINDINGS.md`._

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

## Why the two corpora diverge (the two-mode split)

This is the central finding of `FINDINGS.md`, seen from the acquisition angle. A
citation the linker can't resolve fails for one of two reasons, and genre decides which
dominates:

| | Source sheets | Halachipedia |
|---|---|---|
| Typical citation | canonical Talmud / Tanakh / codes | dense acharonic responsa & klalim |
| Why links fail | **surface form** — the work *is* present, misspelled | **coverage** — the work is *absent* |
| Actionable as | normalization (rules + knowledge tier) | acquisition (digitize the text) |
| Most-cited PD absent work | *none of weight* | **Yad Malachi (243)** |

So "the most-cited public-domain work Sefaria lacks" is a **Halachipedia** phenomenon.
Source sheets cite what Sefaria already has; the acquisition-priority signal — including
Yad Malachi — comes from lived halachic writing like Halachipedia.

## Bottom line

- **Halachipedia:** #1 **Yad Malachi (243)**, #2 **Birkei Yosef (129)**.
- **Source sheets:** no public-domain absent work of weight; the top genuinely-absent
  items are modern/in-copyright, cited ~3–5×, and Yad Malachi appears **0×**.

_Caveats: source-sheet counts come from a 750-sheet sample and are inherently noisy on
crowd-built text; the presence classifier misflags umbrella terms (e.g. "Babylonian
Talmud") as absent — those are treated as present here. Halachipedia figures are from
the committed full-corpus analysis. Author death dates from `SEFARIA-MOST-WANTED.md`._
