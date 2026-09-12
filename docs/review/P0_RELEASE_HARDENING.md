# P0 release hardening review — pre-merge check on PR #1

Branch: `feature/p0-release-hardening`, based on
`origin/feature/p0-integration-live-llm` (PR #1:
https://github.com/JaewanAppleacc/opensource-sw-idea-hackaton/pull/1).

Baseline commit reviewed: `74d6862` (docs: record NVIDIA live
structured-output attempt as blocked).

## Full test results

- Baseline (before any change): `python -m pytest -q` → **188 passed**,
  `git diff --check` clean. Matches PR #1's reported baseline exactly.
- After hardening fixes: `python -m pytest -q` → **201 passed**
  (188 baseline + 13 new tests in `tests/backend/test_provider_factory.py`).
  No existing test was weakened, skipped, or deleted.

## Secret / git safety scan (values never printed)

All checks below were run against the tracked working tree **and** full
git history reachable from this branch (`git log --all -p -S<pattern>`),
not just the current diff.

| Check | Result |
|---|---|
| `.env` tracked as a file | Not tracked, never added in history |
| `nvapi-…` pattern in tracked files (any commit) | 0 matches |
| `sk-ant-…` pattern in tracked files (any commit) | 0 matches |
| Real key in staged/working diff | 0 matches |
| API key in docs/fixtures/exception strings | 0 matches (checked `docs/validation/LIVE_LLM_SMOKE.md` specifically, since it discusses a prior key-exposure incident — it names the incident type and rotation only, never the value) |
| `.env.example` key fields empty | `ANTHROPIC_API_KEY=` and `NVIDIA_API_KEY=` both empty |
| `__pycache__` / `.pyc` / `.log` tracked | None tracked |
| `data/private/**` git-ignored | Confirmed via `git check-ignore -v` on sample paths under it |

**No `SECRET_CANDIDATE_FOUND` entries.** No history rewrite was performed
or needed.

Regarding the prior NVIDIA key-exposure incident already documented in
`docs/validation/LIVE_LLM_SMOKE.md`: that document was re-checked in this
review and contains only the incident type, confirmation that the key was
rotated, and the process fix (clean `.env`, value only ever read via
`grep`/`cut` into a shell variable, never printed) — no key value or
fragment appears there, in this report, or anywhere else touched by this
branch.

## Provider fail-closed review (`backend/app/providers/**`, `config.py`, `errors.py`)

Checked all 10 conditions from the task against the PR #1 baseline:

| # | Condition | Baseline result |
|---|---|---|
| 1 | Exactly `mock`/`anthropic`/`nvidia` supported | OK |
| 2 | Typo/unknown `LLM_PROVIDER` doesn't silently become mock | **FAIL** — `factory.get_provider()` returned `MockExtractionProvider()` for any value other than `"anthropic"`/`"nvidia"`, including typos |
| 3 | Unknown provider fails with an explicit/typed error | **FAIL** — same root cause as #2 |
| 4 | Anthropic/NVIDIA auth/quota/timeout/network errors never become `absent` | OK — `analyze_posting()` calls `provider.extract()` outside its retry/except block; any `ProviderUnavailableError` propagates immediately (already covered by `tests/backend/test_audit_pipeline.py::…RaisingProvider…`) |
| 5 | No automatic mock fallback on real-provider failure | OK — no such fallback exists anywhere in `audit_pipeline.py`/`factory.py` |
| 6 | Real-provider timeout is finite | OK — NVIDIA: explicit `REQUEST_TIMEOUT_SECONDS = 30`; Anthropic: SDK default `Timeout(connect=5.0, read=600, write=600, pool=600)` (verified via `anthropic.Anthropic(api_key="x").timeout`, no network call) |
| 7 | Error strings never contain key/Authorization header/request body | **Hardened** — see below |
| 8 | `/health` `provider_mode` matches real setting | OK — `health.py` reads `settings.llm_provider` directly, no separate/stale state |
| 9 | Mock only selected when `LLM_PROVIDER=mock` (explicitly or by documented default) | Fixed by the #2/#3 fix |
| 10 | Blocked live-validation status not overstated as success | OK — re-read `docs/validation/LIVE_LLM_SMOKE.md`; PASS is scoped only to the mock pipeline, both Anthropic and NVIDIA sections are explicit `BLOCKED …` with no success language |

### Defects found and fixed

**1. `backend/app/providers/factory.py` — silent mock fallback for unknown `LLM_PROVIDER` (conditions 2, 3, 9).**

Before: the final line was an unconditional `return MockExtractionProvider()`,
so `LLM_PROVIDER=Anthropic` (wrong case), a trailing space, or any other
typo would run the deterministic mock while `/health` would report that
same wrong string back — nothing would visibly indicate a real LLM check
never happened. Fixed by making `"mock"` its own explicit branch and
raising the existing `ProviderUnavailableError` (503, `provider_unavailable`
— no new error code, no contract change) for anything else, naming the bad
value in the message so it's diagnosable.

**2. `backend/app/providers/anthropic_provider.py` and `nvidia_provider.py` — error messages not defensively scrubbed of the configured key (condition 7).**

Before: `raise ProviderUnavailableError(f"... {exc}")` interpolated the
underlying SDK/`httpx` exception's `str()` verbatim. Live evidence from PR
#1's own validation (`docs/validation/LIVE_LLM_SMOKE.md`) shows neither the
Anthropic SDK's nor NVIDIA's `httpx` error strings currently include the
key in the exception paths actually observed (billing/auth/timeout
errors) — so this was not an *active* leak, but nothing in the code
guaranteed it, and error `message` fields flow straight into the API's
JSON error response (`APIError.message`). Added a small `_scrub_secret()`
helper (shared, defined once in `anthropic_provider.py`, imported by
`nvidia_provider.py`) that replaces the literal configured key value with
`[REDACTED]` in the exception text before it is wrapped. This is defense
in depth, not a reaction to an observed leak in this codebase — a new
regression test engineers a worst-case exception that embeds the key and
confirms it no longer surfaces.

No other defects were found. `errors.py`, `config.py`, and `.env.example`
required no changes — their existing shape already satisfied every
relevant condition.

## Tests added (`tests/backend/test_provider_factory.py`, 13 tests, no network)

- Unset `LLM_PROVIDER` → mock; explicit `"mock"` → mock
- `"anthropic"` → `AnthropicExtractionProvider`; `"nvidia"` → `NvidiaExtractionProvider`
- Parametrized: `"Anthropic"`, `"nvidia "`, `"openai"`, `"anthropic-v2"`,
  `"MOCK"`, `""` → each raises `ProviderUnavailableError` naming the bad
  value, and is asserted to **not** be a `MockExtractionProvider`
- Anthropic missing key → typed `ProviderUnavailableError` (mirrors the
  existing NVIDIA test in `test_nvidia_provider.py`)
- Anthropic and NVIDIA: a worst-case exception embedding the configured
  key is confirmed **not** to appear in the raised error message

No existing test was modified, weakened, or removed. No live NVIDIA/Anthropic
network call was made anywhere in this review or its tests — all provider
failure paths are exercised with monkeypatched/fake clients.

## API contract

`cd backend && python -m scripts.export_contracts` was re-run after all
fixes. `git status --short contracts/` reported **no changes** —
`contracts/schema.json` and `contracts/openapi.json` are byte-identical to
PR #1's, confirming no request/response model was touched.

## Files changed and why

| File | Reason |
|---|---|
| `backend/app/providers/factory.py` | Fail-closed fix for unknown `LLM_PROVIDER` (defects #1) |
| `backend/app/providers/anthropic_provider.py` | Adds shared `_scrub_secret()` helper + uses it (defect #2) |
| `backend/app/providers/nvidia_provider.py` | Imports and uses `_scrub_secret()` (defect #2) |
| `tests/backend/test_provider_factory.py` | New regression coverage for both fixes (13 tests) |

`.env.example`, `backend/app/errors.py`, `backend/app/config.py` were
reviewed and required no changes.

## Confirmations

- No new product API, endpoint, or request/response model was added.
- No LangGraph/LangChain/RAG/MCP/vector-DB/multi-agent dependency was added.
- No new LLM provider or model was explored; only the three already in PR
  #1 (`mock`, `anthropic`, `nvidia`) were reviewed and hardened.
- **No live Anthropic or NVIDIA network call was made in this review.**
  Every provider-failure test uses a monkeypatched/fake client.
- No real posting, real human label, or real regional statistic was
  created, read, or modified. `data/intake/**`, `data/private/**`,
  `docs/acquisition/**`, `scripts/acquisition/**`, `data/postings/**`, and
  `frontend/**` were not touched.
- `main` and the PR #1 branch itself were never committed to directly; all
  work happened on `feature/p0-release-hardening`.

## Status

## `FIXED_AND_READY_FOR_PR_REVIEW`

Two real, minimal, scoped defects were found and fixed (unknown-provider
fail-closed behavior; defensive key-scrubbing in error messages), backed
by 13 new offline regression tests. Full suite: 201/201 passed. API
contract: byte-identical, unchanged.
