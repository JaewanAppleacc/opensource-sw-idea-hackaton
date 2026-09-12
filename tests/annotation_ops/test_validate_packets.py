import json

from validate_packets import (
    check_annotator_id_isolation,
    check_cross_annotator_provenance,
    check_files_distinct,
    check_no_ai_suggestion_keys,
    check_synthetic_flag_present,
    is_packet_complete,
    validate_packet_pair,
)


def write_jsonl(path, records):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def cell(field, status="absent", evidence_text=None, offsets=None, annotator_id="A", synthetic=False, rubric_version="1.0.0-draft", posting_id="JB-001"):
    return {
        "posting_id": posting_id,
        "field": field,
        "annotator_id": annotator_id,
        "status": status,
        "evidence_text": evidence_text,
        "offsets": offsets,
        "reason_code": "x" if status else None,
        "disagreement_note": None,
        "rubric_version": rubric_version,
        "synthetic_test_fixture": synthetic,
    }


FIELDS = ["salary", "duties", "tools_or_skills", "training_or_mentoring", "probation_terms", "employment_type"]


def full_packet(annotator_id, synthetic=False):
    return [cell(f, annotator_id=annotator_id, synthetic=synthetic) for f in FIELDS]


def test_is_packet_complete_true_when_no_nulls():
    assert is_packet_complete(full_packet("A")) is True


def test_is_packet_complete_false_when_any_null_status():
    rows = full_packet("A")
    rows[0]["status"] = None
    assert is_packet_complete(rows) is False


def test_check_annotator_id_isolation_flags_wrong_id():
    rows = full_packet("A")
    rows[1]["annotator_id"] = "B"
    errors = check_annotator_id_isolation(rows, "A")
    assert len(errors) == 1
    assert "B" in errors[0]


def test_check_no_ai_suggestion_keys_flags_leaked_key():
    rows = full_packet("A")
    rows[0]["ai_suggested"] = True
    errors = check_no_ai_suggestion_keys(rows)
    assert len(errors) == 1


def test_check_synthetic_flag_present_flags_missing():
    rows = full_packet("A")
    del rows[0]["synthetic_test_fixture"]
    errors = check_synthetic_flag_present(rows)
    assert len(errors) == 1


def test_check_synthetic_flag_present_flags_non_bool():
    rows = full_packet("A")
    rows[0]["synthetic_test_fixture"] = "false"
    errors = check_synthetic_flag_present(rows)
    assert len(errors) == 1


def test_check_files_distinct_flags_same_path(tmp_path):
    p = tmp_path / "packet.jsonl"
    write_jsonl(p, full_packet("A"))
    errors = check_files_distinct(p, p)
    assert errors


def test_check_files_distinct_flags_identical_content(tmp_path):
    a = tmp_path / "a.jsonl"
    b = tmp_path / "b.jsonl"
    write_jsonl(a, full_packet("A"))
    write_jsonl(b, full_packet("A"))
    errors = check_files_distinct(a, b)
    assert errors


def test_check_files_distinct_passes_for_different_files(tmp_path):
    a = tmp_path / "a.jsonl"
    b = tmp_path / "b.jsonl"
    write_jsonl(a, full_packet("A"))
    write_jsonl(b, full_packet("B"))
    assert check_files_distinct(a, b) == []


def test_check_cross_annotator_provenance_flags_synthetic_mismatch():
    a_rows = full_packet("A", synthetic=True)
    b_rows = full_packet("B", synthetic=False)
    errors = check_cross_annotator_provenance(a_rows, b_rows)
    assert len(errors) == len(FIELDS)


def test_check_cross_annotator_provenance_flags_rubric_version_mismatch():
    a_rows = full_packet("A")
    b_rows = full_packet("B")
    b_rows[0]["rubric_version"] = "0.9.0-draft"
    errors = check_cross_annotator_provenance(a_rows, b_rows)
    assert len(errors) == 1


