#!/usr/bin/env python3
"""Coverage of the deterministic rules against the verified dataset.

Reports what fraction of known-resolvable citations the rules recover — the
'tier 1 ceiling'. Uses the resolver cache so reruns are cheap. Online.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from normalizer.resolve import resolve, Cache

data = json.load(open(os.path.join(os.path.dirname(__file__), "data", "citation_dataset.json")))
cache = Cache(os.path.join(os.path.dirname(__file__), "pipeline", "verify_cache.json"))

hit, misses = 0, []
for d in data:
    if resolve(d["raw"], cache=cache, polite=0.03):
        hit += 1
    else:
        misses.append(d["raw"])
cache.save()

pct = 100 * hit // len(data)
print(f"rules resolve {hit}/{len(data)} of the verified corpus ({pct}%)")
if "--misses" in sys.argv:
    print("\nunresolved (the knowledge tier):")
    for m in misses:
        print("  ", m)
