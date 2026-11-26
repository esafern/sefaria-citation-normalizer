#!/usr/bin/env python3
"""mishmeret/ref_hook.py, run from the commit the project's Mishmeret config pins (.claude/mishmeret_shim.py), with the
same arguments, or stood in for when imported. A missing checkout or pin is said, and the hook refuses: it fails
closed."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import mishmeret_shim  # noqa: E402

mishmeret_shim.stand_in(__name__, ".claude/hooks/ref_hook.py", "ref_hook", "refuses")
