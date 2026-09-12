from __future__ import annotations

from app.models.common import FIELD_NAMES
from sample_postings import FULLY_SPECIFIED_POSTING, MINIMAL_POSTING_MISSING_MOST_FIELDS, VAGUE_SALARY_POSTING


def test_analyze_returns_all_six_confirmed_fields_with_verified_evidence(client):
    response = client.post("/api/v1/postings/analyze", json={"source_text": FULLY_SPECIFIED_POSTING})
    assert response.status_code == 200
    body = response.json()

    assert set(body["fields"].keys()) == set(FIELD_NAMES)
    for name in FIELD_NAMES:
        field = body["fields"][name]
        assert field["status"] == "confirmed"
        evidence = field["evidence"]
        assert evidence is not None
        assert FULLY_SPECIFIED_POSTING[evidence["start"] : evidence["end"]] == evidence["text"]


def test_analyze_turns_vague_field_into_verification_action(client):
    response = client.post("/api/v1/postings/analyze", json={"source_text": VAGUE_SALARY_POSTING})
    assert response.status_code == 200
    body = response.json()

    assert body["fields"]["salary"]["status"] == "vague"
    actions = [a for a in body["verification_actions"] if a["field"] == "salary"]
    assert len(actions) == 1
    assert actions[0]["triggered_by_status"] == "vague"
    assert actions[0]["channel"] in ("email", "phone", "interview", "document_review", "pre_contract")


def test_analyze_absent_field_gets_no_evidence_and_an_action(client):
    response = client.post("/api/v1/postings/analyze", json={"source_text": MINIMAL_POSTING_MISSING_MOST_FIELDS})
    assert response.status_code == 200
    body = response.json()

    assert body["fields"]["salary"]["status"] == "absent"
    assert body["fields"]["salary"]["evidence"] is None
    assert any(a["field"] == "salary" and a["triggered_by_status"] == "absent" for a in body["verification_actions"])


def test_analyze_rejects_blank_source_text(client):
    response = client.post("/api/v1/postings/analyze", json={"source_text": ""})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "invalid_input"


def test_analyze_rejects_unknown_request_field(client):
    response = client.post(
        "/api/v1/postings/analyze", json={"source_text": FULLY_SPECIFIED_POSTING, "company_rating": 5}
    )
    assert response.status_code == 422


def test_match_returns_curated_jeonbuk_candidate_for_metropolitan_occupation(client):
    response = client.post("/api/v1/postings/match", json={"occupation": "백엔드 개발자", "employment_type": "정규직"})
    assert response.status_code == 200
    body = response.json()

    assert len(body["candidates"]) >= 1
    assert body["candidates"][0]["region"] == "jeonbuk"
    assert "finite curated" in body["dataset_description"]


def test_match_no_candidate_returns_typed_error(client):
    response = client.post("/api/v1/postings/match", json={"occupation": "존재하지-않는-직업"})
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "no_match_found"


def test_full_demo_works_with_real_provider_disabled(client, monkeypatch):
    """LLM_PROVIDER unset (or 'mock') must never require ANTHROPIC_API_KEY."""
    monkeypatch.delenv("LLM_PROVIDER", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    response = client.post("/api/v1/postings/analyze", json={"source_text": FULLY_SPECIFIED_POSTING})
    assert response.status_code == 200
    assert all(f["status"] == "confirmed" for f in response.json()["fields"].values())
