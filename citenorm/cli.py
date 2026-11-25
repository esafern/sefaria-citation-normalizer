"""Command line: citenorm "Berachos 5a" "SA OC 271:1"   (or one citation per line on stdin)

Prints one tab-separated line per citation: the citation, then the Sefaria URL,
"-" when it can't be linked without guessing, or "?" when Sefaria couldn't be
reached (not cached; exit status 1). --explain prints, for each citation, the spellings
tried and every suggestion accepted or rejected, with the reason.
"""
import argparse
import json
import os
import sys

from . import __version__
from .resolve import Cache, resolve, explain, CONVENTIONS, ResolverUnavailable, _cache_dir


def main(argv=None):
    ap = argparse.ArgumentParser(
        prog="citenorm",
        description="Normalize messy Torah citations to Sefaria links (propose candidates, verify with Sefaria).")
    ap.add_argument("citations", nargs="*", help="citations; if none, read one per line from stdin")
    ap.add_argument("--conventions", choices=CONVENTIONS, default="common",
                    help="'strict' leaves bare Shulchan Arukh sections, tractate+chapter:mishnah and "
                         "2-3 letter aliases unlinked instead of following Sefaria's convention")
    ap.add_argument("--json", action="store_true", help="print JSON lines instead of TSV")
    ap.add_argument("--explain", action="store_true",
                    help="show why each citation was linked or left unlinked: the spellings tried, "
                         "the suggestions accepted or rejected (and why). Ignores the cache.")
    ap.add_argument("--cache", default=os.path.join(_cache_dir(), "resolve.json"),
                    help="answer cache (default: ~/.cache/citenorm/resolve.json; '' to disable)")
    ap.add_argument("--polite", type=float, default=0.3,
                    help="seconds to wait between requests to Sefaria (default 0.3)")
    ap.add_argument("--version", action="version", version=f"citenorm {__version__}")
    a = ap.parse_args(argv)

    cits = a.citations or [line.strip() for line in sys.stdin if line.strip()]
    if a.explain:
        return _explain_all(cits, a)
    cache = Cache(a.cache) if a.cache else None
    try:
        failed = 0
        for c in cits:
            try:
                url = resolve(c, cache=cache, polite=a.polite, conventions=a.conventions)
                err = None
            except ResolverUnavailable as e:
                url, err, failed = None, str(e), failed + 1
                print(f"citenorm: {c!r}: Sefaria unreachable ({e})", file=sys.stderr)
            if a.json:
                print(json.dumps({"citation": c, "url": url, **({"error": err} if err else {})},
                                 ensure_ascii=False))
            else:
                print(f"{c}\t{url or ('?' if err else '-')}")
            sys.stdout.flush()
    finally:
        if cache is not None:
            cache.save()
    return 1 if failed else 0


def _explain_all(cits, a):
    """--explain: resolve each citation fresh (no cache) and print the trace. The text view
    is a summary; --json has every step."""
    failed = 0
    for c in cits:
        r = explain(c, conventions=a.conventions, polite=a.polite)
        failed += r["outcome"] == "unavailable"
        if a.json:
            print(json.dumps(r, ensure_ascii=False))
        else:
            print(_explain_text(c, r))
        sys.stdout.flush()
    return 1 if failed else 0


def _explain_text(c, r, max_rejected=5):
    head = {"linked": f"linked: {r['url']}", "unlinked": "left unlinked",
            "unavailable": "Sefaria unreachable (not cached; try again)"}[r["outcome"]]
    out = [c, f"  {head}"]
    steps = r["steps"]
    tried = [st for st in steps if st["step"] == "tried"]
    # suggestions rejected because they drop or add words: the closest first
    word_rejects = [st for st in steps if st["step"] == "rejected" and "suggestion" in st]
    word_rejects.sort(key=lambda st: (st["reason"].count(",") + 1, len(st["reason"])))
    shown = set(id(st) for st in word_rejects[:max_rejected])
    for st in steps:
        kind = st["step"]
        if kind == "candidates":
            cands = st["candidates"]
            out.append(f"    - {len(cands)} spellings: {'; '.join(cands[:8])}" + (" ..." if len(cands) > 8 else ""))
        elif kind == "tried":
            if st is tried[0]:
                out.append(f"    - tried {len(tried)} of them on Sefaria: none is a reference as written"
                           if r["outcome"] != "linked" or not any(x["step"] == "matched" and x.get("via") == "spelling"
                                                                  for x in steps)
                           else f"    - tried {len(tried)} spellings before one matched")
        elif kind == "rejected" and "suggestion" in st:
            if id(st) in shown:
                out.append(f"    - {st['text']}")
        else:
            out.append(f"    - {st['text']}")
    if len(word_rejects) > max_rejected:
        out.append(f"    - ...and {len(word_rejects) - max_rejected} more suggestions rejected (--json for all)")
    return "\n".join(out) + "\n"


if __name__ == "__main__":
    sys.exit(main())
