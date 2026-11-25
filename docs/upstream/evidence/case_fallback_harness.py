"""Offline stand-in for the proposed Library.recase_title_prefix(), run against
Sefaria's real title list. Node identity is approximated (all case-variants of a
title assumed to be the same node; 40/40 sampled groups confirmed live)."""
import json, re, time, urllib.request, urllib.parse, sys
titles = json.load(open('/tmp/sefsrc/titles.json'))['books']
exact = set(titles)
cf = {}
for t in titles:
    cf.setdefault(t.casefold(), t)   # prefer first-seen casing; ambiguity check needs real nodes

def clean(tref):  # mirrors Ref.__clean_tref for lang=en
    tref = tref.strip().replace("_", " ").replace(":", ".")
    return tref[:1].upper() + tref[1:]

def recase_title_prefix(tref):
    for l in range(len(tref), 0, -1):
        if l != len(tref) and tref[l] not in " ,.:_":
            continue
        hit = cf.get(tref[:l].casefold())
        if hit:
            return None if hit == tref[:l] else hit + tref[l:]
    return None

def live(q):
    u = "https://www.sefaria.org/api/name/" + urllib.parse.quote(q) + "?limit=0"
    d = json.load(urllib.request.urlopen(u, timeout=30)); time.sleep(0.6)
    return d.get("ref") if d.get("is_ref") else None
