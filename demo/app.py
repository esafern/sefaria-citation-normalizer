"""citenorm demo: a small WSGI app (standard library only).

  GET  /                  the page (static/index.html)
  GET  /static/<file>     the badge images
  GET  /api/resolve?q=...&conventions=common|strict
                          one citation -> {citation, status, url, ref, convention, cached}
  GET  /api/health        {ok, version}

One citation per request (the page loops), so a request takes seconds, not minutes.

Built for shared hosting where workers are forked and share no memory (LiteSpeed /
Passenger): the answer cache and the rate limits live in one SQLite file under
CITENORM_DEMO_DATA (default ~/citenorm_demo_data), which also holds citenorm's
download cache (Sefaria's title list).

Privacy: no request is logged by this app; the cache keeps citations and their
answers only (no IP, no time per visitor); rate limiting keeps a salted hash of the
IP for two minutes.
"""
import hashlib
import json
import mimetypes
import os
import re
import sqlite3
import sys
import time
import urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
# the archive ships citenorm/ next to this file; in the repository it is one level up
for p in (os.path.dirname(HERE), HERE):
    if p not in sys.path:
        sys.path.insert(0, p)

DATA = os.path.expanduser(os.environ.get("CITENORM_DEMO_DATA", "~/citenorm_demo_data"))
os.makedirs(DATA, exist_ok=True)
os.environ.setdefault("CITENORM_CACHE", os.path.join(DATA, "citenorm"))

from citenorm import __version__                       # noqa: E402
from citenorm.resolve import _resolve_common, _convention_used  # noqa: E402

DB = os.path.join(DATA, "demo.sqlite3")
STATIC = os.path.join(HERE, "static")
SALT = os.environ.get("CITENORM_DEMO_SALT") or hashlib.sha256(DATA.encode()).hexdigest()

MAX_LEN = 200            # characters per citation
PER_IP_NEW = 20          # uncached citations per visitor per minute (each costs Sefaria requests)
PER_IP_ALL = 120         # all citations per visitor per minute
GLOBAL_NEW = 60          # uncached citations per minute across all visitors
POLITE = 0.25            # seconds between this app's requests to Sefaria


def _db():
    con = sqlite3.connect(DB, timeout=10)
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("CREATE TABLE IF NOT EXISTS answers (citation TEXT PRIMARY KEY, url TEXT, t REAL)")
    con.execute("CREATE TABLE IF NOT EXISTS rate (bucket TEXT, minute INTEGER, n INTEGER, "
                "PRIMARY KEY (bucket, minute))")
    return con


class _SqliteCache:
    """The resolver's cache interface (get / in / set / save) over the answers table."""

    def __init__(self, con):
        self.con = con

    def __contains__(self, k):
        return self.con.execute("SELECT 1 FROM answers WHERE citation=?", (k,)).fetchone() is not None

    def get(self, k):
        r = self.con.execute("SELECT url FROM answers WHERE citation=?", (k,)).fetchone()
        return r[0] if r else None

    def set(self, k, v):
        self.con.execute("INSERT OR REPLACE INTO answers VALUES (?,?,?)", (k, v, time.time()))
        self.con.commit()

    def save(self):
        pass


