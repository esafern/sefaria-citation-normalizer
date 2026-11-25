"""Command line: citenorm "Berachos 5a" "SA OC 271:1"   (or one citation per line on stdin)

Prints one tab-separated line per citation: the citation, then the Sefaria URL,
"-" when it can't be linked without guessing, or "?" when Sefaria couldn't be
reached (not cached; exit status 1).
"""
import argparse
import json
import os
import sys

from . import __version__
from .resolve import Cache, resolve, CONVENTIONS, ResolverUnavailable, _cache_dir


def main(argv=None):
    ap = argparse.ArgumentParser(
        prog="citenorm",
        description="Normalize messy Torah citations to Sefaria links (propose candidates, verify with Sefaria).")
    ap.add_argument("citations", nargs="*", help="citations; if none, read one per line from stdin")
    ap.add_argument("--conventions", choices=CONVENTIONS, default="common",
                    help="'strict' leaves bare Shulchan Arukh sections, tractate+chapter:mishnah and "
                         "2-3 letter aliases unlinked instead of following Sefaria's convention")
    ap.add_argument("--json", action="store_true", help="print JSON lines instead of TSV")
    ap.add_argument("--cache", default=os.path.join(_cache_dir(), "resolve.json"),
                    help="answer cache (default: ~/.cache/citenorm/resolve.json; '' to disable)")
    ap.add_argument("--polite", type=float, default=0.3,
                    help="seconds to wait between requests to Sefaria (default 0.3)")
    ap.add_argument("--version", action="version", version=f"citenorm {__version__}")
    a = ap.parse_args(argv)

    cits = a.citations or [line.strip() for line in sys.stdin if line.strip()]
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


if __name__ == "__main__":
    sys.exit(main())
