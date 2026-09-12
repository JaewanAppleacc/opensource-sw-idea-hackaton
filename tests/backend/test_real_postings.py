from __future__ import annotations

import json

import pytest
from app.errors import NoMatchFoundError, PrivateDataUnavailableError
from app.services import real_postings


def write_jsonl(path, records):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def metro_posting(pid, **overrides):
    base = {
        "posting_id": pid,
        "region_group": "metro",
        "municipality": "서울특별시",
        "occupation": "생산직(제조 조립원)",
        "employment_type": "정규직",
        "collection_date": "2026-01-01",
        "source_name": "고용24",
        "source_id_url": "https://example.invalid/x",
        "company_name": "(테스트) 수도권회사",
        "full_text": None,
        "redistributable": False,
        "synthetic_test_fixture": False,
    }
    base.update(overrides)
    return base


def home_posting(pid, **overrides):
    base = {
        "posting_id": pid,
        "region_group": "jeonbuk",
        "municipality": "전주시",
        "occupation": "생산직(제조 조립원)",
        "employment_type": "정규직",
        "collection_date": "2026-01-01",
        "source_name": "고용24",
        "source_id_url": "https://example.invalid/y",
        "company_name": "(테스트) 전북회사",
        "full_text": None,
        "redistributable": False,
        "synthetic_test_fixture": False,
    }
    base.update(overrides)
    return base


@pytest.fixture()
def real_data(tmp_path, monkeypatch):
    postings_path = tmp_path / "real_postings.jsonl"
    pairs_path = tmp_path / "real_matched_pairs.jsonl"
    private_dir = tmp_path / "intake_raw"

    write_jsonl(
        postings_path,
        [
            metro_posting("TEST-MET-01"),
            metro_posting("TEST-MET-02"),
            home_posting("TEST-JB-01"),
            home_posting("TEST-JB-02"),
        ],
    )
    write_jsonl(
        pairs_path,
        [
            {
                "matched_pair_id": "P-TEST-001",
                "metro_posting_id": "TEST-MET-01",
                "jeonbuk_posting_id": "TEST-JB-01",
                "occupation": "생산직(제조 조립원)",
                "employment_type": "정규직",
            }
        ],
    )
    monkeypatch.setenv("REAL_POSTINGS_PATH", str(postings_path))
    monkeypatch.setenv("REAL_MATCHED_PAIRS_PATH", str(pairs_path))
    monkeypatch.setenv("PRIVATE_INTAKE_RAW_DIR", str(private_dir))
    monkeypatch.setenv("DEMO_HOME_REGION", "jeonbuk")
    real_postings.clear_real_postings_cache()
    return {"postings_path": postings_path, "pairs_path": pairs_path, "private_dir": private_dir}


def test_list_capital_area_postings_returns_only_metro(real_data):
    response = real_postings.list_capital_area_postings()
    assert response.home_region == "jeonbuk"
    ids = {p.posting_id for p in response.postings}
    assert ids == {"TEST-MET-01", "TEST-MET-02"}
    assert all(not p.private_text_available for p in response.postings)


def test_private_text_available_reflects_live_filesystem(real_data):
    private_dir = real_data["private_dir"]
    private_dir.mkdir(parents=True)
    (private_dir / "TEST-MET-01.json").write_text(
        json.dumps({"posting_id": "TEST-MET-01", "full_text": "합성 테스트 본문"}, ensure_ascii=False),
        encoding="utf-8",
    )
    response = real_postings.list_capital_area_postings()
    by_id = {p.posting_id: p for p in response.postings}
    assert by_id["TEST-MET-01"].private_text_available is True
    assert by_id["TEST-MET-02"].private_text_available is False


def test_find_home_region_matches_returns_paired_candidate(real_data):
    result = real_postings.find_home_region_matches("TEST-MET-01")
    assert len(result.candidates) == 1
    assert result.candidates[0].posting_id == "TEST-JB-01"
    assert result.candidates[0].region == "jeonbuk"
    assert result.candidates[0].source_text is None  # never leaked through match layer


def test_find_home_region_matches_raises_for_unpaired_metro_posting(real_data):
    with pytest.raises(NoMatchFoundError):
        real_postings.find_home_region_matches("TEST-MET-02")


def test_find_home_region_matches_raises_for_unknown_posting_id(real_data):
    with pytest.raises(NoMatchFoundError):
        real_postings.find_home_region_matches("NOT-A-REAL-ID")


