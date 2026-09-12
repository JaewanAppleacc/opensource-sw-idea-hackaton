# REAL_DATA_ACQUISITION_HANDOFF.md — Parallel task D1

Read alongside `CLAUDE.md`, `DATA_HANDOFF.md`, and
`TASK_REAL_DATA_ACQUISITION.md`. This document is the single source of truth
for the real-data acquisition track's status.

## Decision

> **`BLOCKED_INSUFFICIENT_SAMPLE`**

Reproducible acquisition tooling for both approved paths now exists and is
tested, but **zero real Jeonbuk or metropolitan postings have been ingested
into this repository.** Per the completion criteria in
`TASK_REAL_DATA_ACQUISITION.md`: "코드 작성만으로 READY_FOR_HUMAN_ANNOTATION을
선언하지 마십시오... 실제 10:10 공고, 동일 조건, 원문 접근, 출처·권리 기록이
모두 존재해야 합니다." Code alone cannot satisfy this — real postings must
exist first.

## What exists and is tested

| Deliverable | Path | Status |
|---|---|---|
| Work24/WorkNet API collector (dry-run only) | `scripts/acquisition/work24_client.py`, `scripts/acquisition/work24_endpoint_config.yaml` | Done, tested. Live mode is intentionally blocked (see below). |
| Manual posting intake CLI | `scripts/acquisition/manual_intake.py` | Done, tested against a fixture. Ready to ingest real postings today. |
| Pairing CLI | `scripts/acquisition/pair_postings.py` | Done, tested. |
| Feasibility measurement CLI | `scripts/acquisition/measure_feasibility.py` | Done, tested. Currently reports 0 real postings. |
| Manual intake protocol + sampling rule | `docs/acquisition/MANUAL_INTAKE_GUIDE.md` | Done. |
| Work24 API research trail | `docs/acquisition/WORK24_API_NOTES.md` | Done — official public pages confirm the list/detail endpoints, core parameters, XML format, and detail fields; an approved key and live mapping check are still required. |
| Source terms snapshot | `data/intake/source_terms_snapshot.yaml` | Done, dated 2026-09-12. |
| Occupation feasibility report | `data/intake/occupation_feasibility.json` | Done — currently `"overall_status": "INSUFFICIENT_SAMPLE"`, `"total_real_postings_ingested": 0` (accurate, not invented). |
| Real postings / pairs JSONL | `data/intake/real_postings.jsonl`, `data/intake/real_matched_pairs.jsonl` | **Not produced yet** — no real postings supplied to any agent session as of this handoff. |
| Test suite | `tests/acquisition/**` (26 tests) | All passing, offline/fixture-only. |
| This document | `REAL_DATA_ACQUISITION_HANDOFF.md` | Done. |

`data/postings/postings.jsonl` (the synthetic corpus) was **not** touched or
overwritten, per the task's ownership rules.

## Why the API path is still blocked

Re-checked today via the official public pages (not re-derived from prior
session notes):

- The legacy 워크넷 Open API (`openapi.work.go.kr`) has been shut down and
  merged into 고용24 (Work24) at `work24.go.kr`. "채용정보" is listed as an
  available API category there.
- Work24's official public pages expose the list/detail endpoint URLs, core
  parameter names, mandatory XML response format, and documented detail
  fields. The earlier claim that those facts were hidden behind login was
  incorrect and has been removed.
- An approved key and a live list/detail response are still unavailable in
  this worktree. The official detail-service page also requires Work24
  attribution/linking and prohibits unauthorized reproduction/distribution;
  approved-use terms must be checked before publishing full text.

`scripts/acquisition/work24_endpoint_config.yaml` therefore records the
publicly verified facts but remains `verified: false`. The client refuses a
live call until its response mapping has been checked with an issued key.
Full detail: `docs/acquisition/WORK24_API_NOTES.md`.

## Why the manual-intake path is also empty right now

