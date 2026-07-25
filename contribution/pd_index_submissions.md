# Public-domain most-wanted → Sefaria index submissions

_Draft index (metadata) specs for the Tier-1 public-domain works on
`data/SEFARIA-MOST-WANTED.md` — the works Halachipedia cites often that Sefaria
lacks and whose authors died long enough ago that no licensing is needed._

## Why this exists

Sefaria already digitizes expired-copyright seforim as a core activity ("Texts
Digitized by Sefaria"). So for the **public-domain** tier there's nothing to
negotiate — the ask is just "please add these," and this file does the first
chunk of that work: for each title it drafts what Sefaria's **Add a New Text**
tool (`sefaria.org/add/new`) needs to create the *index record* — English +
Hebrew title, category path, base text (for commentaries), and the structural
schema — modeled on how Sefaria structures analogous works already in the
library.

**Scope / honest limits:**
- This creates the **index shell only.** The actual text still has to be
  sourced (scan/OCR) and proofread — that's the real labor and is Sefaria's to
  schedule. A "source hint" is given where a digital copy is likely to exist.
- **Licensing:** every work here is public domain (author death + 70y elapsed
  as of 2026); Sefaria publishes contributions as **CC0**. Death-year basis is
  noted per work; the two borderline cases are flagged.
- **Schemas need a proofer's eye.** Section structure (siman ranges, which
  Shulchan Arukh sections a commentary covers, volume splits) is drafted from
  what these works are known to be; **confirm against the printed edition**
  before creating the record. Confidence is marked per entry.
