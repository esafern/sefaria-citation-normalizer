# Link-readiness QA — worked example (Yad Malachi, Klalei HaAleph)

The text is **run through Sefaria's linker as a test; no links are inserted**. Citations that resolve as-is need nothing. Citations the linker *detects but cannot link* are flagged with a **candidate normalized citation**, each re-tested against the linker so the suggestion is verified.

_Source passage (unchanged):_

> מדברי רש"י ז"ל בפ"ב דנדרים י"ט ב' משמע דלאו לדחויי ליה קא מכוין. ועיין נדרים י"ט ב'. וכן כתב עוד פ' אין דורשין י"ט ב'. ובפ"ג דיומא ל"א ב' ובשלהי פ"ק דזבחים ט"ו ב'. אך בפרק המפלת כ"ג ב' פירש אי תניא תניא.

## Resolves as-is (1)

| Citation in text | Links to |
|---|---|
| נדרים י"ט ב' | Nedarim 19b |

## Flagged — failed to auto-link (6)

| Citation in text | Candidate normalized cite | Candidate resolves to |
|---|---|---|
| רש"י ז"ל בפ"ב דנדרים י"ט ב' | רש"י על נדרים י"ט ב' | Rashi on Nedarim 19b |
| פ' אין דורשין י"ט ב' | חגיגה י"ט ב' | Chagigah 19b |
| ובפ"ג דיומא ל"א ב' | יומא ל"א ב' | Yoma 31b |
| ובשלהי | _(needs manual review)_ | — |
| פ"ק דזבחים ט"ו ב' | זבחים ט"ו ב' | Zevachim 15b |
| בפרק המפלת כ"ג ב' | נדה כ"ג ב' | Niddah 23b |

**Reading this table.** "Resolves to" means the candidate is *linkable* — it maps to a real Sefaria ref — **not** that it is the semantically correct citation. Linker-verification confirms link-readiness; the **expert reviewer confirms correctness** against the passage (e.g. that the author really meant that daf). Note too that the linker can mis-segment — here `ובשלהי` ("and at the end of") was split off from the Zevachim citation that follows it — which is itself useful signal for the reviewer.

_The flagged list is the deliverable handed to the expert reviewer; the text itself is never modified. Candidate generation here uses a small transparent rule set — in production it plugs into this repo's normalizer._