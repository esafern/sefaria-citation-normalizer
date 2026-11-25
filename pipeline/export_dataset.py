#!/usr/bin/env python3
"""Export the verified web-mined citation pairs as a Hugging Face dataset folder.

Reads pipeline/web_pairs_raw/web_pairs_full.json (made by `web_pairs.py verify` with
WEB_PAIRS_OUT pointing there; see pipeline/web_pairs_raw/full_run.sh) and writes:

  dist/hf-dataset/README.md          the dataset card (from docs/DATASET.md)
  dist/hf-dataset/data/test.jsonl    one pair per line

Upload (needs a Hugging Face account and `pip install huggingface_hub`):
  hf auth login
  hf upload <user>/<dataset-name> dist/hf-dataset . --repo-type dataset

The fields are renamed for outside readers; nothing about this tool's own answers is
included, so the set stays a neutral benchmark.
"""
import collections
import json
import os
import re
import shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "pipeline", "web_pairs_raw", "web_pairs_full.json")
OUT = os.path.join(ROOT, "dist", "hf-dataset")
CARD = os.path.join(ROOT, "docs", "DATASET.md")

SOURCE_NAMES = {
    "miyodeya": "mi_yodeya_dump_2024_04",
    "miyodeya_2024on": "mi_yodeya_api_2024_on",
    "wikipedia_en": "wikipedia_en",
    "se_hermeneutics": "stackexchange_hermeneutics",
    "se_history": "stackexchange_history",
    "se_christianity": "stackexchange_christianity",
}


def main():
    pairs = json.load(open(SRC))["pairs"]
    os.makedirs(os.path.join(OUT, "data"), exist_ok=True)
    n = collections.Counter()
    with open(os.path.join(OUT, "data", "test.jsonl"), "w", encoding="utf-8") as f:
        for p in pairs:
            row = {
                "citation": p["raw"],
                "sefaria_ref": p["sefaria_ref"],
                "sefaria_url": p["href"],
                "resolves_as_written": p["clean"],
                "source": SOURCE_NAMES.get(p["source"], p["source"]),
                "source_url": p["where"],
            }
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
            n[row["source"]] += 1
            n["_mangled" if not p["clean"] else "_clean"] += 1
    card = open(CARD, encoding="utf-8").read()
    # the card in the repo has a front-matter block for Hugging Face between the two markers
    m = re.search(r"<!-- HF-CARD-START -->\n(.*?)<!-- HF-CARD-END -->", card, re.S)
    open(os.path.join(OUT, "README.md"), "w", encoding="utf-8").write(m.group(1) if m else card)
    total = sum(v for k, v in n.items() if not k.startswith("_"))
    print(f"wrote {total} pairs ({n['_mangled']} mangled, {n['_clean']} resolve as written) -> {OUT}")
    for k, v in sorted(n.items()):
        if not k.startswith("_"):
            print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
