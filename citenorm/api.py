"""citenorm REST API, version 1. A WSGI app (standard library only).

  GET  /v1/health
  GET  /v1/resolve?q=<citation>&conventions=common|strict
  POST /v1/resolve        {"citations": [...], "conventions": "common"}   (up to 50)
  GET  /v1/explain?q=<citation>&conventions=common|strict
  GET  /v1/openapi.json

A result: {"citation", "status", "url", "ref", "convention"} where status is
  linked       url and ref are set
  unlinked     the citation can't be linked without guessing (cached)
  unavailable  Sefaria couldn't be reached; not cached, try again later
  deferred     (batch only) the budget of new lookups is used up; send those again later.
               A single GET over the limit gets HTTP 429 with Retry-After instead.

Versioning: /v1/ never changes incompatibly. New endpoints and new fields may be added;
nothing is removed or renamed. A consumer pins the git tag api-v1 (docs/RELEASING.md).

Run locally:  citenorm-api [--port 8780]      Host: any WSGI server, `citenorm.api:application`.

Configuration (environment):
  CITENORM_API_DATA   folder for the SQLite file (default ~/.cache/citenorm/api)
  CITENORM_API_KEYS   path to a file of API keys, one per line ("key  label"); a key raises the
                      client's limits. Sent as the header X-API-Key.
  CITENORM_API_SALT   salt for hashing client addresses (default derived from the data folder)
"""
import hashlib
import json
import os
import re
import sqlite3
import time
import urllib.parse

from . import __version__, code_fingerprint
from .resolve import (ResolverUnavailable, _convention_used, _resolve_common, explain,
                      CONVENTIONS)

API_VERSION = "v1"
MAX_LEN = 300                 # characters per citation
MAX_BATCH = 50                # citations per POST
NEW_PER_REQUEST = 10          # uncached lookups per request (each can take seconds)
POLITE = 0.25                 # seconds between this server's requests to Sefaria

# per minute: (all citations, new = uncached lookups, explains)
LIMITS_ANON = (300, 30, 10)
LIMITS_KEY = (3000, 120, 60)
GLOBAL_NEW = 120              # uncached lookups per minute across all clients (protects Sefaria)

DATA = os.path.expanduser(os.environ.get("CITENORM_API_DATA", "~/.cache/citenorm/api"))
DB = os.path.join(DATA, "api.sqlite3")
SALT = os.environ.get("CITENORM_API_SALT") or hashlib.sha256(DATA.encode()).hexdigest()
FP = code_fingerprint()


# ------------------------------------------------------------------ storage

def _db():
    os.makedirs(DATA, exist_ok=True)
    con = sqlite3.connect(DB, timeout=10)
    con.execute("PRAGMA journal_mode=WAL")
    # answers are keyed by the resolver's code version: a deploy never serves older answers
    con.execute("CREATE TABLE IF NOT EXISTS answers (fp TEXT, citation TEXT, url TEXT, t REAL, "
                "PRIMARY KEY (fp, citation))")
    con.execute("CREATE TABLE IF NOT EXISTS rate (bucket TEXT, minute INTEGER, n INTEGER, "
                "PRIMARY KEY (bucket, minute))")
    return con


class _Cache:
    """The resolver's cache interface over the answers table, for this code version."""

    def __init__(self, con):
        self.con = con

    def __contains__(self, k):
        return self.con.execute("SELECT 1 FROM answers WHERE fp=? AND citation=?", (FP, k)).fetchone() is not None

    def get(self, k):
        r = self.con.execute("SELECT url FROM answers WHERE fp=? AND citation=?", (FP, k)).fetchone()
        return r[0] if r else None

    def set(self, k, v):
        self.con.execute("INSERT OR REPLACE INTO answers VALUES (?,?,?,?)", (FP, k, v, time.time()))
        self.con.commit()

    def save(self):
        pass