The team (via this conversation) chose the manual-intake path over pursuing
the API key today, due to key-issuance friction, and defined a neutral
collection protocol (sort by recency, take from the top, log exclusions
factually — see `docs/acquisition/MANUAL_INTAKE_GUIDE.md`). No posting text
files were attached to this agent session, so `manual_intake.py` has
nothing to ingest yet. This is a real, working, tested tool — it is simply
waiting for real input.

## Exact next human action(s), in order

1. **Supply real posting text.** Using the template in
   `docs/acquisition/MANUAL_INTAKE_GUIDE.md`, collect and paste/attach at
   least 5 Jeonbuk + 5 metropolitan postings (10:10 to meet the documented
   design minimum; 20:20 is the target) for one occupation + employment
   type, sourced the same way and period, sorted by recency and taken from
   the top of the list (no cherry-picking).
2. Run, in order:
   ```bash
   python scripts/acquisition/manual_intake.py --in <your file(s)> --dry-run   # fix any reported errors first
   python scripts/acquisition/manual_intake.py --in <your file(s)>             # writes data/intake/real_postings.jsonl + data/private/intake_raw/
   python scripts/acquisition/pair_postings.py                                 # writes data/intake/real_matched_pairs.jsonl
   python scripts/acquisition/measure_feasibility.py                          # updates data/intake/occupation_feasibility.json
   ```
3. **Read `data/intake/occupation_feasibility.json`.** If `meets_min_10_10`
   is `true` for a candidate, a human must still set
   `human_boundary_review_completed: true` by hand after confirming the
   `tools_or_skills`/`duties` boundary is judgeable for that occupation on
   the real text (this cannot be automated — see
   `TASK_REAL_DATA_ACQUISITION.md` Phase 2, criterion 2). If no candidate
   meets 10:10, collect more postings or change occupation and repeat.
4. Once a candidate occupation is confirmed real and sufficient, re-confirm
   redistribution rights per record are actually filled in (not left at the
   default `unknown`) before treating any full text as safe to publish —
   `unknown`/`no` records correctly keep `full_text: null` in the public
   JSONL today; this is not a bug.
5. Hand `data/intake/real_postings.jsonl` + `data/intake/real_matched_pairs.jsonl`
   to the data/evaluation track (Task B) to replace the synthetic corpus
   under `data/postings/`, following the schema in
   `data/postings/README.md`, per `DATA_HANDOFF.md`'s "Remaining manual
   steps" #4 onward (real annotation, adjudication, splits, stats).

Until step 1 above happens, this remains `BLOCKED_INSUFFICIENT_SAMPLE` —
not `BLOCKED_NO_CREDENTIAL`, because the credential path is not the one
being pursued right now, and not `BLOCKED_LICENSE_OR_MISSING_TEXT`, because
no real text with an unresolvable license problem has been collected to
evaluate.

## How to verify what's here

```bash
python -m pytest tests/acquisition -q      # 26 tests, offline/fixture-only
python -m pytest tests/backend tests/data -q  # regression: 72 + 43 tests, unaffected
python scripts/acquisition/measure_feasibility.py  # confirms 0 real postings today
```

## Known limitations

- `manual_intake.py`'s PII redaction is best-effort regex (phone numbers,
  emails). It does not detect named contact persons — the human supplying
  text is asked to remove those before pasting.
- `pair_postings.py` pairs strictly by (occupation, employment_type) in
  file order; it does not weight by how close two `collection_date` values
  are. With small real batches this is unlikely to matter, but note it if
  batches span a wide date range.
- `measure_feasibility.py`'s `full_text_sufficient_count` is a length
  proxy (≥50 characters), not a judgment about whether the six fields are
  actually addressable — that judgment is exactly what
  `human_boundary_review_completed` exists to capture.
- Work24 requires XML. The current adapter is intentionally dry-run-only and
  its fixture path is JSON; XML parsing plus live tag mapping remains future
  work after a key is issued. It must not be described as live-ready.
