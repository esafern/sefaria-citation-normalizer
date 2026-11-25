#!/usr/bin/env python3
"""The full check: decides whether HEAD may be tagged `known-good` (docs/RELEASING.md).

  1. the offline suites: test_rules_offline.py, test_cache_offline.py, demo/test_demo_offline.py
  2. benchmark.py --strict: 0 WRONG on the 139-citation benchmark (networked; cached per code version)
  3. the web sample (data/web_pairs.json) scored at HEAD's code: no mangled WRONG outside the
     reviewed list in docs/known_wrong.json, and no request errors.
     `python3 pipeline/web_pairs.py eval` produces it (hours on a cold cache, minutes on a warm one).

Run: python3 release_check.py           exit 0 = HEAD may be tagged known-good
     python3 release_check.py --tag     ...and move the tag (needs the repository admin's rights)
"""
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
from citenorm import code_fingerprint  # noqa: E402


def run(*cmd):
    r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    tail = (r.stdout.strip().splitlines() or [""])[-1]
    return r.returncode == 0, tail


def main():
    ok_all = True
    for cmd in (["python3", "test_rules_offline.py"], ["python3", "test_cache_offline.py"],
                ["python3", "demo/test_demo_offline.py"], ["python3", "benchmark.py", "--strict"]):
        ok, tail = run(*cmd)
        print(f"{'ok  ' if ok else 'FAIL'} {' '.join(cmd[1:]):32} {tail[:100]}")
        ok_all &= ok

    meta_path = os.path.join(ROOT, "data", "web_pairs_scored.meta.json")
    scored_path = os.path.join(ROOT, "data", "web_pairs_scored.json")
    fp = code_fingerprint()
    meta = json.load(open(meta_path, encoding="utf-8")) if os.path.exists(meta_path) else {}
    if meta.get("code_fingerprint") != fp:
        print(f"FAIL web sample: scored with code {meta.get('code_fingerprint')}, HEAD is {fp}; "
              f"run python3 pipeline/web_pairs.py eval")
        ok_all = False
    else:
        known = {(w["raw"], w["ours"]) for w in json.load(open(os.path.join(ROOT, "docs", "known_wrong.json"),
                                                                encoding="utf-8"))["mangled"]}
        rows = json.load(open(scored_path, encoding="utf-8"))
        wrong = [(r["raw"], r.get("ours")) for r in rows if not r["clean"] and r.get("outcome") == "WRONG"]
        new = [w for w in wrong if w not in known]
        errs = sum(meta.get("errors", {}).values())
        ok = not new and not errs
        print(f"{'ok  ' if ok else 'FAIL'} web sample (mangled)            {len(wrong)} WRONG, "
              f"{len(new)} not in docs/known_wrong.json, {errs} request errors")
        for w in new:
            print(f"       new WRONG: {w[0]!r} -> {w[1]}")
        ok_all &= ok

    head = subprocess.run(["git", "rev-parse", "--short=8", "HEAD"], cwd=ROOT,
                          capture_output=True, text=True).stdout.strip()
    dirty = subprocess.run(["git", "status", "--porcelain", "--", "citenorm", "demo"], cwd=ROOT,
                           capture_output=True, text=True).stdout.strip()
    if dirty:
        print("FAIL uncommitted changes in citenorm/ or demo/")
        ok_all = False
    print(f"\n{'PASS' if ok_all else 'NOT READY'}: {head} (code {fp})")
    if ok_all and "--tag" in sys.argv:
        subprocess.run(["git", "tag", "-f", "-a", "known-good", "-m",
                        f"full check passed: code {fp}"], cwd=ROOT, check=True)
        subprocess.run(["git", "push", "-f", "origin", "known-good"], cwd=ROOT, check=True)
        print("known-good ->", head)
    return 0 if ok_all else 1


if __name__ == "__main__":
    sys.exit(main())
