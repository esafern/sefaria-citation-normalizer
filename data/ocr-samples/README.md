# OCR samples — Yad Malachi, same passages across every scan

Three passages from **Klalei HaGemara** (part I) — the openings of the **Aleph**, **Bet**, and **Gimel** letter-sections, each two adjacent *klalim* — extracted as **raw embedded-OCR text** from every scan in hand, the *same passage* in each. This is the actual input an ensemble OCR pipeline would align and vote on.

| File | Passage |
|---|---|
| [`aleph-section.md`](aleph-section.md) | Klalei HaGemara, Aleph section opening |
| [`bet-section.md`](bet-section.md) | Klalei HaGemara, Bet section opening |
| [`gimel-section.md`](gimel-section.md) | Klalei HaGemara, Gimel section opening |

## The five witnesses

| Edition | Scan | Script | Embedded-OCR quality on these passages |
|---|---|---|---|
| Berlin ~1857/8 | Google Books | square | **clean & complete** |
| Przemyśl 1877 | Google Books | square | poor — heavy letter-confusion |
| Przemyśl 1888 | Google Books | square | poor — heavy letter-confusion |
| Przemyśl 1877 | HebrewBooks #14122 | square | accurate letters, badly segmented |
| Livorno 1766–7 (part I) | HebrewBooks #32530 | **Rashi** | unusable as-is |

## Why this matters

It makes the process argument concrete. The passages are identical, yet the raw layers disagree wildly — so (a) the embedded layers alone are **not** a finished text; (b) **square type is necessary but not sufficient** (the Przemyśl Google scans are square yet OCR badly); (c) two scans of one edition (Przemyśl 1877, Google vs HebrewBooks #14122) carry **complementary** error profiles worth voting in; and (d) the Rashi first edition needs a Rashi-specific engine. This disagreement is precisely what the multi-engine ensemble + image-grounded adjudication in [`../CASE-YAD-MALACHI.md`](../CASE-YAD-MALACHI.md) is designed to resolve.

_Extraction: `pipeline/extract_ocr_samples.py`. Google Books layers are stored in visual order and reversed per line to logical Hebrew; HebrewBooks layers are logical and used as-is. No correction applied._