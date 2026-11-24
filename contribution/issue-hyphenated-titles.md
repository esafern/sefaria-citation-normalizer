<!-- Draft NEW issue for https://github.com/Sefaria/Sefaria-Project/issues (not posted).
     Permalinks pinned to master @ c18cf5a (2026-11-23). Repro re-checked live 2026-11-25.
     Evidence: contribution/evidence/hyphen_titles_results.json. Post everything below this comment. -->

**Title:** Titles containing a hyphen can never be resolved: `Ref()` splits on `-` before looking up the title (110 of 110 hyphenated titles unreachable)

**Repro** (production, today):

| query | result |
|---|---|
| `/api/name/Pirke de-Rabbi Eliezer 24` | `is_ref: false` |
| `/api/name/Pirkei DeRabbi Eliezer 24` | `is_ref: true` |
| `/api/name/Rosh ha-Shanah 16a` | `is_ref: false` |
| `/api/name/I Divrei Ha-Yamim 1:1` | `is_ref: false` |
| `/api/v3/texts/Pirke de-Rabbi Eliezer 24` | 404 |
| `/api/name/Pirke de-Rabbi Eliezer` | `is_ref: false`, **while `completions` offers `Pirke de-Rabbi Eliezer` itself** |

`Pirke de-Rabbi Eliezer`, `Rosh ha-Shanah` and `I Divrei Ha-Yamim` are all titles in `/api/index/titles`. The autocompleter suggests them, and picking the suggestion fails.

**Cause:** [`Ref.__init_tref`](https://github.com/Sefaria/Sefaria-Project/blob/c18cf5a21703b60048d1698fbc095216fc582422/sefaria/model/text.py#L2573-L2578) splits the whole tref on `[-\u2010-\u2015]` (the range separator) before any title lookup:

```python
parts = [s.strip() for s in re.split("[-\u2010-\u2015]", self.tref)]
if len(parts) > 2:
    raise InputError(f"Couldn't understand ref '{self.tref}' (too many -'s).")
...
base = parts[0]
```

So `Pirke de-Rabbi Eliezer 24` is looked up as `Pirke de` + a "range end" of `Rabbi Eliezer 24`. A title with two hyphens (`Sheʾelot u-teshuvot Min ha-shamayim`) fails earlier with "too many -'s".

**Scope:** I tested every title in `/api/index/titles` that contains a hyphen or dash, live: **110 titles, 0 resolve**. They're alt titles for:
- Pirkei DeRabbi Eliezer (6, e.g. `Pirke de-Rabbi Eliezer`, `Pirqei de-Rabbi Eli’ezer`)
- Rosh Hashanah (`Rosh ha-Shanah`, `Rosh hash-Shanah`, `Rosh Ha-shana`)
- I/II Chronicles and its commentaries (Rashi, Ralbag, Metzudot: 24)
- Arukh HaShulchan, Shulchan Arukh, Beit Shmuel, Kaf HaChayim, Sefer HaChinukh, Ketzot HaChoshen and Vayikra Rabbah sections (`ha-Shulḥan`, `ha-Ezer`, `Va-Yikra`, ...)
- Sefer HaBachur (15), the Kuzari, Ma'arekhet HaElohut, Megillat HaChashmonaim, Maggid Devarav LeYaakov, Shut Min HaShamayim

Every one of these works also has a hyphen-free title, so no text is unreachable. But the hyphenated forms are often the standard academic transliteration, and they are what people write. In ~35,000 citation links I mined from Mi Yodeya and English Wikipedia, **48 begin with `Pirke De-Rabbi Eliezer`** (e.g. `Pirke De-Rabbi Eliezer, chapter 46`). Every one of them fails today, even though the title is in Sefaria's own list.

**Possible fixes:**
1. **Match the title before splitting the range** (preferred). Find the longest title prefix of the whole tref with the existing word-boundary scan, then split only the remainder on dashes. `Genesis 1-2` is unaffected (title `Genesis`, range `1-2`). `Pirke de-Rabbi Eliezer 24` matches the full title, leaving address `24`. The "too many -'s" check would then count dashes in the address only.
2. **Normalize at index time:** add a dash-free key for each hyphenated title to the title→node map and strip dashes inside the title prefix before lookup. More moving parts than (1).
3. **Data only:** remove the 110 hyphenated alt titles. They're dead today, and the autocompleter is offering users titles that fail. This is the cheapest fix, but it gives up the common academic spellings rather than supporting them.

**Two side findings in the same title list** (happy to split these out if useful):
- 19 titles contain HTML markup, e.g. `<i>Kaf ha-Hayyim</i>`, `<i>Shulḥan Arukh, Even ha-Ezer</i>`. They look like metadata that was pasted in with formatting.
- `Drafting - Summer - Product Announcements` appears in the public `/api/index/titles` list. It may be an internal draft that wasn't meant to be public.

Script and full results: [hyphen_titles_results.json](https://github.com/esafern/sefaria-citation-normalizer/blob/next-work/contribution/evidence/hyphen_titles_results.json).
