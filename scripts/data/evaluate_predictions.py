"""Evaluate backend model predictions against human (adjudicated) gold
labels (Phase 6).

Reads a prediction JSONL with the same per-cell shape as an annotation
record ({posting_id, field, status, evidence_text, offsets, ...}; extra
keys are ignored) and reports, from gold labels only:

  - schema failure count (predictions that don't even parse as a valid cell)
  - unsupported/fabricated evidence count (evidence_text/offsets that don't
    match the source posting's full_text -- counted whether or not the
    predicted status happens to be right)
  - a 3x3 confusion matrix over the remaining (schema-valid) predictions
  - overall accuracy / raw correct-incorrect counts (the PRIMARY result)
  - macro precision/recall/F1, always shown with a prominent sample-size
    caveat and never presented as the primary result on a small sample

Per project rules, this script does no LLM calls and no free-form judgment;
every number here is a deterministic count.

Usage:
  python scripts/data/evaluate_predictions.py \\
      --postings data/postings/postings.jsonl \\
      --gold data/demo_synthetic_annotations/adjudicated_demo.jsonl \\
      --predictions tests/data/fixtures/sample_predictions.jsonl \\
      --rubric-version 1.0.0-draft \\
      --out data/reports/demo_evaluation_report.json \\
      --is-gold-source false
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from utils import ALLOWED_STATUSES, REQUIRED_FIELDS, read_jsonl  # noqa: E402

MIN_SAMPLE_SIZE_FOR_MACRO_METRICS_AS_PRIMARY = 100  # far above what this MVP can reach; keeps macro metrics secondary


def check_prediction_schema(pred: dict, postings_by_id: dict[str, dict]) -> str | None:
    """Return an error string if the prediction fails schema validation, else None."""
    pid = pred.get("posting_id")
    field = pred.get("field")
    status = pred.get("status")

    if pid not in postings_by_id:
        return f"unknown posting_id {pid!r}"
    if field not in REQUIRED_FIELDS:
        return f"unknown field {field!r}"
    if status not in ALLOWED_STATUSES:
        return f"status {status!r} not in {sorted(ALLOWED_STATUSES)}"

    evidence_text = pred.get("evidence_text")
    offsets = pred.get("offsets")
    if status == "absent":
        if evidence_text is not None or offsets is not None:
            return "status=absent requires null evidence_text/offsets"
    else:
        if not evidence_text or not (isinstance(offsets, list) and len(offsets) == 2):
            return f"status={status} requires evidence_text and [start, end] offsets"
    return None


def check_evidence_grounded(pred: dict, postings_by_id: dict[str, dict]) -> bool:
    """True if evidence is either absent-as-expected or an exact substring match."""
    status = pred.get("status")
    if status == "absent":
        return True
    evidence_text = pred.get("evidence_text")
    offsets = pred.get("offsets")
    if not (isinstance(offsets, list) and len(offsets) == 2):
        return False
    start, end = offsets
    full_text = postings_by_id[pred["posting_id"]].get("full_text", "")
    if not (isinstance(start, int) and isinstance(end, int) and 0 <= start < end <= len(full_text)):
        return False
    return full_text[start:end] == evidence_text


def confusion_matrix(pairs: list[tuple[str, str]]) -> dict[str, dict[str, int]]:
    matrix = {g: {p: 0 for p in sorted(ALLOWED_STATUSES)} for g in sorted(ALLOWED_STATUSES)}
    for gold, pred in pairs:
        matrix[gold][pred] += 1
    return matrix


def macro_prf1(pairs: list[tuple[str, str]]) -> dict[str, dict[str, float]]:
    labels = sorted(ALLOWED_STATUSES)
    per_class = {}
    for label in labels:
        tp = sum(1 for g, p in pairs if g == label and p == label)
        fp = sum(1 for g, p in pairs if g != label and p == label)
        fn = sum(1 for g, p in pairs if g == label and p != label)
        precision = tp / (tp + fp) if (tp + fp) else 0.0
        recall = tp / (tp + fn) if (tp + fn) else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
        per_class[label] = {"precision": round(precision, 4), "recall": round(recall, 4), "f1": round(f1, 4), "support": tp + fn}
    return per_class


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--postings", required=True, type=Path)
    ap.add_argument("--gold", required=True, type=Path, help="Adjudicated-label file to treat as gold for this run.")
    ap.add_argument("--predictions", required=True, type=Path)
    ap.add_argument("--rubric-version", required=True)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument(
        "--is-gold-source",
        choices=["true", "false"],
        required=True,
        help="Whether --gold is a real two-human-adjudicated gold file (true) or a non-gold demo/test file (false).",
    )
    args = ap.parse_args()
    is_gold_source = args.is_gold_source == "true"

    postings = read_jsonl(args.postings)
    postings_by_id = {p["posting_id"]: p for p in postings}
    gold_rows = read_jsonl(args.gold)
    predictions = read_jsonl(args.predictions)

    gold_by_cell = {
        (r["posting_id"], r["field"]): r.get("adjudicated_status")
        for r in gold_rows
        if r.get("adjudicated_status") is not None
    }

    schema_failures = []
    unsupported_evidence = []
    evaluated_pairs: list[tuple[str, str]] = []
    no_gold_available = []
    seen_cells = set()
    duplicate_predictions = []

    for pred in predictions:
        cell = (pred.get("posting_id"), pred.get("field"))
        if cell in seen_cells:
            duplicate_predictions.append(cell)
            continue
        seen_cells.add(cell)

        err = check_prediction_schema(pred, postings_by_id)
        if err:
            schema_failures.append({"cell": cell, "error": err})
            continue

        if not check_evidence_grounded(pred, postings_by_id):
            unsupported_evidence.append(
                {"cell": cell, "predicted_status": pred.get("status"), "evidence_text": pred.get("evidence_text"), "offsets": pred.get("offsets")}
            )
            # An ungrounded prediction cannot be trusted regardless of its status label;
            # exclude it from the confusion matrix rather than silently crediting it.
            continue

        gold_status = gold_by_cell.get(cell)
        if gold_status is None:
            no_gold_available.append(cell)
            continue

        evaluated_pairs.append((gold_status, pred["status"]))

    n = len(evaluated_pairs)
    correct = sum(1 for g, p in evaluated_pairs if g == p)
    incorrect = n - correct

    report = {
        "rubric_version": args.rubric_version,
        "is_gold_source": is_gold_source,
        "gold_status_note": (
            "is_gold_source=true: results below are reportable against real gold labels."
            if is_gold_source
            else "is_gold_source=false: --gold is a NON-GOLD synthetic/demo adjudicated file. "
            "This report exists only to prove the evaluation script runs correctly end to end "
            "and must not be cited as a model-performance result."
        ),
        "sample_size": {
            "predictions_received": len(predictions),
            "schema_failures": len(schema_failures),
            "unsupported_or_fabricated_evidence": len(unsupported_evidence),
            "duplicate_predictions_ignored": len(duplicate_predictions),
            "no_gold_available_for_cell": len(no_gold_available),
            "evaluated_cells": n,
        },
        "primary_result_raw_counts": {
            "correct": correct,
            "incorrect": incorrect,
            "overall_accuracy": round(correct / n, 4) if n else None,
        },
        "confusion_matrix_gold_rows_pred_cols": confusion_matrix(evaluated_pairs) if n else None,
        "macro_metrics_secondary": {
            "caveat": (
                f"n={n} evaluated cells. Macro precision/recall/F1 on a sample this size is "
                "NOT a defensible primary result (see TASK_DATA_EVALUATION.md Phase 5) and is "
                "reported here only as a secondary, illustrative figure."
                if n < MIN_SAMPLE_SIZE_FOR_MACRO_METRICS_AS_PRIMARY
                else f"n={n} evaluated cells."
            ),
            "per_class": macro_prf1(evaluated_pairs) if n else None,
        },
        "schema_failures_detail": schema_failures,
        "unsupported_evidence_detail": unsupported_evidence,
        "disclaimer": "exploratory sample; not population-generalizable",
    }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Evaluated {n} cells | correct={correct} incorrect={incorrect} | schema_failures={len(schema_failures)} | unsupported_evidence={len(unsupported_evidence)}")
    print(f"Wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
