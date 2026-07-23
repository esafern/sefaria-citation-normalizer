"""Resolve a raw Anglo-Orthodox citation to a Sefaria URL: propose -> verify.

Generate candidate normalizations with rules.candidates(), ask Sefaria's
/api/name which one is a real reference, cache the answer. The rules never have
to be exactly right; Sefaria is the authority and the cache makes it
deterministic and offline-replayable.
"""
import json
import os
import time
import urllib.parse
import urllib.request

from . import rules

BASE = "https://www.sefaria.org"


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


def resolve(citation, cache=None, online=True, polite=0.0):
    """Return a Sefaria URL for `citation`, or None. Cache holds citation->url
    (or None for a known miss)."""
    citation = citation.strip()
    if cache is not None and citation in cache:
        return cache.get(citation)
    url = None
    if online:
        for cand in rules.candidates(citation):
            try:
                url = _name(cand)
            except Exception:
                url = None
                break
            if polite:
                time.sleep(polite)
            if url:
                break
    if cache is not None:
        cache.set(citation, url)
    return url