def _take(con, bucket, limit, n=1):
    """Count n against a per-minute bucket; False if that goes over the limit (then not counted)."""
    minute = int(time.time() // 60)
    con.execute("DELETE FROM rate WHERE minute < ?", (minute - 1,))
    row = con.execute("SELECT n FROM rate WHERE bucket=? AND minute=?", (bucket, minute)).fetchone()
    used = row[0] if row else 0
    if used + n > limit:
        return False
    con.execute("INSERT INTO rate VALUES (?,?,?) ON CONFLICT(bucket, minute) DO UPDATE SET n = n + ?",
                (bucket, minute, n, n))
    con.commit()
    return True


def _keys():
    path = os.environ.get("CITENORM_API_KEYS")
    if not path or not os.path.exists(path):
        return {}
    out = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            parts = line.split(None, 1)
            if parts and not parts[0].startswith("#"):
                out[parts[0]] = (parts[1].strip() if len(parts) > 1 else "")
    return out


# ------------------------------------------------------------------ results

def display_ref(url):
    """https://www.sefaria.org/Mishneh_Torah,_Testimony.4.1 -> 'Mishneh Torah, Testimony 4:1'."""
    path = urllib.parse.unquote(url.split("sefaria.org/", 1)[-1]).split("?")[0].replace("_", " ")
    m = re.match(r"^(.*?)\.(\d.*)$", path)
    return f"{m.group(1)} {m.group(2).replace('.', ':')}" if m else path


def _result(citation, url, conventions):
    conv = _convention_used(citation, url) if url else None
    if url and conventions == "strict" and conv:
        return {"citation": citation, "status": "unlinked", "url": None, "ref": None, "convention": conv}
    if not url:
        return {"citation": citation, "status": "unlinked", "url": None, "ref": None, "convention": None}
    return {"citation": citation, "status": "linked", "url": url, "ref": display_ref(url), "convention": conv}


def _clean(q):
    return re.sub(r"\s+", " ", q or "").strip()


class _ClientError(Exception):
    def __init__(self, status, code, message, retry_after=None):
        super().__init__(message)
        self.status, self.code, self.message, self.retry_after = status, code, message, retry_after


def _resolve_many(con, who, limits, citations, conventions):
    """Resolve a list; cached answers are free, new lookups count against the limits."""
    cache = _Cache(con)
    if not _take(con, f"all:{who}", limits[0], len(citations)):
        raise _ClientError("429 Too Many Requests", "rate_limited", "too many citations this minute", 60)
    out, budget = [], NEW_PER_REQUEST
    for q in citations:
        if q in cache:
            out.append(_result(q, cache.get(q), conventions))
            continue
        if budget <= 0 or not (_take(con, f"new:{who}", limits[1]) and _take(con, "new:*", GLOBAL_NEW)):
            out.append({"citation": q, "status": "deferred", "url": None, "ref": None, "convention": None})
            continue
        budget -= 1
        try:
            url = _resolve_common(q, cache=cache, polite=POLITE)
        except ResolverUnavailable:
            out.append({"citation": q, "status": "unavailable", "url": None, "ref": None, "convention": None})
            continue
        out.append(_result(q, url, conventions))
    return out


# ------------------------------------------------------------------ HTTP

def _client(environ):
    """(id for rate limiting, limits). REMOTE_ADDR only: X-Forwarded-For is client-set."""
    key = environ.get("HTTP_X_API_KEY", "")
    if key:
        if key not in _keys():
            raise _ClientError("401 Unauthorized", "bad_key", "unknown API key")
        return "key:" + hashlib.sha256(key.encode()).hexdigest()[:16], LIMITS_KEY
    ip = environ.get("REMOTE_ADDR") or ""
    return "ip:" + hashlib.sha256((SALT + ip).encode()).hexdigest()[:16], LIMITS_ANON


def _conventions(value):
    value = value or "common"
    if value not in CONVENTIONS:
        raise _ClientError("400 Bad Request", "bad_conventions", f"conventions must be one of {list(CONVENTIONS)}")
    return value


def _one(q):
    q = _clean(q)
    if not q:
        raise _ClientError("400 Bad Request", "missing_q", "q is required")
    if len(q) > MAX_LEN:
        raise _ClientError("400 Bad Request", "too_long", f"a citation may be at most {MAX_LEN} characters")
    return q


def _send(start_response, status, obj, extra=()):
    body = b"" if status.startswith("204") else json.dumps(obj, ensure_ascii=False).encode("utf-8")
    start_response(status, [("Content-Type", "application/json; charset=utf-8"),
                            ("Content-Length", str(len(body))),
                            ("Cache-Control", "no-store"),
                            ("Access-Control-Allow-Origin", "*"),
                            ("Access-Control-Allow-Headers", "Content-Type, X-API-Key"),
                            ("Access-Control-Allow-Methods", "GET, POST, OPTIONS"),
                            ("X-Citenorm-Version", __version__),
                            ("X-Citenorm-Code", FP), *extra])
    return [body]


def _body(environ):
    try:
        n = int(environ.get("CONTENT_LENGTH") or 0)
    except ValueError:
        n = 0
    if n > 200_000:
        raise _ClientError("413 Payload Too Large", "too_large", "request body too large")
    try:
        return json.loads(environ["wsgi.input"].read(n) or b"{}")
    except ValueError:
        raise _ClientError("400 Bad Request", "bad_json", "the body must be JSON")


def application(environ, start_response):
    method = environ.get("REQUEST_METHOD", "GET")
    path = environ.get("PATH_INFO", "/") or "/"
    qs = urllib.parse.parse_qs(environ.get("QUERY_STRING", ""))
    try:
        if method == "OPTIONS":                               # CORS preflight
            return _send(start_response, "204 No Content", {})
        if path == "/v1/health":
            return _send(start_response, "200 OK", {"ok": True, "api": API_VERSION, "version": __version__,
                                                    "code": FP})
        if path == "/v1/openapi.json":
            return _send(start_response, "200 OK", openapi())
        if path == "/v1/resolve":
            con = _db()
            try:
                who, limits = _client(environ)
                if method == "GET":
                    q = _one((qs.get("q") or [""])[0])
                    conv = _conventions((qs.get("conventions") or [""])[0])
                    r = _resolve_many(con, who, limits, [q], conv)[0]
                    if r["status"] == "deferred":       # a single lookup over the limit: say so in HTTP
                        raise _ClientError("429 Too Many Requests", "rate_limited",
                                           "too many new lookups this minute", 60)
                    return _send(start_response, "200 OK", r)
                if method == "POST":
                    body = _body(environ)
                    cits = body.get("citations")
                    if not isinstance(cits, list) or not all(isinstance(c, str) for c in cits):
                        raise _ClientError("400 Bad Request", "bad_citations", "citations must be a list of strings")
                    if len(cits) > MAX_BATCH:
                        raise _ClientError("400 Bad Request", "too_many", f"at most {MAX_BATCH} citations per request")
                    cits = [_one(c) for c in cits]
                    conv = _conventions(body.get("conventions"))
                    return _send(start_response, "200 OK", {"results": _resolve_many(con, who, limits, cits, conv)})
                raise _ClientError("405 Method Not Allowed", "method", "use GET or POST")
            finally:
                con.close()
        if path == "/v1/explain":
            if method != "GET":
                raise _ClientError("405 Method Not Allowed", "method", "use GET")
            con = _db()
            try:
                who, limits = _client(environ)
                q = _one((qs.get("q") or [""])[0])
                conv = _conventions((qs.get("conventions") or [""])[0])
                if not (_take(con, f"explain:{who}", limits[2]) and _take(con, "new:*", GLOBAL_NEW)):
                    raise _ClientError("429 Too Many Requests", "rate_limited", "too many explains this minute", 60)
            finally:
                con.close()
            return _send(start_response, "200 OK", explain(q, conventions=conv, polite=POLITE))
        raise _ClientError("404 Not Found", "not_found", f"no such endpoint: {path}")
    except _ClientError as e:
        extra = [("Retry-After", str(e.retry_after))] if e.retry_after else []
        return _send(start_response, e.status, {"error": {"code": e.code, "message": e.message}}, extra)
    except Exception:
        return _send(start_response, "500 Internal Server Error",
                     {"error": {"code": "internal", "message": "internal error"}})


# ------------------------------------------------------------------ spec

def openapi():
    result = {"type": "object", "properties": {
        "citation": {"type": "string"},
        "status": {"type": "string", "enum": ["linked", "unlinked", "unavailable", "deferred"]},
        "url": {"type": ["string", "null"], "description": "Sefaria URL when linked"},
        "ref": {"type": ["string", "null"], "description": "human-readable reference when linked"},
        "convention": {"type": ["string", "null"], "enum": ["bare_section", "mishnah", "short_alias", None],
                       "description": "the Sefaria convention this reading relies on (strict mode declines it)"}}}
    q = {"name": "q", "in": "query", "required": True, "schema": {"type": "string", "maxLength": MAX_LEN}}
    conv = {"name": "conventions", "in": "query", "schema": {"type": "string", "enum": list(CONVENTIONS),
                                                             "default": "common"}}
    return {
        "openapi": "3.1.0",
        "info": {"title": "citenorm", "version": f"{API_VERSION} ({__version__})",
                 "description": "Normalize Torah citations to Sefaria references. Propose, verify, never guess. "
                                "Not developed by or affiliated with Sefaria.",
                 "license": {"name": "MIT"}},
        "paths": {
            "/v1/resolve": {
                "get": {"summary": "Resolve one citation", "parameters": [q, conv],
                        "responses": {"200": {"description": "the result",
                                              "content": {"application/json": {"schema": result}}}}},
                "post": {"summary": f"Resolve up to {MAX_BATCH} citations",
                         "requestBody": {"content": {"application/json": {"schema": {
                             "type": "object", "required": ["citations"], "properties": {
                                 "citations": {"type": "array", "items": {"type": "string"}, "maxItems": MAX_BATCH},
                                 "conventions": {"type": "string", "enum": list(CONVENTIONS)}}}}}},
                         "responses": {"200": {"description": "results, in order", "content": {"application/json": {
                             "schema": {"type": "object", "properties": {"results": {"type": "array",
                                                                                     "items": result}}}}}}}}},
            "/v1/explain": {"get": {"summary": "Why a citation was linked or left unlinked",
                                    "parameters": [q, conv],
                                    "responses": {"200": {"description": "outcome and steps"}}}},
            "/v1/health": {"get": {"summary": "Health and versions", "responses": {"200": {"description": "ok"}}}},
        },
        "components": {"securitySchemes": {"apiKey": {"type": "apiKey", "in": "header", "name": "X-API-Key"}}},
    }


def main(argv=None):
    """citenorm-api [--port 8780] [--host 127.0.0.1]: serve the API locally."""
    import argparse
    from wsgiref.simple_server import make_server
    ap = argparse.ArgumentParser(prog="citenorm-api", description="Serve the citenorm REST API (v1).")
    ap.add_argument("--port", type=int, default=8780)
    ap.add_argument("--host", default="127.0.0.1")
    a = ap.parse_args(argv)
    print(f"citenorm API {API_VERSION} on http://{a.host}:{a.port}/v1/health  (data: {DATA})")
    make_server(a.host, a.port, application).serve_forever()


if __name__ == "__main__":
    main()
