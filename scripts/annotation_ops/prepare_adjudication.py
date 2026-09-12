"""Pre-flight-checked adjudication queue builder (Phase D2 #4).

Wraps `scripts/data/adjudicate.py` (unchanged) instead of reimplementing it,
and adds the guardrails TASK_ANNOTATION_WORKFLOW_PREP.md requires before any
comparison is produced:

  - refuses to run if either packet has an unanswered (null status) cell
  - refuses to run if either packet fails any `validate_packets.py` check
    (schema/evidence, isolation, AI-suggestion leakage, provenance)
  - writes the full A-vs-B comparison file (agreement cells auto-filled,
    exactly as scripts/data/adjudicate.py already does) AND a second,
    disagreement-only review queue file so a human adjudicator does not have
    to filter the full file by hand
  - prints only raw agreement counts and percent -- no Cohen's kappa here,
    since this step is about producing the review queue, not reporting a
    metric; use `scripts/data/adjudicate.py` directly (or
    `scripts/data/aggregate_stats.py` later) for kappa on a real gold set
  - never resolves a disagreement automatically; a `--verify-final` mode
    checks a human-completed file is actually gold-ready (every cell has a
    non-null `adjudicated_status`, and every disagreement has a non-empty,
    non-auto-filled `adjudicator_note`) before anyone calls it gold

No LLM is used anywhere in this file.

Usage (build the queue):
  python scripts/annotation_ops/prepare_adjudication.py \\
      --packet-a data/private/annotation_run_001/annotator_A/packet.jsonl \\
      --packet-b data/private/annotation_run_001/annotator_B/packet.jsonl \\
      --postings /path/to/real_postings.jsonl \\
      --out data/private/annotation_run_001/adjudication_comparison.jsonl

Usage (verify a human-completed adjudication file before calling it gold):
  python scripts/annotation_ops/prepare_adjudication.py \\
      --verify-final data/private/annotation_run_001/adjudication_comparison.jsonl
"""
from __future__ import annotations

import argparse
from pathlib import Path

from common import ALLOWED_STATUSES, read_jsonl, write_jsonl
from validate_packets import is_packet_complete, validate_packet_pair
from adjudicate import build_adjudication_rows, percent_agreement


def build_queue(
    path_a: Path,
    path_b: Path,
    postings_path: Path,
    out_path: Path,
    review_queue_path: Path,
) -> dict:
    a_records = read_jsonl(path_a)
    b_records = read_jsonl(path_b)

    if not is_packet_complete(a_records):
        raise ValueError(f"REFUSED: {path_a} has unanswered cells (null status). Finish annotation before adjudication.")
    if not is_packet_complete(b_records):
        raise ValueError(f"REFUSED: {path_b} has unanswered cells (null status). Finish annotation before adjudication.")

    ok, results = validate_packet_pair(path_a, path_b, postings_path, allow_incomplete=False)
    if not ok:
        lines = ["REFUSED: packet validation failed."]
        for check, errors in results.items():
            for e in errors:
                lines.append(f"  [{check}] {e}")
        raise ValueError("\n".join(lines))

    rows = build_adjudication_rows(a_records, b_records)
    write_jsonl(out_path, rows)

    disagreements = [r for r in rows if not r["agreement"]]
    write_jsonl(review_queue_path, disagreements)

    pct = percent_agreement(rows)
    return {
        "total_cells": len(rows),
        "agree_count": len(rows) - len(disagreements),
        "disagree_count": len(disagreements),
        "percent_agreement": pct,
        "out_path": str(out_path),
        "review_queue_path": str(review_queue_path),
    }


def verify_final(path: Path) -> tuple[bool, list[str]]:
    """Checks a human-completed adjudication comparison file is gold-ready.

    Not a re-derivation of agreement -- just the completeness/consistency
    contract the schema promises: every cell decided, every disagreement
    backed by an actual human note rather than the agreement auto-fill.
    """
    rows = read_jsonl(path)
    errors: list[str] = []
    for i, r in enumerate(rows):
        loc = f"row {i} ({r.get('posting_id')}/{r.get('field')})"
        status = r.get("adjudicated_status")
        if status is None:
            errors.append(f"{loc}: adjudicated_status is still null")
            continue
        if status not in ALLOWED_STATUSES:
            errors.append(f"{loc}: adjudicated_status {status!r} is not one of {sorted(ALLOWED_STATUSES)}")
            continue

        if not r.get("agreement"):
            note = r.get("adjudicator_note")
            if not note or not note.strip():
                errors.append(f"{loc}: disagreement cell requires a non-empty adjudicator_note")
            elif note.strip().lower().startswith("auto-filled"):
                errors.append(f"{loc}: disagreement cell must not use the agreement auto-fill note")

        if status in ("confirmed", "vague"):
            if not r.get("adjudicated_evidence_text") or not r.get("adjudicated_offsets"):
                errors.append(f"{loc}: adjudicated_status={status} requires adjudicated_evidence_text and adjudicated_offsets")
        elif status == "absent":
            if r.get("adjudicated_evidence_text") is not None or r.get("adjudicated_offsets") is not None:
                errors.append(f"{loc}: adjudicated_status=absent requires null adjudicated_evidence_text/adjudicated_offsets")

    return (not errors), errors


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--packet-a", type=Path)
    ap.add_argument("--packet-b", type=Path)
    ap.add_argument("--postings", type=Path)
    ap.add_argument("--out", type=Path)
    ap.add_argument("--review-queue-out", type=Path, help="Defaults to <out>_disagreements.jsonl next to --out")
    ap.add_argument("--verify-final", type=Path, help="Verify a human-completed adjudication file instead of building a new queue")
    args = ap.parse_args()

    if args.verify_final:
        ok, errors = verify_final(args.verify_final)
        for e in errors:
            print(f"ERROR: {e}")
        print("PASS - ready to call gold" if ok else "FAIL - not yet gold-ready")
        return 0 if ok else 1

    missing = [
        name
        for name, val in [
            ("--packet-a", args.packet_a),
            ("--packet-b", args.packet_b),
            ("--postings", args.postings),
            ("--out", args.out),
        ]
        if val is None
    ]
    if missing:
        ap.error(f"missing required arguments to build a queue: {', '.join(missing)} (or pass --verify-final instead)")

    review_queue_out = args.review_queue_out or args.out.with_name(args.out.stem + "_disagreements" + args.out.suffix)

    try:
        stats = build_queue(args.packet_a, args.packet_b, args.postings, args.out, review_queue_out)
    except ValueError as e:
        print(str(e))
        return 1

    print(f"Wrote {stats['total_cells']} adjudication rows to {stats['out_path']}")
    print(f"Agreement: {stats['agree_count']}/{stats['total_cells']} ({stats['percent_agreement']:.1%})")
    print(f"Disagreements needing human adjudication: {stats['disagree_count']} -> {stats['review_queue_path']}")
    print()
    print("This is agreement between two annotator files, not a gold-label performance claim.")
    print("Fill in adjudicated_* for every disagreement (with a real adjudicator_note), then run:")
    print(f"  python scripts/annotation_ops/prepare_adjudication.py --verify-final {stats['out_path']}")
    print("before treating this file as gold -- see DATA_HANDOFF.md.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
