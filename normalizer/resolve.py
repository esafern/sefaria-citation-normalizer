"""Resolve a raw Anglo-Orthodox citation to a Sefaria URL: propose -> verify.

Generate candidate normalizations with rules.candidates(), ask Sefaria's
/api/name which one is a real reference, cache the answer. The rules never have
to be exactly right; Sefaria is the authority and the cache makes it
deterministic and offline-replayable.

A second pass canonicalizes the tractate/parsha name itself via Sefaria's own
/api/name completions ("Yerushalmi Brachot" -> ask Sefaria what "Brachot"
canonicalizes to -> "Berakhot" -> recompose as "Jerusalem Talmud Berakhot"),
instead of a hand-maintained spelling list: such a list can never keep up with
every Anglo transliteration a writer might use (Brachot/Brachos/B'rachot/...),
but Sefaria's own alt-title data already covers what the rules layer misses.
Ported from rav-shvat-blog's pipeline/sefaria_linker/resolver.py, which had
the same idea but a bug that silently excluded every Tosefta/Mishnah
candidate from ever reaching it (fixed here and there — see INTEGRATION-PLAN.md).
"""
import json
import os
import re
import time
import urllib.parse
import urllib.request

from . import rules
from . import shared_dialect

BASE = "https://www.sefaria.org"

# The renamed corpus-prefix forms rules.candidates() can produce (the
# replacement side of shared_dialect.PREFIXES), longest first so a shorter
# prefix can't shadow a longer one it's a substring of.
_RENAMED_PREFIXES = sorted({repl for _, repl in shared_dialect.PREFIXES}, key=len, reverse=True)


class Cache:
    def __init__(self, path=None):
        self.path = path
        self.data = json.load(open(path)) if path and os.path.exists(path) else {}
        self._dirty = False

    def get(self, k):
        return self.data.get(k)

    def __contains__(self, k):
        return k in self.data

    def set(self, k, v):
        if self.data.get(k) != v:
            self.data[k] = v
            self._dirty = True

    def save(self):
        if self.path and self._dirty:
            json.dump(self.data, open(self.path, "w"), ensure_ascii=False, indent=1, sort_keys=True)
            self._dirty = False


def _name(q, timeout=15):
    d = json.loads(urllib.request.urlopen(
        BASE + "/api/name/" + urllib.parse.quote(q), timeout=timeout).read())
    if d.get("is_ref") and d.get("url"):
        return BASE + "/" + d["url"].lstrip("/")
    return None


def _name_candidates(work, limit=5, timeout=15):
    """Candidate canonical titles for a bare work name, best-first: an exact
    ref match, then typed ref completions (skipping AuthorTopic/Topic
    entries, e.g. "Bereshit" the Topic vs "Bereshit Rabbah" the text), then
    bare completion strings as a last resort (older API shape)."""
    d = json.loads(urllib.request.urlopen(
        BASE + "/api/name/" + urllib.parse.quote(work), timeout=timeout).read())
    out = []

    def add(x):
        if x and x not in out:
            out.append(x)

    if d.get("is_ref") and d.get("ref"):
        add(d["ref"])
    for o in (d.get("completion_objects") or []):
        if o.get("type") == "ref":
            add(o.get("title"))
    for c in (d.get("completions") or []):
        add(c)
    return out[:limit]


def _resolve_via_canonicalization(cands, polite):
    """Second-pass fallback: split a candidate into (corpus prefix, work
    head, numbers), ask Sefaria to canonicalize just the head, recompose."""
    for cand in cands:
        m = re.match(r"^(?P<head>.*?[A-Za-z])\s+(?P<nums>\d[\d:,.\s\-ab]*)$", cand)
        if not m:
            continue
        head, nums = m.group("head"), m.group("nums").strip()
        prefix = ""
        for pre in _RENAMED_PREFIXES:
            if head.startswith(pre):
                prefix, head = pre, head[len(pre):]
                break
        else:
            # No recognized (already-renamed) prefix found. If `head` still
            # carries a raw, un-renamed corpus qualifier ("Yerushalmi
            # Brachot"), a renamed sibling candidate exists elsewhere in
            # `cands` and gets processed correctly on its own turn instead;
            # canonicalizing this one whole would silently drop the
            # qualifier and risk a mislink (Yerushalmi Brachot -> Mishnah
            # Berakhot). This check must come after (not instead of) the
            # loop above: Tosefta/Mishnah/Mishna's PREFIXES rewrite only
            # normalizes a comma, so their "already renamed" and "still
            # raw" forms are the same string — checking this first would
            # wrongly exclude them too.
            if any(re.search(pat, cand, re.I) for pat, _ in shared_dialect.PREFIXES):
                continue
        try:
            canons = _name_candidates(head)
        except Exception:
            return None
        for canon in canons:
            if not canon or canon == head:
                continue
            try:
                url = _name(f"{prefix}{canon} {nums}")
            except Exception:
                return None
            if polite:
                time.sleep(polite)
            if url:
                return url
    return None


def resolve(citation, cache=None, online=True, polite=0.0):
    """Return a Sefaria URL for `citation`, or None. Cache holds citation->url
    (or None for a known miss)."""
    citation = citation.strip()
    if cache is not None and citation in cache:
        return cache.get(citation)
    url = None
    if online:
        cands = rules.candidates(citation)
        for cand in cands:
            try:
                url = _name(cand)
            except Exception:
                url = None
                break
            if polite:
                time.sleep(polite)
            if url:
                break
        if not url:
            url = _resolve_via_canonicalization(cands, polite)
    if cache is not None:
        cache.set(citation, url)
    return url
