"""Tests for scripts/annotation_ops/private_source.py.

Every posting here is entirely self-authored synthetic fixture text --
never the repository's real private_dir content -- per the task rule that
real private originals must never be used as a test fixture.
"""
from __future__ import annotations

import json

from private_source import (
    PrivateSourceError,
    assert_output_under_gitignore,
    check_expected_posting_count,
    check_no_pii_in_evidence,
    check_path_is_gitignored,
    join_public_and_private,
)

import pytest


def write_jsonl(path, records):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def write_private(private_dir, posting_id, full_text, **overrides):
    private_dir.mkdir(parents=True, exist_ok=True)
    record = {
        "posting_id": posting_id,
        "region_group": "jeonbuk",
        "municipality": "가상시",
        "occupation": "생산직(제조 조립원)",
        "employment_type": "정규직",
        "collection_date": "2026-01-01",
        "source_name": "synthetic_test_source",
        "source_id_url": "https://example.invalid/x",
        "company_name": "(테스트) 가상회사",
        "redistribution_permission": "unknown",
        "full_text": full_text,
        "full_text_sha256": "deadbeef",
        "pii_redaction_count": 0,
    }
    record.update(overrides)
    (private_dir / f"{posting_id}.json").write_text(json.dumps(record, ensure_ascii=False), encoding="utf-8")


def public_row(posting_id, **overrides):
    row = {
        "posting_id": posting_id,
        "region_group": "jeonbuk",
        "occupation": "생산직(제조 조립원)",
        "employment_type": "정규직",
        "collection_date": "2026-01-01",
        "source_name": "synthetic_test_source",
        "source_id_url": "https://example.invalid/x",
        "company_name": "(테스트) 가상회사",
        "full_text": None,
        "redistributable": False,
        "synthetic_test_fixture": False,
    }
    row.update(overrides)
    return row


def test_join_succeeds_for_exact_1_to_1_match(tmp_path):
    public_path = tmp_path / "public.jsonl"
    private_dir = tmp_path / "private_raw"
    write_jsonl(public_path, [public_row("TEST-01"), public_row("TEST-02")])
    write_private(private_dir, "TEST-01", "테스트 공고 본문 1")
    write_private(private_dir, "TEST-02", "테스트 공고 본문 2")

    joined = join_public_and_private(public_path, private_dir, strict=True)

    assert len(joined) == 2
    by_id = {r["posting_id"]: r for r in joined}
    assert by_id["TEST-01"]["full_text"] == "테스트 공고 본문 1"
    assert by_id["TEST-02"]["full_text"] == "테스트 공고 본문 2"


def test_join_fails_explicitly_when_private_text_missing(tmp_path):
    public_path = tmp_path / "public.jsonl"
    private_dir = tmp_path / "private_raw"
    write_jsonl(public_path, [public_row("TEST-01"), public_row("TEST-02")])
    write_private(private_dir, "TEST-01", "테스트 공고 본문 1")
    # TEST-02 has no private file at all.

    with pytest.raises(PrivateSourceError) as exc_info:
        join_public_and_private(public_path, private_dir, strict=True)
    assert "TEST-02" in str(exc_info.value)


def test_join_fails_on_duplicate_private_posting_id(tmp_path):
    public_path = tmp_path / "public.jsonl"
    private_dir = tmp_path / "private_raw"
    write_jsonl(public_path, [public_row("TEST-01")])
    private_dir.mkdir(parents=True)
    # Two different files both internally claiming the same posting_id.
    (private_dir / "a.json").write_text(
        json.dumps({"posting_id": "TEST-01", "full_text": "본문 A"}, ensure_ascii=False), encoding="utf-8"
    )
    (private_dir / "b.json").write_text(
        json.dumps({"posting_id": "TEST-01", "full_text": "본문 B"}, ensure_ascii=False), encoding="utf-8"
    )

    with pytest.raises(PrivateSourceError) as exc_info:
        join_public_and_private(public_path, private_dir, strict=True)
    assert "duplicate" in str(exc_info.value).lower()


def test_join_fails_on_duplicate_public_posting_id(tmp_path):
    public_path = tmp_path / "public.jsonl"
    private_dir = tmp_path / "private_raw"
    write_jsonl(public_path, [public_row("TEST-01"), public_row("TEST-01")])
    write_private(private_dir, "TEST-01", "테스트 공고 본문")

    with pytest.raises(PrivateSourceError) as exc_info:
        join_public_and_private(public_path, private_dir, strict=True)
    assert "duplicate" in str(exc_info.value).lower()


def test_orphan_private_file_fails_strict_but_warns_non_strict(tmp_path, capsys):
    public_path = tmp_path / "public.jsonl"
    private_dir = tmp_path / "private_raw"
    write_jsonl(public_path, [public_row("TEST-01")])
    write_private(private_dir, "TEST-01", "테스트 공고 본문")
    write_private(private_dir, "TEST-99", "고아 레코드 본문")  # no matching public row

    with pytest.raises(PrivateSourceError):
        join_public_and_private(public_path, private_dir, strict=True)

    joined = join_public_and_private(public_path, private_dir, strict=False)
    assert len(joined) == 1
    assert joined[0]["posting_id"] == "TEST-01"
    assert "TEST-99" in capsys.readouterr().err


def test_check_expected_posting_count():
    postings = [public_row("A"), public_row("B")]
    assert check_expected_posting_count(postings, expected=2) == []
    errors = check_expected_posting_count(postings, expected=20)
    assert len(errors) == 1
    assert "20" in errors[0]


def test_check_no_pii_in_evidence_flags_phone_and_email():
    clean = [{"posting_id": "A", "field": "duties", "evidence_text": "월급 250만원 지급합니다."}]
    assert check_no_pii_in_evidence(clean) == []

    with_phone = [{"posting_id": "A", "field": "duties", "evidence_text": "문의: 010-1234-5678"}]
    assert len(check_no_pii_in_evidence(with_phone)) == 1

    with_email = [{"posting_id": "A", "field": "duties", "evidence_text": "문의: hr@example.com"}]
    assert len(check_no_pii_in_evidence(with_email)) == 1


def test_check_no_pii_in_evidence_ignores_null_evidence():
    absent = [{"posting_id": "A", "field": "duties", "evidence_text": None}]
    assert check_no_pii_in_evidence(absent) == []


def test_gitignored_path_under_data_private_passes():
    # Uses the real repo's .gitignore (data/private/ is ignored there),
    # but touches no actual file -- git check-ignore is a pure path match.
    assert check_path_is_gitignored("data/private/some_test_subdir/x.jsonl") == []


def test_non_gitignored_path_fails():
    errors = check_path_is_gitignored("backend/some_test_subdir/x.jsonl")
    assert len(errors) == 1
    assert "NOT covered by .gitignore" in errors[0]


def test_assert_output_under_gitignore_raises_for_tracked_path():
    with pytest.raises(PrivateSourceError):
        assert_output_under_gitignore("backend/some_test_subdir")


def test_assert_output_under_gitignore_passes_for_private_path():
    assert_output_under_gitignore("data/private/some_test_subdir") is None
