#!/usr/bin/env python3
"""Offline tests for the REST API (citenorm/api.py), with a stand-in for Sefaria.

Run: python3 test_api_offline.py
"""
import io
import json
import os
import sys
import tempfile

D = tempfile.mkdtemp(prefix="citenorm_api_test_")
os.environ["CITENORM_API_DATA"] = os.path.join(D, "api")
os.environ["CITENORM_CACHE"] = os.path.join(D, "cache")
keyfile = os.path.join(D, "keys.txt")
open(keyfile, "w").write("good-key  test client\n")
os.environ["CITENORM_API_KEYS"] = keyfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from citenorm import resolve as R  # noqa: E402
from citenorm import api  # noqa: E402

KNOWN = {"Berachot 5a": "Berakhot.5a", "YD 289": "Shulchan_Arukh,_Yoreh_De'ah.289"}
TITLES = {"books": [f"Work {i}" for i in range(12000)] + ["Berakhot"]}
state = {"down": False, "calls": 0}


def fake(path, timeout=15):
    state["calls"] += 1
    if state["down"]:
        raise OSError("network down")
    if path == "/api/index/titles":
        return TITLES
    q = __import__("urllib.parse").parse.unquote(path[len("/api/name/"):]).split("?")[0]
    if q in KNOWN:
        return {"is_ref": True, "url": KNOWN[q], "ref": q}
    return {"is_ref": False, "completions": [], "completion_objects": []}


R._get_json = fake
api.POLITE = 0


def call(method, path, query="", body=None, remote="198.51.100.1", headers=None):
    raw = json.dumps(body).encode() if body is not None else b""
    env = {"REQUEST_METHOD": method, "PATH_INFO": path, "QUERY_STRING": query, "REMOTE_ADDR": remote,
           "CONTENT_LENGTH": str(len(raw)), "wsgi.input": io.BytesIO(raw)}
    for k, v in (headers or {}).items():
        env["HTTP_" + k.upper().replace("-", "_")] = v
    out = {}

    def start(status, hdrs):
        out["status"], out["headers"] = status, dict(hdrs)
    data = b"".join(api.application(env, start))
    return int(out["status"][:3]), out["headers"], (json.loads(data) if data else None)


fails = []


def check(name, cond):
    print(("ok   " if cond else "FAIL ") + name)
    if not cond:
        fails.append(name)


st, h, b = call("GET", "/v1/health")
check("health", st == 200 and b["api"] == "v1" and b["code"] == api.FP)
st, h, b = call("GET", "/v1/resolve", "q=Berachos%205a")
check("resolve: linked", st == 200 and b["status"] == "linked" and b["ref"] == "Berakhot 5a")
check("CORS header on responses", h.get("Access-Control-Allow-Origin") == "*")
st, h, b = call("GET", "/v1/resolve", "q=Nothing%20Here%2012")
check("resolve: unlinked", b["status"] == "unlinked" and b["url"] is None)
st, h, b = call("GET", "/v1/resolve", "q=YD%20289")
check("convention reported in common mode", b["status"] == "linked" and b["convention"] == "bare_section")
st, h, b = call("GET", "/v1/resolve", "q=YD%20289&conventions=strict")
check("strict declines the convention", b["status"] == "unlinked" and b["convention"] == "bare_section")

n0 = state["calls"]
call("GET", "/v1/resolve", "q=Berachos%205a")
check("a cached answer makes no request", state["calls"] == n0)

st, h, b = call("POST", "/v1/resolve", body={"citations": [f"Unknown Work {i}" for i in range(api.NEW_PER_REQUEST + 3)]})
statuses = [r["status"] for r in b["results"]]
check("batch: new lookups beyond the per-request budget are deferred",
      statuses.count("deferred") == 3 and statuses[:api.NEW_PER_REQUEST] == ["unlinked"] * api.NEW_PER_REQUEST)

state["down"] = True
st, h, b = call("GET", "/v1/resolve", "q=Berachos%206a")
check("outage -> unavailable", b["status"] == "unavailable")
state["down"] = False
check("outage not cached", "Berachos 6a" not in api._Cache(api._db()))

old_fp = api.FP
api.FP = "other-code"
check("cache is per code version", "Berachos 5a" not in api._Cache(api._db()))
api.FP = old_fp

spoof = [call("GET", "/v1/resolve", f"q=Fresh%20{i}", remote="198.51.100.50",
              headers={"X-Forwarded-For": f"203.0.113.{i}"})[0] for i in range(api.LIMITS_ANON[1] + 3)]
check("per-client limit by REMOTE_ADDR, X-Forwarded-For ignored", 429 in spoof)
st, h, b = call("GET", "/v1/resolve", "q=Fresh%201", remote="198.51.100.50")
check("429 says when to retry", st in (200, 429) and (st == 200 or h.get("Retry-After") == "60"))

st, h, b = call("GET", "/v1/resolve", "q=Berachos%205a", headers={"X-API-Key": "wrong"})
check("unknown API key -> 401", st == 401 and b["error"]["code"] == "bad_key")
st, h, b = call("GET", "/v1/resolve", "q=Berachos%205a", headers={"X-API-Key": "good-key"})
check("known API key works", st == 200 and b["status"] == "linked")

for q, code in (("", "missing_q"), ("q=" + "x" * (api.MAX_LEN + 1), "too_long"),
                ("q=a&conventions=bogus", "bad_conventions")):
    st, h, b = call("GET", "/v1/resolve", q)
    check(f"400 {code}", st == 400 and b["error"]["code"] == code)
st, h, b = call("POST", "/v1/resolve", body={"citations": ["a"] * (api.MAX_BATCH + 1)})
check("400 too_many", st == 400 and b["error"]["code"] == "too_many")
st, h, b = call("POST", "/v1/resolve", body={"citations": "Berachos 5a"})
check("400 bad_citations", st == 400 and b["error"]["code"] == "bad_citations")
st, h, b = call("GET", "/v2/resolve")
check("404 for an unknown version", st == 404)
st, h, b = call("OPTIONS", "/v1/resolve")
check("CORS preflight: 204, no body", st == 204 and b is None and "X-API-Key" in h.get("Access-Control-Allow-Headers", ""))

st, h, b = call("GET", "/v1/explain", "q=Berachos%205a")
check("explain", st == 200 and b["outcome"] == "linked" and b["steps"])
st, h, b = call("GET", "/v1/openapi.json")
check("openapi spec", st == 200 and b["openapi"].startswith("3.") and "/v1/resolve" in b["paths"])

print(f"{'PASS' if not fails else f'{len(fails)} FAILED'}")
sys.exit(1 if fails else 0)
