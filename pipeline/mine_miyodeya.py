#!/usr/bin/env python3
"""Extract a citation corpus from the Mi Yodeya (Judaism Stack Exchange) dump.

Mi Yodeya answers cite halachic/Torah sources in free prose, in wildly varied
Anglo-transliterated forms — ideal raw material for the normalization dataset
(the dialect variety rules overfit to). The dump is CC-BY-SA, downloaded in bulk
from archive.org (no live crawling).

This script does only the *parallel-safe* part: unpack Posts.xml, clean answer
bodies, and sample. The Sefaria find-refs pass over the sample is a separate,
serialized step (reuses mine_wide.find_refs) so it never contends with the
Halachipedia run for Sefaria concurrency.

Two-phase, so it's polite and resumable:
  extract  -> read the .7z, write miyodeya_bodies.json (sampled cleaned text)
"""
import html, json, os, random, re, sys

HERE = os.path.dirname(__file__)
SCRATCH = os.environ.get("MY_SCRATCH",
    "/tmp/claude-0/-home-user-sefaria-citation-normalizer/"
    "7f1ee42f-601d-54be-9f47-b5dde92f8158/scratchpad")
DUMP = os.path.join(SCRATCH, "judaism.7z")
POSTS = os.path.join(SCRATCH, "Posts.xml")
SAMPLE = int(sys.argv[1]) if len(sys.argv) > 1 else 800
SEED = 20260724

_TAG = re.compile(r"<[^>]+>")
_WS = re.compile(r"\s+")


def unpack():
    if os.path.exists(POSTS):
        return
    import py7zr
    with py7zr.SevenZipFile(DUMP, "r") as z:
        z.extract(path=SCRATCH, targets=["Posts.xml"])


def clean(body):
    t = _TAG.sub(" ", body)          # drop HTML
    t = html.unescape(t)
    t = _WS.sub(" ", t).strip()
    return t


def main():
    unpack()
    import xml.etree.ElementTree as ET
    bodies = []
    # stream Posts.xml; PostTypeId 2 = answer (denser citations than questions)
    for _, el in ET.iterparse(POSTS, events=("end",)):
        if el.tag == "row":
            if el.get("PostTypeId") == "2":
                b = clean(el.get("Body", ""))
                if len(b) >= 120:          # skip stubs
                    bodies.append(b)
            el.clear()
    random.seed(SEED)
    random.shuffle(bodies)
    sample = bodies[:SAMPLE]
    json.dump(sample, open(os.path.join(HERE, "miyodeya_bodies.json"), "w"),
              ensure_ascii=False)
    print(f"answers total={len(bodies)}  sampled={len(sample)} "
          f"(avg {sum(len(b) for b in sample)//max(1,len(sample))} chars) "
          f"-> miyodeya_bodies.json")


if __name__ == "__main__":
    main()