def test_home_region_enforcement_rejects_pair_outside_configured_region(real_data, monkeypatch):
    # Simulate a future multi-region pairs file containing an out-of-region
    # candidate; the server must never surface it even though the pair exists.
    pairs_path = real_data["pairs_path"]
    write_jsonl(
        pairs_path,
        [
            {
                "matched_pair_id": "P-TEST-002",
                "metro_posting_id": "TEST-MET-02",
                "jeonbuk_posting_id": "TEST-JB-02-OTHER-REGION",
                "occupation": "생산직(제조 조립원)",
                "employment_type": "정규직",
            }
        ],
    )
    postings_path = real_data["postings_path"]
    write_jsonl(
        postings_path,
        [
            metro_posting("TEST-MET-01"),
            metro_posting("TEST-MET-02"),
            home_posting("TEST-JB-01"),
            home_posting("TEST-JB-02-OTHER-REGION", region_group="jeonnam"),
        ],
    )
    real_postings.clear_real_postings_cache()
    with pytest.raises(NoMatchFoundError):
        real_postings.find_home_region_matches("TEST-MET-02")


def test_resolve_private_text_raises_when_missing(real_data):
    with pytest.raises(PrivateDataUnavailableError):
        real_postings.resolve_private_text("TEST-MET-01")


def test_resolve_private_text_returns_text_when_present(real_data):
    private_dir = real_data["private_dir"]
    private_dir.mkdir(parents=True)
    (private_dir / "TEST-MET-01.json").write_text(
        json.dumps(
            {"posting_id": "TEST-MET-01", "full_text": "합성 테스트 본문", "occupation": "생산직(제조 조립원)"},
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    text, occupation = real_postings.resolve_private_text("TEST-MET-01")
    assert text == "합성 테스트 본문"
    assert occupation == "생산직(제조 조립원)"


def test_resolve_private_text_raises_when_empty(real_data):
    private_dir = real_data["private_dir"]
    private_dir.mkdir(parents=True)
    (private_dir / "TEST-MET-01.json").write_text(
        json.dumps({"posting_id": "TEST-MET-01", "full_text": ""}, ensure_ascii=False), encoding="utf-8"
    )
    with pytest.raises(PrivateDataUnavailableError):
        real_postings.resolve_private_text("TEST-MET-01")


# --- API-level tests ---


def test_api_home_region_listing(client, real_data):
    response = client.get("/api/v1/postings/home-region-listing")
    assert response.status_code == 200
    body = response.json()
    assert body["home_region"] == "jeonbuk"
    assert {p["posting_id"] for p in body["postings"]} == {"TEST-MET-01", "TEST-MET-02"}


def test_api_home_region_matches(client, real_data):
    response = client.post("/api/v1/postings/home-region-matches", json={"metro_posting_id": "TEST-MET-01"})
    assert response.status_code == 200
    assert response.json()["candidates"][0]["posting_id"] == "TEST-JB-01"


def test_api_home_region_matches_no_match_is_404(client, real_data):
    response = client.post("/api/v1/postings/home-region-matches", json={"metro_posting_id": "TEST-MET-02"})
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "no_match_found"


def test_api_analyze_by_id_missing_private_data_is_503(client, real_data):
    response = client.post("/api/v1/postings/analyze-by-id", json={"posting_id": "TEST-MET-01"})
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "private_data_unavailable"


def test_api_analyze_by_id_succeeds_with_private_text(client, real_data):
    private_dir = real_data["private_dir"]
    private_dir.mkdir(parents=True)
    (private_dir / "TEST-MET-01.json").write_text(
        json.dumps(
            {
                "posting_id": "TEST-MET-01",
                "full_text": "월급 250만원(세전) 지급합니다. 고용형태는 정규직입니다.",
                "occupation": "생산직(제조 조립원)",
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    response = client.post("/api/v1/postings/analyze-by-id", json={"posting_id": "TEST-MET-01"})
    assert response.status_code == 200
    body = response.json()
    assert body["posting_id"] == "TEST-MET-01"
    assert set(body["fields"].keys()) == {
        "salary",
        "duties",
        "tools_or_skills",
        "training_or_mentoring",
        "probation_terms",
        "employment_type",
    }


def test_api_analyze_by_id_rejects_extra_field(client, real_data):
    response = client.post(
        "/api/v1/postings/analyze-by-id", json={"posting_id": "TEST-MET-01", "unexpected_field": "x"}
    )
    assert response.status_code == 422
