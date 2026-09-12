#!/usr/bin/env bash
# Runs the full data/evaluation pipeline end to end against the synthetic
# fixtures, exactly as described in DATA_HANDOFF.md's completion check.
# Every artifact this produces is a NON-GOLD demonstration -- see
# data/demo_synthetic_annotations/README.md.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/../.."

echo "1) dataset validator"
python3 scripts/data/validate_dataset.py \
  --postings data/postings/postings.jsonl \
  --pairs data/postings/matched_pairs.jsonl \
  --annotations data/demo_synthetic_annotations/annotator_A.jsonl data/demo_synthetic_annotations/annotator_B.jsonl

echo
echo "2) annotation integrity / adjudication"
python3 scripts/data/adjudicate.py \
  --annotator-a data/demo_synthetic_annotations/annotator_A.jsonl \
  --annotator-b data/demo_synthetic_annotations/annotator_B.jsonl \
  --out data/demo_synthetic_annotations/adjudication_check_output.jsonl
rm -f data/demo_synthetic_annotations/adjudication_check_output.jsonl

echo
echo "3) split + checksum generation"
python3 scripts/data/generate_splits.py \
  --postings data/postings/postings.jsonl \
  --pairs data/postings/matched_pairs.jsonl \
  --adjudicated data/demo_synthetic_annotations/adjudicated_demo.jsonl \
  --rubric-version 1.0.0-draft \
  --out-dir data/splits \
  --label demo

echo
echo "4) aggregate report generation"
python3 scripts/data/aggregate_stats.py \
  --postings data/postings/postings.jsonl \
  --pairs data/postings/matched_pairs.jsonl \
  --adjudicated data/demo_synthetic_annotations/adjudicated_demo.jsonl \
  --rubric-version 1.0.0-draft \
  --out data/reports/demo_aggregate_stats.json
python3 scripts/data/generate_report.py \
  --stats data/reports/demo_aggregate_stats.json \
  --out data/reports/demo_exploratory_report.md

echo
echo "5) evaluation on synthetic prediction fixture"
python3 scripts/data/evaluate_predictions.py \
  --postings data/postings/postings.jsonl \
  --gold data/demo_synthetic_annotations/adjudicated_demo.jsonl \
  --predictions tests/data/fixtures/sample_predictions.jsonl \
  --rubric-version 1.0.0-draft \
  --out data/reports/demo_evaluation_report.json \
  --is-gold-source false

echo
echo "6) pytest suite"
python3 -m pytest tests/data -q

echo
echo "All steps completed. Reminder: every artifact above is NON-GOLD (see data/demo_synthetic_annotations/README.md)."
