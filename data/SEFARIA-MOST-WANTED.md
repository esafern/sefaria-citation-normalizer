# Halachipedia's most-cited works that Sefaria doesn't have

_A candidate priority list for Sefaria's library team._

**Method.** From a 250-page sample of Halachipedia, we extracted the footnote citations, ran each through Sefaria's own `find-refs` linker, and kept what it detected as a citation but couldn't resolve to a text. We reduced each to its base work, counted how often it's cited, and confirmed absence via `/api/name` (a work is 'present' if any real ref title matches, allowing for transliteration and for titles stored under a `Teshuvot`/`Responsa` prefix). Every candidate was re-verified live against `/api/name` (2026-07): works present under a variant or abbreviated spelling were excluded (see the tail), spelling twins and section-volumes were merged into one work, and mis-detected non-texts were dropped.

**Result.** 72 works, 2750 citations. Split by why they're missing:

## Tier 1 — Public domain, not yet digitized

_Author died >70 years ago; Sefaria can add these without licensing._

| Citations | Work | Author |
|---:|---|---|
| 45 | Birkei Yosef | Chida (d.1806) |
| 34 | Pri Chadash | H. da Silva (d.1698) |
| 28 | Chavot Daat | Y. Lorberbaum (d.1832) |
| 24 | Eliya Rabba | Eliyahu Shapira (d.1712) |
| 16 | Radvaz | David ibn Zimra (d.1573); responsa absent, MT commentary present |
| 12 | Hagahot Maimoniyot | Meir HaKohen (13c) |
| 11 | Bet Efraim | E.Z. Margolis (d.1828) |
| 11 | Knesset Hagedola | Chaim Benveniste (d.1673) |
| 10 | Maamar Mordechai | Mordechai Carmi (d.1825) |
| 10 | Darkei Teshuva | Tzvi Hirsch Shapira (d.1913) |
| 10 | Gesher Hachaim | Y.M. Tucazinsky (d.1955) |
| 9 | Ravyah | Eliezer b. Yoel HaLevi (d.1225) |
| 9 | Hagahot Ashri | Israel of Krems (14c) |
| 8 | Daat Torah | Maharsham / S. Schwadron (d.1911) |
| 8 | Maharshag | Shmuel Engel (d.1935) |
| 8 | Avnei Nezer | Avraham Bornsztain (d.1910) |
| 8 | Sidrei Tahara | Elchanan Ashkenazi (d.1780) |
| 7 | Turei Even Rosh Hashana | Aryeh Leib Ginzburg (d.1785) |
| 7 | Rabbenu Yerucham | Yerucham b. Meshullam (14c) |
| 7 | Mishkenot Yakov | Yaakov of Karlin (d.1844) |
| 7 | Maharam Shik | Moshe Schick (d.1879) |

## Tier 2 — Modern / in-copyright

_Recent authorities; would require a licensing arrangement. Ranked by demand._

| Citations | Work | Author |
|---:|---|---|
| 428 | Yalkut Yosef | Yitzchak Yosef |
| 260 | Chazon Ovadyah | Ovadia Yosef (d.2013) |
| 174 | Igrot Moshe | Moshe Feinstein (d.1986) |
| 161 | Shemirat Shabbat KeHilchata | Y.Y. Neuwirth (d.2013) |
| 104 | Halacha Brurah | David Yosef |
| 102 | Yabia Omer | Ovadia Yosef (d.2013) |
| 88 | Yechave Daat | Ovadia Yosef (d.2013) |
| 85 | Chelkat Binyamin | on Hilchot Basar b'Chalav, modern |
| 77 | Or Letzion | Ben Zion Abba Shaul (d.1998) |
| 69 | Piskei Teshuvot | Simcha Rabinowitz, modern |
| 68 | Chazon Ish | A.Y. Karelitz (d.1953) |
| 66 | Shevet Halevi | S.H. Wosner (d.2015) |
| 54 | Tzitz Eliezer | E. Waldenberg (d.2006) |
| 49 | Taharat Habayit | Ovadia Yosef (d.2013) |
| 47 | Badei Hashulchan | modern, on Yoreh De'ah |
| 40 | Minchat Yitzchak | Y.Y. Weiss (d.1989) |
| 39 | Halichot Shlomo | S.Z. Auerbach (d.1995) |
| 39 | Ginzei Hakodesh | modern |
| 39 | Teshuvot VeHanhagot | Moshe Sternbuch, modern |
| 34 | Minchat Shlomo | S.Z. Auerbach (d.1995) |
| 30 | Nitei Gavriel | Gavriel Zinner, modern |
| 28 | Rivevot Efraim | Efraim Greenblatt (d.2014) |
| 26 | Beer Moshe | Moshe Stern (d.1997) |
| 25 | Torat Ribbit | modern |
| 25 | Orchot Shabbat | modern |
| 23 | Menuchat Ahava | modern |
| 23 | Brit Yehuda | Y. Blau (d.2013) |
| 20 | Torat HaMoadim | modern |
| 20 | Minchat Asher | Asher Weiss, modern |
| 14 | Mishneh Halachot | Menashe Klein (d.2011) |
| 12 | Birkat Hashem | modern |
| 12 | Ashrei Ha'ish | rulings of R. Elyashiv, modern |
| 12 | Chut Shani | Nissim Karelitz (d.2019) |
| 12 | Shalmei Yehuda | modern (R. Elyashiv) |
| 12 | Har Tzvi | Tzvi Pesach Frank (d.1960) |
| 11 | Chelkat Yakov | Mordechai Y. Breisch (d.1976) |
| 11 | Horah Brurah | modern |
| 11 | Ateret Paz | Pinchas Zvichi, modern |
| 10 | Ishei Yisrael | A.Y. Pfoifer, modern |
| 9 | Shevet Hakehati | Shammai Gross, modern |
| 9 | Milveh Hashem | modern |
| 9 | Tiltulei Shabbat | modern |
| 8 | Nishmat Avraham | A.S. Abraham (d.2010) |
| 8 | Shulchan Shlomo | S.Z. Auerbach (d.1995) |
| 7 | Divrei Yatziv | Y.Y. Halberstam (d.1994) |
| 7 | Dor Hamelaktim | modern |
| 7 | Az Nidbaru | Binyamin Zilber (d.2008) |
| 7 | Agur Bohalecha | modern |
| 7 | Yaskil Avdi | Ovadia Hedaya (d.1969) |

