# Project instructions: Jeonbuk Career Due-Diligence Agent

## Canonical repository

- GitHub: https://github.com/JaewanAppleacc/opensource-sw-idea-hackaton.git
- Remote: `origin`
- Default branch: `main`
- Keep all implementation, data, tests, and handoff documents for this project in this repository. Do not create a parallel implementation elsewhere.

## Mission

Build the AI, backend, data, and evaluation side of a hackathon MVP for Jeonbuk youth.

The product accepts a metropolitan-area job posting or desired role, presents one or more pre-curated comparable Jeonbuk postings, audits both postings using evidence from the original text, compares only verifiable conditions, and converts unresolved information into concrete verification actions. It may also calculate a small, explicitly hypothetical cash-accumulation comparison from user-entered values.

This is not a general interview coach, a Jeonbuk promotional recommender, a company-rating service, or a future-prediction engine.

## Product flow

1. Accept a metropolitan-area posting or desired role.
2. Extract occupation and employment type.
3. Retrieve comparable Jeonbuk postings from a curated local dataset. The MVP does not need live nationwide search.
4. Audit six fields in every posting.
5. Validate every cited evidence span against the original text.
6. Convert vague or absent fields into an email, phone, interview, document-review, or pre-contract verification action.
7. Compare the two postings without assigning an overall score or winner.
8. If the user supplies financial assumptions, calculate monthly surplus, one-year accumulation, a three-year scenario, and one-variable crossover conditions with deterministic code.

## Six audited fields

- `salary`
- `duties`
- `tools_or_skills`
- `training_or_mentoring`
- `probation_terms`
- `employment_type`

Each posting field has exactly one status:

- `confirmed`: specific enough for the applicant to make the relevant decision.
- `vague`: related wording exists, but it is not specific enough for a decision.
- `absent`: no relevant wording is present.

Do not add `external_verified` to this enum. External facts are orthogonal context and must never mutate a posting field from `vague` or `absent` to `confirmed`.

System failures are also not posting statuses. Return typed errors such as `analysis_failed`, `invalid_input`, or `provider_unavailable` separately.

## Grounding and safety rules

- Structured output must be enforced with Pydantic and/or JSON Schema.
- Reject additional properties.
- Every `confirmed` or `vague` field requires an exact `evidence_text` and offsets into the source posting.
- Verify in code that the evidence text matches the source substring at those offsets.
- Substring existence alone is insufficient. Add deterministic semantic checks where practical. For example, confirmed salary requires an amount or range plus a unit; confirmed probation requires both duration and pay/condition detail.
- If validation fails, retry extraction at most once. If it still fails, return a typed analysis error or downgrade only when the rubric explicitly permits it. Never silently invent evidence.
- Never generate company stability, growth, turnover, culture, career-growth, or risk scores.
- Never describe a company as stable, unstable, growing, suspicious, or high-turnover.
- Never infer actual salary from National Pension contribution data.
- Do not use an LLM for arithmetic, filtering, aggregation, thresholds, or scenario calculations.
- Factual numbers rendered to users must come from typed source data or deterministic calculations, not free-form LLM prose.
- Show assumptions, provenance, reference dates, and limitations with external context.
- Do not persist resumes, personal financial details, or personally identifying data in the MVP.

## Financial comparison rules

Keep the calculator deliberately small. Inputs per option are:

- monthly after-tax income
- monthly housing cost including maintenance
- other monthly living costs
- housing deposit

Primary outputs:

- monthly surplus
- one-year accumulation
- three-year scenario as a secondary, assumption-dependent value
- one-variable crossover condition, rounded to a sensible unit

The deposit is locked wealth, not consumption. Present liquid cash separately from total assets including the deposit, or omit it from accumulated cash and label it separately. Do not provide a five-year forecast. Do not recommend a winner.

## Architecture constraints

- Prefer a plain Python/FastAPI function pipeline.
- Use Pydantic models as the canonical contract.
- LangChain components may be used only when they reduce code for loading or structured output.
- Do not add LangGraph unless the product gains a genuine multi-turn stateful loop.
- Do not add RAG for the one-occupation MVP; the full rubric fits in context.
- Do not add a product-level multi-agent system.
- MCP is optional and may only be added after the core passes tests. If added, expose aggregate statistics and annotation rules for external reuse; the product itself should continue reading SQLite/JSON directly.

## Data and evaluation rules

- Select the occupation only after checking that enough Jeonbuk postings exist from the same source and period.
- Minimum dataset: 10 Jeonbuk and 10 matched metropolitan postings. Target: 20 and 20 if time permits.
- Match source, collection period, occupation, and employment type. Record unmatched cases without inferring why they were unmatched.
- Two humans must label every field independently using `confirmed`, `vague`, or `absent`.
- AI-generated labels may be suggestions but must never be presented as human gold labels.
- Record raw annotator labels, agreement, adjudicated gold labels, and rubric version.
- Freeze a stratified 20% holdout before prompt tuning. Do not inspect or tune on it after freezing.
- With a 10:10 dataset, report raw correct/incorrect counts and overall three-class agreement on the small holdout. Do not overstate per-field F1.
- All regional findings are exploratory sample findings, not claims about all Jeonbuk postings.
- Do not redistribute full posting text unless the source license permits it. Otherwise publish source identifiers/URLs, derived labels, aggregate statistics, and synthetic examples.

## Repository ownership and concurrency

The frontend is owned by another developer. Do not edit `frontend/**`, UI styling, or frontend dependencies unless explicitly asked.

Parallel tracks should own separate paths:

- AI/backend track: `backend/**`, `tests/backend/**`, `contracts/**`
- Data/evaluation track: `data/**`, `scripts/data/**`, `tests/data/**`, `docs/data/**`
- Integration track runs only after both are ready and may edit backend adapters, contracts, root documentation, and tests, but still not `frontend/**`.

The API contract in `contracts/**` is the boundary. Propose contract changes explicitly and avoid silently breaking fields already consumed by the frontend.

Preserve existing user changes. Inspect the repository before editing. Do not rewrite unrelated files.

## Definition of done

The backend is complete when a cached demo can run without internet and perform:

`metropolitan posting -> curated Jeonbuk match -> six-field audit -> evidence validation -> verification actions -> deterministic monthly-surplus comparison`.

The evidence and error paths must be tested. A polished but ungrounded demo is not complete.

