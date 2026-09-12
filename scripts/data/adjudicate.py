"""Compare two independent annotator files and build the adjudication
working file (Phase 4).

For every (posting_id, field) cell, records both raw labels, whether they
agree, and leaves adjudicated_* fields blank (null) for a human adjudicator
to fill in. Also prints percent agreement and, when the observed label
distribution makes it meaningful (more than one status actually appears and
there are enough cells), Cohen's kappa.

This script does not decide gold labels. It only prepares the comparison and
computes agreement statistics. A human adjudicator must fill in
`adjudicated_status` / `adjudicated_evidence_text` / `adjudicated_offsets` /
`adjudicator_note` afterwards (a straight copy is fine when A and B agree;
required to differ from a coin flip when they don't).

Usage:
  python scripts/data/adjudicate.py \\
      --annotator-a data/annotation/annotator_A_template.jsonl \\
      --annotator-b data/annotation/annotator_B_template.jsonl \\
      --out data/annotation/adjudication_output.jsonl
"""
from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from utils import ALLOWED_STATUSES, read_jsonl, write_jsonl  # noqa: E402


def index_by_cell(records: list[dict]) -> dict[tuple[str, str], dict]:
    return {(r["posting_id"], r["field"]): r for r in records}


def build_adjudication_rows(a_records: list[dict], b_records: list[dict]) -> list[dict]:
    a_by_cell = index_by_cell(a_records)
    b_by_cell = index_by_cell(b_records)
    cells = sorted(set(a_by_cell) | set(b_by_cell))

    rows = []
    for pid, field in cells:
        a = a_by_cell.get((pid, field))
        b = b_by_cell.get((pid, field))
        if a is None or b is None:
            raise ValueError(f"cell {(pid, field)} missing from one of the annotator files")

        agreement = (
            a.get("status") is not None
            and b.get("status") is not None
            and a["status"] == b["status"]
            and (a["status"] != "confirmed" and a["status"] != "vague" or a.get("evidence_text") == b.get("evidence_text"))
        )

        rows.append(
            {
                "posting_id": pid,
                "field": field,
                "annotator_a_status": a.get("status"),
                "annotator_a_evidence_text": a.get("evidence_text"),
                "annotator_a_offsets": a.get("offsets"),
                "annotator_a_reason_code": a.get("reason_code"),
                "annotator_b_status": b.get("status"),
                "annotator_b_evidence_text": b.get("evidence_text"),
                "annotator_b_offsets": b.get("offsets"),
                "annotator_b_reason_code": b.get("reason_code"),
                "agreement": agreement,
                "adjudicated_status": a.get("status") if agreement else None,
                "adjudicated_evidence_text": a.get("evidence_text") if agreement else None,
                "adjudicated_offsets": a.get("offsets") if agreement else None,
                "adjudicator_note": (
                    "auto-filled: A and B agreed" if agreement else None
                ),
                "rubric_version": a.get("rubric_version") or b.get("rubric_version"),
            }
        )
    return rows


def percent_agreement(rows: list[dict]) -> float:
    decided = [r for r in rows if r["annotator_a_status"] is not None and r["annotator_b_status"] is not None]
    if not decided:
        return float("nan")
    agree = sum(1 for r in decided if r["agreement"])
    return agree / len(decided)


def cohens_kappa(rows: list[dict]) -> float | None:
    """Unweighted Cohen's kappa over the 3-class status (confirmed/vague/absent),
    ignoring the evidence-text component of `agreement`. Returns None when
    the label distribution is degenerate (e.g. only one status observed
    across both annotators) — in that case kappa is undefined/uninformative
    and percent agreement should be reported instead, per project rules
    against overstating small-sample metrics.
    """
    decided = [
        r for r in rows
        if r["annotator_a_status"] in ALLOWED_STATUSES and r["annotator_b_status"] in ALLOWED_STATUSES
    ]
    n = len(decided)
    if n == 0:
        return None

    labels = sorted(ALLOWED_STATUSES)
    a_counts = Counter(r["annotator_a_status"] for r in decided)
    b_counts = Counter(r["annotator_b_status"] for r in decided)

    observed_agreement = sum(1 for r in decided if r["annotator_a_status"] == r["annotator_b_status"]) / n
    expected_agreement = sum((a_counts[l] / n) * (b_counts[l] / n) for l in labels)

    if len(a_counts) <= 1 and len(b_counts) <= 1:
        return None
    if expected_agreement >= 1.0:
        return None

    return (observed_agreement - expected_agreement) / (1 - expected_agreement)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--annotator-a", required=True, type=Path)
    ap.add_argument("--annotator-b", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args()

    a_records = read_jsonl(args.annotator_a)
    b_records = read_jsonl(args.annotator_b)

    rows = build_adjudication_rows(a_records, b_records)
    write_jsonl(args.out, rows)

    pct = percent_agreement(rows)
    kappa = cohens_kappa(rows)
    decided = sum(1 for r in rows if r["annotator_a_status"] is not None and r["annotator_b_status"] is not None)

    print(f"Wrote {len(rows)} adjudication rows to {args.out}")
    print(f"Cells with both annotators decided: {decided}/{len(rows)}")
    if decided == 0:
        print("Percent agreement: n/a (no decided cells yet)")
    else:
        print(f"Percent agreement (status + evidence): {pct:.1%}")
    if kappa is None:
        print("Cohen's kappa: not reported (label distribution too degenerate/small to be meaningful)")
    else:
        print(f"Cohen's kappa (status only, 3-class): {kappa:.3f}")

    disagreements = [r for r in rows if r["annotator_a_status"] is not None and r["annotator_b_status"] is not None and not r["agreement"]]
    if disagreements:
        print(f"\n{len(disagreements)} disagreement(s) need adjudicator review:")
        for r in disagreements:
            print(f"  {r['posting_id']}/{r['field']}: A={r['annotator_a_status']!r} vs B={r['annotator_b_status']!r}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
