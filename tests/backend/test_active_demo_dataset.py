"""Coverage for the active-demo-listing filter (TASK "데모 전체를 연구직
청년 페르소나 + 연구직 공고 비교로 전환"). Exercises the *real* repo data
under data/intake/** (no monkeypatched paths) so these tests keep validating
whatever real, verified 연구개발 pairs are actually ingested -- they must
keep passing as ACTIVE_DEMO_MATCHED_PAIR_IDS grows.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest
from app.errors import PrivateDataUnavailableError
from app.services import real_postings

PRODUCTION_OCCUPATION = "생산직(제조 조립원)"
REPRESENTATIVE_METRO_ID = "MET-00"
REPRESENTATIVE_JEONBUK_ID = "JB-00"


@pytest.fixture(autouse=True)
def _clear_cache():
    real_postings.clear_real_postings_cache()
    yield
    real_postings.clear_real_postings_cache()


def _real_postings_by_id() -> dict:
    return real_postings._load_real_postings_by_id(str(real_postings._real_postings_path()))


def test_active_demo_listing_returns_only_research_postings():
    response = real_postings.list_capital_area_postings()
    assert len(response.postings) > 0
    for item in response.postings:
        assert item.occupation != PRODUCTION_OCCUPATION


def test_representative_pair_is_first_in_the_listing():
    response = real_postings.list_capital_area_postings()
    assert response.postings[0].posting_id == REPRESENTATIVE_METRO_ID


def test_representative_metro_posting_matches_to_the_jeonbuk_representative():
    result = real_postings.find_home_region_matches(REPRESENTATIVE_METRO_ID)
    assert len(result.candidates) >= 1
    assert result.candidates[0].posting_id == REPRESENTATIVE_JEONBUK_ID


def test_every_active_pair_has_matching_occupation_and_employment_type():
    postings_by_id = _real_postings_by_id()
    active = [r for r in postings_by_id.values() if r.get("matched_pair_id") in real_postings.ACTIVE_DEMO_MATCHED_PAIR_IDS]
    assert len(active) > 0
    by_pair: dict[str, list[dict]] = {}
    for record in active:
        by_pair.setdefault(record["matched_pair_id"], []).append(record)
    for pair_id, records in by_pair.items():
        metro = next((r for r in records if r["region_group"] == "metro"), None)
        jeonbuk = next((r for r in records if r["region_group"] == "jeonbuk"), None)
        assert metro is not None and jeonbuk is not None, f"{pair_id} is missing its metro or jeonbuk side"
        assert metro["occupation"] == jeonbuk["occupation"], pair_id
        assert metro["employment_type"] == jeonbuk["employment_type"], pair_id
        # 연구직 범위 -- 생산·조립은 절대 active 세트에 들어가지 않는다.
        assert metro["occupation"] != PRODUCTION_OCCUPATION, pair_id


def test_production_postings_are_preserved_but_excluded_from_active_listing():
    postings_by_id = _real_postings_by_id()
    production_ids = {
        pid for pid, r in postings_by_id.items() if r.get("occupation") == PRODUCTION_OCCUPATION and r.get("region_group") == "metro"
    }
    assert len(production_ids) > 0, "the original 10:10 production sample must still be on disk"

    listing_ids = {item.posting_id for item in real_postings.list_capital_area_postings().postings}
    assert listing_ids.isdisjoint(production_ids)

    # Still reachable through every other function -- never deleted.
    sample_id = sorted(production_ids)[0]
    matches = real_postings.find_home_region_matches(sample_id)
    assert len(matches.candidates) >= 0  # does not raise NoMatchFoundError due to missing data


def test_private_text_missing_fails_closed_for_representative_posting():
    # This machine has no data/private/intake_raw/** staged by default.
    with pytest.raises(PrivateDataUnavailableError):
        real_postings.resolve_private_text(REPRESENTATIVE_METRO_ID)


def test_private_text_hash_mismatch_fails_closed(tmp_path, monkeypatch):
    private_dir = tmp_path / "intake_raw"
    private_dir.mkdir(parents=True)
    monkeypatch.setenv("PRIVATE_INTAKE_RAW_DIR", str(private_dir))

    (private_dir / f"{REPRESENTATIVE_METRO_ID}.json").write_text(
        json.dumps({"posting_id": REPRESENTATIVE_METRO_ID, "full_text": "이것은 원문이 아닌 위조된 텍스트입니다."}, ensure_ascii=False),
        encoding="utf-8",
    )
    real_postings.clear_real_postings_cache()
    with pytest.raises(PrivateDataUnavailableError):
        real_postings.resolve_private_text(REPRESENTATIVE_METRO_ID)


def test_private_text_hash_match_succeeds(tmp_path, monkeypatch):
    # Verifies the *positive* path (matching hash resolves normally) with a
    # small isolated fixture record, since fabricating private text whose
    # SHA-256 equals the real representative posting's hash isn't possible.
    private_dir = tmp_path / "intake_raw"
    postings_path = tmp_path / "real_postings.jsonl"
    private_dir.mkdir(parents=True)
    body = "실험용 원문 텍스트입니다."
    digest = hashlib.sha256(body.encode("utf-8")).hexdigest()
    postings_path.write_text(
        json.dumps(
            {
                "posting_id": "HASH-OK",
                "region_group": "metro",
                "occupation": "테스트직",
                "employment_type": "정규직",
                "full_text_sha256": digest,
            },
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    (private_dir / "HASH-OK.json").write_text(
        json.dumps({"posting_id": "HASH-OK", "full_text": body, "occupation": "테스트직"}, ensure_ascii=False),
        encoding="utf-8",
    )
    monkeypatch.setenv("PRIVATE_INTAKE_RAW_DIR", str(private_dir))
    monkeypatch.setenv("REAL_POSTINGS_PATH", str(postings_path))
    real_postings.clear_real_postings_cache()

    text, occupation = real_postings.resolve_private_text("HASH-OK")
    assert text == body
    assert occupation == "테스트직"


def test_active_demo_matched_pair_ids_never_reference_a_synthetic_fixture():
    postings_by_id = _real_postings_by_id()
    for record in postings_by_id.values():
        if record.get("matched_pair_id") in real_postings.ACTIVE_DEMO_MATCHED_PAIR_IDS:
            assert not record.get("synthetic_test_fixture", False)


def test_api_contract_fields_unchanged_for_posting_list_item():
    # TASK requires no field deletions from the existing API contract.
    from app.models.listing import PostingListItem

    required_fields = {
        "posting_id",
        "company_name",
        "region",
        "municipality",
        "occupation",
        "employment_type",
        "source_url",
        "collection_date",
        "is_synthetic",
        "private_text_available",
    }
    assert required_fields.issubset(set(PostingListItem.model_fields.keys()))
