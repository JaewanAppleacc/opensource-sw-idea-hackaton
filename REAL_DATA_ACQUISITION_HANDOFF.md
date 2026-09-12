# REAL_DATA_ACQUISITION_HANDOFF.md — Parallel task D1 (+ 2026-09-12 real-postings-comparable-domain pass)

Read alongside `CLAUDE.md`, `DATA_HANDOFF.md`, `TASK_REAL_DATA_ACQUISITION.md`,
and `docs/acquisition/REAL_SOURCE_SEARCH_LOG.md`. This document is the single
source of truth for the real-data acquisition track's status.

## Decision

> **`MIN_SAMPLE_MET_PENDING_HUMAN_BOUNDARY_REVIEW`**

As of 2026-09-12, **10 real Jeonbuk + 10 real metropolitan postings for
생산직(제조 조립원)/정규직 have been ingested** into
`data/intake/real_postings.jsonl` (full text: `data/private/intake_raw/`,
gitignored), paired 10-for-10 in `data/intake/real_matched_pairs.jsonl`, and
confirmed by `scripts/acquisition/measure_feasibility.py`
(`data/intake/occupation_feasibility.json`: `meets_min_10_10: true`,
`overall_status: "MIN_SAMPLE_MET_PENDING_HUMAN_BOUNDARY_REVIEW"`).

This is **not** `READY_FOR_HUMAN_ANNOTATION` and **not** gold. Per
`TASK_REAL_DATA_ACQUISITION.md`: "코드 작성만으로 READY_FOR_HUMAN_ANNOTATION을
선언하지 마십시오... 실제 10:10 공고, 동일 조건, 원문 접근, 출처·권리 기록이
모두 존재해야 합니다." All of those now exist for real data, but two
independent humans have not yet annotated any of it, and
`human_boundary_review_completed` in `data/intake/occupation_feasibility.json`
is deliberately left `null` — only a human may set it, after confirming the
`duties`/`tools_or_skills` boundary is actually judgeable on this real text
(not just on the earlier synthetic fixtures).

See `docs/acquisition/REAL_SOURCE_SEARCH_LOG.md` for: the full feasibility
scan across the three requested domains (금융·경영 / IT·디지털 / 생산·기술),
why 생산직(제조 조립원) was chosen over the closest alternative (회계
사무원, which actually had a slightly higher raw search-result count), the
two postings excluded during collection for occupation mismatch (and their
factual replacements), and the sample-level comparability review.

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
| Occupation feasibility report | `data/intake/occupation_feasibility.json` | **Updated 2026-09-12** — `"overall_status": "MIN_SAMPLE_MET_PENDING_HUMAN_BOUNDARY_REVIEW"`, `"total_real_postings_ingested": 20`, `meets_min_10_10: true`, `meets_target_20_20: false`, `human_boundary_review_completed: null` (a human must set this). |
| Real postings / pairs JSONL | `data/intake/real_postings.jsonl`, `data/intake/real_matched_pairs.jsonl` | **Produced 2026-09-12** — 20 real postings (10 jeonbuk + 10 metro), 10 matched pairs, 0 unmatched. See `docs/acquisition/REAL_SOURCE_SEARCH_LOG.md`. |
| Excluded postings log | `data/intake/excluded_postings.jsonl` | **Produced 2026-09-12** — 2 postings excluded during collection for occupation mismatch, with factual reasons. |
| Cross-domain feasibility scan + selection rationale | `docs/acquisition/REAL_SOURCE_SEARCH_LOG.md` | **Produced 2026-09-12** — 금융·경영/IT·디지털/생산·기술 raw counts, occupation selection reasoning, sample-level comparability review. |
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

## How the manual-intake path was filled (2026-09-12)

The team chose the manual-intake path over pursuing the API key, due to
key-issuance friction (unchanged from the earlier decision). On 2026-09-12,
an agent session acted as the "team member" the manual-intake protocol
describes: it researched candidate occupations across three requested
domains (금융·경영 / IT·디지털 / 생산·기술) using 고용24's own public
"채용정보 상세검색" web screen (not the API, not a scraper, not a private
platform), selected 생산직(제조 조립원)/정규직 per the documented selection
principle, then opened 20 individual public detail pages one at a time (top
of a fixed, recency-sorted, same-filter list for each region) and
transcribed the visible text verbatim into
`data/private/intake_source/real_postings.txt` (gitignored, not committed)
following the template in `docs/acquisition/MANUAL_INTAKE_GUIDE.md`. Full
reasoning, raw search-result counts for every candidate in all three
domains, and the sample-level comparability review are in
`docs/acquisition/REAL_SOURCE_SEARCH_LOG.md` — read that document before
building on this data.

## What was run, in order

