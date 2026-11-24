<!-- Draft comment for https://github.com/Sefaria/Sefaria-Project/issues/1016
     Not posted. Permalinks pinned to master @ c18cf5a (2026-11-23). Re-check before posting. -->

This is still happening, and it isn't specific to `/api/links` or to the search index. It's in `Ref()`'s title lookup, so every endpoint that builds a `Ref` is affected, **including the linker**.

**Repro** (production, today):

| query | `Bava Metzia 58b` | `Bava metzia 58b` |
|---|---|---|
| `/api/name` | `is_ref: true` | `is_ref: false`, though `completions[0]` is `Bava Metzia` |
| `/api/v3/texts` | 200 | 404 "Could not find title in reference" |
| `/api/links`, `/api/related` | 434 links | error |
| `/api/find-refs` | resolved | span detected, `refs: null` |

**Cause:**
- [`Ref.__clean_tref`](https://github.com/Sefaria/Sefaria-Project/blob/c18cf5a21703b60048d1698fbc095216fc582422/sefaria/model/text.py#L2553-L2557) capitalizes only the first character (deliberately, per the "Song Of Songs" comment).
- [`Ref.__init_tref`](https://github.com/Sefaria/Sefaria-Project/blob/c18cf5a21703b60048d1698fbc095216fc582422/sefaria/model/text.py#L2593-L2598) then looks up title prefixes in `library.get_title_node_dict()`, which is an exact-match dict.
- So `Rosh hashanah`, `Moed katan` and `Bava metzia` miss, while one-word titles work in any case, which is exactly the pattern in the original report.
- The autocompleter lowercases its input ([`autospell.normalizer`](https://github.com/Sefaria/Sefaria-Project/blob/c18cf5a21703b60048d1698fbc095216fc582422/sefaria/model/autospell.py#L96)), which is why `/api/name` suggests the right title in the same response that says `is_ref: false`.

**Why alt titles don't solve it:** `/api/index/titles` already has 1,097 groups of titles that differ only in case (`Rosh HaShanah`/`Rosh Hashanah`, `Even HaEzer`/`Even Haezer`, even a lowercase `shulchan aruch orach chaim`). Each word with an inner capital doubles the possible casings, and common forms are still missing. In ~8,800 citations from Halachipedia that don't currently resolve, fixing only the capitalization of the title makes **104** resolve, most of them `Kaf Hachaim` (85), plus `Sefer Hachinuch`, `Mishna brurah`, `magen avraham`, `tosefta shabbat` and others.

**Proposed fix:**
- When `__init_tref` raises `InputError`, look the title prefix up once more in a case-folded copy of the title→node map.
- Leave out any case-folded key that maps to more than one node, so the fallback never has to choose between two texts.
- If it matches, re-parse with the stored casing. If the re-parse also fails, raise the original error.

What this changes:
- Refs that parse today never reach the new code.
- It never guesses a spelling: it only resolves to a node the correctly-cased input would already reach.
- Hebrew is untouched.
- I resolved **every** title in all 1,097 case-variant groups live (2,207 titles): **no group maps to two different refs**. A miscasing that isn't in the title list (`Rosh hashanah`-style) fails today for **1,093 of 1,093** groups.
- Side finding: 18 of those alt titles start with a lowercase letter (`vaYikra`, `shulchan aruch orach chaim`, `or zarua, Volume II`, ...) and **can never match**, because `__clean_tref` capitalizes the first letter before the lookup. Data-side case fixes can fail even on their own terms; the fallback would make these work too.

Would you accept a PR along these lines? It's roughly 60 lines in `text.py` plus tests in `ref_test.py`. I'm happy to adjust where the retry lives (e.g. inside `__init_tref` next to the term-dict reinit) if you'd prefer that.
