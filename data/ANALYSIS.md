# English-halacha citation analysis

_Cuts from the full 640-page Halachipedia corpus (`work_frequency.json`, 38,195
detections) and the find-refs cache. Companion to `SEFARIA-MOST-WANTED.md`
(what Sefaria lacks) — this looks at what English halacha cites and what's
present-but-untranslated._

## Most-cited works overall (present + absent)

| Cites | Status | Work |
|---:|---|---|
| 2,143 | present | Shulchan Aruch |
| 1,859 | present | Mishnah Berurah |
| 990 | present | Rema |
| 800 | **absent** | Yalkut Yosef |
| 509 | present | Kaf HaChaim |
| 464 | present | Magen Avraham |
| 441 | present | Aruch Hashulchan / Rambam |
| 412 | present | Kitzur Shulchan Aruch |
| 388 | **absent** | Shemirat Shabbat KeHilchata |
| 387 | present | Shach |
| 364 / 284 | **absent** | Igrot Moshe / Yabia Omer |

The present works dominate the head; the absent ones are the modern
acquisition-priority (see the most-wanted list).

## Genre profile of the present citations

```
27%  halakhic codes (Shulchan Aruch, Mishnah Berurah, Aruch Hashulchan…)
18%  Mishnah          15%  Talmud Bavli
13%  commentary        9%  other / acharonim
 7%  Tanakh            6%  Rambam
```

English **halacha** writing leans on **codes + their commentaries** (~40%), where
the Sefaria source-sheet corpus was Talmud/Tanakh-dominated. Different genre →
different canon → different gaps. It's why normalization rules tuned on source
sheets recover ~43% there but only ~2% here.

## Translation gap — present, but only in Hebrew

A third axis: works Sefaria **has but hasn't translated**. Measured by sampling
each work's text for English coverage (version-existence is too noisy — Hebrew-only
works still carry stub/community "en" tags). Full data in `english_gap.json`;
top of the list:

| Cites | En | Work |
|---:|---:|---|
| 99 | 0% | Shach (Siftei Kohen on Yoreh De'ah) |
| 47 | 2% | Aruch HaShulchan, Yoreh De'ah |
| 38 | 0% | Rosh on Pesachim |
| 32 | 0% | Chayei Adam |
| 26 | 0% | Pitchei Teshuva on Yoreh De'ah |
| 23 | 0% | Beit Yosef, Yoreh De'ah |
| 20 | 0% | Chokhmat Adam |
| 17 | 0% | Teshuvot HaRivash |
| 16 | 0% | Kol Bo |

44 works total under 40% English coverage. The pattern: the **nosei keilim** on
Shulchan Aruch (Shach, Taz, Bach, Beit Shmuel, Pitchei Teshuva), the **Rishonic
Talmud commentaries** (Rosh, Ran, Rif on specific masechtot), and the **Ashkenazi
codes** (Chayei Adam, Chochmat Adam).

### Cost is not uniform
- **Tractable / cheaper, high-impact:** the self-contained Ashkenazi codes —
  Chayei Adam, Chochmat Adam (Nishmat Adam), Kol Bo, Pitchei Teshuva. Finite,
  structured, heavily cited. Best effort-to-impact.
- **Expensive:** Beit Yosef (vast), Aruch HaShulchan (multi-volume), and the
  Rishonim on the daf (Rosh, Ran, Rif). Dense, *elliptical* commentary — costly
  per page because it assumes the base text.

### Existing translations to license?
For most of this list — Shach, Taz, Beit Yosef, Bach, Beit Shmuel, Rosh/Ran/Rif —
**no complete non-ArtScroll English translation exists**, so there is nothing to
license; the realistic path is Sefaria **commissioning** original translation (as
with the William Davidson Talmud), prioritized by this demand list. ArtScroll
covers much of it but is not licensable (own closed digital library). The few
realistic partners — Koren/Steinsaltz (already Sefaria's Talmud partner) and
academic presses (Yale Judaica, Brill) — cover Talmud and some Rishonim, not these
halachic commentaries.

_Caveats: English coverage sampled from each work's opening section (ranks well,
not a precise %). Translation-availability is a domain assessment, not
machine-verified — an automated Wikipedia/Wikidata check proved unreliable for
these works (thin coverage, poor title matching); a definitive answer needs a
library-catalog (WorldCat/publisher) pass._
