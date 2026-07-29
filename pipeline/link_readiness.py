#!/usr/bin/env python3
"""Link-readiness QA for a digitized text — test, don't touch.

Runs a passage through Sefaria's linker (`/api/find-refs`) purely as a *test* of
auto-linkability. It never inserts links (links are Sefaria's own connections layer,
built at ingest). It reports:
  - which citations the linker resolves on the text as-is, and
  - which citations it detects but FAILS to link (`linkFailed: true`) — each flagged
    with a **candidate normalized citation**, itself re-tested against the linker so
    the suggestion is verified, not guessed.

The candidate generator here is deliberately small and transparent; in production it
plugs into this repo's fuller normalizer. Output: data/link-readiness-demo.md.

Polite-guest API use: async results are cached to link_cache/; calls are paced.
"""
import hashlib, json, os, re, time, urllib.request

HERE = os.path.dirname(__file__)
CACHE = os.path.join(HERE, "link_cache")
os.makedirs(CACHE, exist_ok=True)
UA = {"User-Agent": "citation-research/0.1 (Yad Malachi link-readiness)",
      "Content-Type": "application/json"}

# --- Sefaria linker (async), cached ------------------------------------------
def find_refs(body):
    key = os.path.join(CACHE, hashlib.md5(body.encode()).hexdigest() + ".json")
    if os.path.exists(key):
        return json.load(open(key))
    req = urllib.request.Request("https://www.sefaria.org/api/find-refs",
        data=json.dumps({"text": {"title": "", "body": body}}).encode(), headers=UA)
    tid = json.loads(urllib.request.urlopen(req, timeout=30).read())["task_id"]
    out = None
    for _ in range(30):
        time.sleep(1.0)
        d = json.loads(urllib.request.urlopen(
            "https://www.sefaria.org/api/async/" + tid, timeout=30).read())
        if d.get("ready"):
            out = d["result"]["body"]["results"]
            break
    json.dump(out, open(key, "w"), ensure_ascii=False)
    time.sleep(0.4)
    return out or []


# --- tiny, transparent candidate generator -----------------------------------
TRACTATES = {  # Hebrew tractate name -> canonical (enough for the demo)
    "ברכות": "Berakhot", "שבת": "Shabbat", "עירובין": "Eruvin", "פסחים": "Pesachim",
    "יומא": "Yoma", "סוכה": "Sukkah", "ביצה": "Beitzah", "תענית": "Taanit",
    "מגילה": "Megillah", "חגיגה": "Chagigah", "יבמות": "Yevamot", "כתובות": "Ketubot",
    "נדרים": "Nedarim", "גיטין": "Gittin", "קידושין": "Kiddushin", "נדה": "Niddah",
    "זבחים": "Zevachim", "חולין": "Chullin", "בכורות": "Bekhorot", "כריתות": "Keritot",
    "בבא קמא": "Bava Kamma", "בבא מציעא": "Bava Metzia", "בבא בתרא": "Bava Batra",
    "סנהדרין": "Sanhedrin", "מכות": "Makkot", "שבועות": "Shevuot",
}
# a few named perakim -> tractate (illustrative; the full map lives in the normalizer)
PEREK_TRACTATE = {"המפלת": "נדה", "אין דורשין": "חגיגה", "כל הבשר": "חולין",
                  "המקבל": "בבא מציעא", "השוכר את הפועלים": "בבא מציעא"}
COMMENTATORS = {"רש\"י": "רש\"י", "תוס'": "תוספות", "רמב\"ם": "רמב\"ם",
                "רא\"ש": "רא\"ש", "ר\"ן": "ר\"ן", "ריטב\"א": "ריטב\"א"}
DAF = re.compile(r'[א-ת]["״]?[א-ת]?\s*[אב][\'׳]')  # e.g.  י"ט ב'


def candidate(cite):
    """Best-effort normalized citation for a failed span, or None."""
    s = cite.replace("״", '"').replace("׳", "'")
    daf_m = DAF.search(s)
    daf = daf_m.group(0).strip() if daf_m else None
    # masechet: explicit tractate name, else a named perek -> tractate
    mas = next((h for h in sorted(TRACTATES, key=len, reverse=True) if h in s), None)
    if not mas:
        pk = next((p for p in PEREK_TRACTATE if p in s), None)
        mas = PEREK_TRACTATE.get(pk) if pk else None
    if not (mas and daf):
        return None
    comm = next((c for c in COMMENTATORS if c in s), None)
    core = f"{mas} {daf}"
    return f"{comm} על {core}" if comm else core


# --- the QA pass -------------------------------------------------------------
def qa(passage):
    results = find_refs(passage)
    resolved, failed = [], []
    for r in results:
        (resolved if not r["linkFailed"] else failed).append(r)
    rows = []
    for r in failed:
        cand = candidate(r["text"])
        verified = None
        if cand:
            cr = find_refs(cand)
            ok = [x for x in cr if not x["linkFailed"]]
            verified = ok[0]["refs"] if ok else None
        rows.append((r["text"], cand, verified))
    return resolved, rows


DEMO = ('מדברי רש"י ז"ל בפ"ב דנדרים י"ט ב\' משמע דלאו לדחויי ליה קא מכוין. '
        'ועיין נדרים י"ט ב\'. וכן כתב עוד פ\' אין דורשין י"ט ב\'. '
        'ובפ"ג דיומא ל"א ב\' ובשלהי פ"ק דזבחים ט"ו ב\'. '
        'אך בפרק המפלת כ"ג ב\' פירש אי תניא תניא.')

if __name__ == "__main__":
    resolved, rows = qa(DEMO)
    out = ["# Link-readiness QA — worked example (Yad Malachi, Klalei HaAleph)", "",
           "The text is **run through Sefaria's linker as a test; no links are inserted**. "
           "Citations that resolve as-is need nothing. Citations the linker *detects but "
           "cannot link* are flagged with a **candidate normalized citation**, each "
           "re-tested against the linker so the suggestion is verified.", "",
           "_Source passage (unchanged):_", "", "> " + DEMO, "",
           f"## Resolves as-is ({len(resolved)})", "",
           "| Citation in text | Links to |", "|---|---|"]
    for r in resolved:
        out.append(f"| {r['text']} | {', '.join(r['refs'])} |")
    out += ["", f"## Flagged — failed to auto-link ({len(rows)})", "",
            "| Citation in text | Candidate normalized cite | Candidate resolves to |",
            "|---|---|---|"]
    for text, cand, ver in rows:
        c = cand or "_(needs manual review)_"
        v = ", ".join(ver) if ver else ("—" if not cand else "**did not resolve**")
        out.append(f"| {text} | {c} | {v} |")
    out += ["",
            "**Reading this table.** \"Resolves to\" means the candidate is *linkable* — "
            "it maps to a real Sefaria ref — **not** that it is the semantically correct "
            "citation. Linker-verification confirms link-readiness; the **expert reviewer "
            "confirms correctness** against the passage (e.g. that the author really meant "
            "that daf). Note too that the linker can mis-segment — here `ובשלהי` (\"and at "
            "the end of\") was split off from the Zevachim citation that follows it — which "
            "is itself useful signal for the reviewer.", "",
            "_The flagged list is the deliverable handed to the expert reviewer; the text "
            "itself is never modified. Candidate generation here uses a small transparent "
            "rule set — in production it plugs into this repo's normalizer._"]
    path = os.path.join(HERE, "..", "data", "link-readiness-demo.md")
    open(path, "w").write("\n".join(out))
    print(f"resolved={len(resolved)} flagged={len(rows)} -> data/link-readiness-demo.md")