def test_validate_packet_pair_passes_for_clean_complete_packets(tmp_path):
    postings_path = tmp_path / "postings.jsonl"
    write_jsonl(postings_path, [{"posting_id": "JB-001", "region_group": "jeonbuk", "occupation": "x", "employment_type": "정규직", "full_text": "월급 250만원 지급.", "matched_pair_id": "P1", "unmatched": False}])
    a_path = tmp_path / "annotator_A" / "packet.jsonl"
    b_path = tmp_path / "annotator_B" / "packet.jsonl"
    a_rows = full_packet("A")
    a_rows[0].update(status="confirmed", evidence_text="250만원", offsets=[3, 8])
    b_rows = full_packet("B")
    b_rows[0].update(status="confirmed", evidence_text="250만원", offsets=[3, 8])
    write_jsonl(a_path, a_rows)
    write_jsonl(b_path, b_rows)

    ok, results = validate_packet_pair(a_path, b_path, postings_path)
    assert ok, results


def test_validate_packet_pair_fails_on_annotator_id_contamination(tmp_path):
    postings_path = tmp_path / "postings.jsonl"
    write_jsonl(postings_path, [{"posting_id": "JB-001", "region_group": "jeonbuk", "occupation": "x", "employment_type": "정규직", "full_text": "월급 250만원 지급.", "matched_pair_id": "P1", "unmatched": False}])
    a_path = tmp_path / "annotator_A" / "packet.jsonl"
    b_path = tmp_path / "annotator_B" / "packet.jsonl"
    a_rows = full_packet("A")
    a_rows[0]["annotator_id"] = "B"  # contamination
    b_rows = full_packet("B")
    write_jsonl(a_path, a_rows)
    write_jsonl(b_path, b_rows)

    ok, results = validate_packet_pair(a_path, b_path, postings_path)
    assert not ok
    assert results["annotator_A isolation (annotator_id)"]


def _write_private_json(private_dir, posting_id, full_text):
    private_dir.mkdir(parents=True, exist_ok=True)
    (private_dir / f"{posting_id}.json").write_text(
        json.dumps({"posting_id": posting_id, "full_text": full_text}, ensure_ascii=False), encoding="utf-8"
    )


def test_validate_packet_pair_joins_private_text_for_evidence_check(real_private_subdir):
    postings_path = real_private_subdir / "public.jsonl"
    write_jsonl(postings_path, [{"posting_id": "JB-001", "region_group": "jeonbuk", "occupation": "x", "employment_type": "정규직", "full_text": None, "matched_pair_id": "P1", "unmatched": False}])
    private_dir = real_private_subdir / "private_raw"
    _write_private_json(private_dir, "JB-001", "월급 250만원 지급.")

    a_path = real_private_subdir / "annotator_A" / "packet.jsonl"
    b_path = real_private_subdir / "annotator_B" / "packet.jsonl"
    a_rows = full_packet("A")
    a_rows[0].update(status="confirmed", evidence_text="250만원", offsets=[3, 8])
    b_rows = full_packet("B")
    b_rows[0].update(status="confirmed", evidence_text="250만원", offsets=[3, 8])
    write_jsonl(a_path, a_rows)
    write_jsonl(b_path, b_rows)

    ok, results = validate_packet_pair(a_path, b_path, postings_path, private_dir=private_dir)
    assert ok, results


