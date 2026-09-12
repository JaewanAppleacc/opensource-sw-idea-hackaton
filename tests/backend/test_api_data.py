from __future__ import annotations

from conftest import FIXTURES_DIR


def test_gap_stats_refuses_when_no_gold_labels_present(client, monkeypatch):
    monkeypatch.setenv("GOLD_LABELS_PATH", str(FIXTURES_DIR / "does_not_exist.json"))
    response = client.get("/api/v1/data/gap-stats")
    assert response.status_code == 200  # a typed "not ready" body, not a 5xx
    body = response.json()
    assert body["ready"] is False
    assert body["error"]["code"] == "data_not_ready"
    assert body["stats"] is None


def test_gap_stats_returns_exploratory_stats_once_gold_labels_exist(client, monkeypatch):
    monkeypatch.setenv("GOLD_LABELS_PATH", str(FIXTURES_DIR / "gold_labels_sample.json"))
    response = client.get("/api/v1/data/gap-stats")
    assert response.status_code == 200
    body = response.json()
    assert body["ready"] is True
    assert body["stats"]["exploratory"] is True
    assert body["stats"]["sample_size_postings"] == 3
