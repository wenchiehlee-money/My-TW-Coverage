---
name: skill-my-tw-coverage-enrichment-json
description: >-
  Extract, review, validate, and later render My-TW-Coverage Markdown enrichment as atomic JSON,
  prioritized by biztrends.TW/StockID_TWSE_TPEX_focus.csv. Use when converting
  My-TW-Coverage Pilot_Reports Markdown into structured enrichment JSON, reviewing competitors,
  peers, customers, suppliers, moats, risks, technologies, products, applications, or planning
  JSON-canonical enrichment migration.
---

# My-TW-Coverage Enrichment JSON Skill

## Purpose

Convert `../My-TW-Coverage/Pilot_Reports/**/*.md` from presentation Markdown into atomic draft JSON, using `StockID_TWSE_TPEX_focus.csv` as the first review universe.

Current state:

- `My-TW-Coverage` stores enrichment permanently in Markdown report sections.
- `scripts/update_enrichment.py` in `My-TW-Coverage` only applies three text blobs: `desc`, `supply_chain`, and `cust`.
- There is no current canonical enrichment JSON, claim table, evidence table, or review manifest.

Target state:

- Atomic JSON is canonical.
- Markdown is rendered presentation.
- Focus tickers are reviewed one by one before broad migration.

## Standard Workflow

Run from `../My-TW-Coverage` root:

```bash
python skills/skill-my-tw-coverage-enrichment-json/scripts/extract_enrichment_json.py
```

Equivalent explicit command:

```bash
python skills/skill-my-tw-coverage-enrichment-json/scripts/extract_enrichment_json.py \
  --focus ../biztrends.TW/StockID_TWSE_TPEX_focus.csv \
  --coverage-root . \
  --out data/enrichment_draft \
  --manifest data/enrichment_manifest.csv
```

It can also run from `biztrends.TW` root:

```bash
python skills/skill-my-tw-coverage-enrichment-json/scripts/extract_enrichment_json.py \
  --focus StockID_TWSE_TPEX_focus.csv \
  --coverage-root ../My-TW-Coverage \
  --out ../My-TW-Coverage/data/enrichment_draft \
  --manifest ../My-TW-Coverage/data/enrichment_manifest.csv
```

Useful scopes:

```bash
python skills/skill-my-tw-coverage-enrichment-json/scripts/extract_enrichment_json.py --ticker 2330
python skills/skill-my-tw-coverage-enrichment-json/scripts/extract_enrichment_json.py --limit 10
```

All-report migration preview:

```bash
python skills/skill-my-tw-coverage-enrichment-json/scripts/extract_enrichment_json.py \
  --all-reports \
  --out data/enrichment_all_draft \
  --manifest data/enrichment_all_manifest.csv

python skills/skill-my-tw-coverage-enrichment-json/scripts/render_enrichment_markdown.py \
  --json-dir data/enrichment_all_draft \
  --out output/enrichment_all_rendered \
  --compare output/enrichment_all_render_compare.csv
```

## JSON Layering

Draft JSON should keep both structured atoms and original Markdown snippets:

- `profile`: ticker, company name, sector, industry, market cap, enterprise value, source path.
- `business`: summary text plus extracted wikilinks.
- `supply_chain`: upstream, midstream, downstream, other rows.
- `relationships`: customers, suppliers, competitors, peers, substitutes.
- `competitive_position`: moats, risks, competitive notes.
- `entities`: all wikilinks with simple type classification.
- `source_text`: original section bodies, so migration is non-lossy.
- `quality`: parser status, review status, warnings, and counts.

Do not treat the first parsed JSON as approved. It is a draft review artifact.

## Atomic Relationship Rules

Normalize competitive language into structured keys:

- `競爭對手`, `主要競爭對手`, `競爭同業`, `競爭:` -> `relationships.competitors`.
- `同業`, `同業包括`, `同業比較` -> `relationships.peers` unless direct competition is explicit.
- `避開紅海競爭`, `利基`, `技術領先`, `成本優勢`, `良率`, `客戶黏著` -> `competitive_position.moats` or `competitive_position.notes`.
- `替代`, `取代`, `外包轉自製`, `自研` -> `relationships.substitutes`.

When extraction is ambiguous, preserve text in `source_text` and add a `quality.warnings` entry instead of inventing a precise atom.

Do not auto-fill `relationships.competitors` from same-folder or same-industry peers. If competitors are not explicit in source or reviewed JSON, leave the array empty and review it manually. Folder peers are classification context, not validated competitors.

## Review Rules

For each focus ticker:

1. Confirm filename identity: `Ticker_公司名.md` must match `StockID_TWSE_TPEX_focus.csv`.
2. Check all customers, suppliers, competitors, peers, technologies, products, and applications are specific named entities where possible.
3. Keep generic labels as labels, not wikilink entities.
4. Preserve original Markdown snippets until rendered Markdown diff is clean.
5. Mark reviewed files by updating manifest status from `parsed` to `needs_review`, `reviewed`, or `approved`.

## Boundaries

- This skill does not update financial tables.
- This skill does not produce evidence-linked model signals yet.
- This skill does not directly update `biztrends.TW/data/company_segment_weights.csv`.
- Future evidence linking can add per-atom `evidence`, `confidence`, and `status`, but initial migration should focus on non-lossy atomic structure.
