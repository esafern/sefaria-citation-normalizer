<!-- DRAFT email. Per Sefaria's README, library/data problems go to corrections@sefaria.org,
     not GitHub. Re-checked live 2026-11-25. Evidence: contribution/evidence/rambam_hilchot_aliases.json.
     Edit freely; send everything below the line. -->

**To:** corrections@sefaria.org
**Subject:** Title data: three Mishneh Torah aliases point to the wrong sections, plus a few other title-list issues

---

Hi,

While checking citation links against your title list, I found some title data problems. The first one sends readers to the wrong text; the rest are smaller.

**1. Three Mishneh Torah section aliases are rotated (6 alias titles).**

In Sefer Mishpatim, the Hebrew-name aliases for three sections each point to a neighboring section:

| Alias (both `Rambam, …` and `Mishneh Torah, …` forms) | Means | Currently resolves to |
|---|---|---|
| Hilchot Malveh veLoveh | Creditor and Debtor | **Inheritances** |
| Hilchot To`en veNit`an | Plaintiff and Defendant | **Creditor and Debtor** |
| Hilchot Nehalot | Inheritances | **Plaintiff and Defendant** |

For example, `https://www.sefaria.org/api/name/Rambam, Hilchot Malveh veLoveh 5:1` returns *Mishneh Torah, Inheritances 5:1*. The other ~160 `Rambam, Hilchot …` / `Mishneh Torah, Hilchot …` aliases I checked all resolve correctly.

**2. An internal title is attached to the Mishnah Berurah.**

The Mishnah Berurah index has `Drafting - Summer - Product Announcements` among its English titles. It appears in the public title list and in autocomplete, along with `…, Introduction` and `…, Introduction to the Laws of Shabbat`. It looks like it was pasted in by accident.

**3. Fifty titles contain HTML markup.**

For example, `<i>Mishnah Berurah</i>`, `<i>Shulḥan Arukh, Oraḥ Ḥayyim</i>`, `Rambam, <i>Hilkhot Melakhim</i>`, and one with a broken tag: `Rambam, <i>Hilkhot Evel</i`. Nobody can type these, so they never match a citation, but they do show up in the title list and could show up in autocomplete. I can send the full list.

**4. Eighteen titles start with a lowercase letter and can never match.**

Examples: `vaYikra`, `shulchan aruch orach chaim`, `sichos haran`, `tzidkat hatzadik`, and `or zarua, Volume II` (plus 13 more `or zarua` titles). The ref parser capitalizes the first letter of a citation before looking it up, so a stored title that starts in lowercase is never found. This one is really a code issue; I've described it on GitHub #1016. Mentioning it here in case the data fix is easier.

(Separately, titles containing a hyphen can't be resolved at all. That's a code issue and I filed it as GitHub #4150.)

Thanks for all the work on the library.

Eric Safern
