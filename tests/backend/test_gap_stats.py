from __future__ import annotations

from app.services.gap_stats import compute_gap_stats
from conftest import FIXTURES_DIR


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
