# Lessons learned

_What the 2026-11-23/24 sessions taught about building this normalizer. Read
alongside `HANDOFF.md` ("Current status"). Each lesson names the incident that taught it._

1. **Measure correctness, not "something resolved."** `benchmark.py` reported 83% for
   months while 7 of those "resolved" citations linked to the wrong text. For a system
   whose promise is "unlinked, never mislinked", wrong links are the number to track.
   *Now:* `benchmark.py --strict` fails on any WRONG.

2. **Check against labels you didn't make.** The first guard looked perfect on the old
   benchmark (0 wrong); the web pairs immediately found 29 more wrong links. 32 of the 139
   benchmark rows had been labeled by our own rules, so the benchmark was partly scoring
   the rules against themselves (one of those labels was simply wrong: `Sh'mot 19`).

3. **People who link to Sefaria label the data for free.** Link text is the citation as a
   human wrote it; the href is the right answer. Mi Yodeya, Wikipedia and other Stack
   Exchange sites gave ~20k labeled pairs in an afternoon, with no manual or LLM labeling,
   from openly licensed, bulk-downloadable sources.

4. **"Closest title" suggestions change meaning in predictable ways.** Asking `/api/name`
   to canonicalize a name returns completions that *drop* words (Palagi, Tosfot), *add*
   them (`, Prefatory Remarks`, `Sefer`, `I`), *reorder* them (Arukh HaShulchan -> Shulchan
   Arukh), *add numbers* (`, Part 1`), or *pick an edition* through an alt title (Noda
   BiYehudah **I**). Each failure mode became an explicit check in `_keeps_all_words`.
   Canonicalization may change spelling and casing, never meaning.

5. **Every fix gets run against the whole test set, not just its motivating case.** My
   own fixes introduced new mislinks three times: allowing `Sefer` to be added (*Sefer
   Yesodei HaTorah* is a different book), Hilchot -> Rambam (the Baal HaTanya also wrote a
   *Hilkhot Talmud Torah*), and quoted `Y"D` reaching the bare-section rule. All were
   caught only by re-running the broad data.

6. **Over-generating rewrites is safe; choosing between meanings is not.** A rewritten
   candidate only counts if Sefaria verifies it exactly, so a bad rewrite just fails to
   resolve. Mislinks come from *choices*: a section (`YD` -> Shulchan Arukh or Tur?), an
   edition, I vs II Samuel, Mishnah vs Bavli. When the text doesn't make the choice, leave
   it unlinked. Where convention makes a choice usually right (bare sections: 87% Shulchan
   Arukh), measure it and make it an explicit owner decision, not a silent default.

7. **Bounded lists are fine; open-ended spelling lists aren't.** The 24 Tanakh book names
   and a handful of abbreviations are finite and stable, so a table is right. Tractate
   and section spellings are an open tail, so they're resolved through Sefaria's own
   titles and completions instead. When a name is also something else (Shoftim is a
   parasha; Yonah is a person), restrict where the table applies or leave the name out.

8. **Separate label noise from errors, or the errors get buried.** Writers link the
   commentary they were reading, use Christian verse numbering, cite one place and link
   another, or make typos. A `label_noise` bucket (same location, differing only by
   something the writer didn't say) kept the WRONG list down to real problems.

9. **Read the raw data before trusting a filter.** Hand-reading 40 random pairs exposed
   prose link text (`writes`, `cattlemen`), double-encoded URLs (`%252C`), `sefaria.org.il`
   links, and abbreviation-only anchors (`S"A O"C`) that the first filter rejected.

10. **Keep the evaluation sample stable.** Adding a source silently reshuffled the sample
    twice (a shared random state, then alphabetical dedup credit). Before/after numbers on
    different samples mean nothing. Existing sources now come first in a fixed order, and
    a check confirms the original 1,000 rows survive.

11. **Every external service has its own limits; respect them.** The Common Crawl CDX
    index timed out on every query; Stack Exchange's API stops at page 25 without a key
    (slide the date window instead) and returns throttling errors as HTTP 400; Quora's
    robots.txt forbids AI use; Reddit's terms are restrictive. Serial pacing, honoring
    backoff, bulk dumps over crawling, and checking robots.txt kept every source usable.

12. **A Sefaria API quirk is often a Sefaria bug worth reporting, with data.** The case
    sensitivity of `Ref()` was already a 2022 issue (#1016) with no replies. What a report
    can add is the cause in their code, the scope (every Ref endpoint, including their own
    linker), and a full check that a fix is safe: all 1,097 case-variant groups resolve to
    one text each. That check also turned up two more unreachable title families
    (lowercase-initial, hyphenated).

13. **Concurrent jobs must not share a writable cache.** A background full run and a
    sample run shared one resolver cache file. Each loaded it at start and overwrote it on
    save, so either could write back answers computed by older code, and the other then
    reported them as current. Give every run its own cache (keyed by its output) and
    clear it whenever the code it caches changes.

14. **Stop background processes by PID, never by pattern.** `pkill -f "web_pairs.py eval$"`
    meant for one job also killed another with the identical command line, losing hours
    of a full run. `ps`, pick the PID, `kill <pid>`.

15. **Autocomplete is not a lookup.** `/api/name` completions are ranked for humans
    typing, not for canonicalization; the right title is often in Sefaria's title list
    but not in the top suggestions. Matching against the full title list, with the same
    guard and live verification, recovers these without guessing.

16. **Coarse labels make a benchmark flatter itself.** Labels derived from the old rules
    (`Genesis 1:1 (SP)` labeled "Genesis 1") scored coarse answers as "correct". Relabeling
    to what the text actually says turned 7 apparent successes into visible "coarser"
    results, which were then fixed (precise-first candidate order, verse-part letters).

17. **Check what users will actually see, in a real browser.** The demo looked right in its
    tests but a rendered screenshot showed a link in the browser's default blue (unreadable in
    dark mode), quoted examples that read badly, and, worse, a one-hour cache header on the page
    itself, which made Chrome show a stale copy after an update. The visitor-facing page is now
    served `no-cache`; only images are cached. Test screenshots must use a fresh browser profile.

18. **Respect another project's process when contributing to it.** The Girsa demo has an operator
    role, a stability-first rule and a go that only the reviewer can give. An outside session
    prepares a self-contained archive, checks and a deploy guide, and hands off; it doesn't send
    messages under a role it doesn't hold, or touch that repository.