def test_validate_packet_pair_flags_evidence_offset_mismatch_against_private_text(real_private_subdir):
    postings_path = real_private_subdir / "public.jsonl"
    write_jsonl(postings_path, [{"posting_id": "JB-001", "region_group": "jeonbuk", "occupation": "x", "employment_type": "정규직", "full_text": None, "matched_pair_id": "P1", "unmatched": False}])
    private_dir = real_private_subdir / "private_raw"
    _write_private_json(private_dir, "JB-001", "월급 250만원 지급.")

    a_path = real_private_subdir / "annotator_A" / "packet.jsonl"
    b_path = real_private_subdir / "annotator_B" / "packet.jsonl"
    a_rows = full_packet("A")
    # Wrong offsets for the claimed evidence text.
    a_rows[0].update(status="confirmed", evidence_text="250만원", offsets=[0, 5])
    b_rows = full_packet("B")
    b_rows[0].update(status="confirmed", evidence_text="250만원", offsets=[3, 8])
    write_jsonl(a_path, a_rows)
    write_jsonl(b_path, b_rows)

    ok, results = validate_packet_pair(a_path, b_path, postings_path, private_dir=private_dir)
    assert not ok
    assert results["annotator_A schema/evidence"]


def test_validate_packet_pair_flags_pii_in_evidence():
    a_rows = full_packet("A")
    a_rows[0]["evidence_text"] = "문의: 010-1234-5678"
    b_rows = full_packet("B")
    from private_source import check_no_pii_in_evidence

    assert check_no_pii_in_evidence(a_rows)
    assert check_no_pii_in_evidence(b_rows) == []


def test_validate_packet_pair_enforces_gitignored_output_only_in_private_dir_mode(tmp_path):
    """Without --private-dir (the synthetic-fixture path), an arbitrary
    tmp_path output location must still be accepted -- this is the existing,
    pre-real-data behavior and must not regress.
    """
    postings_path = tmp_path / "postings.jsonl"
    write_jsonl(postings_path, [{"posting_id": "JB-001", "region_group": "jeonbuk", "occupation": "x", "employment_type": "정규직", "full_text": "월급 250만원 지급.", "matched_pair_id": "P1", "unmatched": False}])
    a_path = tmp_path / "annotator_A" / "packet.jsonl"
    b_path = tmp_path / "annotator_B" / "packet.jsonl"
    write_jsonl(a_path, full_packet("A"))
    write_jsonl(b_path, full_packet("B"))

    ok, results = validate_packet_pair(a_path, b_path, postings_path)
    assert ok, results
    assert "annotator_A output path gitignored" not in results


def test_validate_packet_pair_expected_posting_count_mismatch_fails(tmp_path):
    postings_path = tmp_path / "postings.jsonl"
    write_jsonl(postings_path, [{"posting_id": "JB-001", "region_group": "jeonbuk", "occupation": "x", "employment_type": "정규직", "full_text": "월급 250만원 지급.", "matched_pair_id": "P1", "unmatched": False}])
    a_path = tmp_path / "annotator_A" / "packet.jsonl"
    b_path = tmp_path / "annotator_B" / "packet.jsonl"
    write_jsonl(a_path, full_packet("A"))
    write_jsonl(b_path, full_packet("B"))

    ok, results = validate_packet_pair(a_path, b_path, postings_path, expected_posting_count=20)
    assert not ok
    assert results["expected posting count"]


def test_validate_packet_pair_real_gitignored_output_passes_in_private_dir_mode(real_private_subdir):
    postings_path = real_private_subdir / "public.jsonl"
    write_jsonl(postings_path, [{"posting_id": "JB-001", "region_group": "jeonbuk", "occupation": "x", "employment_type": "정규직", "full_text": None, "matched_pair_id": "P1", "unmatched": False}])
    private_dir = real_private_subdir / "private_raw"
    _write_private_json(private_dir, "JB-001", "월급 250만원 지급.")
    a_path = real_private_subdir / "annotator_A" / "packet.jsonl"
    b_path = real_private_subdir / "annotator_B" / "packet.jsonl"
    write_jsonl(a_path, full_packet("A"))
    write_jsonl(b_path, full_packet("B"))

    ok, results = validate_packet_pair(a_path, b_path, postings_path, private_dir=private_dir, allow_incomplete=True)
    assert results["annotator_A output path gitignored"] == []
    assert results["annotator_B output path gitignored"] == []
