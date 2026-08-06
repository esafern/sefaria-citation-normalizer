# Halachipedia's most-cited works that Sefaria doesn't have

_A candidate priority list for Sefaria's library team._

**Method.** From the full 640-page Halachipedia corpus (every substantial content page), we extracted the footnote citations, ran each through Sefaria's own `find-refs` linker, and kept what it detected as a citation but couldn't resolve to a text. We reduced each to its base work, counted how often it's cited, and confirmed absence via `/api/name` (a work is 'present' if any real ref title matches, allowing for transliteration and for titles stored under a `Teshuvot`/`Responsa` prefix). Every candidate was re-verified live against `/api/name` (2026-07): works present under a variant or abbreviated spelling were excluded (see the tail), spelling twins and section-volumes were merged into one work, and mis-detected non-texts were dropped.

**Result.** 71 works, 6771 citations. Split by why they're missing:

_See also: `CASE-YAD-MALACHI.md` — a data-grounded digitization case for the top public-domain absent work; `ANALYSIS.md` — most-cited works, genre profile, and the present-but-untranslated gap; `MOST-CITED-ABSENT-BY-CORPUS.md` — the top public-domain absent works in Halachipedia vs. Sefaria source sheets, and why they diverge._

**Copyright-date re-check (2026-08-05).** The Tier 1/Tier 2 split was classified once by hand, anchored to whatever "today" was at classification time — it doesn't re-check itself as years pass. `pipeline/wikidata_deathdates.py` cross-checked each tier-1/tier-2 author's death year against Wikidata (P570) and flagged anything crossing the 70-years-since-death public-domain threshold as of now. Result: **Chazon Ish** (A.Y. Karelitz, d.1953 — 73 years ago) had aged past the threshold since this list was first built and is reclassified PD; **Rokeach**'s death year is corrected from 1230 to 1238 per Wikidata (doesn't change its tier). 38 of 55 checkable authors were confirmed matching; 16 had no confident Wikidata match (mostly older/obscure figures already unambiguous by century, not in doubt); 15 have no individual author name recorded at all (anonymous/institutional works like "modern rabbinical institute") and couldn't be checked this way. Full detail in `data/wikidata_deathdate_findings.json`. Worth re-running this check periodically — the threshold only moves one direction.

## Tier 1 — Public domain, not yet digitized

_Author died >70 years ago; Sefaria can add these without licensing._

| Citations | Work | Author |
|---:|---|---|
| 243 | Yad Malachi | Malachi HaKohen (d.1772) |
| 160 | Chazon Ish | A.Y. Karelitz (d.1953) |
| 129 | Birkei Yosef | Chida (d.1806) |
| 114 | Pri Chadash | H. da Silva (d.1698) |
| 54 | Chavot Daat | Y. Lorberbaum (d.1832) |
| 32 | Avnei Nezer | Avraham Bornsztain (d.1910) |
| 32 | Sdei Chemed | C.C. Medini (d.1904) |
| 31 | Darkei Teshuva | Tzvi Hirsch Shapira (d.1913) |
| 30 | Sidrei Tahara | Elchanan Ashkenazi (d.1780) |
| 29 | Hagahot Maimoniyot | Meir HaKohen (13c) |
| 28 | Rabbenu Yerucham | Yerucham b. Meshullam (14c) |
| 25 | Knesset Hagedola | Chaim Benveniste (d.1673) |
| 24 | Maamar Mordechai | Mordechai Carmi (d.1825) |
| 22 | Mekor Chaim | Chavot Yair / Yair Bacharach (d.1702) |
| 21 | Gesher Hachaim | Y.M. Tucazinsky (d.1955) |
| 19 | Maharam Shik | Moshe Schick (d.1879) |
| 18 | Daat Torah | Maharsham / S. Schwadron (d.1911) |
| 18 | Yafeh Lelev | Yitzchak Palache (d.1907) |
| 18 | Maharam Chalavah Pesachim | Maharam Chalava (14c) |
| 18 | Rokeach | Eleazar of Worms (d.1238) |
| 17 | Ravyah | Eliezer b. Yoel HaLevi (d.1225) |
| 17 | Machzik Bracha | Chida (d.1806) |

## Tier 2 — Modern / in-copyright

_Recent authorities; would require a licensing arrangement. Ranked by demand._

