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
Checked each work below via WorldCat and Judaica-publisher catalogs (replacing
the earlier Wikidata-based attempt, which proved unreliable — see caveat). The
original assumption holds for nearly everything: **no complete, independently-
published English translation exists** for the Rishonic commentaries (Rosh,
Ran, Rashba, Rif, Tosafot) or the Acharonic nosei keilim on Shulchan Aruch
(Shach, Taz, Bach, Beit Shmuel, Chelkat Mechokek), or for Beit Yosef, Kessef
Mishneh, Kol Bo, Havot Yair, Teshuvot HaRivash, or Teshuvot HaRosh. Sefaria's
own site already carries the only English these works have (partial/community
translations) — there is no outside edition to license, so the realistic path
stays **commissioning** original translation (as with the William Davidson
Talmud), prioritized by this demand list.

- **Rashi on Talmud** — confirmed absent as a standalone translation too:
  Soncino's Talmud paraphrases Rashi into its own English rendering and
  footnotes but never published Rashi as an independent English work.
- **Chayei Adam / Chochmat Adam / Nishmat Adam** — small Orthodox presses
  (Hoffman, and a Chochmas Adam edition from a niddah/kashrut-focused
  publisher) have translated **individual hilchot** — Chanukah, Megillah,
  Niddah, Meat & Milk — with facing-page Hebrew/English. These are excerpts of
  single sections, not complete-work editions, so they don't change the
  commission-vs-license calculus for the work as a whole.
- **Aruch HaShulchan — new finding, different from the rest of this list.** A
  complete English translation exists: all four sections (Orach Chaim, Yoreh
  De'ah, Even HaEzer, Choshen Mishpat; ~24,161 subsections), made by Joshua
  Broyde (an ML engineer, not a Judaica publisher) using an LLM, sourced from
  Sefaria's own Hebrew text, and published free online with code+data on
  GitHub ([Seforim Blog writeup](https://seforimblog.com/2026/05/translating-the-aruch-hashulchan-with-ai-method-and-lessons/)).
  This isn't a "license an existing human translation" opportunity — it's an
  AI first-pass the author himself flags as imperfect, and no explicit reuse
  license is stated — but it's a real, complete, freely-available draft
  Sefaria could evaluate for direct incorporation or as scaffolding to human-
  review, which is a materially different (and cheaper) option than
  commissioning Aruch HaShulchan from scratch. Worth a direct conversation
  with Broyde before assuming either the quality or the rights.

_Caveats: English coverage sampled from each work's opening section (ranks well,
not a precise %). This library-catalog pass is a web-search-based domain
assessment (WorldCat + publisher sites), not a systematic bibliographic
search — absence of evidence for a translation isn't definitive proof none
exists, especially for small/out-of-print Judaica editions that don't surface
well in general search. Treat "no complete translation found" as reasonably
confident, not certain._
