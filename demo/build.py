#!/usr/bin/env python3
"""Build the demo archive: dist/citenorm-demo-<commit>.tar.gz

Contents (one folder, citenorm-demo/): passenger_wsgi.py, app.py, static/, check_demo.py,
DEPLOY.md, a copy of the citenorm package, and VERSION (package version + commit).
Refuses to build from a dirty tree, so the archive always matches a commit.
"""
import os
import subprocess
import sys
import tarfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def git(*a):
    return subprocess.check_output(["git", *a], cwd=ROOT).decode().strip()


def main():
    if git("status", "--porcelain", "--", "demo", "citenorm"):
        sys.exit("demo/ or citenorm/ has uncommitted changes; commit first")
    sha = git("rev-parse", "--short=8", "HEAD")
    sys.path.insert(0, ROOT)
    from citenorm import __version__
    os.makedirs(os.path.join(ROOT, "dist"), exist_ok=True)
    out = os.path.join(ROOT, "dist", f"citenorm-demo-{sha}.tar.gz")
    files = [("demo/passenger_wsgi.py", "passenger_wsgi.py"), ("demo/app.py", "app.py"),
             ("demo/check_demo.py", "check_demo.py"), ("demo/DEPLOY.md", "DEPLOY.md")]
    files += [(f"demo/static/{f}", f"static/{f}") for f in sorted(os.listdir(os.path.join(ROOT, "demo", "static")))]
    files += [(f"citenorm/{f}", f"citenorm/{f}") for f in sorted(os.listdir(os.path.join(ROOT, "citenorm")))
              if f.endswith(".py")]
    version = os.path.join(ROOT, "dist", "VERSION")
    open(version, "w").write(f"citenorm {__version__}, commit {sha}\n")
    with tarfile.open(out, "w:gz") as tar:
        for src, dst in files:
            tar.add(os.path.join(ROOT, src), arcname=f"citenorm-demo/{dst}")
        tar.add(version, arcname="citenorm-demo/VERSION")
    # what goes public: no email addresses, no home-folder paths
    import re
    with tarfile.open(out) as tar:
        for m in tar.getmembers():
            if m.isfile() and not m.name.endswith(".png"):
                text = tar.extractfile(m).read().decode("utf-8", "replace")
                if re.search(r"[\w.+-]+@[\w-]+\.[\w.]+|/Users/|/home/", text):
                    sys.exit(f"refusing: {m.name} contains an email address or a home-folder path")
    print(out, f"({os.path.getsize(out) // 1024} KB)")


if __name__ == "__main__":
    main()
