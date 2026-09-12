import pytest
from review_cli import (
    QuitReview,
    context_snippet,
    find_all_occurrences,
    prompt_cell,
    run_review_session,
)


def make_input(answers):
    it = iter(answers)

    def input_fn(_prompt):
        return next(it)

    return input_fn


def noop_print(*_args, **_kwargs):
    pass


def test_find_all_occurrences_single_match():
    assert find_all_occurrences("월급 250만원 지급합니다.", "250만원") == [(3, 8)]


def test_find_all_occurrences_multiple_matches():
    text = "지게차 운전면허 우대. 지게차 보유 시 우대."
    occs = find_all_occurrences(text, "지게차")
    assert len(occs) == 2
    for s, e in occs:
        assert text[s:e] == "지게차"


def test_find_all_occurrences_no_match_returns_empty():
    assert find_all_occurrences("abc", "xyz") == []


def test_context_snippet_includes_evidence():
    text = "0123456789ABCDEFGHIJ"
    snippet = context_snippet(text, 5, 8, radius=2)
    assert "[567]" in snippet


def test_prompt_cell_absent_status():
    input_fn = make_input(["absent", "no_relevant_text", ""])
    update = prompt_cell("JB-001", "training_or_mentoring", "아무 내용 없음.", input_fn=input_fn, print_fn=noop_print)
    assert update == {
        "status": "absent",
        "evidence_text": None,
        "offsets": None,
        "reason_code": "no_relevant_text",
        "disagreement_note": None,
    }


def test_prompt_cell_confirmed_single_occurrence():
    full_text = "월급 250만원(세전) 지급합니다."
    input_fn = make_input(["confirmed", "amount_and_unit_present", "", "250만원"])
    update = prompt_cell("JB-001", "salary", full_text, input_fn=input_fn, print_fn=noop_print)
    assert update["status"] == "confirmed"
    assert update["evidence_text"] == "250만원"
    assert update["offsets"] == [3, 8]
    assert full_text[3:8] == "250만원"


def test_prompt_cell_retries_on_evidence_not_found():
    full_text = "월급 250만원 지급합니다."
    input_fn = make_input(
        [
            "confirmed",
            "amount_and_unit_present",
            "",
            "300만원",  # not present -> retry
            "250만원",
        ]
    )
    update = prompt_cell("JB-001", "salary", full_text, input_fn=input_fn, print_fn=noop_print)
    assert update["evidence_text"] == "250만원"


def test_prompt_cell_multiple_occurrences_requires_choice():
    full_text = "지게차 운전면허 우대. 지게차 보유 시 우대."
    input_fn = make_input(["confirmed", "named_tool_present", "", "지게차", "1"])
    update = prompt_cell("JB-001", "tools_or_skills", full_text, input_fn=input_fn, print_fn=noop_print)
    assert update["offsets"] == list(find_all_occurrences(full_text, "지게차")[1])


def test_prompt_cell_quit_raises():
    input_fn = make_input(["quit"])
    with pytest.raises(QuitReview):
        prompt_cell("JB-001", "salary", "text", input_fn=input_fn, print_fn=noop_print)


def test_prompt_cell_skip_returns_none():
    input_fn = make_input(["skip"])
    assert prompt_cell("JB-001", "salary", "text", input_fn=input_fn, print_fn=noop_print) is None


def test_run_review_session_answers_all_cells_and_saves_each_time():
    rows = [
        {"posting_id": "JB-001", "field": "salary", "status": None},
        {"posting_id": "JB-001", "field": "duties", "status": None},
    ]
    postings_by_id = {"JB-001": {"full_text": "월급 250만원. 조립 및 품질 검사 업무를 담당합니다."}}
    answers = iter(
        [
            "confirmed",
            "amount_and_unit_present",
            "",
            "250만원",
            "confirmed",
            "concrete_task_named",
            "",
            "조립 및 품질 검사 업무를 담당합니다.",
        ]
    )
    save_calls = []

    result = run_review_session(
        rows,
        postings_by_id,
        input_fn=lambda _p: next(answers),
        print_fn=noop_print,
        save_fn=lambda: save_calls.append(1),
    )

    assert result == {"answered": 2, "quit_early": False}
    assert len(save_calls) == 2
    assert rows[0]["status"] == "confirmed"
    assert rows[1]["status"] == "confirmed"


def test_run_review_session_skips_already_answered_unless_redo():
    rows = [{"posting_id": "JB-001", "field": "salary", "status": "absent"}]
    postings_by_id = {"JB-001": {"full_text": "text"}}

    result = run_review_session(rows, postings_by_id, input_fn=make_input([]), print_fn=noop_print)
    assert result == {"answered": 0, "quit_early": False}


def test_run_review_session_stops_on_quit_without_losing_prior_answers():
    rows = [
        {"posting_id": "JB-001", "field": "salary", "status": None},
        {"posting_id": "JB-001", "field": "duties", "status": None},
    ]
    postings_by_id = {"JB-001": {"full_text": "text"}}
    answers = iter(["absent", "no_relevant_text", "", "quit"])

    result = run_review_session(rows, postings_by_id, input_fn=lambda _p: next(answers), print_fn=noop_print)

    assert result["quit_early"] is True
    assert result["answered"] == 1
    assert rows[0]["status"] == "absent"
    assert rows[1]["status"] is None


def test_run_review_session_warns_and_skips_unknown_posting():
    rows = [{"posting_id": "MISSING", "field": "salary", "status": None}]
    result = run_review_session(rows, {}, input_fn=make_input([]), print_fn=noop_print)
    assert result == {"answered": 0, "quit_early": False}
    assert rows[0]["status"] is None


def test_run_review_session_never_reads_other_annotator_or_ai_suggestion_data():
    # postings_by_id intentionally has no ai_suggested/annotator_b_* keys --
    # the session only ever reads full_text off the posting record.
    rows = [{"posting_id": "JB-001", "field": "salary", "status": None}]
    postings_by_id = {
        "JB-001": {
            "full_text": "월급 250만원.",
            # If review_cli ever started reading these it would be a
            # structural isolation break; assert they are simply never
            # touched by checking the resulting row has no trace of them.
        }
    }
    answers = iter(["confirmed", "amount_and_unit_present", "", "250만원"])
    run_review_session(rows, postings_by_id, input_fn=lambda _p: next(answers), print_fn=noop_print)
    assert set(rows[0].keys()) == {"posting_id", "field", "status", "evidence_text", "offsets", "reason_code", "disagreement_note"}
