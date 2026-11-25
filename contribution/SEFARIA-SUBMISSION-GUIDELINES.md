# How Sefaria takes contributions (reviewed 2026-11-25)

Sources: `Sefaria/Sefaria-Project` README ("Bugs and Corrections", "A Note on Contributions"),
`.github/pull_request_template.md`, `AGENTS.md`, and how maintainers have actually handled
outside issues and PRs in the last ~18 months. The repo has no CONTRIBUTING file, no issue
templates, no code of conduct; license GPL-3.0.

## Where things go

| What | Channel |
|---|---|
| Problems in the library's texts or data (wrong alias, bad title) | **email corrections@sefaria.org** |
| Bugs using the website or app | Formstack bug form (linked in README) |
| Bugs in the code | GitHub Issues |
| Follow-up with engineering | developers@sefaria.org (named by a maintainer on #3327) |
| "I want to build a feature" | build a "Powered by Sefaria" project instead of a PR |

## How they behave in practice

- **Outside code contributions are not accepted.** README: "we rarely prioritize public code
  contributions." On #3448 (June 2026): "we don't currently have a process in place for
  reviewing and merging external PRs."
- **Issues are closed when they're handed to the internal team**, usually with a one-line
  "thanks, our team will investigate." Closing is not rejection (explained on #3327), but the
  public issue then stops tracking the fix. Your #3539 went this way (closed in 6 days).
- Response time on bug issues: typically under a week for a first reply. Some get engineering
  follow-up on GitHub (#2702: a fix announced and confirmed in the thread). Others go quiet;
  one reporter had to chase by email.
- **The PR template asks for a human-written summary**: "Please write this yourself rather than
  having an AI agent generate it." The detailed description may be AI-generated. Their own repo
  carries an `AGENTS.md` and `agent_docs/`, so AI-assisted work is normal there; they just want
  the author's own understanding up front.

## What this means for our submissions

1. **#1016 comment (posted 2026-11-24):** it was posted as raw HTML (pasted from a rendered
   preview), 23k characters, so formatting and links are probably lost. Edit it to the raw
   Markdown in `contribution/issue-1016-comment.md`. Also consider softening the closing PR offer
   ("Would you accept a PR…"): given their stated policy, the realistic ask is "here's the cause
   and a safe fix shape; happy to share the patch." Keep the draft PR as a reference to attach or
   link, not something to open.
2. **#4150 (hyphenated titles, posted 2026-11-24):** right channel. Expect "thanks, passing to the
   team" and a close.
3. **Data errors** (rotated Mishneh Torah aliases, the stray Mishnah Berurah title, HTML in
   titles): email corrections@sefaria.org, not GitHub. Draft:
   `contribution/email-corrections-data-errors.md`.
4. **Bigger asks** (the case-insensitive fallback, conventions questions, the dataset or the
   dialect map as linker test cases): best as a direct conversation with developers@sefaria.org,
   since PRs aren't a channel. Draft: `contribution/email-developers-conventions.md`.
5. **"Powered by Sefaria":** this repo (normalizer + most-wanted list + web-pairs dataset) fits
   their suggested path for outside builders. Listing it there is another route to visibility.
