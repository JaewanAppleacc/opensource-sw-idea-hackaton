import json

import pytest
from build_packets import build_packet_rows, build_packets, is_synthetic
from common import FIELDS, read_jsonl
from private_source import PrivateSourceError


def write_jsonl_file(path, records):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def make_posting(**overrides):
    base = {
        "posting_id": "JB-901",
        "region_group": "jeonbuk",
        "occupation": "생산직(제조 조립원)",
        "employment_type": "정규직",
        "full_text": "월급 250만원(세전) 지급합니다.",
        "source_name": "worknet_open_api",
    }
    base.update(overrides)
    return base


RUBRIC_YAML = """
rubric_version: "1.0.0-draft"
allowed_statuses: [confirmed, vague, absent]
fields: {}
"""


def test_is_synthetic_true_for_synthetic_fixture_source_name():
    assert is_synthetic({"source_name": "synthetic_fixture_v1"}) is True


def test_is_synthetic_true_for_explicit_flag():
    assert is_synthetic({"synthetic_test_fixture": True}) is True


def test_is_synthetic_false_for_real_source_by_default():
    assert is_synthetic({"source_name": "worknet_open_api"}) is False
    assert is_synthetic({}) is False


def test_build_packet_rows_shape_matches_schema():
    postings = [make_posting()]
    rows = build_packet_rows(postings, "A", "1.0.0-draft")
    assert len(rows) == len(FIELDS)
    row = rows[0]
    assert set(row.keys()) == {
        "posting_id",
        "field",
        "annotator_id",
        "status",
        "evidence_text",
        "offsets",
        "reason_code",
        "disagreement_note",
        "rubric_version",
        "synthetic_test_fixture",
    }
    assert row["annotator_id"] == "A"
    assert row["status"] is None
    assert row["synthetic_test_fixture"] is False


def test_build_packets_writes_two_isolated_packets_and_manifest(tmp_path):
    postings_path = tmp_path / "real_postings.jsonl"
    write_jsonl_file(postings_path, [make_posting(posting_id="JB-901"), make_posting(posting_id="MET-901", region_group="metro")])

    rubric_path = tmp_path / "rubric.yaml"
    rubric_path.write_text(RUBRIC_YAML, encoding="utf-8")

    out_dir = tmp_path / "run_001"
    manifest = build_packets(postings_path, rubric_path, out_dir)

    a_rows = read_jsonl(out_dir / "annotator_A" / "packet.jsonl")
    b_rows = read_jsonl(out_dir / "annotator_B" / "packet.jsonl")

    assert len(a_rows) == 2 * len(FIELDS)
    assert len(b_rows) == 2 * len(FIELDS)
    assert all(r["annotator_id"] == "A" for r in a_rows)
    assert all(r["annotator_id"] == "B" for r in b_rows)
    assert all(r["status"] is None for r in a_rows + b_rows)
    # Same posting/field order for both annotators.
    assert [(r["posting_id"], r["field"]) for r in a_rows] == [(r["posting_id"], r["field"]) for r in b_rows]
    # No AI suggestion content anywhere in a blank packet.
    assert all("ai_suggested" not in r and "suggested_status" not in r for r in a_rows)

    assert manifest["posting_count"] == 2
    assert manifest["cell_count_per_annotator"] == 2 * len(FIELDS)
    assert manifest["rubric_version"] == "1.0.0-draft"
    assert manifest["input_postings_sha256"]
    assert manifest["generated_at"].endswith("Z")

    manifest_on_disk = json.loads((out_dir / "manifest.json").read_text(encoding="utf-8"))
    assert manifest_on_disk["posting_count"] == 2


def test_build_packets_rejects_posting_missing_full_text(tmp_path):
    postings_path = tmp_path / "bad_postings.jsonl"
    write_jsonl_file(postings_path, [make_posting(full_text=None)])
    rubric_path = tmp_path / "rubric.yaml"
    rubric_path.write_text(RUBRIC_YAML, encoding="utf-8")

    with pytest.raises(ValueError, match="full_text"):
        build_packets(postings_path, rubric_path, tmp_path / "out")


