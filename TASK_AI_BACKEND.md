# Parallel task A: AI and backend implementation

Read `CLAUDE.md` completely before working. This task runs in parallel with `TASK_DATA_EVALUATION.md`. Do not edit the data track's owned paths or `frontend/**`.

## Objective

Implement a locally runnable FastAPI backend for the Jeonbuk career due-diligence MVP. Use fixture data initially so backend development is not blocked by the final dataset.

## First actions

1. Inspect the repository, existing framework, tests, and instructions.
2. If no backend exists, create a minimal Python/FastAPI package under `backend/` without modifying the frontend.
3. Define the canonical Pydantic models first and export a frontend-readable schema under `contracts/`.
4. Add a deterministic mock LLM provider so all endpoints and tests work without an API key.

## Required domain models

Create typed models equivalent to:

- `PostingInput`
- `PostingAnalysis`
- `AuditedField`
- `EvidenceSpan`
- `VerificationAction`
- `ExternalContext`
- `MatchCandidate`
- `FinancialOption`
- `FinancialComparison`
- typed API error models

`AuditedField.status` must allow only `confirmed`, `vague`, and `absent`.

Required behavior:

- `confirmed` and `vague` require evidence.
- `absent` must have null evidence.
- `ExternalContext` is separate from posting fields.
- No free-text interpretation or company-rating field is allowed.
- Reject unknown fields in all models.

## Endpoints

Implement versioned endpoints. Exact paths may follow existing repository conventions, but the capabilities must be present.

### Health

`GET /api/v1/health`

Return service status, model-provider mode, and dataset availability without secrets.

### Analyze a posting

`POST /api/v1/postings/analyze`

Input:

- posting ID if available
- source text
- optional source URL
- optional expected occupation

Output:

- six audited fields
- exact evidence spans
- validation warnings
- verification actions for vague/absent fields
- typed errors when analysis cannot be completed

Pipeline:

1. Validate input.
2. Call the structured extraction provider.
3. Validate JSON/Pydantic schema.
4. Check offsets and exact source substring.
5. Apply deterministic field rules.
6. Retry once on recoverable extraction failure.
7. Generate actions only from validated gaps.

Do not downgrade provider or schema failure to `absent`; that would falsely describe the posting.

### Match a Jeonbuk posting

`POST /api/v1/postings/match`

For the MVP, read a curated local JSONL/SQLite dataset. Match by explicit occupation and employment type first. Return at most three candidates with:

- source ID and URL
- matching fields
- mismatch fields
- a plain description that the result comes from the finite curated dataset

Do not claim that candidates are the best postings in Jeonbuk. Do not use a vector database or live scraping.

The endpoint must work initially with a small fixture dataset owned by this track. Add an adapter so the data track's final file can replace the fixture without changing the API.

### Compare financial assumptions

`POST /api/v1/finance/compare`

Inputs for metropolitan and Jeonbuk options:

- monthly after-tax income
- monthly housing plus maintenance
- other monthly living costs
- deposit
- explicitly named scenario assumptions

Outputs:

- monthly surplus for each option
- one-year accumulated liquid cash
- three-year assumption-dependent liquid cash
- deposit shown separately as locked wealth
- one-variable crossover condition with the varied variable and all held-constant assumptions

The crossover variable must be `monthly housing plus maintenance` on the option that currently has the lower value, not income. Varying income produces an algebraic tautology (surplus difference == income difference), which gives the user no new information. Housing cost is externally verifiable before an offer decision and is what the user should go check. Round the crossover threshold to a sensible unit (for example, the nearest 100,000 KRW), not the raw computed value.

All calculations must be pure deterministic functions with unit tests. Never use the LLM here. Do not produce a winner or recommendation.

### Regional sample statistics

`GET /api/v1/data/gap-stats`

Read only adjudicated human labels when available. Return sample counts, filters, rubric version, label proportions, and an explicit `exploratory: true` flag. If gold labels are absent, return a typed not-ready response rather than using AI labels.

## Evidence harness

Implement and test:

- exact substring/offset validation
- no evidence for `absent`
- required evidence for `confirmed` and `vague`
- salary confirmed rule: numeric amount/range plus time/currency unit
- probation confirmed rule: duration and material condition/pay detail
- common vague markers
- schema rejection of unsupported keys and statuses
- maximum one retry
- safe typed failure after retry exhaustion

Keep field-specific rules configurable so the data track's rubric can later supply them.

## Provider abstraction

Implement a narrow interface with at least:

- deterministic mock/fixture provider
- one real structured-output provider selected from dependencies or available environment

Use environment variables for secrets and provide `.env.example` without real keys. Do not log posting contents or user financial inputs by default.

## Tests

At minimum cover:

- valid confirmed evidence
- vague salary such as `회사 내규에 따름`
- truly absent field
- fabricated evidence string
- correct text at wrong offsets
- irrelevant but real evidence being rejected by a deterministic rule
- invalid status/additional property
- provider failure and retry exhaustion
- no Jeonbuk match
- deterministic financial calculations
- deposit not counted as consumption
- crossover result and rounding
- stats endpoint refusing non-gold labels

## Deliverables

- backend implementation
- backend tests
- machine-readable contract in `contracts/`
- local fixture dataset sufficient for backend tests only
- `.env.example`
- backend run/test instructions
- short `BACKEND_HANDOFF.md` describing endpoints, assumptions, known limitations, and example payloads

## Completion check

Demonstrate with commands that:

1. tests pass;
2. the server starts locally;
3. one metropolitan fixture returns at least one curated Jeonbuk candidate;
4. one posting returns all six audited fields with verified evidence;
5. one vague field becomes a verification action;
6. financial comparison is deterministic; and
7. the full demo still works with the real provider disabled.

Do not implement MCP, RAG, LangGraph, or multi-agent orchestration in this task.

