# API contract

Machine-readable contract consumed by the frontend and any other client.
Generated from the backend's canonical Pydantic models -- do not hand-edit
these files.

- `schema.json` -- JSON Schema for every public domain model (`PostingInput`,
  `PostingAnalysis`, `AuditedField`, `EvidenceSpan`, `VerificationAction`,
  `ValidationWarning`, `ExternalContext`, `MatchRequest`, `MatchCandidate`,
  `MatchResponse`, `FinancialOption`, `FinancialAssumptions`,
  `FinancialComparisonRequest`, `FinancialComparison`, `FinancialOptionResult`,
  `CrossoverResult`, `GapStats`, `GapStatsFilters`, `GapStatsResponse`,
  `APIError`).
- `openapi.json` -- full OpenAPI document for the running FastAPI app,
  including all `/api/v1/**` routes and error envelopes.

## Regenerating

```bash
cd backend
source ../.venv/bin/activate   # or your own virtualenv with backend/requirements.txt installed
python -m scripts.export_contracts
```

Commit the regenerated files alongside any model change. Every model in
this contract rejects additional properties (`extra="forbid"`) and enforces
the `AuditedField.status` enum as exactly `confirmed` / `vague` / `absent` --
never add an `external_verified` status; external context is a separate,
non-mutating model (`ExternalContext`).

## Stability notes for the frontend

- `PostingAnalysis.fields` is always keyed by all six field names:
  `salary`, `duties`, `tools_or_skills`, `training_or_mentoring`,
  `probation_terms`, `employment_type`.
- `confirmed` and `vague` fields always carry non-null `evidence`
  (`{text, start, end}`, offsets into the posting text you submitted).
  `absent` fields never carry evidence.
- Typed errors are always returned as `{"error": {"code", "message",
  "details"}}` with `code` one of `invalid_input`, `analysis_failed`,
  `provider_unavailable`, `no_match_found`, `data_not_ready`.
- `GET /api/v1/data/gap-stats` always returns `{"ready": bool, "stats": ...,
  "error": ...}` -- check `ready` before reading `stats`; it is `false`
  (with a `data_not_ready` error) until the data track publishes adjudicated
  gold labels.
- Financial figures are deterministic; `FinancialComparison` never contains
  a recommended winner.