- **Absence** is taken from the merged full-corpus most-wanted list, which was
  live-verified against `/api/name`. Two caveats carried over: **Eliya Rabba is
  excluded here** (it's already on Sefaria as "Eliyah Rabbah on Shulchan Arukh,
  Orach Chayim" — a false-absent in the list), and **Radvaz** is included only
  for its responsa, which need a presence re-check (see its entry).

## Sefaria conventions this follows (from live index lookups)

| Work type | Category path | Title pattern | Schema (sectionNames / addressTypes) |
|---|---|---|---|
| Commentary on Shulchan Arukh | `Halakhah › Shulchan Arukh › Commentary › <Work>` | `<Work> on Shulchan Arukh, <Section>` | `["Siman","Seif"]` / `["Siman","Seif"]`; multi-section works are **complex** (one node per SA section) |
| Commentary on Mishneh Torah | `Halakhah › Mishneh Torah › Commentary › <Work>` | `<Work> on Mishneh Torah, <Sefer>` | `["Chapter","Halakhah","Comment"]` |
| Commentary on the Tur | `Halakhah › Tur › Commentary` | node per Tur section | complex (per Tur section → Siman) |
| Responsa | `Responsa › Acharonim` (or `Rishonim`) | `Teshuvot <Name>` / `Responsa <Name>` | complex (node per SA section → Siman) |
| Rishonim halakhic monograph | `Halakhah › Rishonim` | work title | `["Siman","Paragraph"]` or complex |
| Talmud commentary (chiddushim) | `Talmud › Bavli › Commentary › <Work>` | `<Work> on <Tractate>` | base = tractate; `["Daf","Line"]` |

_(Verified against: Turei Zahav & Siftei Kohen on SA YD; Kessef Mishneh on
Mishneh Torah; Beit Yosef on the Tur; Noda BiYehudah & Sefer Chasidim.)_

---

## Group A — Commentaries on the Shulchan Arukh

Category `Halakhah › Shulchan Arukh › Commentary › <Work>`; base text = the SA
section(s); schema `["Siman","Seif"]`. Works spanning several SA sections are
**complex** (one Siman/Seif node per section).

### A1. Birkei Yosef — ברכי יוסף
- **Author:** Chaim Yosef David Azulai (Chida), d.1806. _(AuthorTopic exists on Sefaria.)_
- **Base / structure:** glosses on the Shulchan Arukh across **OC, YD, EH, CM** → complex, one `["Siman","Seif"]` node per section.
- **Source hint:** widely reprinted; HebrewBooks/Otzar scans plentiful.
- **Confidence:** high on identity/category; **verify which SA sections & siman ranges** are covered per volume.

### A2. Machzik Bracha — מחזיק ברכה
- **Author:** Chida, d.1806.
- **Base / structure:** glosses on the Shulchan Arukh (primarily **OC & YD**) → complex per section, `["Siman","Seif"]`.
- **Note:** same author as Birkei Yosef; keep as a **separate index** (distinct work), both under the Chida AuthorTopic.
- **Confidence:** medium — confirm section coverage.

### A3. Pri Chadash — פרי חדש
- **Author:** Chizkiyah da Silva, d.1698.
- **Base / structure:** commentary on Shulchan Arukh **Orach Chaim and Yoreh De'ah** → complex, `["Siman","Seif"]` per section.
- **Source hint:** standard on the SA page in print; scans plentiful.
- **Confidence:** high.

### A4. Chavot Daat — חוות דעת
- **Author:** Yaakov Lorberbaum of Lissa, d.1832.
- **Base / structure:** on Shulchan Arukh **Yoreh De'ah**, hilchot issur v'heter (≈ siman 87–111). Single-section `["Siman","Seif"]`.
- **Confidence:** high on identity; confirm exact siman span.

### A5. Darkei Teshuva — דרכי תשובה
- **Author:** Tzvi Hirsch Shapira of Munkatch, d.1913.
- **Base / structure:** on Shulchan Arukh **Yoreh De'ah** (a vast collectanea). `["Siman","Seif"]`.
- **Confidence:** high; note it is large — likely multi-volume in print.

### A6. Sidrei Tahara — סדרי טהרה
- **Author:** Elchanan ben Shmuel Ashkenazi, d.1780.
- **Base / structure:** on Shulchan Arukh **Yoreh De'ah**, hilchot niddah (≈ siman 183–200). `["Siman","Seif"]`.
- **Confidence:** high on identity; confirm siman span.

### A7. Maamar Mordechai — מאמר מרדכי
- **Author:** Mordechai Carmi (Karmi), d.1825.
- **Base / structure:** on Shulchan Arukh **Orach Chaim**. `["Siman","Seif"]`.
- **Confidence:** high. _(Disambiguation: not the Maamar Mordechai responsa of R. Mordechai Halevi Ettinga; this is Carmi on OC.)_

### A8. Mekor Chaim — מקור חיים
- **Author:** Yair Chaim Bacharach (of Chavot Yair), d.1702.
- **Base / structure:** short commentary on Shulchan Arukh **Orach Chaim**. `["Siman","Seif"]`.
- **Note:** his responsa **Chavot Yair** is a separate work (check separately; may already be present).
- **Confidence:** medium — the name "Mekor Chaim" is shared by later works; confirm this is the Bacharach OC commentary the citations intend.

### A9. Daat Torah — דעת תורה
- **Author:** Shalom Mordechai Schwadron (Maharsham), d.1911.
- **Base / structure:** on Shulchan Arukh **Yoreh De'ah**, issur v'heter. `["Siman","Seif"]`.
- **Note:** distinct from the Maharsham **responsa** (Teshuvot Maharsham). Keep separate.
- **Confidence:** high.

### A10. Yafeh Lelev — יפה ללב
- **Author:** Yitzchak Palache (son of Chaim Palache), d.1907.
- **Base / structure:** glosses on the Shulchan Arukh (**OC, YD, EH, CM** across volumes) → complex per section, `["Siman","Seif"]`.
- **Confidence:** medium — confirm sections/volumes.

---

## Group B — Commentary on the Mishneh Torah

### B1. Hagahot Maimoniyot — הגהות מיימוניות
- **Author:** Meir HaKohen of Rothenburg (talmid of the Maharam), 13th c.
- **Category:** `Halakhah › Mishneh Torah › Commentary › Hagahot Maimoniyot`.
- **Base / structure:** glosses printed alongside the Mishneh Torah, **per sefer/hilchot** → complex, one `["Chapter","Halakhah","Comment"]` node per MT section it covers (mirror Kessef Mishneh's structure).
- **Source hint:** printed in standard Rambam editions (Vilna/Frankel).
- **Confidence:** high on category/model; **the per-section node list must be built** from which hilchot the glosses actually cover.

---

## Group C — Commentary on the Tur

### C1. Knesset HaGedolah — כנסת הגדולה
- **Author:** Chaim Benveniste, d.1673.
- **Category:** `Halakhah › Tur › Commentary` (glosses on the Beit Yosef / Tur).
- **Base / structure:** complex, one node per Tur section (**OC, YD, EH, CM**) → Siman.
- **Confidence:** medium — Knesset HaGedolah has both Hagahot on the Beit Yosef and on the Tur; confirm the layer/structure against the printed edition (may warrant its own schema rather than a pure commentary link).

---

## Group D — Responsa

Category `Responsa › Acharonim` (or `Rishonim`); complex (node per SA section → Siman), like Noda BiYehudah.

### D1. Teshuvot HaRadbaz — שו"ת רדב"ז  ⚠ verify presence first
- **Author:** David ibn Zimra (Radbaz), d.1573.
- **Category:** `Responsa › Rishonim` (or early Acharonim).
- **⚠ Caveat:** the most-wanted list marks "responsa absent, MT commentary present," but a live `/api/name` probe returned a completion **"Teshuvot HaRadbaz Volume 1"** — so the responsa may already be present. **Re-check before submitting**; if present, drop from this list.
- **Confidence:** identity high; **absence uncertain** (the point of the caveat).

### D2. Avnei Nezer — אבני נזר
- **Author:** Avraham Bornsztain of Sochatchov, d.1910.
- **Category:** `Responsa › Acharonim`.
- **Base / structure:** responsa across **OC, YD, EH, CM** → complex, node per section → Siman.
- **Source hint:** standard; scans plentiful.
- **Confidence:** high.

### D3. Teshuvot Maharam Shik — שו"ת מהר"ם שיק
- **Author:** Moshe Schick (Maharam Shik), d.1879.
- **Category:** `Responsa › Acharonim`.
- **Base / structure:** responsa ordered by SA sections → complex per section → Siman.
- **Note:** his **commentary on the 613 mitzvot** (Maharam Shik al Taryag Mitzvot) is a separate work.
- **Confidence:** high.

---

## Group E — Rishonim halakhic works

Category `Halakhah › Rishonim` (Talmud-commentary chiddushim go under `Talmud`).

### E1. Sefer HaRokeach — ספר הרוקח
- **Author:** Eleazar of Worms (the Rokeach), d.1230.
- **Category:** `Halakhah › Rishonim`.
- **Structure:** halakhic-ethical work in numbered **simanim** → `["Siman","Paragraph"]` (model: Sefer Chasidim).
- **Confidence:** high on model; confirm siman count/segmentation.

### E2. Ravyah — ראבי"ה
- **Author:** Eliezer ben Yoel HaLevi (Ravyah), d.1225.
- **Category:** `Halakhah › Rishonim`.
- **Structure:** halakhot arranged **by tractate** → complex, node per tractate → Siman.
- **Note:** an AuthorTopic "Ra'avyah" exists on Sefaria (topic only, no text).
- **Confidence:** medium — modern editions differ in siman numbering; confirm against the edition to be digitized.

### E3. Rabbeinu Yerucham (Toldot Adam v'Chavah) — רבינו ירוחם, תולדות אדם וחוה
- **Author:** Yerucham ben Meshullam, 14th c.
- **Category:** `Halakhah › Rishonim`.
- **Structure:** two works — **Toldot Adam v'Chavah** (Netivim, subdivided) and **Sefer Meisharim** (Netivim). Complex, node per Netiv → sub-section. Consider two indexes or one with two top nodes.
- **Note:** AuthorTopic "Rabbenu Yerucham" exists (topic only).
- **Confidence:** medium — netiv structure is idiosyncratic; design the schema from the print edition.

### E4. Chiddushei Maharam Chalava on Pesachim — חידושי מהר"ם חלאווה על פסחים
- **Author:** Meir ben Shlomo (Maharam) Chalava, 14th c.
- **Category:** `Talmud › Bavli › Commentary › Maharam Chalava` (base = **Pesachim**).
- **Structure:** chiddushim keyed to the daf → `["Daf","Line"]` (or `["Daf","Paragraph"]`), linked to Pesachim.
- **Confidence:** high on category/model; confirm segmentation granularity.

---

## Group F — Encyclopedic / methodological / topical (custom schema)

These are **not** simple commentaries; each needs a schema designed with Sefaria
(flagging so no one force-fits them into `["Siman","Seif"]`).

### F1. Sdei Chemed — שדי חמד
- **Author:** Chaim Chizkiyahu Medini, d.1904.
- **Category:** `Halakhah › Acharonim` (or a Reference/Encyclopedia category).
- **Structure:** a **halakhic encyclopedia** — Kllalim (alphabetical, by letter → entry), Maarechet entries, and topical volumes (e.g., Asifat Dinim, chametz u'matzah). Large, multi-volume → **complex custom schema**, likely one top node per maarechet/kllal letter.
- **Confidence:** identity high; **schema is a real design task** — do not auto-generate.

### F2. Yad Malachi — יד מלאכי
- **Author:** Malachi HaKohen, d.1785.
- **Category:** `Halakhah › Acharonim` (methodology — kllei ha-Talmud / kllei ha-poskim).
- **Structure:** rules arranged **alphabetically within sections** (kllalei ha-Talmud; kllalei ha-poskim; misc.) → complex, node per section → numbered rule.
- **Confidence:** medium — confirm the section division and rule numbering.

### F3. Gesher HaChaim — גשר החיים  ⚠ borderline PD date
- **Author:** Yechiel Michel Tucazinsky, d.1955.
- **Category:** `Halakhah › Acharonim` (hilchot aveilut — laws of death & mourning).
- **Structure:** topical monograph in **three parts**, chapters → sections → `["Chapter","Paragraph"]` per part (complex).
- **⚠ Caveat:** d.1955 → life+70 lapses in **2026**; PD status is fresh and jurisdiction-dependent. **Confirm the copyright determination** before treating as CC0.
- **Confidence:** medium.

---

## Summary table

| # | Work | Author (d.) | Type | Category root | Status |
|---|---|---|---|---|---|
| A1 | Birkei Yosef | Chida (1806) | SA commentary | Shulchan Arukh | ready to draft |
| A2 | Machzik Bracha | Chida (1806) | SA commentary | Shulchan Arukh | verify sections |
| A3 | Pri Chadash | da Silva (1698) | SA commentary (OC,YD) | Shulchan Arukh | ready |
| A4 | Chavot Daat | Lorberbaum (1832) | SA YD commentary | Shulchan Arukh | ready |
| A5 | Darkei Teshuva | T.H. Shapira (1913) | SA YD commentary | Shulchan Arukh | ready (large) |
| A6 | Sidrei Tahara | E. Ashkenazi (1780) | SA YD commentary | Shulchan Arukh | ready |
| A7 | Maamar Mordechai | M. Carmi (1825) | SA OC commentary | Shulchan Arukh | ready |
| A8 | Mekor Chaim | Y. Bacharach (1702) | SA OC commentary | Shulchan Arukh | confirm identity |
| A9 | Daat Torah | Maharsham (1911) | SA YD commentary | Shulchan Arukh | ready |
| A10 | Yafeh Lelev | Y. Palache (1907) | SA commentary | Shulchan Arukh | verify sections |
| B1 | Hagahot Maimoniyot | Meir HaKohen (13c) | MT gloss | Mishneh Torah | build node list |
| C1 | Knesset HaGedolah | C. Benveniste (1673) | Tur gloss | Tur | confirm layer |
| D1 | Teshuvot HaRadbaz | ibn Zimra (1573) | Responsa | Responsa | ⚠ verify presence |
| D2 | Avnei Nezer | Bornsztain (1910) | Responsa | Responsa | ready |
| D3 | Maharam Shik | M. Schick (1879) | Responsa | Responsa | ready |
| E1 | Sefer HaRokeach | Eleazar of Worms (1230) | Rishonim halakhah | Halakhah | ready |
| E2 | Ravyah | Eliezer b. Yoel (1225) | Rishonim halakhah | Halakhah | confirm siman |
| E3 | Rabbeinu Yerucham | Yerucham b. Meshullam (14c) | Rishonim halakhah | Halakhah | design schema |
| E4 | Maharam Chalava on Pesachim | M. Chalava (14c) | Talmud commentary | Talmud | ready |
| F1 | Sdei Chemed | Medini (1904) | Encyclopedia | Halakhah | design schema |
| F2 | Yad Malachi | Malachi HaKohen (1785) | Methodology | Halakhah | design schema |
| F3 | Gesher HaChaim | Tucazinsky (1955) | Aveilut monograph | Halakhah | ⚠ borderline PD |

**Excluded from submission:** _Eliya Rabba_ — already on Sefaria (Eliyah Rabbah
on SA OC); listed as absent in error and flagged to the pipeline track.

---
_Source of the absent-PD set: `data/SEFARIA-MOST-WANTED.md` (full 640-page
Halachipedia corpus, live-verified). Conventions grounded in Sefaria's
`/api/v2/index` for analogous works. This is a draft for a human contributor +
the Sefaria library team, not an automated import._