| Citations | Work | Author |
|---:|---|---|
| 945 | Yalkut Yosef | Yitzchak Yosef |
| 573 | Chazon Ovadyah | Ovadia Yosef (d.2013) |
| 485 | Igrot Moshe | Moshe Feinstein (d.1986) |
| 409 | Shemirat Shabbat KeHilchata | Y.Y. Neuwirth (d.2013) |
| 320 | Yabia Omer | Ovadia Yosef (d.2013) |
| 240 | Halacha Brurah | David Yosef |
| 209 | Or Letzion | Ben Zion Abba Shaul (d.1998) |
| 189 | Piskei Teshuvot | Simcha Rabinowitz, modern |
| 186 | Badei Hashulchan | modern, on Yoreh De'ah |
| 170 | Yechave Daat | Ovadia Yosef (d.2013) |
| 166 | Shevet Halevi | S.H. Wosner (d.2015) |
| 141 | Tzitz Eliezer | E. Waldenberg (d.2006) |
| 117 | Nitei Gavriel | Gavriel Zinner, modern |
| 109 | Chelkat Binyamin | on Hilchot Basar b'Chalav, modern |
| 108 | Taharat Habayit | Ovadia Yosef (d.2013) |
| 102 | Halichot Shlomo | S.Z. Auerbach (d.1995) |
| 98 | Minchat Yitzchak | Y.Y. Weiss (d.1989) |
| 88 | Rivevot Efraim | Efraim Greenblatt (d.2014) |
| 68 | Teshuvot VeHanhagot | Moshe Sternbuch, modern |
| 64 | Tiltulei Shabbat | modern |
| 60 | Minchat Shlomo | S.Z. Auerbach (d.1995) |
| 56 | Menuchat Ahava | modern |
| 52 | Orchot Shabbat | modern |
| 45 | Torat HaMoadim | modern |
| 43 | Halichot Olam | Yitzchak Yosef, modern |
| 42 | Ginzei Hakodesh | modern |
| 41 | Shalmei Yehuda | modern (R. Elyashiv) |
| 36 | Mishpitei Aretz | modern (Torah VeHaaretz) |
| 35 | Beer Moshe | Moshe Stern (d.1997) |
| 33 | Mishneh Halachot | Menashe Klein (d.2011) |
| 32 | Ishei Yisrael | A.Y. Pfoifer, modern |
| 29 | Agur Bohalecha | modern |
| 28 | Brit Yehuda | Y. Blau (d.2013) |
| 28 | Chut Shani | Nissim Karelitz (d.2019) |
| 28 | Pitchei Choshen | Yaakov Blau (d.2013) |
| 27 | Yismach Lev | modern |
| 25 | Torat Ribbit | modern |
| 24 | Otzar Haposkim | modern rabbinical institute |
| 23 | Chelkat Yakov | Mordechai Y. Breisch (d.1976) |
| 22 | Ashrei Ha'ish | rulings of R. Elyashiv, modern |
| 22 | Horah Brurah | modern |
| 21 | Minchat Asher | Asher Weiss, modern |
| 21 | Har Tzvi | Tzvi Pesach Frank (d.1960) |
| 20 | Shulchan Shlomo | S.Z. Auerbach (d.1995) |
| 20 | Amot Shel Halacha | modern |
| 19 | Matnat Yado | modern |
| 18 | Nishmat Avraham | A.S. Abraham (d.2010) |
| 18 | Nefesh Harav | H. Schachter on R. Soloveitchik, modern |
| 17 | Yaskil Avdi | Ovadia Hedaya (d.1969) |

## Excluded: present under a variant spelling

_Flagged absent by exact match but found on Sefaria after normalization — NOT wanted._

| Cited-as | Actually on Sefaria as |
|---|---|
| Simla Chadasha | Simlah Chadashah |
| Shem HaGedolim | Shem HaGedolim, Maarekhet Sefarim |
| Chaye Adam | Chayei Adam |
| Beiur Halacha | Beur Halacha |
| Levush | Levush HaOrah |
| Eliya Rabba | Eliyah Rabbah on Shulchan Arukh, Orach Chayim |
| Chatom Sofer | Chatam Sofer on Torah |
| Dirshu | Dirshuni I |
| Trumat Hadeshen | Terumat HaDeshen |
| Mishna Brura | Mishna Brurah |
| Pri Megadim | Pri Megadim on Yoreh De'ah |
| Meiri | Meiri on Yoma |
| Orchot Chaim | Orchot Chaim L'HaRosh |
| Pri Megadim M"Z | (via normalization) |
| Radvaz | Teshuvot HaRadbaz Volume 1 |
| Gemara Bava Metsia | (via normalization) |
| Tashbetz | Tashbetz Katan |
| Rabbenu Yonah | Rabbeinu Yonah on Berakhot; Sha'arei Teshuvah |
| Maharsham | Teshuvot Maharsham Volume I |
| Sma | Me'irat Einayim on Shulchan Arukh, Choshen Mishpat |
| Smag | SeMaG |
| Pri Megadim E"A | (via normalization) |
| Sama | Me'irat Einayim on Shulchan Arukh, Choshen Mishpat |
| Eliyah Rabba | Eliyah Rabbah on Shulchan Arukh, Orach Chayim |
| Magen Avot | Magen Avot on Avot |
| Tiferet | Tiferet Yosef |
| Smak | Semak |
| Mishna Halachot | (via normalization) |
| Hatrumah | Sefer HaTerumah |
| Korban Netanel | Korban Netanel on Yoma |
| Shibolei Haleket | Shibolei HaLeket on Pesach Haggadah |
| Meiri Pesachim | Meiri on Pesachim |
| Bet Shmuel | Bet Shmu'el, Even ha-Ezer |
| Trumot | T’rumoth |
| Rav Pealim | Responsa Rav Pealim |
| Or Zaruah | Ohr Zarua |

---
_Caveats: covers the 640 substantial Halachipedia pages (stub/short pages excluded); work-name extraction is heuristic; frequency reflects Halachipedia's Anglo-Orthodox canon, not Sefaria's whole user base. Only the top works by frequency are verified against Sefaria, so the least-cited tail may be incomplete. Counts are lower bounds — a work also present under one spelling and absent under another is undercounted here. Era is classified by author death year (work-level, from the citation context where the title alone is ambiguous)._
