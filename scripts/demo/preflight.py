#!/usr/bin/env python3
"""Offline demo readiness preflight check.

Run from anywhere:  python3 scripts/demo/preflight.py

Never prints posting text, PII, secrets, .env values, or API keys -- only
booleans, counts, and posting_id/file names (posting_ids are not personal
data; they are this project's own public dataset identifiers, e.g. JB-01).
Exit code 0 means every gating check passed; 1 means at least one failed.

This does not replace `python -m pytest -q` / `npx playwright test` -- it's
a fast, read-only sanity check of the *environment* (is private data
present and internally consistent, is the provider mock, is a frontend
origin allowed) before spending time on a full run or a live demo.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Optional

REPO_ROOT = Path(__file__).resolve().parents[2]


def _load_env_file() -> None:
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    load_dotenv(REPO_ROOT / ".env", override=False)


def _read_jsonl(path: Path) -> list[dict]:
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


def check_public_data() -> tuple[bool, str, Optional[dict]]:
    postings_path = REPO_ROOT / "data" / "intake" / "real_postings.jsonl"
    pairs_path = REPO_ROOT / "data" / "intake" / "real_matched_pairs.jsonl"
    if not postings_path.is_file() or not pairs_path.is_file():
        return False, "real_postings.jsonl or real_matched_pairs.jsonl missing", None

    try:
        postings = _read_jsonl(postings_path)
        pairs = _read_jsonl(pairs_path)
    except (json.JSONDecodeError, OSError) as exc:
        return False, f"could not read public intake files: {exc}", None

    ids = [p.get("posting_id") for p in postings]
    if len(ids) != len(set(ids)):
        return False, "duplicate posting_id in real_postings.jsonl", None

    by_id = {p["posting_id"]: p for p in postings if p.get("posting_id")}
    return True, f"{len(postings)} public postings, {len(pairs)} matched pairs", by_id


def check_private_data(public_by_id: dict) -> tuple[bool, str, list[Path]]:
    private_dir_str = os.environ.get("PRIVATE_INTAKE_RAW_DIR")
    if not private_dir_str:
        return False, "PRIVATE_INTAKE_RAW_DIR is not set", []
    private_dir = Path(private_dir_str)
    if not private_dir.is_dir():
        return False, f"PRIVATE_INTAKE_RAW_DIR does not exist", []

    private_files = sorted(private_dir.glob("*.json"))
    if not private_files:
        return False, "PRIVATE_INTAKE_RAW_DIR exists but has no .json files", []
    return True, f"{len(private_files)} private record(s) found", private_files


def check_hash_integrity(public_by_id: dict, private_files: list[Path]) -> tuple[bool, str]:
    claimed: dict[str, dict] = {}
    for path in private_files:
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return False, f"unreadable private file (name only): {path.name}"
        posting_id = record.get("posting_id")
        if not posting_id or posting_id != path.stem:
            return False, f"filename/posting_id mismatch (name only): {path.name}"
        if posting_id in claimed:
            return False, f"duplicate posting_id across private files: {posting_id}"
        claimed[posting_id] = record

    missing = sorted(set(public_by_id) - set(claimed))
    orphan = sorted(set(claimed) - set(public_by_id))

    hash_mismatch = []
    synthetic = []
    for posting_id, record in claimed.items():
        if record.get("synthetic_test_fixture") is True:
            synthetic.append(posting_id)
        expected_hash = public_by_id.get(posting_id, {}).get("full_text_sha256")
        full_text = record.get("full_text")
        if not expected_hash or not full_text:
            continue
        actual_hash = hashlib.sha256(full_text.encode("utf-8")).hexdigest()
        if actual_hash != expected_hash:
            hash_mismatch.append(posting_id)

    ok = not missing and not orphan and not hash_mismatch and not synthetic
    detail = (
        f"matched={len(claimed) - len(orphan)} missing={len(missing)} "
        f"orphan={len(orphan)} hash_mismatch={len(hash_mismatch)} synthetic={len(synthetic)}"
    )
    return ok, detail


def check_mock_provider() -> tuple[bool, str]:
    provider = os.environ.get("LLM_PROVIDER", "mock")
    # Deliberately never reads/prints ANTHROPIC_API_KEY / NVIDIA_API_KEY.
    return provider == "mock", f"LLM_PROVIDER={provider!r}"


def check_cors() -> tuple[bool, str]:
    origins = os.environ.get("CORS_ORIGINS", "")
    has_frontend_port = any(port in origins for port in ("5173", "5183"))
    return has_frontend_port, "frontend dev/e2e origin present" if has_frontend_port else "no known frontend origin in CORS_ORIGINS"


def main() -> int:
    _load_env_file()

    results: list[tuple[str, bool, str]] = []

    public_ok, public_detail, public_by_id = check_public_data()
    results.append(("PUBLIC_DATA", public_ok, public_detail))

    if public_ok:
        private_ok, private_detail, private_files = check_private_data(public_by_id)
    else:
        private_ok, private_detail, private_files = False, "skipped (public data check failed)", []
    results.append(("PRIVATE_DATA", private_ok, private_detail))

    if public_ok and private_ok:
        hash_ok, hash_detail = check_hash_integrity(public_by_id, private_files)
    else:
        hash_ok, hash_detail = False, "skipped (public or private data not available)"
    results.append(("HASH_INTEGRITY", hash_ok, hash_detail))

    mock_ok, mock_detail = check_mock_provider()
    results.append(("MOCK_PROVIDER", mock_ok, mock_detail))

    cors_ok, cors_detail = check_cors()
    results.append(("CORS", cors_ok, cors_detail))

    all_ok = all(ok for _, ok, _ in results)
    for name, ok, detail in results:
        print(f"{name}: {'PASS' if ok else 'FAIL'} ({detail})")
    print(f"DEMO_READY: {'PASS' if all_ok else 'FAIL'}")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
