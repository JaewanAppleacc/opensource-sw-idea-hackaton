"""Build a SYNTHETIC, NOT-GOLD demo annotation set purely to exercise the
adjudication / split / statistics / evaluation scripts end to end.

IMPORTANT: nothing produced by this script is a real human annotation. Two
independent human passes have not happened (see DATA_HANDOFF.md). This
script perturbs the rule-based AI suggestions to *simulate* two annotators
with a realistic-but-fake disagreement rate, purely so the rest of the
pipeline's code paths (adjudicate.py, generate_splits.py, aggregate_stats.py,
evaluate_predictions.py) can be run and tested before real annotation
exists. Every output file and every row is tagged accordingly and none of it
may be called "gold" anywhere in this repository.

Run: python scripts/data/build_demo_synthetic_annotations.py
Writes: data/demo_synthetic_annotations/annotator_A.jsonl
        data/demo_synthetic_annotations/annotator_B.jsonl
        data/demo_synthetic_annotations/adjudicated_demo.jsonl
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from adjudicate import build_adjudication_rows  # noqa: E402
from utils import read_jsonl, write_jsonl  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[2]
SUGGESTIONS_PATH = REPO_ROOT / "data" / "annotation" / "ai_suggestions.jsonl"
OUT_DIR = REPO_ROOT / "data" / "demo_synthetic_annotations"
RUBRIC_VERSION = "1.0.0-draft"

REASON_CODES = {
    "confirmed": "meets_confirmed_criteria_per_rubric",
    "vague": "wording_present_not_decision_useful",
    "absent": "no_relevant_text",
}

# (posting_id, field) -> forced status, to hand-construct a handful of
# disagreements for annotator B rather than leaving it purely accidental.
B_DISAGREEMENTS: dict[tuple[str, str], str] = {
    ("JB-001", "probation_terms"): "absent",  # A says vague, B misses it entirely
    ("JB-006", "training_or_mentoring"): "vague",  # A says confirmed, B underreads it
    ("JB-008", "tools_or_skills"): "confirmed",  # A says vague, B overreads it (no real evidence -> will use short span)
    ("MET-004", "duties"): "vague",  # A says confirmed, B underreads it
    ("MET-007", "probation_terms"): "confirmed",  # A says vague, B overreads it
    ("JB-002", "salary"): "absent",  # A says vague, B misses it
}


def to_annotator_record(suggestion: dict, annotator_id: str) -> dict:
    return {
        "posting_id": suggestion["posting_id"],
        "field": suggestion["field"],
        "annotator_id": annotator_id,
        "status": suggestion["suggested_status"],
        "evidence_text": suggestion["evidence_text"],
        "offsets": suggestion["offsets"],
        "reason_code": REASON_CODES[suggestion["suggested_status"]],
        "disagreement_note": None,
        "rubric_version": RUBRIC_VERSION,
        "synthetic_test_fixture": True,
    }


def main() -> None:
    suggestions = read_jsonl(SUGGESTIONS_PATH)

    a_records = [to_annotator_record(s, "A") for s in suggestions]
    b_records = []
    for s in suggestions:
        key = (s["posting_id"], s["field"])
        rec = to_annotator_record(s, "B")
        if key in B_DISAGREEMENTS:
            forced_status = B_DISAGREEMENTS[key]
            rec["status"] = forced_status
            if forced_status == "absent":
                rec["evidence_text"] = None
                rec["offsets"] = None
            # else: forced_status is confirmed/vague and the underlying
            # suggestion already had non-null evidence_text/offsets for every
            # key in B_DISAGREEMENTS below, so the existing span is reused.
            rec["reason_code"] = REASON_CODES[forced_status]
            rec["disagreement_note"] = "synthetic forced disagreement for pipeline testing"
        b_records.append(rec)

    write_jsonl(OUT_DIR / "annotator_A.jsonl", a_records)
    write_jsonl(OUT_DIR / "annotator_B.jsonl", b_records)

    rows = build_adjudication_rows(a_records, b_records)
    # DEMO-ONLY auto-adjudication: on disagreement, take annotator A's label
    # and stamp the row so it is unmistakably not a real adjudicator decision.
    for row in rows:
        if not row["agreement"]:
            row["adjudicated_status"] = row["annotator_a_status"]
            row["adjudicated_evidence_text"] = row["annotator_a_evidence_text"]
            row["adjudicated_offsets"] = row["annotator_a_offsets"]
            row["adjudicator_note"] = (
                "DEMO ONLY -- auto-resolved to annotator A for pipeline testing; "
                "NOT a real adjudicator decision"
            )
        row["synthetic_test_fixture"] = True

    write_jsonl(OUT_DIR / "adjudicated_demo.jsonl", rows)
    print(f"Wrote {len(a_records)} rows to annotator_A.jsonl / annotator_B.jsonl")
    print(f"Wrote {len(rows)} rows to adjudicated_demo.jsonl (SYNTHETIC, NOT GOLD)")


if __name__ == "__main__":
    main()