def test_build_packets_rejects_duplicate_posting_id(tmp_path):
    postings_path = tmp_path / "dup_postings.jsonl"
    write_jsonl_file(postings_path, [make_posting(), make_posting()])
    rubric_path = tmp_path / "rubric.yaml"
    rubric_path.write_text(RUBRIC_YAML, encoding="utf-8")

    with pytest.raises(ValueError, match="duplicate posting_id"):
        build_packets(postings_path, rubric_path, tmp_path / "out")


def test_build_packets_rejects_rubric_missing_version(tmp_path):
    postings_path = tmp_path / "postings.jsonl"
    write_jsonl_file(postings_path, [make_posting()])
    rubric_path = tmp_path / "rubric.yaml"
    rubric_path.write_text("allowed_statuses: [confirmed, vague, absent]\n", encoding="utf-8")

    with pytest.raises(ValueError, match="rubric_version"):
        build_packets(postings_path, rubric_path, tmp_path / "out")


def _write_private_json(private_dir, posting_id, full_text):
    private_dir.mkdir(parents=True, exist_ok=True)
    (private_dir / f"{posting_id}.json").write_text(
        json.dumps({"posting_id": posting_id, "full_text": full_text}, ensure_ascii=False), encoding="utf-8"
    )


def test_build_packets_with_private_dir_joins_full_text(real_private_subdir):
    postings_path = real_private_subdir / "public.jsonl"
    write_jsonl_file(postings_path, [make_posting(posting_id="TEST-01", full_text=None)])
    rubric_path = real_private_subdir / "rubric.yaml"
    rubric_path.write_text(RUBRIC_YAML, encoding="utf-8")

    private_dir = real_private_subdir / "private_raw"
    _write_private_json(private_dir, "TEST-01", "합성 테스트 공고 본문입니다.")

    out_dir = real_private_subdir / "packets"
    manifest = build_packets(postings_path, rubric_path, out_dir, private_dir=private_dir)

    assert manifest["posting_count"] == 1
    a_rows = read_jsonl(out_dir / "annotator_A" / "packet.jsonl")
    # Packets never carry full_text, regardless of join mode.
    assert all("full_text" not in row for row in a_rows)
    # The public source file itself must remain untouched (still null).
    public_rows = read_jsonl(postings_path)
    assert public_rows[0]["full_text"] is None


def test_build_packets_with_private_dir_rejects_non_gitignored_out_dir(tmp_path, real_private_subdir):
    postings_path = real_private_subdir / "public.jsonl"
    write_jsonl_file(postings_path, [make_posting(posting_id="TEST-01", full_text=None)])
    rubric_path = real_private_subdir / "rubric.yaml"
    rubric_path.write_text(RUBRIC_YAML, encoding="utf-8")
    private_dir = real_private_subdir / "private_raw"
    _write_private_json(private_dir, "TEST-01", "합성 테스트 공고 본문입니다.")

    # tmp_path is outside this repository entirely -- never gitignored.
    with pytest.raises(PrivateSourceError, match="NOT covered by .gitignore"):
        build_packets(postings_path, rubric_path, tmp_path / "packets", private_dir=private_dir)


def test_build_packets_with_private_dir_fails_on_missing_text(real_private_subdir):
    postings_path = real_private_subdir / "public.jsonl"
    write_jsonl_file(
        postings_path,
        [make_posting(posting_id="TEST-01", full_text=None), make_posting(posting_id="TEST-02", full_text=None)],
    )
    rubric_path = real_private_subdir / "rubric.yaml"
    rubric_path.write_text(RUBRIC_YAML, encoding="utf-8")
    private_dir = real_private_subdir / "private_raw"
    _write_private_json(private_dir, "TEST-01", "합성 테스트 공고 본문입니다.")
    # TEST-02 has no private file.

    with pytest.raises(PrivateSourceError, match="TEST-02"):
        build_packets(postings_path, rubric_path, real_private_subdir / "packets", private_dir=private_dir)
