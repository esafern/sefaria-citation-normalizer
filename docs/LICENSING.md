# Licensing

## Data

Fixed by the sources: the web-mined pairs come from CC BY-SA sources (Stack Exchange,
Wikipedia), so the datasets are **CC BY-SA 4.0**, attributed per row. Details per file:
`data/README.md`.

## Code: MIT (decided 2026-11-25)

The owner chose MIT, as recommended below. The comparison is kept for the record.

### The comparison

| | MIT | GPL-3.0 |
|---|---|---|
| What it allows | Anyone may use, change and ship the code, including in closed-source or commercial products, as long as they keep the notice. | Anyone may use and change it, but if they distribute their version, it must also be GPL with source. |
| Matches Sefaria? | No. Sefaria's own code is GPL-3.0. But this tool doesn't copy Sefaria's code; it calls its public API, so it isn't bound by Sefaria's license either way. | Yes, the same license as Sefaria-Project, which some in that community will appreciate. |
| Adoption | Easiest: blogs, publishers, apps and companies can embed it without legal review. The most-used libraries in this space are MIT, BSD or Apache. | Some organizations avoid GPL dependencies, which reduces reuse in commercial or closed products (e.g. a publisher's website). |
| Protection | Someone could build a closed improved version and not share it back. | Improvements that are distributed must be shared back. Note: a web service that only *runs* it (not distributes it) needn't share changes; that would take AGPL. |
| Contributions back to Sefaria | If Sefaria ever wanted to absorb parts (e.g. the case-insensitive fallback), MIT code can go into a GPL project. | GPL code can go into a GPL project too. Both work. |
| Your private blog repo, which vendors `shared_dialect.py` | No obligations unless you distribute it. | Same: private use of GPL code creates no obligation. Only distribution would. |

**Recommendation: MIT.** The goal is for blogs, Q&A sites and publishers to actually use
this to fix their citations, and MIT removes every obstacle to that. It's still compatible
with Sefaria's GPL. Choose GPL-3.0 if keeping all improvements open matters more to you
than reach.

Done: `LICENSE` at the root, `license = "MIT"` in `pyproject.toml`, the README's License
section, and a copy of LICENSE in the demo archive.
