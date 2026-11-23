# Draft PR: case-insensitive title fallback in `Ref()`

_Draft for `Sefaria/Sefaria-Project`, base `master`. Written against `master` @
`c18cf5a217` (2026-11-23). **Not posted, and the code is untested against a real
Sefaria install** (it needs their MongoDB). The evidence below comes from an offline
copy of the lookup function run against the live title list, with results checked
live. Companion to `SEFARIA-CASE-SENSITIVITY-BUG.md`; post it as a follow-up to
issue #1016._

---

## Title

`fix(ref): resolve titles case-insensitively when the exact-case lookup fails`

## Description (PR body)

Fixes #1016.

`Ref()` matches titles against `library.get_title_node_dict()` with an exact,
case-sensitive dict lookup. `__clean_tref` capitalizes only the first character, so
any other casing difference makes a real citation unresolvable:

| input | today | with this PR |
|---|---|---|
| `Bava metzia 58b` | `InputError` | `Bava Metzia 58b` |
| `Kaf Hachaim 103:5` | `InputError` | `Kaf HaChayim on Shulchan Arukh, Orach Chayim 103:5` |
| `Mishna berura 267:9` | `InputError` | `Mishnah Berurah 267:9` |
| `magen avraham (340:1)` | `InputError` | `Magen Avraham 340:1` |

Because every Ref-based endpoint shares this lookup, the failure appears in
`/api/name` (`is_ref: false` even though `completions[0]` is the right title),
`/api/v3/texts` (404), `/api/texts`, `/api/links`, `/api/related`, and **`find-refs`**.
The linker detects `Bava metzia 58b` in running text but returns `refs: null`.

Today this is worked around in the data. `/api/index/titles` has **1,097 groups of
titles that differ only in case** (`Rosh HaShanah`/`Rosh Hashanah`,
`Even HaEzer`/`Even Haezer`, `meilah`, `shulchan aruch orach chaim`), each added as
an alt title by hand. That can't cover every combination: each word with an inner
capital (`HaChaim`, `BeYehuda`) doubles the possible casings, so common forms like
`Kaf Hachaim` and `Sefer Hachinuch` still fail.

### What changes

1. **`Library.get_casefold_title_node_dict(lang)`** is a case-folded view of the
   existing title→node map, built lazily and cleared wherever the existing derived
   title caches are cleared. **Keys that would map to more than one distinct node are
   dropped**, so the fallback can never choose between two different texts.
2. **`Library.recase_title_prefix(tref, lang)`** finds the longest leading title with
   the same word-boundary scan `__init_tref` already uses. If that prefix is a
   wrong-case form of exactly one title, it returns `tref` with the stored casing.
   It returns `None` if the prefix already matches exactly, or for Hebrew.
3. **`Ref.__init__`** keeps the current parse as the first attempt. Only if it raises
   `InputError` does it re-case the title prefix and parse once more. If that also
   fails, **the original exception is raised**, so error messages are unchanged.

### Why this is safe

- **No behavior change for any ref that parses today.** The new code runs only on the
  exception path.
- **The fallback never guesses a spelling.** It only changes casing, and only to a
  title already in the library's own title map. It resolves to exactly the node that
  correctly-cased input would reach. Prefixes that fold to more than one node are
  excluded.
- **No case-only collisions found in practice.** A random sample of 40 of the 1,097
  case-variant groups (85 titles) was resolved live: every group pointed at the same
  ref. The ambiguity guard exists for future data, not because of a known collision.
- **Hebrew is untouched**: `lang == "he"` returns early, same as `__clean_tref`.
- **Cost:** a single dict built once per lang (about 67k entries) and reset with the
  other derived caches. The retry happens only on parse failure, and each step of the
  prefix scan is a dict lookup.

### Evidence

Run on 8,789 citation strings from Halachipedia that Sefaria currently fails to
resolve:

