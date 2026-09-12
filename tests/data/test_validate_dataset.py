from validate_dataset import (
    validate_annotation_file,
    validate_matched_pairs,
    validate_postings,
)


def make_posting(**overrides):
    base = {
        "posting_id": "JB-001",
        "region_group": "jeonbuk",
        "municipality": "전주시",
        "occupation": "생산직(제조 조립원)",
        "employment_type": "정규직",
        "full_text": "월급 250만원(세전) 지급합니다.",
        "matched_pair_id": "P01",
        "unmatched": False,
        "unmatched_reason": None,
    }
    base.update(overrides)
    return base


def test_valid_postings_pass():
    postings = [
        make_posting(),
        make_posting(posting_id="MET-001", region_group="metro", municipality="서울특별시"),
    ]
    result = validate_postings(postings)
    assert result.ok, result.errors


def test_duplicate_posting_id_is_error():
    postings = [make_posting(), make_posting()]
    result = validate_postings(postings)
    assert not result.ok
    assert any("duplicate posting_id" in e for e in result.errors)


def test_invalid_region_group_is_error():
    postings = [make_posting(region_group="honam")]
    result = validate_postings(postings)
    assert not result.ok


def test_unmatched_requires_null_pair_and_reason():
    postings = [make_posting(unmatched=True, matched_pair_id=None, unmatched_reason=None)]
    result = validate_postings(postings)
    assert not result.ok
    assert any("unmatched_reason" in e for e in result.errors)

    postings_ok = [
        make_posting(unmatched=True, matched_pair_id=None, unmatched_reason="no candidate found under recorded query")
    ]
    result_ok = validate_postings(postings_ok)
    assert result_ok.ok, result_ok.errors


def test_matched_pairs_require_same_occupation_and_employment_type():
    jb = make_posting()
    met = make_posting(posting_id="MET-001", region_group="metro", employment_type="계약직")
    postings_by_id = {jb["posting_id"]: jb, met["posting_id"]: met}
    pairs = [{"matched_pair_id": "P01", "jeonbuk_posting_id": "JB-001", "metro_posting_id": "MET-001"}]

    result = validate_matched_pairs(pairs, postings_by_id)
    assert not result.ok
    assert any("employment_type mismatch" in e for e in result.errors)


def test_matched_pairs_valid_pass():
    jb = make_posting()
    met = make_posting(posting_id="MET-001", region_group="metro")
    postings_by_id = {jb["posting_id"]: jb, met["posting_id"]: met}
    pairs = [{"matched_pair_id": "P01", "jeonbuk_posting_id": "JB-001", "metro_posting_id": "MET-001"}]

    result = validate_matched_pairs(pairs, postings_by_id)
    assert result.ok, result.errors


ALL_FIELDS = [
    "salary",
    "duties",
    "tools_or_skills",
    "training_or_mentoring",
    "probation_terms",
    "employment_type",
]


def full_annotation_for(posting_id: str, overrides_by_field=None):
    overrides_by_field = overrides_by_field or {}
    rows = []
    for field in ALL_FIELDS:
        row = {
            "posting_id": posting_id,
            "field": field,
            "status": "absent",
            "evidence_text": None,
            "offsets": None,
            "reason_code": "no_relevant_text",
            "rubric_version": "1.0.0-draft",
        }
        row.update(overrides_by_field.get(field, {}))
        rows.append(row)
    return rows


def test_annotation_confirmed_requires_matching_substring():
    posting = make_posting(full_text="월급 250만원(세전) 지급합니다.")
    postings_by_id = {posting["posting_id"]: posting}
    rows = full_annotation_for(
        "JB-001",
        {
            "salary": {
                "status": "confirmed",
                "evidence_text": "월급 250만원(세전) 지급합니다.",
                "offsets": [0, len("월급 250만원(세전) 지급합니다.")],
                "reason_code": "amount_and_unit_present",
            }
        },
    )
    result = validate_annotation_file(rows, postings_by_id)
    assert result.ok, result.errors


def test_annotation_mismatched_offsets_is_error():
    posting = make_posting(full_text="월급 250만원(세전) 지급합니다.")
    postings_by_id = {posting["posting_id"]: posting}
    rows = full_annotation_for(
        "JB-001",
        {
            "salary": {
                "status": "confirmed",
                "evidence_text": "월급 250만원(세전) 지급합니다.",
                "offsets": [1, 5],  # deliberately wrong
                "reason_code": "amount_and_unit_present",
            }
        },
    )
    result = validate_annotation_file(rows, postings_by_id)
    assert not result.ok
    assert any("does not match full_text" in e for e in result.errors)


def test_annotation_absent_with_evidence_is_error():
    posting = make_posting()
    postings_by_id = {posting["posting_id"]: posting}
    rows = full_annotation_for(
        "JB-001",
        {"salary": {"status": "absent", "evidence_text": "월급 250만원", "offsets": [0, 5]}},
    )
    result = validate_annotation_file(rows, postings_by_id)
    assert not result.ok
    assert any("requires evidence_text and offsets to be null" in e for e in result.errors)


def test_annotation_missing_field_is_error():
    posting = make_posting()
    postings_by_id = {posting["posting_id"]: posting}
    rows = full_annotation_for("JB-001")[:-1]  # drop employment_type
    result = validate_annotation_file(rows, postings_by_id)
    assert not result.ok
    assert any("missing annotation cells" in e for e in result.errors)


def test_annotation_incomplete_is_warning_not_error_when_allowed():
    posting = make_posting()
    postings_by_id = {posting["posting_id"]: posting}
    rows = full_annotation_for("JB-001")
    for row in rows:
        row["status"] = None
        row["reason_code"] = None
    result = validate_annotation_file(rows, postings_by_id, allow_incomplete=True)
    assert result.ok
    assert len(result.warnings) == len(ALL_FIELDS)


def test_annotation_invalid_status_is_error():
    posting = make_posting()
    postings_by_id = {posting["posting_id"]: posting}
    rows = full_annotation_for("JB-001", {"salary": {"status": "external_verified"}})
    result = validate_annotation_file(rows, postings_by_id)
    assert not result.ok
    assert any("not one of" in e for e in result.errors)
