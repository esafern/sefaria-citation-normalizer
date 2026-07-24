#!/usr/bin/env python3
"""Serialized Sefaria find-refs pass over the Mi Yodeya answer sample.

Run this ONLY after the Halachipedia mining has finished — it reuses the same
paced find_refs so Sefaria never sees more than one find-refs stream at a time.
Reads miyodeya_bodies.json (raw CC-BY-SA answer text, gitignored) and writes
miyodeya_failures.json (short citation strings find-refs detected but couldn't
resolve) — the only artifact committed, matching hp_failures.json.
"""
import json, os, re, time
from mine_wide import find_refs  # paced, cached, deterministic keys

HERE = os.path.dirname(__file__)
ascii_h = re.compile(r"[A-Za-z]")


def main():
    bodies = json.load(open(os.path.join(HERE, "miyodeya_bodies.json")))
    failed, detected = set(), 0
    for i, body in enumerate(bodies, 1):
        for chunk in [body[j:j + 3500] for j in range(0, min(len(body), 7000), 3500)]:
            try:
                for r in find_refs(chunk):
                    t = (r.get("text") or "").strip()
                    if not t or not ascii_h.search(t):
                        continue
                    detected += 1
                    if r.get("linkFailed") or not r.get("refs"):
                        failed.add(t)
            except Exception as e:
                print("  err", str(e)[:50], flush=True)
        if i % 25 == 0:
            print(f"  {i}/{len(bodies)} answers | detected {detected} | distinct failures {len(failed)}", flush=True)
            json.dump(sorted(failed), open(os.path.join(HERE, "miyodeya_failures.json"), "w"),
                      ensure_ascii=False, indent=0)
    json.dump(sorted(failed), open(os.path.join(HERE, "miyodeya_failures.json"), "w"),
              ensure_ascii=False, indent=0)
    print(f"\nDONE: {detected} detected, {len(failed)} distinct unresolved -> miyodeya_failures.json", flush=True)


if __name__ == "__main__":
    main()
