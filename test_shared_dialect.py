#!/usr/bin/env python3
"""Diff-check: normalizer/shared_dialect.py must stay byte-identical to its
vendored twin in the blog repo. Run: python3 test_shared_dialect.py

Why a byte-compare instead of a live cross-repo import: the two repos'
Sefaria linkers evolve on independent, uncoordinated schedules (see
INTEGRATION-PLAN.md), so a live dependency would let a change here silently
break the blog's build, discovered only when the blog next runs. Vendoring
plus this check makes drift loud instead of silent.

This only catches drift when THIS repo's test suite runs (an identical
check lives in the blog repo too, for the same reason from its side) — it
is skipped, not failed, if the sibling repo isn't checked out locally (e.g.
CI on just this repo), since that's an environment fact, not drift.
"""
import filecmp
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
MINE = os.path.join(HERE, "normalizer", "shared_dialect.py")
SIBLING = os.environ.get(
    "BLOG_REPO",
    os.path.join(HERE, "..", "rav-shvat-blog"),
)
THEIRS = os.path.join(SIBLING, "pipeline", "sefaria_linker", "shared_dialect.py")

if not os.path.exists(THEIRS):
    print(f"  skip  sibling repo not found at {THEIRS} "
          f"(set BLOG_REPO to check against a different checkout)")
    sys.exit(0)

if filecmp.cmp(MINE, THEIRS, shallow=False):
    print(f"  ok    shared_dialect.py identical to {THEIRS}")
    sys.exit(0)

print(f"  FAIL  shared_dialect.py has DRIFTED from {THEIRS}")
print("        the two repos' dialect layers were supposed to stay vendored")
print("        byte-identical — see INTEGRATION-PLAN.md for how to reconcile.")
sys.exit(1)
