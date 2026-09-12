# Evidence-Grounded Harness

Standalone reference for this product's AI safety/evaluation harness (see
`docs/architecture/EXPANSION_TECH_ASSESSMENT.md` section 5 for the full
adoption-decision writeup this summarizes). Unchanged by
`feature/work24-ai-extension-layer` -- no backend file was touched on this
branch.

## What it is

Not a framework. A chain of deterministic checks, entirely hand-written,
that sits between any LLM/mock provider's raw output and what a user ever
sees:

```text
Provider (mock | anthropic | nvidia)
        │  raw dict, never trusted
        ▼
RawExtraction.model_validate()         ── schema gate (extra=forbid, 6 fields exactly once)
        │
        ▼
validate_evidence_span() per field     ── source_text[start:end] == evidence_text, else reject
        │  (schema/evidence failure -> retry once, MAX_ATTEMPTS=2; provider failure -> never retried)
        ▼
evaluate_confirmed() per field         ── deterministic rubric rule; downgrade-only, never invent
        │
        ▼
AuditedField (status ∈ {confirmed, vague, absent}, reason_code required)
        │
        ▼
build_verification_action() for vague/absent
        │
        ▼
PostingAnalysis  ──────────────────────► API response (StrictModel, extra=forbid)
```

## Controls, by file

- **Schema validation** — every request/response model is a `StrictModel`
  (`backend/app/models/common.py`, `extra="forbid"`); raw provider output
  additionally validates against `RawExtraction`
  (`backend/app/providers/raw.py`).
- **Evidence offset/substring verification** — `validate_evidence_span()`
  (`backend/app/services/evidence.py`) rejects any evidence whose
  `source_text[start:end]` doesn't match the claimed text exactly.
- **Deterministic downgrade rules** — `evaluate_confirmed()`
  (`backend/app/rules/field_rules.py:71`) can only downgrade
  confirmed→vague→absent, never upgrade, never invent.
- **Retry limit** — exactly one retry on schema/evidence failure
  (`MAX_ATTEMPTS = 2`, `backend/app/services/audit_pipeline.py:23`); a
  provider connectivity failure is never retried and never silently
  downgraded into a posting status.
- **Provider fail-closed** — an unrecognized `LLM_PROVIDER` value raises a
  typed error instead of falling back to mock
  (`backend/app/providers/factory.py`); `_scrub_secret`
  (`anthropic_provider.py:68`) strips the configured key from any exception
  text before it reaches an API response.
- **Closed three-value status enum** — `confirmed | vague | absent` only.
  `external_verified` is never added; external context is shown separately
  and never mutates a field's status (`ExternalContext`,
  `backend/app/models/posting.py`).
- **Frontend presentation layer never widens this enum for backend
  purposes** — `feature/work24-ai-extension-layer` adds a UI-only
  `not_evaluated` display status (`src/lib/comparisonAxes.ts`,
  `AxisDisplayStatus`) for sub-items that have no backing atomic field at
  all (근로시간·교대제·통근, 복지·기숙사·통근지원). It is structurally
  excluded from `buildPriorityUnresolvedList` (only matches
  `'vague' | 'absent'`) and never sent to or received from the backend --
  the backend's `FieldStatus` type is untouched.
- **Tests and contract verification** — automated test suite
  (`python -m pytest -q`) plus a contract-diff discipline
  (`contracts/schema.json`/`openapi.json` regenerated and diffed before
  every merge in this project's history).

## What would NOT improve this

A third-party "LLM eval harness" or LangChain-style output-parsing layer
would either duplicate these checks or replace them with a looser, more
generic notion of "groundedness" than this product's exact-substring
requirement. See `EXPANSION_TECH_ASSESSMENT.md` section 2's explicit
warning: do not claim LangChain (or any framework) prevents hallucination.
This harness is what does that work today, independent of provider or
framework choice.
