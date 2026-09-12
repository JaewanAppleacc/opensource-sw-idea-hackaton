# Sequential task C: Integrate AI/backend and data outputs

Run this task only after `TASK_AI_BACKEND.md` and `TASK_DATA_EVALUATION.md` have produced their handoff documents. Read `CLAUDE.md`, `BACKEND_HANDOFF.md`, and `DATA_HANDOFF.md` first.

Do not edit `frontend/**`. The objective is to make the backend/data boundary stable and hand the frontend developer a tested contract.

## Objectives

1. Replace backend fixture adapters with the curated data adapter without changing the public API.
2. Make the full offline demo deterministic.
3. Evaluate the model only on the appropriate split.
4. Produce a concise frontend handoff and demo package.

## Integration steps

1. Compare backend Pydantic schemas with data schemas and list mismatches before editing.
2. Write the smallest adapters required; do not mechanically rewrite either track.
3. Load rubric rules from the versioned data file.
4. Load curated match pairs from JSONL/SQLite.
5. Ensure regional statistics reject non-adjudicated labels.
6. Run extraction on the development split and save predictions separately.
7. Permit prompt changes only using the development split.
8. Freeze the prompt/configuration and record its hash/version.
9. Run the holdout once for the reported result. If a critical software bug requires a rerun, document the bug and rerun reason; do not silently tune.
10. Generate human-readable evaluation and regional exploratory reports.

## Required demo anchors

Select and cache exactly three same-occupation, same-employment-type postings:

- one metropolitan posting with confirmed salary;
- one Jeonbuk posting with confirmed salary for financial comparison;
- one additional Jeonbuk posting with at least three useful vague/absent examples for the audit demonstration.

Do not fabricate real-company facts. Use properly sourced records where permitted or clearly labeled synthetic/anonymous demo fixtures.

## Offline demo test

Verify the following path with all network access disabled and the real model provider disabled where practical:

1. metropolitan demo posting is accepted;
2. curated Jeonbuk matches are returned;
3. all six fields are audited;
4. evidence offsets match the original text;
5. vague/absent fields yield verification actions;
6. confirmed salary values can be supplied to deterministic comparison;
7. monthly surplus, one-year value, three-year scenario, and crossover condition are returned;
8. errors are user-safe and contain no secrets.

## Frontend handoff

Create `FRONTEND_API_HANDOFF.md` containing:

- base URL and run command
- endpoint table
- request/response examples
- complete status and error enums
- empty/loading/error behavior
- source/provenance display requirements
- exact labels recommended for confirmed/vague/absent
- finite-curated-dataset disclosure for matches
- financial assumption disclosure
- three demo payloads and expected responses

Also export an OpenAPI document or equivalent machine-readable contract.

## Final checks

- backend and data tests pass;
- no frontend files were changed;
- no API keys or personal information are committed;
- no unsupported population-wide regional claim appears in reports;
- no AI-generated annotation is presented as human gold;
- no company score, ranking, winner, or future certainty is produced;
- README clearly separates implemented, cached-demo, and future features.

Do not add MCP until this task is complete. If time remains afterward, a separate optional task may expose rubric and aggregate-statistics tools without routing the product through MCP.

