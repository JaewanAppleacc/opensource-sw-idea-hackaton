from adjudicate import build_adjudication_rows, cohens_kappa, percent_agreement


def cell(posting_id, field, status, evidence_text=None, offsets=None):
    return {
        "posting_id": posting_id,
        "field": field,
        "status": status,
        "evidence_text": evidence_text,
        "offsets": offsets,
        "reason_code": "x",
        "rubric_version": "1.0.0-draft",
        "synthetic_test_fixture": False,
    }


def test_full_agreement_all_cells_agree():
    a = [cell("JB-001", "salary", "confirmed", "월급 250만원", [0, 6])]
    b = [cell("JB-001", "salary", "confirmed", "월급 250만원", [0, 6])]
    rows = build_adjudication_rows(a, b)
    assert rows[0]["agreement"] is True
    assert percent_agreement(rows) == 1.0


def test_same_status_different_evidence_is_disagreement():
    a = [cell("JB-001", "salary", "confirmed", "월급 250만원", [0, 6])]
    b = [cell("JB-001", "salary", "confirmed", "다른 텍스트", [10, 15])]
    rows = build_adjudication_rows(a, b)
    assert rows[0]["agreement"] is False


def test_absent_ignores_evidence_field_for_agreement():
    a = [cell("JB-001", "salary", "absent")]
    b = [cell("JB-001", "salary", "absent")]
    rows = build_adjudication_rows(a, b)
    assert rows[0]["agreement"] is True


def test_status_mismatch_is_disagreement():
    a = [cell("JB-001", "salary", "confirmed", "월급 250만원", [0, 6])]
    b = [cell("JB-001", "salary", "vague", "협의 후 결정", [0, 6])]
    rows = build_adjudication_rows(a, b)
    assert rows[0]["agreement"] is False


def test_adjudication_preserves_explicit_non_synthetic_provenance():
    a = [cell("JB-001", "salary", "absent")]
    b = [cell("JB-001", "salary", "absent")]
    rows = build_adjudication_rows(a, b)
    assert rows[0]["synthetic_test_fixture"] is False


def test_percent_agreement_across_multiple_cells():
    a = [
        cell("JB-001", "salary", "confirmed", "x", [0, 1]),
        cell("JB-001", "duties", "absent"),
        cell("JB-001", "employment_type", "vague", "y", [0, 1]),
    ]
    b = [
        cell("JB-001", "salary", "confirmed", "x", [0, 1]),
        cell("JB-001", "duties", "absent"),
        cell("JB-001", "employment_type", "absent"),
    ]
    rows = build_adjudication_rows(a, b)
    assert percent_agreement(rows) == 2 / 3


def test_kappa_is_none_when_only_one_label_observed():
    a = [cell("JB-001", "salary", "absent"), cell("JB-002", "salary", "absent")]
    b = [cell("JB-001", "salary", "absent"), cell("JB-002", "salary", "absent")]
    rows = build_adjudication_rows(a, b)
    assert cohens_kappa(rows) is None


def test_kappa_is_1_for_perfect_agreement_with_varied_labels():
    a = [
        cell("JB-001", "salary", "confirmed", "x", [0, 1]),
        cell("JB-002", "salary", "vague", "y", [0, 1]),
        cell("JB-003", "salary", "absent"),
        cell("JB-004", "salary", "confirmed", "x", [0, 1]),
    ]
    b = [
        cell("JB-001", "salary", "confirmed", "x", [0, 1]),
        cell("JB-002", "salary", "vague", "y", [0, 1]),
        cell("JB-003", "salary", "absent"),
        cell("JB-004", "salary", "confirmed", "x", [0, 1]),
    ]
    rows = build_adjudication_rows(a, b)
    kappa = cohens_kappa(rows)
    assert kappa == 1.0
