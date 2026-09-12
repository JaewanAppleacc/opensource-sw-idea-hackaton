import json

from conftest import FIXTURES_DIR
from manual_intake import run
from acquisition_utils import read_jsonl

SAMPLE_FILE = FIXTURES_DIR / "sample_manual_intake.txt"


def _run(tmp_path, input_paths, dry_run=False):
    out = tmp_path / "real_postings.jsonl"
    excluded_out = tmp_path / "excluded_postings.jsonl"
    private_dir = tmp_path / "intake_raw"
    code = run(input_paths, out, excluded_out, private_dir, dry_run)
    return code, out, excluded_out, private_dir


def test_valid_fixture_parses_and_writes_expected_counts(tmp_path):
    code, out, excluded_out, private_dir = _run(tmp_path, [SAMPLE_FILE])
    assert code == 0

    public_records = read_jsonl(out)
    assert len(public_records) == 2
    assert {r["posting_id"] for r in public_records} == {"JB-TEST-01", "MET-TEST-01"}

    excluded_records = read_jsonl(excluded_out)
    assert len(excluded_records) == 1
    assert excluded_records[0]["excluded_reason"] == "중복 공고 (JB-TEST-01과 동일 채용ID)"

    assert (private_dir / "JB-TEST-01.json").exists()
    assert (private_dir / "MET-TEST-01.json").exists()


def test_dry_run_writes_nothing(tmp_path):
    code, out, excluded_out, private_dir = _run(tmp_path, [SAMPLE_FILE], dry_run=True)
    assert code == 0
    assert not out.exists()
    assert not excluded_out.exists()
    assert not private_dir.exists()


def test_redistribution_permission_gates_public_full_text(tmp_path):
    _, out, _, private_dir = _run(tmp_path, [SAMPLE_FILE])
    public_by_id = {r["posting_id"]: r for r in read_jsonl(out)}

    # redistribution_permission: unknown -> public full_text must be null
    assert public_by_id["JB-TEST-01"]["redistributable"] is False
    assert public_by_id["JB-TEST-01"]["full_text"] is None
    assert public_by_id["JB-TEST-01"]["full_text_sha256"]

    # redistribution_permission: yes -> public full_text is present
    assert public_by_id["MET-TEST-01"]["redistributable"] is True
    assert public_by_id["MET-TEST-01"]["full_text"]

    # Private copy always has the full text, regardless of permission.
    private_jb = json.loads((private_dir / "JB-TEST-01.json").read_text(encoding="utf-8"))
    assert "부품 조립" in private_jb["full_text"]


def test_pii_is_redacted_from_full_text(tmp_path):
    _, _, _, private_dir = _run(tmp_path, [SAMPLE_FILE])
    private_jb = json.loads((private_dir / "JB-TEST-01.json").read_text(encoding="utf-8"))
    assert "010-1234-5678" not in private_jb["full_text"]
    assert "hr@example.invalid" not in private_jb["full_text"]
    assert private_jb["pii_redaction_count"] >= 2


def test_duplicate_posting_id_is_rejected_and_writes_nothing(tmp_path):
    dup_file = tmp_path / "dup.txt"
    dup_file.write_text(
        "\n".join(
            [
                "===== A =====",
                "posting_id: JB-DUP-01",
                "region_group: jeonbuk",
                "municipality: 전주시",
                "source_name: 고용24",
                "source_url: https://example.invalid/a",
                "collection_date: 2026-09-12",
                "occupation: 생산직(제조 조립원)",
                "employment_type: 정규직",
                "company_name: 회사A",
                "redistribution_permission: unknown",
                "--- FULL TEXT ---",
                "본문 A",
                "",
                "===== B =====",
                "posting_id: JB-DUP-01",
                "region_group: jeonbuk",
                "municipality: 전주시",
                "source_name: 고용24",
                "source_url: https://example.invalid/b",
                "collection_date: 2026-09-12",
                "occupation: 생산직(제조 조립원)",
                "employment_type: 정규직",
                "company_name: 회사B",
                "redistribution_permission: unknown",
                "--- FULL TEXT ---",
                "본문 B",
            ]
        ),
        encoding="utf-8",
    )
    code, out, _, private_dir = _run(tmp_path, [dup_file])
    assert code == 1
    assert not out.exists()
    assert not private_dir.exists()


