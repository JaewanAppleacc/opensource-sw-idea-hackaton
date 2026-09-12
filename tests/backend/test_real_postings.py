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


def test_find_home_region_matches_puts_the_pre_linked_pair_first(real_data):
    # The base fixture has TEST-MET-01<->TEST-JB-01 pre-linked, plus
    # TEST-JB-02 as an unlinked same-group posting -- both are eligible, so
    # the response has exactly 2 candidates, pre-linked one first.
    result = real_postings.find_home_region_matches("TEST-MET-01")
    assert [c.posting_id for c in result.candidates] == ["TEST-JB-01", "TEST-JB-02"]
    assert result.candidates[0].region == "jeonbuk"
    assert all(c.source_text is None for c in result.candidates)  # never leaked through match layer


def test_find_home_region_matches_falls_back_to_group_when_unpaired(real_data):
    # TEST-MET-02 has no pre-linked pair, but TEST-JB-01/02 are still
    # eligible same-group candidates -- this must not be "no match".
    result = real_postings.find_home_region_matches("TEST-MET-02")
    assert [c.posting_id for c in result.candidates] == ["TEST-JB-01", "TEST-JB-02"]


def test_find_home_region_matches_caps_at_three_and_stays_deterministic(real_data):
    postings_path = real_data["postings_path"]
    write_jsonl(
        postings_path,
        [
            metro_posting("TEST-MET-01"),
            home_posting("TEST-JB-01"),
            home_posting("TEST-JB-02"),
            home_posting("TEST-JB-03"),
            home_posting("TEST-JB-04"),
        ],
    )
    real_postings.clear_real_postings_cache()

    first = real_postings.find_home_region_matches("TEST-MET-01")
    ids = [c.posting_id for c in first.candidates]
    assert len(ids) == 3
    assert ids[0] == "TEST-JB-01"  # pre-linked pair still first
    assert len(set(ids)) == 3  # no duplicate posting_id

    second = real_postings.find_home_region_matches("TEST-MET-01")
    assert [c.posting_id for c in second.candidates] == ids  # deterministic across repeated calls


def test_find_home_region_matches_returns_all_when_fewer_than_three_exist(real_data):
    # Base fixture only has two eligible candidates (TEST-JB-01, TEST-JB-02)
    # -- must return exactly those two, never padded with a fake third.
    result = real_postings.find_home_region_matches("TEST-MET-01")
    assert len(result.candidates) == 2


def test_find_home_region_matches_excludes_a_different_occupation(real_data):
    postings_path = real_data["postings_path"]
    write_jsonl(
        postings_path,
        [
            metro_posting("TEST-MET-01"),
            home_posting("TEST-JB-01"),
            home_posting("TEST-JB-OTHER-OCC", occupation="사무직"),
        ],
    )
    real_postings.clear_real_postings_cache()
    result = real_postings.find_home_region_matches("TEST-MET-01")
    ids = [c.posting_id for c in result.candidates]
    assert "TEST-JB-OTHER-OCC" not in ids


def test_find_home_region_matches_excludes_a_different_employment_type(real_data):
    postings_path = real_data["postings_path"]
    write_jsonl(
        postings_path,
        [
            metro_posting("TEST-MET-01"),
            home_posting("TEST-JB-01"),
            home_posting("TEST-JB-PARTTIME", employment_type="계약직"),
        ],
    )
    real_postings.clear_real_postings_cache()
    result = real_postings.find_home_region_matches("TEST-MET-01")
    ids = [c.posting_id for c in result.candidates]
    assert "TEST-JB-PARTTIME" not in ids


def test_find_home_region_matches_excludes_synthetic_fixture_rows(real_data):
    postings_path = real_data["postings_path"]
    write_jsonl(
        postings_path,
        [
            metro_posting("TEST-MET-01"),
            home_posting("TEST-JB-01"),
            home_posting("TEST-JB-SYNTHETIC", synthetic_test_fixture=True),
        ],
    )
    real_postings.clear_real_postings_cache()
    result = real_postings.find_home_region_matches("TEST-MET-01")
    ids = [c.posting_id for c in result.candidates]
    assert "TEST-JB-SYNTHETIC" not in ids


