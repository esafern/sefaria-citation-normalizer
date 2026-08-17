# Bug report: `/api/name` ref-resolution is case-sensitive beyond the first letter, even when the suggestion engine already has the correct casing

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

- Observed: 2026-08-18, `www.sefaria.org` production, `/api/name`.
- Source read: `Sefaria/Sefaria-Project` (public GitHub), `reader/views.py`,
  `sefaria/model/text.py`, `sefaria/model/autospell.py`, current `master` as of
  2026-08-18.