- The fallback **re-cases 140** of them (the rest have no wrong-case title prefix).
- **104 of the 140 then resolve** (checked live by querying the re-cased string).
  Examples: `Kaf Hachaim …` ×85, `Sefer Hachinuch (529)` → `Sefer HaChinukh 529`,
  `Mishna brurah` → `Mishnah Berurah`, `tosefta shabbat 13:7` → `Tosefta Shabbat
  13:7`, `Shibbolei Haleket 263` → `Shibbolei HaLeket 263`.
- **The other 36 still fail, for reasons that have nothing to do with case**: address
  formats the parser doesn't accept (`Sefer HaChinuch Mitzvah 603`,
  `Terumat HaDeshen 108`), complex texts cited without a section
  (`Kaf HaChaim YD 116:12`), and noise. They raise the same `InputError` as today.

### Open questions for reviewers

- Should the fallback also apply to `library.get_term_dict()` (term lookups)? It's
  left out here to keep the change small.
- Is `__init__` the right place, or would you rather have the retry inside
  `__init_tref` beside the term-dict reinit?
- Should `_validate()` failures also trigger the retry? This PR does not, on purpose.
  A range error after a successful title match is not a casing problem.

---

## Diff

```diff
--- a/sefaria/model/text.py
+++ b/sefaria/model/text.py
@@ class Ref(...):
     def __init__(self, tref=None, _obj=None):
@@
         if tref:
             self.orig_tref = tref
             self._lang = "he" if is_all_hebrew(tref) else "en"
             self.tref = self.__clean_tref(tref, self._lang)
-            self.__init_tref()
+            try:
+                self.__init_tref()
+            except InputError as original_error:
+                # Titles are matched case-sensitively. If the citation starts with a known
+                # title in the wrong case ("Bava metzia 58b"), retry once with the library's
+                # casing. Refs that parse today never reach this branch.
+                recased = library.recase_title_prefix(self.tref, self._lang)
+                if recased is None:
+                    raise
+                self.__reset_parse_state()
+                self.tref = recased
+                try:
+                    self.__init_tref()
+                except InputError:
+                    raise original_error
             self._validate()
         elif _obj:
@@
+    def __reset_parse_state(self):
+        """Undo partial state left by a failed __init_tref before re-parsing."""
+        self.index = None
+        self.book = None
+        self.primary_category = None
+        self.sections = []
+        self.toSections = []
+        self.index_node = None
+        self.__init_ref_pointer_vars()
+
@@ class Library(object):
     def __init__(self):
@@
         # Maps, keyed by language, from titles to schema nodes
         self._title_node_maps = {lang: {} for lang in self.langs}
+
+        # Case-folded view of _title_node_maps, built lazily, keyed by language.
+        # See get_casefold_title_node_dict().
+        self._casefold_title_node_maps = {}
@@
     def _reset_index_derivative_objects(self, include_auto_complete=False):
         self._full_title_lists = {}
         self._full_title_list_jsons = {}
         self._title_regex_strings = {}
         self._title_regexes = {}
+        self._casefold_title_node_maps = {}
@@
     def rebuild(self, include_toc=False, include_auto_complete=False):
@@
             self._title_regex_strings = {}
             self._title_regexes = {}
+            self._casefold_title_node_maps = {}
             Ref.clear_cache()
@@
     def get_title_node_dict(self, lang="en"):
         ...
         return self._title_node_maps[lang]
+
+    def get_casefold_title_node_dict(self, lang="en"):
+        """
+        :param lang: "he" or "en"
+        :return: dict of title.casefold() -> (stored title, node).
+
+        Keys whose titles point at more than one distinct node are left out,
+        so a case-insensitive lookup can never choose between two texts.
+        """
+        title_dict = self.get_title_node_dict(lang)  # may trigger a rebuild, which resets ours
+        casefolded = self._casefold_title_node_maps.get(lang)
+        if casefolded is None:
+            casefolded, ambiguous = {}, set()
+            for title, node in title_dict.items():
+                key = title.casefold()
+                if key in casefolded and casefolded[key][1] is not node:
+                    ambiguous.add(key)
+                else:
+                    casefolded.setdefault(key, (title, node))
+            for key in ambiguous:
+                del casefolded[key]
+            self._casefold_title_node_maps[lang] = casefolded
+        return casefolded
+
+    def recase_title_prefix(self, tref, lang="en"):
+        """
+        If `tref` begins with a known title in the wrong case, return `tref` with that
+        prefix in the library's casing ("Bava metzia 58b" -> "Bava Metzia 58b").
+        Otherwise return None. Uses the same word-boundary prefix scan as
+        Ref.__init_tref. English only.
+        """
+        if lang != "en":
+            return None
+        exact = self.get_title_node_dict(lang)
+        casefolded = self.get_casefold_title_node_dict(lang)
+        for end in range(len(tref), 0, -1):
+            if end != len(tref) and tref[end] not in " ,.:_":
+                continue  # do not stop in the middle of a word
+            prefix = tref[:end]
+            if prefix in exact:
+                return None  # longest title already matches exactly; casing isn't the problem
+            hit = casefolded.get(prefix.casefold())
+            if hit:
+                return hit[0] + tref[end:]
+        return None
```