def test_find_home_region_matches_raises_when_no_eligible_candidate_exists(real_data):
    postings_path = real_data["postings_path"]
    write_jsonl(
        postings_path,
        [
            metro_posting("TEST-MET-UNIQUE", occupation="특수직"),
            home_posting("TEST-JB-01"),  # different occupation, not eligible
        ],
    )
    real_postings.clear_real_postings_cache()
    with pytest.raises(NoMatchFoundError):
        real_postings.find_home_region_matches("TEST-MET-UNIQUE")


def test_find_home_region_matches_raises_for_unknown_posting_id(real_data):
    with pytest.raises(NoMatchFoundError):
        real_postings.find_home_region_matches("NOT-A-REAL-ID")


def test_home_region_enforcement_never_surfaces_a_pair_outside_configured_region(real_data, monkeypatch):
    # Simulate a future multi-region pairs file containing an out-of-region
    # candidate; the server must never surface it even though the pair
    # exists -- but a same-group posting that *is* in the home region must
    # still come through via the group fallback.
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
    result = real_postings.find_home_region_matches("TEST-MET-02")
    ids = [c.posting_id for c in result.candidates]
    assert ids == ["TEST-JB-01"]
    assert "TEST-JB-02-OTHER-REGION" not in ids


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


@pytest.mark.parametrize(
    "malicious_posting_id",
    [
        "../secret",
        "../../etc/passwd",
        "../../../../etc/passwd",
        "sub/dir",
        "/etc/passwd",
        "..%2f..%2fetc%2fpasswd",
        "TEST-MET-01/../../secret",
    ],
)
def test_resolve_private_text_rejects_path_traversal_posting_ids(real_data, tmp_path, malicious_posting_id):
    """posting_id ultimately comes from a client-supplied request field
    (AnalyzeByIdRequest.posting_id) with no character restriction beyond
    min_length=1 -- it must never be able to escape the private intake_raw
    directory via path separators or "..", regardless of what a file
    outside that directory happens to contain."""
    outside_secret = tmp_path / "secret.json"
    outside_secret.write_text(
        json.dumps({"posting_id": "irrelevant", "full_text": "SHOULD NOT BE READABLE"}, ensure_ascii=False),
        encoding="utf-8",
    )
    private_dir = real_data["private_dir"]
    private_dir.mkdir(parents=True, exist_ok=True)

    with pytest.raises(PrivateDataUnavailableError):
        real_postings.resolve_private_text(malicious_posting_id)


@pytest.mark.parametrize("malicious_posting_id", ["../secret", "/etc/passwd", "a/../../b"])
def test_private_text_available_rejects_path_traversal_posting_ids(real_data, malicious_posting_id):
    private_dir = real_data["private_dir"]
    private_dir.mkdir(parents=True, exist_ok=True)
    assert real_postings.private_text_available(malicious_posting_id) is False


def test_api_analyze_by_id_rejects_path_traversal_posting_id(client, real_data, tmp_path):
    outside_secret = tmp_path / "secret.json"
    outside_secret.write_text(
        json.dumps({"posting_id": "irrelevant", "full_text": "SHOULD NOT BE READABLE"}, ensure_ascii=False),
        encoding="utf-8",
    )
    response = client.post(
        "/api/v1/postings/analyze-by-id",
        json={"posting_id": "../secret"},
    )
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "private_data_unavailable"


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
    body = response.json()
    assert body["candidates"][0]["posting_id"] == "TEST-JB-01"
    assert len(body["candidates"]) == 2  # base fixture has exactly two eligible candidates
    assert all(c["source_text"] is None for c in body["candidates"])  # MatchCandidate never carries full_text here


def test_api_home_region_matches_group_fallback_when_unpaired(client, real_data):
    # TEST-MET-02 has no pre-linked pair, but still has eligible same-group
    # candidates -- this is a 200 with candidates, not a 404.
    response = client.post("/api/v1/postings/home-region-matches", json={"metro_posting_id": "TEST-MET-02"})
    assert response.status_code == 200
    ids = [c["posting_id"] for c in response.json()["candidates"]]
    assert ids == ["TEST-JB-01", "TEST-JB-02"]


def test_api_home_region_matches_no_eligible_candidate_is_404(client, real_data):
    postings_path = real_data["postings_path"]
    write_jsonl(
        postings_path,
        [
            metro_posting("TEST-MET-UNIQUE", occupation="특수직"),
            home_posting("TEST-JB-01"),
        ],
    )
    real_postings.clear_real_postings_cache()
    response = client.post("/api/v1/postings/home-region-matches", json={"metro_posting_id": "TEST-MET-UNIQUE"})
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