def test_empty_full_text_is_rejected(tmp_path):
    bad_file = tmp_path / "empty.txt"
    bad_file.write_text(
        "\n".join(
            [
                "posting_id: JB-EMPTY-01",
                "region_group: jeonbuk",
                "municipality: 전주시",
                "source_name: 고용24",
                "source_url: https://example.invalid/empty",
                "collection_date: 2026-09-12",
                "occupation: 생산직(제조 조립원)",
                "employment_type: 정규직",
                "company_name: 회사",
                "redistribution_permission: unknown",
                "--- FULL TEXT ---",
                "",
            ]
        ),
        encoding="utf-8",
    )
    code, out, _, _ = _run(tmp_path, [bad_file])
    assert code == 1
    assert not out.exists()


def test_invalid_region_group_is_rejected(tmp_path):
    bad_file = tmp_path / "badregion.txt"
    bad_file.write_text(
        "\n".join(
            [
                "posting_id: JB-BADREGION-01",
                "region_group: honam",
                "municipality: 전주시",
                "source_name: 고용24",
                "source_url: https://example.invalid/badregion",
                "collection_date: 2026-09-12",
                "occupation: 생산직(제조 조립원)",
                "employment_type: 정규직",
                "company_name: 회사",
                "redistribution_permission: unknown",
                "--- FULL TEXT ---",
                "본문",
            ]
        ),
        encoding="utf-8",
    )
    code, out, _, _ = _run(tmp_path, [bad_file])
    assert code == 1
    assert not out.exists()


def test_missing_required_field_is_rejected(tmp_path):
    bad_file = tmp_path / "missingfield.txt"
    bad_file.write_text(
        "\n".join(
            [
                "posting_id: JB-MISSING-01",
                "region_group: jeonbuk",
                # municipality intentionally omitted
                "source_name: 고용24",
                "source_url: https://example.invalid/missing",
                "collection_date: 2026-09-12",
                "occupation: 생산직(제조 조립원)",
                "employment_type: 정규직",
                "company_name: 회사",
                "redistribution_permission: unknown",
                "--- FULL TEXT ---",
                "본문",
            ]
        ),
        encoding="utf-8",
    )
    code, out, _, _ = _run(tmp_path, [bad_file])
    assert code == 1
    assert not out.exists()


def test_bad_date_format_is_rejected(tmp_path):
    bad_file = tmp_path / "baddate.txt"
    bad_file.write_text(
        "\n".join(
            [
                "posting_id: JB-BADDATE-01",
                "region_group: jeonbuk",
                "municipality: 전주시",
                "source_name: 고용24",
                "source_url: https://example.invalid/baddate",
                "collection_date: 2026/09/12",
                "occupation: 생산직(제조 조립원)",
                "employment_type: 정규직",
                "company_name: 회사",
                "redistribution_permission: unknown",
                "--- FULL TEXT ---",
                "본문",
            ]
        ),
        encoding="utf-8",
    )
    code, out, _, _ = _run(tmp_path, [bad_file])
    assert code == 1
    assert not out.exists()


def test_rerunning_against_existing_output_rejects_cross_batch_duplicate(tmp_path):
    code, out, _, _ = _run(tmp_path, [SAMPLE_FILE])
    assert code == 0

    # Re-running the same file against the same --out must fail (already ingested).
    code2 = run([SAMPLE_FILE], out, tmp_path / "excluded_postings.jsonl", tmp_path / "intake_raw", False)
    assert code2 == 1
