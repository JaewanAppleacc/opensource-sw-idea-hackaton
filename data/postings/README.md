# Curated posting corpus (Phase 3)

**Status: 100% synthetic.** `postings.jsonl` and `matched_pairs.jsonl` in
this directory are self-authored fixtures (see
`scripts/data/build_synthetic_fixtures.py`), not real scraped or sourced job
postings. `source_name` is always `synthetic_fixture_v1` and
`source_id_url` is always `null` on every record so this can never be
mistaken for real data downstream. See `data/sources/source_inventory.yaml`
for why no real postings exist yet and `DATA_HANDOFF.md` for the remaining
manual step to fix that.

Because the text is self-authored fiction, it carries no license
restriction and is safe to keep in the public repository layer — unlike
real postings, which must be checked per-source before redistribution (see
`data/README.md`).

## `postings.jsonl` schema

| Field | Type | Notes |
|---|---|---|
| `posting_id` | str | Stable ID, e.g. `JB-001`, `MET-001`. Unique. |
| `region_group` | `"jeonbuk"` \| `"metro"` | |
| `municipality` | str | e.g. `전주시`, `서울특별시`. |
| `occupation` | str | Same value across the whole fixture set: `생산직(제조 조립원)`. |
| `employment_type` | str | `정규직` for matched pairs; `계약직` for the two unmatched demo records. |
| `collection_date` | `null` | Always null here — there is no real collection date for fiction. Kept in the schema so a real-data importer has somewhere to put it. |
| `fixture_build_date` | str (YYYY-MM-DD) | When this synthetic record was authored. |
| `source_name` | str | Always `synthetic_fixture_v1`. |
| `source_id_url` | `null` | Always null here. |
| `company_name` | str | Always prefixed `(예시)` ("example") and uses an invented company name. |
| `full_text` | str | The fictional posting text; evidence offsets in the annotation files point into this string. |
| `redistributable` | bool | Always `true` here. |
| `matched_pair_id` | str \| `null` | Points into `matched_pairs.jsonl`; null iff `unmatched` is true. |
| `match_criteria` | str \| `null` | Free-text description of what was matched on. |
| `unmatched` | bool | True for the two intentionally-unmatched demo records. |
| `unmatched_reason` | str \| `null` | Required, factual reason when `unmatched` is true — never an inference about scarcity. |

## `matched_pairs.jsonl` schema

One row per matched pair: `matched_pair_id`, `jeonbuk_posting_id`,
`metro_posting_id`, `occupation`, `employment_type`, `match_criteria`.

## Regenerating

```
python scripts/data/build_synthetic_fixtures.py
```

This is fully deterministic — re-running it produces byte-identical output,
so the script itself is the record of how these fixtures were built.
