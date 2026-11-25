#!/usr/bin/env python3
"""Offline checks of the demo app (no network): the per-visitor limit can't be dodged
with X-Forwarded-For, and the page and static files are served with the right headers.

Run: python3 demo/test_demo_offline.py
"""
import os
import sqlite3
import sys
import tempfile
import time

os.environ["CITENORM_DEMO_DATA"] = tempfile.mkdtemp(prefix="citenorm_demo_test_")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import app  # noqa: E402

fails = []

# a cached answer, so no request goes to Sefaria
con = app._db()
con.execute("INSERT OR REPLACE INTO answers VALUES (?,?,?)",
            ("Berachos 5a", "https://www.sefaria.org/Berakhot.5a", time.time()))
con.commit()
con.close()


def call(path, query="", remote="198.51.100.7", xff=None):
    env = {"REQUEST_METHOD": "GET", "PATH_INFO": path, "QUERY_STRING": query, "REMOTE_ADDR": remote}
    if xff:
        env["HTTP_X_FORWARDED_FOR"] = xff
    out = {}

    def start(status, headers):
        out["status"], out["headers"] = status, dict(headers)
    body = b"".join(app.application(env, start))
    return out["status"], out["headers"], body


# 1. a spoofed X-Forwarded-For per request must not reset the visitor's count
codes = [call("/api/resolve", "q=Berachos%205a", xff=f"203.0.113.{i % 250}")[0][:3]
         for i in range(app.PER_IP_ALL + 5)]
if "429" not in codes:
    fails.append("per-visitor limit dodged with X-Forwarded-For")
# 2. another real address is counted separately
if call("/api/resolve", "q=Berachos%205a", remote="198.51.100.8")[0][:3] != "200":
    fails.append("a different REMOTE_ADDR was limited")
# 3. headers: the page is never cached, images may be
st, h, _ = call("/")
if not st.startswith("200") or h.get("Cache-Control") != "no-cache":
    fails.append(f"page headers: {st} {h.get('Cache-Control')}")
st, h, _ = call("/static/powered-by-sefaria-white.png")
if not st.startswith("200") or h.get("Content-Type") != "image/png":
    fails.append(f"badge: {st} {h.get('Content-Type')}")
# 4. no path traversal
if not call("/static/../app.py")[0].startswith("404"):
    fails.append("path traversal")

for f in fails:
    print("FAIL", f)
print("demo offline checks:", "PASS" if not fails else f"{len(fails)} failed")
sys.exit(1 if fails else 0)
