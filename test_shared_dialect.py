#!/usr/bin/env python3
"""Drift check: the CODE of citenorm/shared_dialect.py must stay identical to
its vendored twin in a second, private consumer. The module docstrings may
differ, so each copy can describe itself.

The twin's location comes from the environment (DIALECT_TWIN) or from the
local, untracked file private/dialect_twin_path. With neither, the check is
skipped, not failed: that's an environment fact (e.g. CI), not drift.

Run: python3 test_shared_dialect.py
"""
import ast
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
MINE = os.path.join(HERE, "citenorm", "shared_dialect.py")


def twin_path():
    p = os.environ.get("DIALECT_TWIN")
    local = os.path.join(HERE, "private", "dialect_twin_path")
    if not p and os.path.exists(local):
        p = open(local).read().strip()
    return os.path.expanduser(p) if p else None


def code_only(path):
    """The module's code with its docstring removed, normalized by ast."""
    tree = ast.parse(open(path, encoding="utf-8").read())
    body = tree.body
    if body and isinstance(body[0], ast.Expr) and isinstance(getattr(body[0], "value", None), ast.Constant) \
            and isinstance(body[0].value.value, str):
        body = body[1:]
    return ast.dump(ast.Module(body=body, type_ignores=[]))


theirs = twin_path()
if not theirs or not os.path.exists(theirs):
    print("  skip  no twin configured (set DIALECT_TWIN or private/dialect_twin_path)")
    sys.exit(0)
if code_only(MINE) == code_only(theirs):
    print("  ok    shared_dialect.py code identical to its twin")
    sys.exit(0)
print("  FAIL  shared_dialect.py code has DRIFTED from its twin")
sys.exit(1)
