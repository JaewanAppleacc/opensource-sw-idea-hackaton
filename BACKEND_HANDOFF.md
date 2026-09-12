# Backend handoff

Status: **AI/backend track complete** per `TASK_AI_BACKEND.md`. Runs fully
offline with the deterministic mock provider; no API key required.

## Run it

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt

cd backend
uvicorn app.main:app --reload --port 8000
```

Health check: `curl http://127.0.0.1:8000/api/v1/health`

## Test it

```bash
source .venv/bin/activate
python -m pytest tests/backend -q
```

66 tests, all offline (mock provider, bundled fixture dataset). No network
access or API key required.

## Regenerate the contract

Whenever a model in `backend/app/models/**` changes:

```bash
cd backend
python -m scripts.export_contracts
```

Regenerates `contracts/schema.json` and `contracts/openapi.json`. Commit both.

## Endpoints

All under `/api/v1`. Errors are always `{"error": {"code", "message",
"details"}}` with `code` in `invalid_input`, `analysis_failed`,
`provider_unavailable`, `no_match_found`, `data_not_ready`.

### `GET /health`

Service status, active provider mode (`mock` / `anthropic`), dataset
availability, rubric version. No secrets.

```json
{"status": "ok", "provider_mode": "mock", "dataset_available": true, "rubric_version": "v1"}
```

### `POST /postings/analyze`

Input: `{"posting_id?": str, "source_text": str, "source_url?": str, "expected_occupation?": str}`

Pipeline: mock/real provider extracts a candidate status + evidence span per
field -> Pydantic schema validation (`extra="forbid"`, closed status enum,
at most one retry on schema/evidence failure) -> exact substring/offset
check against `source_text` -> deterministic per-field rule
(`backend/app/rules/field_rules.yaml`) that can only **downgrade**
confirmed -> vague -> absent, never upgrade and never invent evidence ->
verification action generated for every vague/absent field.

Example request:

```json
{"source_text": "직무: 백엔드 개발자\n고용형태: 정규직으로 채용합니다\n담당업무: 결제 시스템 API 설계 및 개발, 서버 배포 자동화 구축\n사용언어: Python과 SQL을 사용하며 AWS 인프라를 운영합니다\n급여: 연봉 3,200만원 (세전)\n수습기간: 입사 후 3개월이며 수습 중에도 급여의 100%를 동일하게 지급합니다\n멘토링: 입사 후 1개월간 사수가 1:1로 정기 교육을 진행합니다\n"}
```

Example response (abridged): every field `confirmed`, each with an
`evidence.text` that is an exact substring of `source_text` at
`evidence.start:evidence.end`, `verification_actions: []`.

For `"급여: 회사 내규에 따름"`, `salary` comes back `"status": "vague"`,
`"reason_code": "vague_marker_matched"`, and a `verification_actions` entry
`{"field": "salary", "channel": "email", "triggered_by_status": "vague", ...}`.

### `POST /postings/match`

Input: `{"occupation": str, "employment_type?": str, "posting_id?": str}`

Reads the local curated dataset (`JEONBUK_DATASET_PATH`, defaults to this
track's small synthetic fixture at
`backend/app/datasets/jeonbuk_fixture.jsonl`). Matches by exact occupation
(required) and employment type (optional; ranks matches and reports
mismatches rather than hiding them). Returns at most 3 candidates, each
carrying a fixed `description` stating the result comes from a finite
curated dataset -- never a "best in Jeonbuk" claim. Raises
`no_match_found` (404) when the occupation has zero candidates.

### `POST /finance/compare`

Pure deterministic arithmetic, no LLM. Input: `metropolitan` and `jeonbuk`
`FinancialOption` objects (`monthly_income_after_tax`,
`monthly_housing_cost`, `monthly_other_living_cost`, `deposit`), plus
optional named `assumptions` (`annual_income_growth_rate`,
`annual_cost_growth_rate`, `rounding_unit_krw`, default 100,000 KRW).

Output per option: `monthly_surplus`, `one_year_liquid_cash`,
`three_year_liquid_cash` (secondary, assumption-dependent), `deposit_locked`
kept separate from liquid cash, and `*_total_with_deposit` for anyone who
wants the deposit folded back in explicitly. `crossover` always varies
`monthly_housing_cost` on whichever option currently has the **lower**
housing cost (ties resolve to `jeonbuk`) -- never income, since varying
income is an algebraic tautology. `threshold_value` is rounded to
`rounding_unit_krw`. No field ever names a winner; `disclaimer` says so
explicitly.