```bash
python scripts/acquisition/manual_intake.py --in data/private/intake_source/real_postings.txt --dry-run   # passed, 0 errors
python scripts/acquisition/manual_intake.py --in data/private/intake_source/real_postings.txt             # wrote 20 public + 20 private + 2 excluded records
python scripts/acquisition/pair_postings.py                                                                 # wrote 10 pairs, 0 unmatched
python scripts/acquisition/measure_feasibility.py                                                           # MIN_SAMPLE_MET_PENDING_HUMAN_BOUNDARY_REVIEW
```

No changes were made to `manual_intake.py`, `pair_postings.py`,
`measure_feasibility.py`, or `acquisition_utils.py` — the existing,
already-tested pipeline was used as-is per this task's instructions.

## Exact next human action(s), in order

1. **Confirm the duties/tools_or_skills boundary is judgeable on this real
   text**, then set `human_boundary_review_completed: true` by hand in
   `data/intake/occupation_feasibility.json` (an agent must not do this —
   see `TASK_REAL_DATA_ACQUISITION.md` Phase 2, criterion 2, and
   `TASK_ANNOTATION_WORKFLOW_PREP.md`'s absolute rule that only real human
   labeling may produce gold-adjacent status).
2. **(Optional, to reach the 20:20 target)** collect 10 more Jeonbuk + 10
   more metropolitan postings for the same occupation/employment type,
   same source, same sampling rule, and re-run the three commands above
   (manual_intake.py --in accepts multiple files and will append, refusing
   duplicate `posting_id`s).
3. **Re-confirm redistribution rights** for 고용24 postings before ever
   changing any record's `redistribution_permission` away from `unknown` —
   none of the 20 records ingested today have confirmed publish rights;
   `full_text` stays `null` in the public JSONL correctly.
4. **Run two independent human annotators** through
   `scripts/annotation_ops/build_packets.py` (see the parallel
   `feature/annotation-workflow-prep` track) pointed at
   `data/intake/real_postings.jsonl` is not itself annotatable because
   `full_text` is `null` there for redistribution reasons — annotators need
   the private full text. Point the packet builder at a copy of
   `data/private/intake_raw/*.json` full text (or extend the annotation-ops
   tooling to read from there) rather than the public JSONL. This is a
   concrete integration gap between the D1/real-postings pass and the D2
   annotation-ops pass — flag it to whoever runs annotation next.
5. Once two independent annotations exist and are adjudicated (see
   `data/annotation/schema.md`, `scripts/data/adjudicate.py`), hand the
   result to the data/evaluation track (Task B) to replace/extend the
   synthetic corpus under `data/postings/`, following
   `DATA_HANDOFF.md`'s "Remaining manual steps" #5 onward.

Until step 1 (human boundary review) is complete, nothing here may be
called `READY_FOR_HUMAN_ANNOTATION`, gold, or a performance/regional
finding — the correct status right now is exactly
`MIN_SAMPLE_MET_PENDING_HUMAN_BOUNDARY_REVIEW`.

## How to verify what's here

```bash
python -m pytest tests/acquisition -q      # 26 tests, offline/fixture-only
python -m pytest tests/backend tests/data -q  # regression: 119 tests, unaffected
python scripts/acquisition/measure_feasibility.py  # re-confirms 20 real postings, MIN_SAMPLE_MET_PENDING_HUMAN_BOUNDARY_REVIEW
```

Also spot-checked manually this pass (not scripted): every public record in
`data/intake/real_postings.jsonl` has `full_text: null`; every private
record in `data/private/intake_raw/*.json` has real transcribed text with
phone numbers redacted to `[REDACTED_PHONE]`; no contact-person names were
present in any of the 20 originals.

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
- The real 20 postings ingested 2026-09-12 all came from 고용24's public
  search UI, not the Open API — `work24_client.py` (the API path) is
  unaffected by this pass and remains `blocked_no_credentials`.
- All 10 metropolitan postings landed in 인천/경기, none in 서울, because
  that is what the top of the recency-sorted result list contained for this
  exact keyword/filter combination on 2026-09-12 — see
  `docs/acquisition/REAL_SOURCE_SEARCH_LOG.md` §4 for the observed (not
  assumed) distribution.
- Two matched pairs (P-REAL-004, P-REAL-009) have a minor career-level /
  education-level mismatch between the Jeonbuk and metro side because
  `pair_postings.py` pairs strictly by file order within
  (occupation, employment_type), not by career level — see
  `docs/acquisition/REAL_SOURCE_SEARCH_LOG.md` §5 for the specifics. This
  is a known, documented limitation of the pairing script, not a bug
  introduced this pass; a human annotator should be aware of it when
  reading those two pairs.
- `training_or_mentoring` looked absent (no explicit OJT/사수 structure) in
  all 20 real postings collected this pass — a pre-labeling observation
  from reading the source text while collecting it, not a labeling result,
  flagged here so it doesn't come as a surprise during annotation.
