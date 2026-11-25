# Bug report: `/api/name` ref-resolution is case-sensitive beyond the first letter, even when the suggestion engine already has the correct casing

> ## Research notes (2026-11-23) — read before filing
>
> **Re-verified live on 2026-11-23** against production and Sefaria-Project `master`
> @ `c18cf5a217`: every repro below still behaves as described, and the quoted code
> (`Ref.__clean_tref`, `Ref.__init_tref`, `get_name_completions`, autospell's
> `normalizer`) is unchanged.
>
> **1. Already reported: file as a comment on #1016, not a new issue.**
> [Sefaria/Sefaria-Project#1016](https://github.com/Sefaria/Sefaria-Project/issues/1016)
> ("Case sensitivity inconsistent with 2-word titles in names/refs on Links REST API",
> opened 2022-09-18 by DovOps, **still open, zero replies, no labels**) is the same
> bug seen from `/api/links`, even using `Rosh Hashanah` as its example. The reporter
> guessed it was a search-index or data problem. What this draft adds is the root cause
> (one shared code path in `Ref()`), the wider scope, and evidence that a fix is safe.
>
> **2. It's not just `/api/name`.** Everything that builds a `Ref` fails the same way
> (all tested with `Bava metzia 58b` vs `Bava Metzia 58b`):
>
> | endpoint | wrong case | correct case |
> |---|---|---|
> | `/api/name` | `is_ref: false` | resolves |
> | `/api/v3/texts` | 404 "Could not find title in reference" | 200 |
> | `/api/texts` (legacy) | 200 + error body | 200 |
> | `/api/links` | error | 434 links |
> | `/api/related` | error | 434 links, 218 sheets |
> | **`/api/find-refs` (the linker)** | span **detected**, `refs: null` | resolves |
>
> The `find-refs` row is the strongest point: Sefaria's own linker finds the citation in
> running text and then can't resolve it, so users don't get a link.
>
> **3. Sefaria already handles this in the data, one title at a time.** In
> `/api/index/titles` (67,472 titles), **1,097 groups of titles differ only by
> case**, each added as an alternate title by hand: `Rosh HaShanah`/`Rosh Hashanah`,
> `Even HaEzer`/`Even Haezer`, `Meilah`/`meilah`, even a lowercase
> `shulchan aruch orach chaim`. This matches the maintainers' stated preference in
> #1526 (2023, closed by rneiss: "we're probably not going to change the underlying API
> behavior, but we would love the various alt-titles … solve this issue on the data
> end"). **Expect that pushback.** The counter-argument is that 1,097 manual patches show
> the data approach can't keep up. `Kaf Hachaim`, `Sefer Hachinuch`, `Bava metzia` and
> `Terumat Hadeshen` all still fail.
>
> **4. A case-insensitive fallback looks safe.** The obvious objection is that
> lowercasing could merge two different titles. Of the 1,097 case-only groups, a random
> sample of 40 (85 titles) was resolved live: **0 groups mapped to different refs, 0
> unresolved**, so every case variant Sefaria has added points to the same text.
> **Full run 2026-11-24 (all 1,097 groups, 2,207 titles): 0 divergent; 1,093/1,093
> synthetic miscasings fail today; 18 lowercase-initial alt titles and 24 hyphenated
> titles are unreachable** (see `docs/upstream/evidence/casefold_groups_results.json`). The 27
> groups with all-caps words (`GRA`/`Gra`, `JT`, Roman numerals) were checked by eye and
> also look like the same text. Proposed fix: on an exact-match miss, look up a
> lowercased title map, and accept only if the lowercased key maps to exactly **one**
> node. That keeps it safe even if a real collision is added later.
>
> **5. Measured impact in our corpus.** Of the 8,789 unresolved Halachipedia citation
> strings (`pipeline/hp_unresolved.json`), **138 would resolve with case-insensitive
> matching alone**, spread over 19 works. Top ones: `Kaf Hachaim` (98), `Sefer Hachinuch`
> (16), then `Mishna brurah`, `Sefer Hamitzvot`, `Terumat Hadeshen`, `Shibbolei Haleket`,
> `Noda Beyehuda`, `Magen avraham`, `Bava metzia`. Live check: `Kaf Hachaim 103:5` →
> unresolved; `Kaf HaChaim 103:5` → *Kaf HaChayim on Shulchan Arukh, Orach Chayim
> 103:5*. (This was an offline title-list match that mimics `__init_tref`'s
> word-boundary prefix loop, not a full live re-run of all 138.)
>
> **Suggested filing:** a comment on #1016 with the root cause, the endpoint table, the
> 0-collision result, the unique-match fix, and a short repro. Optionally offer a PR, since
> the change is small and confined to `Ref.__init_tref` + `Library`. The body below is
> the original 2026-08-18 draft, still accurate; trim it into that comment.

## Summary

`GET /api/name/<query>` decides `is_ref` / `url` via `Ref()`'s exact-match title
lookup (`sefaria/model/text.py`), which normalizes almost nothing about casing —
`Ref._Ref__clean_tref` force-capitalizes only the *first* letter of the whole
input string (deliberately, to avoid title-casing "Song Of Songs" into
something wrong) and leaves every other letter as typed. Any citation whose
internal-word casing doesn't exactly match the stored title's casing fails to
resolve as a ref, **even when the same request's own `completions` list
contains the correctly-cased title as its top suggestion.**

This isn't a gap in the fuzzy/spell-corrected matcher (`sefaria/model/
autospell.py` — `AutoCompleter`/`TitleTrie`/`SpellChecker`/`NGramMatcher`) — that
system is not in the `is_ref` decision path at all. It only populates
`completions`/`completion_objects`. The two systems having such different
tolerance for casing, while sharing one endpoint and one input, is what makes
this surprising: the site already "knows" the right title and says so in the
same response that reports `is_ref: false`.

## Impact

Any client that trusts `is_ref`/`url` to decide whether a citation string
refers to something real — an auto-linker, an API integration, anything built
against `/api/name` as documented — will silently fail to link/resolve a
citation purely because of casing that doesn't affect meaning, while the fix
(the correct casing) is sitting unused in the same JSON payload.

## Steps to reproduce

```
$ curl -s 'https://www.sefaria.org/api/name/Rosh%20Hashanah%2030a' | python3 -c \
    'import json,sys; d=json.load(sys.stdin); print(d["is_ref"], d.get("url"))'
True Rosh_Hashanah.30a

$ curl -s 'https://www.sefaria.org/api/name/Rosh%20hashanah%2030a' | python3 -c \
    'import json,sys; d=json.load(sys.stdin); print(d["is_ref"], d.get("url"))'
False None
```

The only difference between the two queries is the case of one letter
("Hashanah" -> "hashanah") in the middle of the string — not the leading
letter, which is separately force-capitalized regardless of input casing:

```
$ curl -s 'https://www.sefaria.org/api/name/rosh%20Hashanah%2030a' | python3 -c \
    'import json,sys; d=json.load(sys.stdin); print(d["is_ref"], d.get("url"))'
True Rosh_Hashanah.30a
```

## Actual response (failing query)

```json
{
  "lang": "en",
  "is_ref": false,
  "completions": ["Rosh HaShanah", "Rosh Hashanah", "Rosh on Rosh Hashanah", ...],
  "completion_objects": [
    {"title": "Rosh HaShanah", "key": "Rosh Hashanah", "type": "ref", "is_primary": false, "order": 1000000},
    ...
  ]
}
```

`completions[0]` / `completions[1]` already name the correct title
(`"Rosh HaShanah"` / `"Rosh Hashanah"`) — the request just doesn't use it to
resolve `is_ref`.

## Expected

Either `is_ref`/`url` resolution falls back to a case-insensitive (or
normalized-casing) match against the same title data the completion engine
already indexes, or — at minimum — the response is internally consistent: if
`completions` can confidently name the title, `is_ref` shouldn't silently say
no with no path to a correction.

## A second example (not just Talmud daf addressing)

Same defect on a book-level reference, no locator involved:

```
$ curl -s 'https://www.sefaria.org/api/name/Chovot%20HaLevavot' | python3 -c \
    'import json,sys; d=json.load(sys.stdin); print(d["is_ref"], d.get("url"))'
True Duties_of_the_Heart

$ curl -s 'https://www.sefaria.org/api/name/Chovot%20Halevavot' | python3 -c \
    'import json,sys; d=json.load(sys.stdin); print(d["is_ref"], d.get("url"))'
False None
```

## Root cause (read directly from the public repo, `Sefaria/Sefaria-Project`)

- `reader/views.py`'s `name_api`/`get_name_completions` sets `is_ref` from
  `ref = Ref(name)` (a try/except around the strict parser) — completely
  separate from the `completer.complete(...)` call that produces `completions`.
- `sefaria/model/text.py`, `Ref.__init__` -> `Ref._Ref__clean_tref`:
  ```python
  try:
      # capitalize first letter (don't title case all to avoid e.g., "Song Of Songs")
      tref = tref[0].upper() + tref[1:]
  except IndexError:
      pass
  ```
  No other casing normalization happens before the title lookup.
- `Ref.__init_tref` resolves titles via `library.get_title_node_dict(self._lang)`,
  an exact-string dict (`Library._title_node_maps[lang]`), tried at
  progressively shorter word-boundary prefixes. No `.lower()` / `IGNORECASE`
  anywhere in that path (confirmed by reading `Library.all_titles_regex_string`
  too — titles are `re.escape()`'d verbatim and the compiled regex carries no
  case-insensitive flag).
- By contrast, `sefaria/model/autospell.py`'s `AutoCompleter` normalizes input
  before trie lookup (lowercasing for English, per its own docs) — which is
  exactly why `completions` finds the right title while `is_ref` doesn't.

## Suggested fix / workaround

- Fix: when the exact-case lookup in `Ref.__init_tref` misses, retry against a
  case-normalized form of `library.get_title_node_dict()` (or reuse
  `AutoCompleter`'s existing normalization) before giving up and raising
  `InputError`.
- Workaround for API consumers until then: generate a title-cased candidate (and
  a "Ha"-compound-aware casing variant, e.g. `Halevavot` -> `HaLevavot`) as an
  additional query before accepting a citation as unresolved.

## Environment

- Observed: 2026-08-18; re-verified 2026-11-23, `www.sefaria.org` production.
- Source read: `Sefaria/Sefaria-Project` (public GitHub), `reader/views.py`,
  `sefaria/model/text.py`, `sefaria/model/autospell.py`, current `master` as of
  2026-08-18.


---

## Related data error (found 2026-11-25; separate from the case-sensitivity bug)

The alternate title `Rambam, Hilchot Malveh veLoveh` ("Laws of Creditor and Debtor") is
attached to the wrong Mishneh Torah section:

```
/api/name/Rambam, Hilchot Malveh veLoveh 5:1  ->  Mishneh Torah, Inheritances 5:1
/api/name/Mishneh Torah, Creditor and Debtor 5:1  ->  Mishneh Torah, Creditor and Debtor 5:1
```

Any citation using that alias links to Inheritances instead of Creditor and Debtor.
Found while auditing mislinks over ~19k web-mined citation pairs.
