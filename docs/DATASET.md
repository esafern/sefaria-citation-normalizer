# The citation-to-Sefaria dataset

About 19,000 real citations of Jewish texts, as people wrote them, each paired with the
Sefaria reference they linked it to. Built for evaluating citation normalizers and linkers;
published on Hugging Face (see the README for the link once it's up) and rebuilt by
`pipeline/export_dataset.py`. The section between the markers below is the dataset card.

<!-- HF-CARD-START -->
---
license: cc-by-sa-4.0
language:
- en
pretty_name: Torah citations linked to Sefaria
size_categories:
- 10K<n<100K
task_categories:
- text-classification
tags:
- entity-linking
- citations
- jewish-texts
- sefaria
- talmud
- torah
configs:
- config_name: default
  data_files:
  - split: test
    path: data/test.jsonl
---

# Torah citations linked to Sefaria

About 19,000 citations of Jewish texts (Tanakh, Talmud, Mishnah, Midrash, halachic codes,
commentaries) exactly as people wrote them in English, each paired with the
[Sefaria](https://www.sefaria.org) reference they hyperlinked it to.

Many are written in the shorthand and transliterations of English Torah writing
("Berachos 5a", "S\"A O\"C 271:1", "Hilchos Eidus 4:1", "Pirke De-Rabbi Eliezer, chapter 24"),
which makes this a test set for citation normalization and entity linking.

## How it was made

When a writer hyperlinks a citation to sefaria.org, the link text is the citation as a person
wrote it, and the link target is a reference the writer chose. So each pair is labeled by its
writer, not by an annotator or a model.

1. Every link to sefaria.org was collected from:
   - Mi Yodeya (Judaism Stack Exchange): the archive.org data dump of April 2024, and
     posts since then through the public Stack Exchange API;
   - English Wikipedia (articles that link to Sefaria, through the MediaWiki API);
   - the Hermeneutics, History and Christianity Stack Exchange sites (data dumps).
2. A pair was kept only if the link text names a work and contains a number, and every number
   in the link text appears in the link target. This drops prose links ("writes", "here") and
   links whose text and target disagree (e.g. text "Shabbat 105b", target Joshua 24:31).
3. Each link target was checked live against Sefaria's `/api/name` and normalized to
   Sefaria's canonical form (`sefaria_ref`). Dead links were dropped.

## Fields

| Field | Meaning |
|---|---|
| `citation` | The link text: the citation as written. |
| `sefaria_ref` | The canonical Sefaria reference of the link target. |
| `sefaria_url` | The link as the writer made it. |
| `resolves_as_written` | `true` if Sefaria's `/api/name` already resolves `citation` as written (about 62%); `false` if it needs normalizing (about 38%, the interesting part). |
| `source` | Where it came from (see above). |
| `source_url` | The post or article, for attribution. |

## Known noise and caveats

- **The label is the writer's choice.** Sometimes it's more or less specific than the text
  (text "Yevamot 3b", link Yevamot 3b:17), or it points at the commentary the writer was
  reading rather than the cited verse (text "Kiddushin 81a", link Ritva on Kiddushin 81a). A
  fair scorer treats "less specific but containing" and "same place, different commentary layer"
  separately from wrong answers.
- **Some links don't match their text** despite the filter (a typo'd verse, the wrong book).
  In a manual review of disagreements, roughly half were writer-side noise.
- **Some citations are genuinely ambiguous** without their surrounding sentence ("YD 289" could
  be the Shulchan Arukh or the Tur; "Shmuel 23:8" could be I or II Samuel).
- **Verse numbering:** a few writers use Christian chapter/verse numbering (Genesis 32:32 vs
  Sefaria's 32:33).
- English-language sources only. A small number of citations from Hebrew Wikipedia were
  collected but are not included.

## License and attribution

CC BY-SA 4.0, inherited from the sources (Stack Exchange and Wikipedia content is CC BY-SA).
Each row's `source_url` is its attribution. The Sefaria references are facts about Sefaria's
public library; this dataset is not made or endorsed by Sefaria.

## Citation

Built with [citenorm](https://github.com/esafern/sefaria-citation-normalizer), a normalizer
that proposes candidate spellings and lets Sefaria verify them. Its evaluation scripts
(`benchmark.py`, `pipeline/web_pairs.py eval`) score against this set.
<!-- HF-CARD-END -->