## Tests (`sefaria/model/tests/ref_test.py`)

```python
class Test_case_insensitive_titles:
    @pytest.mark.parametrize("miscased, canonical", [
        ("Bava metzia 58b", "Bava Metzia 58b"),
        ("Rosh hashanah 30a", "Rosh Hashanah 30a"),   # "Rosh" is itself a title: exact
                                                       # path matches it, then fails
        ("BAVA METZIA 58b", "Bava Metzia 58b"),
        ("Chovot Halevavot", "Chovot HaLevavot"),
        ("Kaf Hachaim 103:5", "Kaf HaChaim 103:5"),
        ("Bava metzia 58b-59a", "Bava Metzia 58b-59a"),
    ])
    def test_miscased_title_resolves_like_canonical(self, miscased, canonical):
        assert Ref(miscased) == Ref(canonical)
        assert Ref(miscased).normal() == Ref(canonical).normal()

    def test_correct_case_is_unchanged(self):
        assert Ref("Song of Songs 1:1").normal() == "Song of Songs 1:1"

    def test_spelling_errors_still_fail(self):
        with pytest.raises(InputError):
            Ref("Bava metziaa 58b")

    def test_original_error_is_preserved(self):
        # Title fixed by casing but address still invalid -> same error as before
        with pytest.raises(InputError) as e:
            Ref("Bava metzia 999b")
        assert "Bava metzia 999b" in str(e.value) or "999" in str(e.value)

    def test_hebrew_untouched(self):
        assert library.recase_title_prefix("בבא מציעא נח ב", "he") is None

    def test_ambiguous_casefold_key_is_dropped(self, monkeypatch):
        a, b, c = object(), object(), object()
        monkeypatch.setattr(library, "get_title_node_dict",
                            lambda lang="en": {"Foo Bar": a, "Foo bar": b, "Baz Qux": c, "Baz qux": c})
        monkeypatch.setattr(library, "_casefold_title_node_maps", {})
        cf = library.get_casefold_title_node_dict("en")
        assert "foo bar" not in cf          # two different nodes -> never guessed
        assert cf["baz qux"][1] is c        # same node under two casings -> fine
```

_Note: `test_original_error_is_preserved` may need adjusting to whatever exception
text `_validate` / `__get_sections` produces for an out-of-range daf. The intent is
only that the retry doesn't change the error a user sees._

---

## Before posting (our side)

- [ ] Run their test suite locally (needs MongoDB with a library dump, per their dev
      setup docs) and adjust the code to what actually passes. Untested so far.
- [ ] Check Ruff formatting (their CI enforces it; see merged PR #4097).
- [ ] Decide: post the issue comment on #1016 first and offer the PR, or open both
      together. Given the "fix it in the data" stance in #1526, **comment first**.
