"""Shared helpers for the data/evaluation scripts. Standard library only —
this package intentionally has no dependency on backend/** or contracts/**.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Iterable, Iterator

ALLOWED_STATUSES = {"confirmed", "vague", "absent"}
REQUIRED_FIELDS = [
    "salary",
    "duties",
    "tools_or_skills",
    "training_or_mentoring",
    "probation_terms",
    "employment_type",
]


def read_jsonl(path: Path) -> list[dict]:
    records = []
    with Path(path).open(encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as e:
                raise ValueError(f"{path}:{line_no}: invalid JSON ({e})") from e
    return records


def write_jsonl(path: Path, records: Iterable[dict]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def sha256_of_file(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_of_records(records: Iterable[dict]) -> str:
    """Order-sensitive checksum over a canonical JSON encoding of records."""
    h = hashlib.sha256()
    for rec in records:
        h.update(json.dumps(rec, ensure_ascii=False, sort_keys=True).encode("utf-8"))
    return h.hexdigest()


def load_postings_by_id(postings_path: Path) -> dict[str, dict]:
    return {rec["posting_id"]: rec for rec in read_jsonl(postings_path)}
