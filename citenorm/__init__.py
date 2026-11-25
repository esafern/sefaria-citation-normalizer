"""citenorm: normalize messy Torah citations to Sefaria references (propose, then verify)."""

__version__ = "0.1.0"


def code_fingerprint():
    """A short hash of the resolver's code. Caches of answers are named after it, so a
    change to the rules or checks never reads answers computed by older code."""
    import hashlib
    import os
    h = hashlib.sha256()
    here = os.path.dirname(os.path.abspath(__file__))
    for name in ("rules.py", "resolve.py", "shared_dialect.py"):
        with open(os.path.join(here, name), "rb") as f:
            h.update(f.read())
    return h.hexdigest()[:10]
