#!/usr/bin/env python3
"""Check a running citenorm demo against known answers. Standard library only.

  python3 check_demo.py https://girsa.net/cite/       # a deployed copy
  python3 check_demo.py http://127.0.0.1:8765/         # local (python3 demo/app.py)

Exit 0 if everything matches, 1 otherwise. Each citation costs Sefaria requests
the first time (then it's cached on the server), so don't run it in a loop.
"""
import json
import sys
import time
import urllib.parse
import urllib.request

EXPECT = [   # (citation, conventions, expected status, expected ref or None)
    ("Berachos 5a", "common", "linked", "Berakhot 5a"),
    ("Hilchos Eidus 4:1", "common", "linked", "Mishneh Torah, Testimony 4:1"),
    ("Ohr HaChaim to Shemot 23:2", "common", "linked", "Or HaChaim on Exodus 23:2"),
    ('B"M 59b', "common", "linked", "Bava Metzia 59b"),
    ("Shmuel 23:8", "common", "unlinked", None),
    ("YD 289", "common", "linked", "Shulchan Arukh, Yoreh De'ah 289"),
    ("YD 289", "strict", "unlinked", None),
]


def get(base, path, raw=False):
    req = urllib.request.Request(urllib.parse.urljoin(base, path), headers={"User-Agent": "citenorm-demo-check"})
    with urllib.request.urlopen(req, timeout=120) as r:
        body = r.read()
        return (r.status, r.headers.get("Content-Type", ""), body) if raw else json.loads(body)


def main():
    base = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8765/"
    if not base.endswith("/"):
        base += "/"
    fails = []
    h = get(base, "api/health")
    print("health:", h)
    if not h.get("ok"):
        fails.append("health")
    st, ct, body = get(base, "", raw=True)
    print(f"page: {st} {ct} {len(body)} bytes")
    if st != 200 or b"Citation linker for Sefaria" not in body:
        fails.append("page")
    for img in ("powered-by-sefaria-white.png", "powered-by-sefaria-blue.png"):
        st, ct, body = get(base, "static/" + img, raw=True)
        if st != 200 or ct != "image/png":
            fails.append(img)
    for q, conv, want_status, want_ref in EXPECT:
        t = time.time()
        r = get(base, "api/resolve?" + urllib.parse.urlencode({"q": q, "conventions": conv}))
        ok = r.get("status") == want_status and r.get("ref") == want_ref
        print(f"{'ok  ' if ok else 'FAIL'} {q!r:32} {conv:6} -> {r.get('status')} {r.get('ref')}  ({time.time() - t:.1f}s)")
        if not ok:
            fails.append(q)
    print("PASS" if not fails else f"FAILED: {fails}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
