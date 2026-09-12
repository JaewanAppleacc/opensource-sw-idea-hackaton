"""End-to-end checks against the real repository files (Phase 6 completion
check, automated). These exercise the CLIs as subprocesses so they match
exactly what a developer running the documented commands would see.
"""
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = REPO_ROOT / "scripts" / "data"
DATA = REPO_ROOT / "data"


def run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, *args], cwd=REPO_ROOT, capture_output=True, text=True)


def test_postings_and_pairs_validate_clean():
    result = run(
        str(SCRIPTS / "validate_dataset.py"),
        "--postings", str(DATA / "postings" / "postings.jsonl"),
        "--pairs", str(DATA / "postings" / "matched_pairs.jsonl"),
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "PASS" in result.stdout


def test_ai_suggestions_pass_validation_as_a_full_annotation_file(tmp_path):
    # ai_suggestions.jsonl uses field name `suggested_status`, not `status` --
    # convert to the annotation schema shape before validating, since that's
    # the same conversion a human template-prefill step would do.
    suggestions = [json.loads(l) for l in (DATA / "annotation" / "ai_suggestions.jsonl").read_text(encoding="utf-8").splitlines() if l]
    as_annotations = [
        {
            "posting_id": s["posting_id"],
            "field": s["field"],
            "status": s["suggested_status"],
            "evidence_text": s["evidence_text"],
            "offsets": s["offsets"],
            "reason_code": "ai_suggested_placeholder",
            "rubric_version": s["rubric_version"],
        }
        for s in suggestions
    ]
    converted_path = tmp_path / "converted_ai_suggestions.jsonl"
    converted_path.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in as_annotations), encoding="utf-8")

    result = run(
        str(SCRIPTS / "validate_dataset.py"),
        "--postings", str(DATA / "postings" / "postings.jsonl"),
        "--pairs", str(DATA / "postings" / "matched_pairs.jsonl"),
        "--annotations", str(converted_path),
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_demo_synthetic_annotations_validate_clean():
    result = run(
        str(SCRIPTS / "validate_dataset.py"),
        "--postings", str(DATA / "postings" / "postings.jsonl"),
        "--pairs", str(DATA / "postings" / "matched_pairs.jsonl"),
        "--annotations",
        str(DATA / "demo_synthetic_annotations" / "annotator_A.jsonl"),
        str(DATA / "demo_synthetic_annotations" / "annotator_B.jsonl"),
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_full_pipeline_runs_end_to_end(tmp_path):
    splits_dir = tmp_path / "splits"
    stats_path = tmp_path / "stats.json"
    report_path = tmp_path / "report.md"
    eval_out = tmp_path / "eval.json"

    r1 = run(
        str(SCRIPTS / "generate_splits.py"),
        "--postings", str(DATA / "postings" / "postings.jsonl"),
        "--pairs", str(DATA / "postings" / "matched_pairs.jsonl"),
        "--adjudicated", str(DATA / "demo_synthetic_annotations" / "adjudicated_demo.jsonl"),
        "--rubric-version", "1.0.0-draft",
        "--out-dir", str(splits_dir),
        "--label", "test",
    )
    assert r1.returncode == 0, r1.stdout + r1.stderr
    manifest = json.loads((splits_dir / "manifest_test.json").read_text(encoding="utf-8"))
    assert manifest["is_gold"] is False
    assert set(manifest["holdout_regions_present"]) <= {"jeonbuk", "metro"}
    assert len(manifest["holdout_regions_present"]) == 2  # both regions present

    r2 = run(
        str(SCRIPTS / "aggregate_stats.py"),
        "--postings", str(DATA / "postings" / "postings.jsonl"),
        "--pairs", str(DATA / "postings" / "matched_pairs.jsonl"),
        "--adjudicated", str(DATA / "demo_synthetic_annotations" / "adjudicated_demo.jsonl"),
        "--rubric-version", "1.0.0-draft",
        "--out", str(stats_path),
    )
    assert r2.returncode == 0, r2.stdout + r2.stderr
    stats = json.loads(stats_path.read_text(encoding="utf-8"))
    assert stats["disclaimer"] == "exploratory sample; not population-generalizable"
    assert stats["is_gold"] is False

    r3 = run(
        str(SCRIPTS / "generate_report.py"),
        "--stats", str(stats_path),
        "--out", str(report_path),
    )
    assert r3.returncode == 0, r3.stdout + r3.stderr
    report_text = report_path.read_text(encoding="utf-8")
    assert "NOT GOLD" in report_text
    assert "exploratory sample; not population-generalizable" in report_text

    r4 = run(
        str(SCRIPTS / "evaluate_predictions.py"),
        "--postings", str(DATA / "postings" / "postings.jsonl"),
        "--gold", str(DATA / "demo_synthetic_annotations" / "adjudicated_demo.jsonl"),
        "--predictions", str(REPO_ROOT / "tests" / "data" / "fixtures" / "sample_predictions.jsonl"),
        "--rubric-version", "1.0.0-draft",
        "--out", str(eval_out),
        "--is-gold-source", "false",
    )
    assert r4.returncode == 0, r4.stdout + r4.stderr
    eval_report = json.loads(eval_out.read_text(encoding="utf-8"))
    assert eval_report["sample_size"]["schema_failures"] == 1
    assert eval_report["sample_size"]["unsupported_or_fabricated_evidence"] == 1
    assert eval_report["sample_size"]["duplicate_predictions_ignored"] == 1
    assert eval_report["primary_result_raw_counts"]["correct"] == 19
    assert eval_report["primary_result_raw_counts"]["incorrect"] == 3
