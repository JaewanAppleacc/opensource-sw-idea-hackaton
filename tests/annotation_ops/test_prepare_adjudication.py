import json

import pytest
from common import read_jsonl
from prepare_adjudication import build_queue, verify_final


def write_jsonl(path, records):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


FIELDS = ["salary", "duties", "tools_or_skills", "training_or_mentoring", "probation_terms", "employment_type"]


def cell(field, annotator_id, status="absent", evidence_text=None, offsets=None, synthetic=False, posting_id="JB-001"):
    return {
        "posting_id": posting_id,
        "field": field,
        "annotator_id": annotator_id,
        "status": status,
        "evidence_text": evidence_text,
        "offsets": offsets,
        "reason_code": "x",
        "disagreement_note": None,
        "rubric_version": "1.0.0-draft",
        "synthetic_test_fixture": synthetic,
    }


def make_postings_file(tmp_path):
    postings_path = tmp_path / "postings.jsonl"
    write_jsonl(
        postings_path,
        [
            {
                "posting_id": "JB-001",
                "region_group": "jeonbuk",
                "occupation": "x",
                "employment_type": "정규직",
                "full_text": "월급 250만원 지급. 조립 및 품질 검사 업무를 담당합니다.",
                "matched_pair_id": "P1",
                "unmatched": False,
            }
        ],
    )
    return postings_path


def test_build_queue_refuses_when_packet_a_incomplete(tmp_path):
    postings_path = make_postings_file(tmp_path)
    a_rows = [cell(f, "A") for f in FIELDS]
    a_rows[0]["status"] = None  # incomplete
    b_rows = [cell(f, "B") for f in FIELDS]
    a_path = tmp_path / "annotator_A" / "packet.jsonl"
    b_path = tmp_path / "annotator_B" / "packet.jsonl"
    write_jsonl(a_path, a_rows)
    write_jsonl(b_path, b_rows)

    with pytest.raises(ValueError, match="unanswered cells"):
        build_queue(a_path, b_path, postings_path, tmp_path / "out.jsonl", tmp_path / "review.jsonl")


def test_build_queue_refuses_on_validation_failure(tmp_path):
    postings_path = make_postings_file(tmp_path)
    a_rows = [cell(f, "A") for f in FIELDS]
    a_rows[0]["annotator_id"] = "B"  # contamination -> validate_packets should fail
    b_rows = [cell(f, "B") for f in FIELDS]
    a_path = tmp_path / "annotator_A" / "packet.jsonl"
    b_path = tmp_path / "annotator_B" / "packet.jsonl"
    write_jsonl(a_path, a_rows)
    write_jsonl(b_path, b_rows)

    with pytest.raises(ValueError, match="REFUSED: packet validation failed"):
        build_queue(a_path, b_path, postings_path, tmp_path / "out.jsonl", tmp_path / "review.jsonl")


def test_build_queue_writes_comparison_and_disagreement_only_review_queue(tmp_path):
    postings_path = make_postings_file(tmp_path)
    a_rows = [cell(f, "A") for f in FIELDS]
    b_rows = [cell(f, "B") for f in FIELDS]
    # Disagree on exactly one field.
    a_rows[0].update(status="confirmed", evidence_text="250만원", offsets=[3, 8])
    b_rows[0].update(status="vague", evidence_text="250만원", offsets=[3, 8])

    a_path = tmp_path / "annotator_A" / "packet.jsonl"
    b_path = tmp_path / "annotator_B" / "packet.jsonl"
    write_jsonl(a_path, a_rows)
    write_jsonl(b_path, b_rows)

    out_path = tmp_path / "comparison.jsonl"
    review_path = tmp_path / "review.jsonl"
    stats = build_queue(a_path, b_path, postings_path, out_path, review_path)

    assert stats["total_cells"] == len(FIELDS)
    assert stats["disagree_count"] == 1
    assert stats["agree_count"] == len(FIELDS) - 1

    review_rows = read_jsonl(review_path)
    assert len(review_rows) == 1
    assert review_rows[0]["field"] == "salary"
    assert review_rows[0]["adjudicated_status"] is None

    comparison_rows = read_jsonl(out_path)
    agreed = [r for r in comparison_rows if r["agreement"]]
    assert all(r["adjudicated_status"] is not None for r in agreed)


def test_verify_final_fails_when_status_still_null(tmp_path):
    path = tmp_path / "final.jsonl"
    write_jsonl(path, [{"posting_id": "JB-001", "field": "salary", "adjudicated_status": None, "agreement": True}])
    ok, errors = verify_final(path)
    assert not ok
    assert any("still null" in e for e in errors)


def test_verify_final_fails_when_disagreement_missing_note(tmp_path):
    path = tmp_path / "final.jsonl"
    write_jsonl(
        path,
        [
            {
                "posting_id": "JB-001",
                "field": "salary",
                "agreement": False,
                "adjudicated_status": "confirmed",
                "adjudicated_evidence_text": "250만원",
                "adjudicated_offsets": [3, 8],
                "adjudicator_note": None,
            }
        ],
    )
    ok, errors = verify_final(path)
    assert not ok
    assert any("adjudicator_note" in e for e in errors)


def test_verify_final_fails_when_disagreement_reuses_auto_fill_note(tmp_path):
    path = tmp_path / "final.jsonl"
    write_jsonl(
        path,
        [
            {
                "posting_id": "JB-001",
                "field": "salary",
                "agreement": False,
                "adjudicated_status": "confirmed",
                "adjudicated_evidence_text": "250만원",
                "adjudicated_offsets": [3, 8],
                "adjudicator_note": "auto-filled: A and B agreed",
            }
        ],
    )
    ok, errors = verify_final(path)
    assert not ok


def test_verify_final_passes_for_properly_completed_file(tmp_path):
    path = tmp_path / "final.jsonl"
    write_jsonl(
        path,
        [
            {
                "posting_id": "JB-001",
                "field": "salary",
                "agreement": True,
                "adjudicated_status": "absent",
                "adjudicated_evidence_text": None,
                "adjudicated_offsets": None,
                "adjudicator_note": "auto-filled: A and B agreed",
            },
            {
                "posting_id": "JB-001",
                "field": "duties",
                "agreement": False,
                "adjudicated_status": "confirmed",
                "adjudicated_evidence_text": "조립 및 품질 검사 업무를 담당합니다.",
                "adjudicated_offsets": [10, 30],
                "adjudicator_note": "A missed the explicit process description; B's read is correct.",
            },
        ],
    )
    ok, errors = verify_final(path)
    assert ok, errors