## Tier 3 — Absent, era not yet classified

_Detected as absent; author/copyright status not hand-checked. Longer tail._

| Citations | Work |
|---:|---|
| 14 | Mekor Chaim |
| 9 | Halichot Olam |

## Excluded: present under a variant spelling

_Flagged absent by exact match but found on Sefaria after normalization — NOT wanted._

| Cited-as | Actually on Sefaria as |
|---|---|
| Shulchan Aruch Harav | Shulchan Arukh HaRav |
| Chatom Sofer | Chatam Sofer on Torah |
| Beiur Halacha | Beur Halacha |
| Pri Megadim | Pri Megadim on Yoreh De'ah |
| Mishna Brura | Mishna Brurah |
| Levush | Levush HaOrah |
| Chaye Adam | Chayei Adam |
| Meiri | Meiri on Yoma |
| Gemara Bava Metsia | (via normalization) |
| Trumat Hadeshen | Terumat HaDeshen |
| Dirshu | Dirshuni I |
| Tashbetz | Tashbetz Katan |
| Shem HaGedolim | Shem HaGedolim, Maarekhet Sefarim |
| Orchot Chaim | Orchot Chaim L'HaRosh |
| Sma | Me'irat Einayim on Shulchan Arukh, Choshen Mishpat |
| Pri Megadim M"Z | (via normalization) |
| Smag | SeMaG |
| Pri Megadim E"A | (via normalization) |
| Sama | Me'irat Einayim on Shulchan Arukh, Choshen Mishpat |
| Maharil | Teshuvot Maharil |
| Rabbenu Yonah | Rabbeinu Yonah on Berakhot; Sha'arei Teshuvah |
| Magen Avot | Magen Avot on Avot |
| Halachot Ketanot | Halachot Ketanot LaRif |
| Smak | Semak |
| Maharsham | Teshuvot Maharsham Volume I |
| Rambam Hilchos Machalas Asuros | Mishneh Torah, Forbidden Foods |
| Aruch | Aruch Hashulchan |
| torah | Torah Ohr |
| Mishna Halachot | (via normalization) |
| Hatrumah | Sefer HaTerumah |
| Rambam, Mishneh Torah: Hilchot Tefillah U'Birkat Cohanim, Chapter | Mishneh Torah, Prayer and the Priestly Blessing |
| Rav Pealim | Responsa Rav Pealim |
| Rambam Malveh Vloveh | Rambam, Malveh veLoveh |
| Issur V’heter | Issur V'Heter L'Rabbeinu Yerucham |
| Bedek Habayit | Bedek HaBayit on Torat HaBayit HaArokh |
| Shibolei Haleket | Shibolei HaLeket on Pesach Haggadah |
| Rashba responsa | Teshuvot haRashba (parts I-VII) |
| Rambam Machalot Assurot | Rambam, Ma'achalot Assurot |
| Chochmas Adom | Chochmat Adam |
| Rambam Sefer HaMitzvot | Sefer HaMitzvot |

---
_Caveats: 250-page sample (not all of Halachipedia); work-name extraction is heuristic; frequency reflects Halachipedia's Anglo-Orthodox canon, not Sefaria's whole user base. Counts are lower bounds — a work also present under one spelling and absent under another is undercounted here. Tier-1/2 era is classified by author death year; a handful of genuinely ambiguous titles remain in Tier 3._
