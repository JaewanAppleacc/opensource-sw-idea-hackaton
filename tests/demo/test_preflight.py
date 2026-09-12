"""Unit tests for scripts/demo/preflight.py against synthetic fixtures only
-- never against this machine's real data/private/intake_raw (which may or
may not exist here) or its real .env. Nothing here prints posting text.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = REPO_ROOT / "scripts" / "demo" / "preflight.py"

_spec = importlib.util.spec_from_file_location("demo_preflight", SCRIPT_PATH)
preflight = importlib.util.module_from_spec(_spec)
sys.modules["demo_preflight"] = preflight
_spec.loader.exec_module(preflight)  # type: ignore[union-attr]


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def test_check_public_data_reports_counts(tmp_path, monkeypatch):
    monkeypatch.setattr(preflight, "REPO_ROOT", tmp_path)
    intake = tmp_path / "data" / "intake"
    _write_jsonl(intake / "real_postings.jsonl", [{"posting_id": "JB-01"}, {"posting_id": "MET-01"}])
    _write_jsonl(intake / "real_matched_pairs.jsonl", [{"matched_pair_id": "P-1"}])

    ok, detail, by_id = preflight.check_public_data()
    assert ok is True
    assert "2 public postings" in detail
    assert set(by_id) == {"JB-01", "MET-01"}


def test_check_public_data_fails_on_duplicate_posting_id(tmp_path, monkeypatch):
    monkeypatch.setattr(preflight, "REPO_ROOT", tmp_path)
    intake = tmp_path / "data" / "intake"
    intake.mkdir(parents=True)
    _write_jsonl(intake / "real_postings.jsonl", [{"posting_id": "JB-01"}, {"posting_id": "JB-01"}])
    _write_jsonl(intake / "real_matched_pairs.jsonl", [])

    ok, detail, by_id = preflight.check_public_data()
    assert ok is False
    assert by_id is None


def test_check_private_data_fails_when_env_var_unset(monkeypatch):
    monkeypatch.delenv("PRIVATE_INTAKE_RAW_DIR", raising=False)
    ok, detail, files = preflight.check_private_data({})
    assert ok is False
    assert files == []


def test_check_private_data_fails_when_dir_missing(tmp_path, monkeypatch):
    monkeypatch.setenv("PRIVATE_INTAKE_RAW_DIR", str(tmp_path / "does-not-exist"))
    ok, detail, files = preflight.check_private_data({})
    assert ok is False


def test_hash_integrity_passes_for_matching_records(tmp_path):
    full_text = "합성 테스트 본문입니다."
    public_by_id = {"JB-01": {"posting_id": "JB-01", "full_text_sha256": _sha256(full_text)}}
    private_dir = tmp_path / "intake_raw"
    private_dir.mkdir()
    (private_dir / "JB-01.json").write_text(
        json.dumps({"posting_id": "JB-01", "full_text": full_text}, ensure_ascii=False), encoding="utf-8"
    )

    ok, detail = preflight.check_hash_integrity(public_by_id, [private_dir / "JB-01.json"])
    assert ok is True
    assert "hash_mismatch=0" in detail


def test_hash_integrity_detects_mismatch(tmp_path):
    public_by_id = {"JB-01": {"posting_id": "JB-01", "full_text_sha256": _sha256("original text")}}
    private_dir = tmp_path / "intake_raw"
    private_dir.mkdir()
    (private_dir / "JB-01.json").write_text(
        json.dumps({"posting_id": "JB-01", "full_text": "tampered text"}, ensure_ascii=False), encoding="utf-8"
    )

    ok, detail = preflight.check_hash_integrity(public_by_id, [private_dir / "JB-01.json"])
    assert ok is False
    assert "hash_mismatch=1" in detail


def test_hash_integrity_detects_orphan_and_missing(tmp_path):
    public_by_id = {"JB-01": {"posting_id": "JB-01", "full_text_sha256": _sha256("x")}}
    private_dir = tmp_path / "intake_raw"
    private_dir.mkdir()
    (private_dir / "JB-99.json").write_text(
        json.dumps({"posting_id": "JB-99", "full_text": "x"}, ensure_ascii=False), encoding="utf-8"
    )

    ok, detail = preflight.check_hash_integrity(public_by_id, [private_dir / "JB-99.json"])
    assert ok is False
    assert "missing=1" in detail
    assert "orphan=1" in detail


def test_hash_integrity_rejects_synthetic_fixture(tmp_path):
    full_text = "합성 테스트 본문"
    public_by_id = {"JB-01": {"posting_id": "JB-01", "full_text_sha256": _sha256(full_text)}}
    private_dir = tmp_path / "intake_raw"
    private_dir.mkdir()
    (private_dir / "JB-01.json").write_text(
        json.dumps(
            {"posting_id": "JB-01", "full_text": full_text, "synthetic_test_fixture": True}, ensure_ascii=False
        ),
        encoding="utf-8",
    )

    ok, detail = preflight.check_hash_integrity(public_by_id, [private_dir / "JB-01.json"])
    assert ok is False
    assert "synthetic=1" in detail


def test_check_mock_provider(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "mock")
    assert preflight.check_mock_provider() == (True, "LLM_PROVIDER='mock'")

    monkeypatch.setenv("LLM_PROVIDER", "anthropic")
    ok, _ = preflight.check_mock_provider()
    assert ok is False


def test_check_cors(monkeypatch):
    monkeypatch.setenv("CORS_ORIGINS", "http://localhost:5183")
    ok, _ = preflight.check_cors()
    assert ok is True

    monkeypatch.setenv("CORS_ORIGINS", "http://localhost:9999")
    ok, _ = preflight.check_cors()
    assert ok is False
