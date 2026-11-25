#!/usr/bin/env python3
"""Offline tests for the resolver's files and failure handling (no network).

From girsa-demo-operator's findings on demo 2f6a5cd6 (2026-11-25): on a host whose
locale isn't UTF-8, the title list was written as a 100-byte stub; every worker then read
the stub as an empty index, and answers computed without it were cached as "unlinked" for
good. Each case runs in a subprocess under LC_ALL=C with Python's UTF-8 mode off, the
host's conditions, with a stand-in for Sefaria's API.

Run: python3 test_cache_offline.py
"""
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))

PRELUDE = r'''
import json, os, sys
sys.path.insert(0, HERE)
from citenorm import resolve as R
FAKE = {"books": ["B\u2019resh."] + [f"Work Number {i}" for i in range(12000)] + ["Berakhot"]}
calls = {"titles": 0}
def fake_get_json(path, timeout=15):
    if path == "/api/index/titles":
        calls["titles"] += 1
        return FAKE
    raise OSError("network down")
R._get_json = fake_get_json
'''

CASES = {
    "titles survive a non-UTF-8 locale": r'''
idx = R._title_index()
p = R._titles_path()
assert os.path.getsize(p) > 100000, os.path.getsize(p)
with open(p, encoding="utf-8") as f:
    assert len(json.load(f)["books"]) == len(FAKE["books"])
assert idx, "index empty"
''',
    "a stub titles.json is replaced, not used": r'''
open(R._titles_path(), "w").write('{"books": ["B')       # the 100-byte stub, broken JSON
titles = R._load_titles()
assert len(titles) == len(FAKE["books"]) and calls["titles"] == 1
''',
    "a too-small titles.json is replaced": r'''
with open(R._titles_path(), "w", encoding="utf-8") as f:
    json.dump({"books": ["Berakhot"]}, f)
assert len(R._load_titles()) == len(FAKE["books"]) and calls["titles"] == 1
''',
    "no title list -> error, never an empty index": r'''
def down(path, timeout=15):
    raise OSError("network down")
R._get_json = down
try:
    R._title_index()
    raise SystemExit("expected ResolverUnavailable")
except R.ResolverUnavailable:
    pass
assert R._TITLE_INDEX is None, "a failure must not be remembered"
''',
    "an outage is not cached as unlinked": r'''
c = R.Cache(os.path.join(os.environ["CITENORM_CACHE"], "answers.json"))
try:
    R.resolve("Berachos 5a", cache=c, polite=0)
    raise SystemExit("expected ResolverUnavailable")
except R.ResolverUnavailable:
    pass
assert "Berachos 5a" not in c, "an outage was cached"
c.save()
''',
    "the cache file is UTF-8 and written atomically": r'''
p = os.path.join(os.environ["CITENORM_CACHE"], "answers.json")
c = R.Cache(p); c.set("B\u2019rakhot 2a", None); c.set("Berakhot 2a", "https://www.sefaria.org/Berakhot.2a"); c.save()
assert R.Cache(p).get("Berakhot 2a").endswith("Berakhot.2a") and "B\u2019rakhot 2a" in R.Cache(p)
assert not [f for f in os.listdir(os.environ["CITENORM_CACHE"]) if ".tmp." in f]
''',
    "the demo reports an outage and caches nothing": r'''
os.environ["CITENORM_DEMO_DATA"] = os.environ["CITENORM_CACHE"]
sys.path[:0] = [os.path.join(HERE, "demo"), HERE]       # the repository, or the demo archive
import app, sqlite3
obj, status = app.resolve_one("Hilchos Eidus 4:1", "common", "198.51.100.9")
assert obj.get("status") == "error", obj
n = sqlite3.connect(app.DB).execute("SELECT COUNT(*) FROM answers").fetchone()[0]
assert n == 0, f"{n} answers cached during an outage"
''',
}


def main():
    env = dict(os.environ, LC_ALL="C", LANG="C")
    env.pop("PYTHONUTF8", None)
    fails = 0
    for name, body in CASES.items():
        with tempfile.TemporaryDirectory() as d:
            env["CITENORM_CACHE"] = d
            code = f"HERE = {HERE!r}\n" + PRELUDE + body
            r = subprocess.run([sys.executable, "-X", "utf8=0", "-c", code], env=env,
                               capture_output=True, text=True)
            ok = r.returncode == 0
            fails += not ok
            print(("ok   " if ok else "FAIL ") + name)
            if not ok:
                print("     " + (r.stderr or r.stdout).strip().splitlines()[-1])
    print(f"{len(CASES) - fails}/{len(CASES)} passed")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
