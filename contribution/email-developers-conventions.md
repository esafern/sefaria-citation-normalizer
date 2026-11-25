<!-- DRAFT email for you to edit. Asks Sefaria's engineers how THEY resolve three ambiguous
     citation patterns, which are exactly our open decisions 1, 5 and 6 (HANDOFF.md). Their answer
     doesn't bind us, but matching Sefaria's own linker keeps our links consistent with what
     readers see on sefaria.org. Numbers from the 2026-11-25 full web run. -->

**To:** developers@sefaria.org
**Subject:** How should ambiguous citations resolve? Three conventions, with data

---

Hi,

I'm building an open-source normalizer that turns messy English Torah citations (`Berachos 5a`,
`S"A O"C 271:1`, `Hil. M'lachim 11:1`) into Sefaria refs. It proposes candidate spellings and lets
`/api/name` confirm them, and I'm trying hard to make sure it never links a citation to the wrong
text. To test it, I collected about 19,000 citations that people hyperlinked to Sefaria on Mi Yodeya
and Wikipedia, so the link target serves as the correct answer.
(Repo: https://github.com/esafern/sefaria-citation-normalizer)

Three patterns come up often, and Sefaria already answers each one implicitly through aliases and
`Ref()` behavior. Before I decide how my tool handles them, I'd like to know whether those answers
are deliberate, and what your linker does:

**1. A Shulchan Arukh section with no work named** (`YD 289`, `O.C. 122:1`).
In my data, 477 citations look like this. 87% of the writers linked the Shulchan Arukh, and 13%
linked something else: the Tur, Arukh HaShulchan, Mishnah Berurah, Beit Yosef, or a responsum
(usually named just outside the link). Is "bare section = Shulchan Arukh" the convention you
follow?

**2. A tractate plus chapter:mishnah** (`Kilayim 9:3`, `Berachot 2:4`).
`Ref()` resolves these to the Mishnah, since Bavli refs check the Mishnah pattern first. In my data
some writers meant the Yerushalmi or the Mishneh Torah section of the same name. Is Mishnah the
intended default?

**3. Short abbreviations that collide** (`Ber` is your alias for Berakhot, but `Ber.` also means
Bereshit in academic writing).
Do you treat 2–3 letter aliases as confident matches, or does the linker require more context?

Two related things you may already know about: I commented on #1016 (case sensitivity in `Ref()`)
and filed #4150 (hyphenated titles can't resolve). I've also sent a few title-data problems to
corrections@. If any of this would be useful to your linker team, the dataset of about 19,000
verified citation→ref pairs is available.

Thanks,
Eric Safern
