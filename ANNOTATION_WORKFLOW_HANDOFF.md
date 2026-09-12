# ANNOTATION_WORKFLOW_HANDOFF.md — annotation-ops track (Parallel task D2)

Read alongside `CLAUDE.md`, `DATA_HANDOFF.md`, and
`TASK_ANNOTATION_WORKFLOW_PREP.md`. This document covers only what was built
on branch `feature/annotation-workflow-prep`: the tooling that lets two
independent humans run real annotation once real postings exist. **It does
not produce, and this branch did not produce, any real label.**

## TL;DR

- Built and tested: a path-driven packet generator, a single-annotator
  review CLI, a completeness/isolation validator, and a pre-flight-checked
  adjudication queue builder + gold-readiness verifier.
- All of it is exercised end-to-end against the repo's existing synthetic
  fixtures (`data/postings/postings.jsonl`, `synthetic_test_fixture: true`
  throughout) — see [How to verify](#how-to-verify-what-is-here).
- Nothing in `scripts/annotation_ops/**` or its tests writes to, or claims
  to produce, a gold label. No real posting was read or annotated by this
  work.
- `scripts/data/generate_annotation_templates.py`, `scripts/data/adjudicate.py`,
  and `scripts/data/validate_dataset.py` were **not modified** — every new
  tool imports and reuses them as-is, so nothing already consumed downstream
  (per `DATA_HANDOFF.md`'s remaining steps) changes shape.

## What was built

| Deliverable (per TASK_ANNOTATION_WORKFLOW_PREP.md) | Path | Status |
|---|---|---|
| #1 Packet generator with arbitrary input path | `scripts/annotation_ops/build_packets.py` | Done, tested |
| #2 Human review/input-assist CLI | `scripts/annotation_ops/review_cli.py` | Done, tested |
| #3 Completeness + isolation validator | `scripts/annotation_ops/validate_packets.py` | Done, tested |
| #4 Adjudication pre-flight + review queue + gold-readiness check | `scripts/annotation_ops/prepare_adjudication.py` | Done, tested |
| Shared helpers | `scripts/annotation_ops/common.py` | Done |
| Annotator guide | `docs/annotation/HUMAN_ANNOTATION_GUIDE.md` | Done |
| This document | `ANNOTATION_WORKFLOW_HANDOFF.md` | Done |
| Tests | `tests/annotation_ops/*.py` (43 tests) | Done, all passing |

### 1. `build_packets.py`

```bash
python scripts/annotation_ops/build_packets.py \
  --postings /path/to/real_postings.jsonl \
  --rubric data/rubric/rubric.yaml \
  --out-dir data/private/annotation_run_001
```

- Takes the postings path as an argument (unlike
  `scripts/data/generate_annotation_templates.py`, which is hard-coded to
  the repo's own synthetic fixture file) so a real, non-redistributable
  posting file living outside the public repo layer can be used directly.
- Writes `annotator_A/packet.jsonl` and `annotator_B/packet.jsonl` in
  separate directories, same posting/field order, annotator IDs kept
  strictly separate. Rows are blank (`status: null`) and contain **no** AI
  suggestion content.
- Every row carries `rubric_version` (read from the rubric file, not
  hard-coded) and an explicit boolean `synthetic_test_fixture` (derived the
  same way `generate_annotation_templates.py` already does: true only if the
  source posting says so; false by default for real data — never guessed).
- Never copies posting `full_text` into the packet — packets reference
  `posting_id` + `field` only, so a posting file that must stay local still
  works.
- Writes `manifest.json` alongside the packets: input file path + SHA-256,
  rubric path + version, generation timestamp (UTC), posting count, and
  cell count per annotator. The manifest is explicitly labeled as run
  provenance, not a gold marker.

### 2. `review_cli.py`

```bash
python scripts/annotation_ops/review_cli.py \
  --packet data/private/annotation_run_001/annotator_A/packet.jsonl \
  --postings /path/to/real_postings.jsonl
```

- Reads exactly one packet (one annotator's own file) and the shared
  posting text — structurally, it has no code path that opens the other
  annotator's file or `ai_suggestions.jsonl`.
- Per cell: shows the full posting text and current field, asks for
  `status`, `reason_code`, an optional note, and — for `confirmed`/`vague`
  — the exact evidence excerpt. It searches the source text for that
  excerpt and computes offsets automatically; if the excerpt occurs more
  than once, it lists every occurrence with surrounding context and lets
  the human pick.
- Never suggests or infers a status; it only removes manual offset
  arithmetic and typos from the loop.
- Saves the packet back to disk after every answered cell (not just at
  exit), so `Ctrl+C` or a crash loses at most the in-progress cell.
  Re-running the same command resumes automatically (already-answered
  cells are skipped unless `--redo` is passed).

### 3. `validate_packets.py`

```bash
python scripts/annotation_ops/validate_packets.py \
  --packet-a data/private/annotation_run_001/annotator_A/packet.jsonl \
  --packet-b data/private/annotation_run_001/annotator_B/packet.jsonl \
  --postings /path/to/real_postings.jsonl \
  [--allow-incomplete]
```

Runs `scripts/data/validate_dataset.py`'s existing schema/evidence checks
against each file unchanged, then adds:

- `annotator_id` isolation (no cross-file contamination),
- packet A and packet B are not the same file (different resolved path
  *and* different content checksum),
- neither file contains an AI-suggestion-only key (`ai_suggested` /
  `suggested_status`),
- every row has an explicit boolean `synthetic_test_fixture` (fails loudly
  if missing, per the "missing provenance is rejected rather than guessed"
  rule in `data/annotation/schema.md`),
- A and B agree on `synthetic_test_fixture` and `rubric_version` per cell.

### 4. `prepare_adjudication.py`

```bash
# Build the queue (refuses unless both packets are complete and valid):
python scripts/annotation_ops/prepare_adjudication.py \
  --packet-a data/private/annotation_run_001/annotator_A/packet.jsonl \
  --packet-b data/private/annotation_run_001/annotator_B/packet.jsonl \
  --postings /path/to/real_postings.jsonl \
  --out data/private/annotation_run_001/adjudication_comparison.jsonl

# Verify a human-completed file before anyone calls it gold:
python scripts/annotation_ops/prepare_adjudication.py \
  --verify-final data/private/annotation_run_001/adjudication_comparison.jsonl
```

- Wraps `scripts/data/adjudicate.py` unmodified — refuses to call it at all
  if either packet has a null `status` anywhere, or fails any
  `validate_packets.py` check (including the provenance-mismatch checks).
- Writes the full A-vs-B comparison file (agreement cells auto-filled,
  exactly as `adjudicate.py` already does) **and** a second file containing
  only the disagreement rows, so the human adjudicator has a ready-made
  review queue instead of filtering the full file by hand.
- Prints only raw agreement count and percent — no Cohen's kappa here.
  Kappa (when the label distribution supports it, per project rules against
  overstating small-sample metrics) stays a job for
  `scripts/data/adjudicate.py` directly or `scripts/data/aggregate_stats.py`
  once real gold exists.
- Never resolves a disagreement automatically. `--verify-final` checks a
  human-completed file has a non-null `adjudicated_status` on every row and
  a real (non-auto-filled) `adjudicator_note` on every disagreement, so
  "gold-ready" is a checked fact, not an assumption.

## What this branch explicitly did NOT do

- Did not collect, view, or annotate any real Jeonbuk/metropolitan posting.
- Did not modify `data/postings/**`, `data/intake/**`, `frontend/**`,
  `backend/**`, or `contracts/**`.
- Did not modify `scripts/data/generate_annotation_templates.py`,
  `scripts/data/adjudicate.py`, or `scripts/data/validate_dataset.py` —
  every new script imports them as-is.
- Did not create, write to, or reference any real annotator output file.
- Did not compute or claim any human agreement rate, Cohen's kappa, or model
  accuracy number. Every number in this document's test output below is
  against the repo's synthetic fixtures and is labeled as such.

## How to verify what is here

```bash
python -m pytest tests/annotation_ops tests/backend tests/data -q
```

All 158 tests pass as of this writing (43 in `tests/annotation_ops`, plus
the pre-existing backend and data suites, confirming this branch did not
break either track). Every fixture used in `tests/annotation_ops` is
inline, synthetic, and marked `synthetic_test_fixture` appropriately in the
assertions.

A full manual smoke test was also run against the repo's real synthetic
fixture file, `data/postings/postings.jsonl` (22 postings, itself already
labeled `synthetic_fixture_v1` / non-real — see
`data/postings/README.md`), exercising the entire chain outside pytest:

1. `build_packets.py` against `data/postings/postings.jsonl` → two 132-cell
   packets + manifest.
2. Every cell filled in via `review_cli.py`'s scriptable `run_review_session`
   (used the same way the interactive CLI does internally).
3. `validate_packets.py` on the complete packets → `PASS`.
4. `prepare_adjudication.py` → refuses on an incomplete packet and on an
   isolation violation (annotator_id contamination); succeeds once both
   packets are complete and valid, producing a comparison file and a
   disagreement-only review queue.
5. `--verify-final` correctly rejects a file with a null
   `adjudicated_status` or a disagreement missing a real `adjudicator_note`,
   and accepts a properly completed one.

None of this smoke-test output was written into the repository or is
referenced as a result anywhere else — it only exercised the tools.

## Remaining human actions (unchanged from DATA_HANDOFF.md, now unblocked by this tooling)

This branch does not shorten `DATA_HANDOFF.md`'s remaining-steps list — it
only makes step 5 onward executable once real data exists:

1. Get a real posting source and confirm ≥10 Jeonbuk + ≥10 metropolitan
   postings exist (`TASK_REAL_DATA_ACQUISITION.md`, tracked separately —
   this branch's job was the tooling, not the data).
2. Run `build_packets.py` against the real postings file once it exists.
3. Have two humans independently run `review_cli.py` against their own
   packet (`docs/annotation/HUMAN_ANNOTATION_GUIDE.md`), without seeing each
   other's file or `ai_suggestions.jsonl`.
4. Run `validate_packets.py` on both completed files.
5. Run `prepare_adjudication.py` to build the comparison + review queue.
6. Have a human adjudicator fill in `adjudicated_status` /
   `adjudicated_evidence_text` / `adjudicated_offsets` / `adjudicator_note`
   for every disagreement row (agreement rows may keep the auto-fill).
7. Run `prepare_adjudication.py --verify-final` on the completed file.
8. Only after step 7 passes: proceed to
   `scripts/data/generate_splits.py --is-gold true`,
   `scripts/data/aggregate_stats.py`, and `scripts/data/generate_report.py`,
   per `DATA_HANDOFF.md`.

Until step 7 passes, nothing produced by this workflow may be called gold,
reported as a human agreement rate, or cited as a performance/regional
finding.
