from __future__ import annotations

import json
from pathlib import Path

from app.models.common import FIELD_NAMES
from app.services.gap_stats import compute_gap_stats

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"


def test_missing_gold_labels_returns_typed_not_ready(monkeypatch):
    monkeypatch.setenv("GOLD_LABELS_PATH", str(FIXTURES_DIR / "does_not_exist.json"))
    response = compute_gap_stats()
    assert response.ready is False
    assert response.stats is None
    assert response.error is not None
    assert response.error.code == "data_not_ready"


def test_gold_labels_present_returns_stats(monkeypatch):
    monkeypatch.setenv("GOLD_LABELS_PATH", str(FIXTURES_DIR / "gold_labels_sample.json"))
    response = compute_gap_stats()

    assert response.ready is True
    assert response.error is None
    assert response.stats is not None
    assert response.stats.sample_size_postings == 3
    assert response.stats.sample_size_cells == 18  # 3 postings * 6 fields
    assert response.stats.exploratory is True
    assert response.stats.rubric_version == "v1"

    salary_proportions = response.stats.label_proportions["salary"]
    assert abs(sum(salary_proportions.values()) - 1.0) < 1e-9


def test_malformed_gold_labels_file_is_not_ready_not_a_crash(monkeypatch, tmp_path):
    bad_file = tmp_path / "malformed.json"
    bad_file.write_text("{not valid json", encoding="utf-8")
    monkeypatch.setenv("GOLD_LABELS_PATH", str(bad_file))

    response = compute_gap_stats()
    assert response.ready is False
    assert response.error.code == "data_not_ready"


def test_data_track_jsonl_gold_is_joined_with_posting_metadata(monkeypatch, tmp_path):
    postings_path = tmp_path / "postings.jsonl"
    postings = [
        {
            "posting_id": "JB-REAL-1",
            "region_group": "jeonbuk",
            "occupation": "생산직",
            "employment_type": "정규직",
        },
        {
            "posting_id": "MET-REAL-1",
            "region_group": "metro",
            "occupation": "생산직",
            "employment_type": "정규직",
        },
    ]
    postings_path.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False) for row in postings) + "\n",
        encoding="utf-8",
    )

    gold_path = tmp_path / "adjudicated_labels.jsonl"
    cells = []
    for posting_id in ("JB-REAL-1", "MET-REAL-1"):
        for index, field in enumerate(FIELD_NAMES):
            cells.append(
                {
                    "posting_id": posting_id,
                    "field": field,
                    "adjudicated_status": "confirmed" if index == 0 else "vague",
                    "rubric_version": "1.0.0",
                    "synthetic_test_fixture": False,
                }
            )
    gold_path.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False) for row in cells) + "\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("GOLD_LABELS_PATH", str(gold_path))
    monkeypatch.setenv("POSTINGS_DATASET_PATH", str(postings_path))

    response = compute_gap_stats()

    assert response.ready is True
    assert response.stats is not None
    assert response.stats.sample_size_postings == 2
    assert response.stats.sample_size_cells == 12
    assert set(response.stats.label_proportions_by_region) == {"jeonbuk", "metro"}
    assert response.stats.label_proportions_by_region["jeonbuk"]["salary"]["confirmed"] == 1.0


def test_synthetic_demo_adjudication_is_never_reported_as_gold(monkeypatch):
    synthetic_demo = (
        REPO_ROOT
        / "data"
        / "demo_synthetic_annotations"
        / "adjudicated_demo.jsonl"
    )
    monkeypatch.setenv("GOLD_LABELS_PATH", str(synthetic_demo))

    response = compute_gap_stats()

    assert response.ready is False
    assert response.stats is None
    assert response.error is not None
    assert "synthetic" in response.error.message
