from __future__ import annotations

import json

import pytest


def _write_private_text(private_dir, posting_id: str, full_text: str) -> None:
    private_dir.mkdir(parents=True, exist_ok=True)
    (private_dir / f"{posting_id}.json").write_text(
        json.dumps({"posting_id": posting_id, "full_text": full_text}, ensure_ascii=False), encoding="utf-8"
    )


def _write_structured(path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


@pytest.fixture()
def structured_env(tmp_path, monkeypatch):
    private_dir = tmp_path / "intake_raw"
    structured_path = tmp_path / "work24_structured.jsonl"
    monkeypatch.setenv("PRIVATE_INTAKE_RAW_DIR", str(private_dir))
    monkeypatch.setenv("WORK24_STRUCTURED_PATH", str(structured_path))
    monkeypatch.setenv("REAL_POSTINGS_PATH", str(tmp_path / "real_postings_empty.jsonl"))
    (tmp_path / "real_postings_empty.jsonl").write_text("", encoding="utf-8")
    return {"private_dir": private_dir, "structured_path": structured_path}


def test_analyze_by_id_uses_hybrid_pipeline_when_structured_record_exists(client, structured_env):
    posting_id = "HYBRID-01"
    _write_private_text(
        structured_env["private_dir"],
        posting_id,
        "급여: 연봉 3,000만원 ~ 4,000만원\n담당업무: 서비스 운영 및 관리 업무를 담당합니다\n고용형태: 정규직\n",
    )
    _write_structured(
        structured_env["structured_path"],
        [
            {
                "posting_id": posting_id,
                "occupation_name": "테스트 직종",
                "employment_type": "정규직",
                "salary_type": "연봉",
                "salary_min": 30_000_000,
                "salary_max": 40_000_000,
                "weekly_hours": 40.0,
                "detailed_work_hours": "주 5일 근무",
            }
        ],
    )

    response = client.post("/api/v1/postings/analyze-by-id", json={"posting_id": posting_id})
    assert response.status_code == 200
    body = response.json()

    assert body["fields"]["salary"]["provenance"] == "WORK24_STRUCTURED"
    assert body["fields"]["salary"]["status"] == "confirmed"
    assert body["fields"]["salary"]["evidence"] is None
    assert body["fields"]["employment_type"]["provenance"] == "WORK24_STRUCTURED"
    assert body["fields"]["duties"]["provenance"] == "SLM_EXTRACTED"
    assert body["work_hours"] is not None
    assert body["work_hours"]["status"] == "confirmed"


def test_analyze_by_id_falls_back_to_legacy_pipeline_when_no_structured_record(client, structured_env):
    posting_id = "LEGACY-01"
    _write_private_text(
        structured_env["private_dir"],
        posting_id,
        "급여: 연봉 3,000만원\n담당업무: 서비스 운영 및 관리 업무를 담당합니다\n고용형태: 정규직\n",
    )
    # work24_structured.jsonl deliberately has no entry for LEGACY-01.
    _write_structured(structured_env["structured_path"], [])

    response = client.post("/api/v1/postings/analyze-by-id", json={"posting_id": posting_id})
    assert response.status_code == 200
    body = response.json()

    # Every field comes from the unchanged six-field provider pipeline.
    for name in body["fields"]:
        assert body["fields"][name]["provenance"] == "SLM_EXTRACTED"
    assert body["work_hours"] is None  # unchanged not_evaluated MVP-scope behavior


def test_analyze_by_id_structured_absent_work_hours_when_registry_lacks_them(client, structured_env):
    posting_id = "HYBRID-02"
    _write_private_text(structured_env["private_dir"], posting_id, "담당업무: 아무 설명 없음\n")
    _write_structured(
        structured_env["structured_path"],
        [
            {
                "posting_id": posting_id,
                "occupation_name": "테스트 직종",
                "employment_type": "정규직",
            }
        ],
    )

    response = client.post("/api/v1/postings/analyze-by-id", json={"posting_id": posting_id})
    assert response.status_code == 200
    body = response.json()
    assert body["work_hours"]["status"] == "structured_absent"
