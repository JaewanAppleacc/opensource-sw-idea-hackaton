from evaluate_predictions import (
    check_evidence_grounded,
    check_prediction_schema,
    confusion_matrix,
    macro_prf1,
)

POSTINGS_BY_ID = {
    "JB-001": {"posting_id": "JB-001", "full_text": "월급 250만원(세전) 지급합니다."},
}


def test_schema_valid_confirmed_prediction_passes():
    pred = {"posting_id": "JB-001", "field": "salary", "status": "confirmed", "evidence_text": "월급 250만원(세전) 지급합니다.", "offsets": [0, 15]}
    assert check_prediction_schema(pred, POSTINGS_BY_ID) is None


def test_schema_rejects_unknown_status():
    pred = {"posting_id": "JB-001", "field": "salary", "status": "maybe", "evidence_text": "x", "offsets": [0, 1]}
    err = check_prediction_schema(pred, POSTINGS_BY_ID)
    assert err is not None and "not in" in err


def test_schema_rejects_confirmed_without_evidence():
    pred = {"posting_id": "JB-001", "field": "salary", "status": "confirmed", "evidence_text": None, "offsets": None}
    err = check_prediction_schema(pred, POSTINGS_BY_ID)
    assert err is not None


def test_schema_rejects_unknown_posting():
    pred = {"posting_id": "NOPE", "field": "salary", "status": "absent"}
    err = check_prediction_schema(pred, POSTINGS_BY_ID)
    assert err is not None and "unknown posting_id" in err


def test_evidence_grounded_true_for_exact_substring():
    text = "월급 250만원(세전) 지급합니다."
    pred = {"posting_id": "JB-001", "status": "confirmed", "evidence_text": text, "offsets": [0, len(text)]}
    assert check_evidence_grounded(pred, POSTINGS_BY_ID) is True


def test_evidence_grounded_false_for_fabricated_text():
    pred = {"posting_id": "JB-001", "status": "confirmed", "evidence_text": "완전히 다른 문장", "offsets": [0, 8]}
    assert check_evidence_grounded(pred, POSTINGS_BY_ID) is False


def test_evidence_grounded_true_for_absent():
    pred = {"posting_id": "JB-001", "status": "absent", "evidence_text": None, "offsets": None}
    assert check_evidence_grounded(pred, POSTINGS_BY_ID) is True


def test_confusion_matrix_counts_pairs():
    pairs = [("confirmed", "confirmed"), ("confirmed", "vague"), ("absent", "absent")]
    matrix = confusion_matrix(pairs)
    assert matrix["confirmed"]["confirmed"] == 1
    assert matrix["confirmed"]["vague"] == 1
    assert matrix["absent"]["absent"] == 1
    assert matrix["vague"]["vague"] == 0


def test_macro_prf1_perfect_predictions():
    pairs = [("confirmed", "confirmed"), ("vague", "vague"), ("absent", "absent")]
    result = macro_prf1(pairs)
    for label in ("confirmed", "vague", "absent"):
        assert result[label]["precision"] == 1.0
        assert result[label]["recall"] == 1.0
        assert result[label]["f1"] == 1.0


def test_macro_prf1_reports_support_from_gold():
    pairs = [("confirmed", "vague"), ("confirmed", "confirmed")]
    result = macro_prf1(pairs)
    assert result["confirmed"]["support"] == 2
    assert result["vague"]["support"] == 0