def _take(con, bucket, limit):
    """Count one request against a per-minute bucket; False if over the limit."""
    minute = int(time.time() // 60)
    con.execute("DELETE FROM rate WHERE minute < ?", (minute - 1,))
    con.execute("INSERT INTO rate VALUES (?,?,1) ON CONFLICT(bucket, minute) DO UPDATE SET n = n + 1",
                (bucket, minute))
    con.commit()
    n = con.execute("SELECT n FROM rate WHERE bucket=? AND minute=?", (bucket, minute)).fetchone()[0]
    return n <= limit


def display_ref(url):
    """https://www.sefaria.org/Mishneh_Torah,_Testimony.4.1 -> 'Mishneh Torah, Testimony 4:1'."""
    path = urllib.parse.unquote(url.split("sefaria.org/", 1)[-1]).split("?")[0].replace("_", " ")
    m = re.match(r"^(.*?)\.(\d.*)$", path)
    if not m:
        return path
    return f"{m.group(1)} {m.group(2).replace('.', ':')}"


def _json(start_response, obj, status="200 OK"):
    body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
    start_response(status, [("Content-Type", "application/json; charset=utf-8"),
                            ("Cache-Control", "no-store"),
                            ("Content-Length", str(len(body)))])
    return [body]


def _static(start_response, name):
    path = os.path.normpath(os.path.join(STATIC, name))
    if not path.startswith(STATIC + os.sep) or not os.path.isfile(path):
        start_response("404 Not Found", [("Content-Type", "text/plain")])
        return [b"not found"]
    body = open(path, "rb").read()
    ctype = mimetypes.guess_type(path)[0] or "application/octet-stream"
    if ctype.startswith("text/"):
        ctype += "; charset=utf-8"
    # the page itself must never be cached (an update would go unseen); the images may be
    cache = "no-cache" if name.endswith(".html") else "public, max-age=86400"
    start_response("200 OK", [("Content-Type", ctype), ("Content-Length", str(len(body))),
                              ("Cache-Control", cache),
                              ("X-Content-Type-Options", "nosniff")])
    return [body]


def resolve_one(q, conventions, ip):
    q = re.sub(r"\s+", " ", q or "").strip()
    if not q:
        return {"error": "empty"}, "400 Bad Request"
    if len(q) > MAX_LEN:
        return {"error": f"longer than {MAX_LEN} characters"}, "400 Bad Request"
    con = _db()
    try:
        who = hashlib.sha256((SALT + ip).encode()).hexdigest()[:16]
        if not _take(con, "all:" + who, PER_IP_ALL):
            return {"error": "too many requests; please wait a minute"}, "429 Too Many Requests"
        cache = _SqliteCache(con)
        cached = q in cache
        if not cached and not (_take(con, "new:" + who, PER_IP_NEW) and _take(con, "new:*", GLOBAL_NEW)):
            return {"error": "busy; please wait a minute"}, "429 Too Many Requests"
        try:
            url = _resolve_common(q, cache=cache, polite=POLITE)
        except Exception:
            return {"citation": q, "status": "error",
                    "error": "Sefaria didn't answer; please try again shortly"}, "200 OK"
        conv = _convention_used(q, url) if url else None
        if url and conventions == "strict" and conv:
            return {"citation": q, "status": "unlinked", "convention": conv, "cached": cached}, "200 OK"
        if not url:
            return {"citation": q, "status": "unlinked", "cached": cached}, "200 OK"
        return {"citation": q, "status": "linked", "url": url, "ref": display_ref(url),
                "convention": conv, "cached": cached}, "200 OK"
    finally:
        con.close()


def application(environ, start_response):
    path = environ.get("PATH_INFO", "/") or "/"
    method = environ.get("REQUEST_METHOD", "GET")
    if method not in ("GET", "HEAD"):
        start_response("405 Method Not Allowed", [("Allow", "GET")])
        return [b""]
    if path == "" and environ.get("SCRIPT_NAME"):      # mounted at /cite: send /cite to /cite/
        start_response("301 Moved Permanently", [("Location", environ["SCRIPT_NAME"] + "/")])
        return [b""]
    if path in ("/", "/index.html"):
        return _static(start_response, "index.html")
    if path.startswith("/static/"):
        return _static(start_response, path[len("/static/"):])
    if path == "/api/health":
        return _json(start_response, {"ok": True, "version": __version__})
    if path == "/api/resolve":
        qs = urllib.parse.parse_qs(environ.get("QUERY_STRING", ""))
        q = (qs.get("q") or [""])[0]
        conv = (qs.get("conventions") or ["common"])[0]
        conv = conv if conv in ("common", "strict") else "common"
        # REMOTE_ADDR only: X-Forwarded-For is set by the client and can be anything, so
        # trusting it let a visitor dodge the per-visitor limits (girsa-demo-operator's LOW on
        # 2f6a5cd6). On girsa.net's host REMOTE_ADDR is the visitor's real address.
        ip = environ.get("REMOTE_ADDR") or ""
        obj, status = resolve_one(q, conv, ip)
        return _json(start_response, obj, status)
    start_response("404 Not Found", [("Content-Type", "text/plain")])
    return [b"not found"]


if __name__ == "__main__":                     # local preview: python3 demo/app.py [port]
    from wsgiref.simple_server import make_server
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8765
    print(f"http://127.0.0.1:{port}/  (data in {DATA})")
    make_server("127.0.0.1", port, application).serve_forever()