### `GET /data/gap-stats`

Reads only adjudicated human gold labels from `GOLD_LABELS_PATH` (default
`data/gold/adjudicated_labels.json`, owned by the data track). Response is
always `{"ready": bool, "stats": ..., "error": ...}`. Until the data track
publishes that file, this returns `{"ready": false, "error": {"code":
"data_not_ready", ...}}` -- it never falls back to AI-generated labels.
`stats.exploratory` is always `true`.

## Domain models & contract

Canonical Pydantic models live in `backend/app/models/**`; the
machine-readable export lives in `contracts/` (`schema.json`,
`openapi.json`, see `contracts/README.md`). All contract models reject
additional properties. `AuditedField.status` is exactly `confirmed` /
`vague` / `absent` -- no `external_verified`. `ExternalContext` is a
separate model and nothing in the pipeline ever uses it to mutate a
posting field's status (the MVP pipeline always returns `external_context:
[]`; the model exists so a future integration has a typed, provenanced
place to put it).

## Provider abstraction

`app/providers/base.py` defines the narrow interface
(`extract(source_text, expected_occupation) -> dict`). Two implementations:

- `MockExtractionProvider` (default, `LLM_PROVIDER=mock`): fully
  deterministic and offline. Finds the line in the posting text containing
  each field's anchor keywords and reports that exact line (correct
  offsets) as a "confirmed" candidate; the deterministic rule layer then
  decides the real status. Never invents text not present in the source.
- `AnthropicExtractionProvider` (`LLM_PROVIDER=anthropic`, needs
  `ANTHROPIC_API_KEY` and the optional `anthropic` package): forces a
  structured tool call matching the same wire schema. Any missing
  dependency/key/request failure raises `ProviderUnavailableError`
  (503) -- never silently downgraded to a posting status, and never
  retried (retrying an unavailable provider wastes nothing but gains
  nothing).

## Deterministic field rules

`backend/app/rules/field_rules.yaml` (+ `field_rules.py`) holds, per field:
anchor keywords (for the mock provider), vague markers, relevance keywords,
and a confirmed-criteria rule (`amount_and_unit` for salary,
`duration_and_condition` for probation, `specific_keywords` for the rest).
Override the whole file via `FIELD_RULES_PATH` once the data track ships
its own rubric-derived version -- no pipeline code changes needed.

## Known limitations / assumptions

- **Fixture data only.** `backend/app/datasets/jeonbuk_fixture.jsonl` (5
  records) is synthetic, written for this track's tests/demo -- not real
  scraped postings. Swap in the data track's file via
  `JEONBUK_DATASET_PATH` without touching any code.
- **Rule-based mock provider, not an LLM.** It is deterministic and
  offline by design (per `TASK_AI_BACKEND.md`), but its recall depends on
  the posting following a roughly one-topic-per-line layout with
  recognizable Korean keywords. The real provider (`AnthropicExtractionProvider`)
  is the intended production path; it has not been exercised against a
  live API key in this environment (no key was available here) -- its
  `provider_unavailable` failure path is covered by tests, its happy path
  is not.
- **`gap-stats` has no gold labels yet.** `data/gold/adjudicated_labels.json`
  does not exist in this repo yet (data track's job). The endpoint is
  fully implemented and tested against a synthetic fixture
  (`tests/backend/fixtures/gold_labels_sample.json`); it will pick up the
  real file automatically once the data track publishes it, or via
  `GOLD_LABELS_PATH`.
- **`external_context` is always `[]`.** The `ExternalContext` model and
  its non-mutation guarantee are implemented and modeled in the contract,
  but no external data source is wired into the pipeline in this MVP.
- **No persistence.** Nothing is written to disk; posting text and
  financial inputs are never logged.
- **Three-year scenario** compounds `annual_income_growth_rate` /
  `annual_cost_growth_rate` (both default `0.0`) over 3 years on top of the
  entered monthly figures -- it is explicitly a scenario, not a forecast,
  and there is no five-year projection.

## Ownership / boundaries respected

Everything above lives under `backend/**`, `tests/backend/**`,
`contracts/**`, plus this file and `.env.example` at the repo root.
`frontend/**` and `data/**` (data/rubric/annotation track) were not
touched.
