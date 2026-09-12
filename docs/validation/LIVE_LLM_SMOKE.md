# Live LLM smoke validation (Phase B + Phase C, P0 integration)

This record distinguishes two separate results, per the task's requirement
not to conflate them: the offline mock pipeline check, and the real
Anthropic provider check. **Do not read one as evidence for the other.**

## Environment

- Date/time: 2026-09-12 (KST)
- Branch: `feature/p0-integration-live-llm` (merged from `origin/main` +
  `origin/feature/real-data-acquisition` + `origin/feature/annotation-workflow-prep`)
- Backend run via: `python3 -m uvicorn app.main:app --app-dir backend --port <port>`
- Fixture posting used for both checks: `MET-001` (synthetic, from
  `data/postings/postings.jsonl`, `synthetic_test_fixture`/`source_name: synthetic_fixture_v1`
  — not a real posting, contains no personal data or real company identity)

## Phase B — offline mock pipeline (baseline, required before Phase C)

- Provider: `mock` (`LLM_PROVIDER=mock`)
- `GET /api/v1/health` → `200 OK`, `{"status":"ok","provider_mode":"mock","dataset_available":true,"rubric_version":"1.0.0-draft"}`
- `POST /api/v1/postings/analyze` with `MET-001` → `200 OK`
- Automated check (`verify_analysis.py`, ad hoc script, not committed —
  logic mirrors `backend/app/services/evidence.py`) confirmed:
  - Exactly the 6 required fields present, each exactly once:
    `salary`, `duties`, `tools_or_skills`, `training_or_mentoring`,
    `probation_terms`, `employment_type`.
  - Every field's `status` is one of `confirmed | vague | absent`.
  - Every `confirmed`/`vague` field's `evidence.text` is an exact substring
    of the source text at `evidence.start:evidence.end` (verified: 5 of 5
    confirmed fields for this posting; `tools_or_skills` came back `absent`
    with `evidence: null`, which is correct for this posting text — it does
    not mention specific tools/certifications).
  - The `absent` field (`tools_or_skills`) produced exactly one
    `verification_action` (`channel: interview`).
  - No company stability/growth/culture/risk judgement appeared anywhere in
    the response.
- **Result: PASS.** The offline pipeline is verified end-to-end. This is
  the pre-existing behavior from the AI/backend track's own test suite
  (72 backend tests, unchanged by this integration) plus this manual smoke
  check; it is not itself evidence that live Anthropic calls succeed.

## Phase C — real Anthropic provider check

- Provider: `anthropic` (`LLM_PROVIDER=anthropic`, `ANTHROPIC_MODEL=claude-sonnet-5`)
- `ANTHROPIC_API_KEY`: present (confirmed via `test -n "$ANTHROPIC_API_KEY"`
  only; the value was never displayed, logged, or written to any file by
  this validation).
- `GET /api/v1/health` → `200 OK`,
  `{"status":"ok","provider_mode":"anthropic","dataset_available":true,"rubric_version":"1.0.0-draft"}`
  — confirms the app is actually configured for the real provider, not a
  silent mock fallback.
- `POST /api/v1/postings/analyze` with the same `MET-001` posting →
  **`503 Service Unavailable`**:
  ```json
  {"error": {"code": "provider_unavailable", "message": "anthropic request failed: Error code: 400 - {'type': 'error', 'error': {'type': 'invalid_request_error', 'message': 'Your credit balance is too low to access the Anthropic API. Please go to Plans & Billing to upgrade or purchase credits.'}, 'request_id': 'req_011CeyYRjgBJPqrWsKKKwa4S'}", "details": null}}
  ```

### Result: **BLOCKED — Anthropic account has insufficient credit balance.**

This is **not** a code defect and **not** a missing/invalid key:

- The key was accepted far enough to reach Anthropic's billing check (a
  bad/missing key would fail earlier, inside the SDK client construction,
  with a different message).
- The failure is Anthropic's own `invalid_request_error` /
  "credit balance too low" response, surfaced to us as an HTTP 400 from
  their API.
- Our pipeline correctly classified this as `provider_unavailable`
  (typed error, HTTP 503) rather than downgrading any field to `absent` or
  falling back to the mock provider silently. `provider_mode` in the health
  check confirms `anthropic` was genuinely selected throughout.
- No actual six-field analysis output exists from the real Anthropic model
  for this run — do not read the Phase B mock output as if it were the
  Phase C result.

### What was and was not fixed

No code changes were needed or made to `backend/**` for this check: model
ID resolution (`ANTHROPIC_MODEL` env var → `Settings.anthropic_model` →
`AnthropicExtractionProvider(model=...)`), the forced-tool-call structured
output schema, and the `provider_unavailable` error mapping were all
already correct and required no fix.

### Confirmation of no secret exposure

- The raw key value never appeared in any command output, exception
  message, log file, or file written by this validation.
- `grep -inE "sk-ant|authorization|x-api-key"` against the server's stdout
  log for this run returned no matches.
- `ANTHROPIC_API_KEY` was sourced from a local, gitignored `.env` file
  (never committed) into the shell environment for the duration of the
  live-mode server process only, then that process was stopped.

## Next step to complete Phase C

A human needs to add credit / upgrade the plan on the Anthropic account
tied to this key (console.anthropic.com → Plans & Billing), then re-run:

```bash
export ANTHROPIC_API_KEY='...'   # your own terminal, never pasted into chat
export LLM_PROVIDER=anthropic
export ANTHROPIC_MODEL=claude-sonnet-5
python3 -m uvicorn app.main:app --app-dir backend --port 8812 &
curl -s http://127.0.0.1:8812/api/v1/health
curl -s -X POST http://127.0.0.1:8812/api/v1/postings/analyze \
  -H "Content-Type: application/json" \
  -d '{"posting_id":"MET-001","source_text":"<MET-001 full_text from data/postings/postings.jsonl>","expected_occupation":"생산직(제조 조립원)"}'
```
and re-verify the same conditions listed under Phase B against the real
response.
