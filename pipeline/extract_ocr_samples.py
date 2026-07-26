#!/usr/bin/env python3
"""Extract the *same* passages from every Yad Malachi scan's embedded OCR layer, to
compare raw OCR quality edition-by-edition (the raw material for an ensemble).

Three passages from Klalei HaGemara (part I) — the openings of the Aleph, Bet, and
Gimel letter-sections, each two adjacent klalim — are pulled from each scan and
written to data/ocr-samples/<section>-section.md.

Scans are the public-domain witnesses (not committed here — multi-MB PDFs):
  - Google Books full-view: Berlin ~1857/8, Przemyśl 1877, Przemyśl 1888.
  - HebrewBooks: Przemyśl 1877 #14122; Livorno 1766–7 part I #32530.
Put the PDFs in a directory and pass it as argv[1] (default: ./scans), named as in
SCANS below.

Direction: Google Books stores the text layer in *visual* order (reversed per line to
logical Hebrew here); HebrewBooks stores *logical* order (used as-is). No correction
is applied — this is the untouched embedded layer.
"""
import fitz, os, sys

SCANS_DIR = sys.argv[1] if len(sys.argv) > 1 else "scans"
OUT = os.path.join(os.path.dirname(__file__), "..", "data", "ocr-samples")
NLINES = 14

# (edition, scan-source, script, filename, direction, {section: 0-indexed page})
WITNESSES = [
    ("Berlin ~1857/8", "Google Books", "square", "berlin_1857.pdf", "google",
     {"Aleph": 13, "Bet": 37, "Gimel": 45}),
    ("Przemyśl 1877", "Google Books", "square", "przemysl_1877_google.pdf", "google",
     {"Aleph": 21, "Bet": 57, "Gimel": 69}),
    ("Przemyśl 1888", "Google Books", "square", "przemysl_1888_google.pdf", "google",
     {"Aleph": 17, "Bet": 44, "Gimel": 52}),
    ("Przemyśl 1877", "HebrewBooks #14122", "square", "hebrewbooks_14122.pdf", "hb",
     {"Aleph": 21, "Bet": 57, "Gimel": 69}),
    ("Livorno 1766–7 (part I)", "HebrewBooks #32530", "Rashi", "hebrewbooks_32530.pdf", "hb",
     {"Aleph": 9, "Bet": 43, "Gimel": 53}),
]
SECTIONS = [("Aleph", "כללי האלף"), ("Bet", "כללי הבית"), ("Gimel", "כללי הגימל")]


def spaceless(s):
    return "".join(s.split())


def excerpt(path, direction, pno, needle):
    d = fitz.open(path)
    lines = [l for l in d[pno].get_text("text").splitlines() if l.strip()]
    if direction == "google":
        lines = [l[::-1] for l in lines]  # visual -> logical
    d.close()
    ndl = spaceless(needle)
    for i, l in enumerate(lines):
        if ndl in spaceless(l):
            return lines[i:i + NLINES]
    # header OCR failed (garbled Rashi): skip a leading page-number/short line
    i = 0
    while i < len(lines) and len(spaceless(lines[i])) <= 3:
        i += 1
    return lines[i:i + NLINES]


def main():
    for key, needle in SECTIONS:
        out = [f"# Yad Malachi — Klalei HaGemara, {key} section — same passage, every scan's OCR", ""]
        for ed, src, script, fn, direction, pages in WITNESSES:
            path = os.path.join(SCANS_DIR, fn)
            if not os.path.exists(path):
                print(f"missing {path}; skipping", file=sys.stderr)
                continue
            out.append(f"## {ed} — {src} ({script}) — scan page {pages[key] + 1}")
            out.append("```text")
            out += excerpt(path, direction, pages[key], needle)
            out += ["```", ""]
        open(os.path.join(OUT, f"{key.lower()}-section.md"), "w").write("\n".join(out))
        print("wrote", f"{key.lower()}-section.md")


if __name__ == "__main__":
    main()
