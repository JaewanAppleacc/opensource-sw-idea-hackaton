"""Shared helpers for scripts/annotation_ops/*.

This package prepares the *process* for two independent human annotators
(packet generation, a local review CLI, isolation/completeness validation,
and adjudication pre-flight checks) per TASK_ANNOTATION_WORKFLOW_PREP.md.
It does not label any real posting itself.

Depends only on the standard library, PyYAML, and the existing
`scripts/data/utils.py` helpers (imported, not copied), so the annotator
templates this produces stay byte-compatible with
`scripts/data/validate_dataset.py` and `scripts/data/adjudicate.py` without
requiring any change to those files.
"""
from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DATA = REPO_ROOT / "scripts" / "data"
if str(SCRIPTS_DATA) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DATA))

import yaml  # noqa: E402

from utils import (  # noqa: E402
    ALLOWED_STATUSES,
    REQUIRED_FIELDS,
    read_jsonl,
    sha256_of_file,
    sha256_of_records,
    write_jsonl,
)

FIELDS = REQUIRED_FIELDS
ANNOTATOR_IDS = ["A", "B"]

# Keys that only ever appear in scripts/data/ai_suggest_labels.py output.
# A real annotator packet must never contain these -- their presence means
# an AI suggestion leaked into a human file.
AI_SUGGESTION_ONLY_KEYS = {"ai_suggested", "suggested_status"}

__all__ = [
    "ALLOWED_STATUSES",
    "REQUIRED_FIELDS",
    "FIELDS",
    "ANNOTATOR_IDS",
    "AI_SUGGESTION_ONLY_KEYS",
    "read_jsonl",
    "write_jsonl",
    "sha256_of_file",
    "sha256_of_records",
    "utc_now_iso",
    "load_rubric_version",
    "load_postings",
]


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load_rubric_version(rubric_path: Path) -> str:
    with Path(rubric_path).open(encoding="utf-8") as f:
        rubric = yaml.safe_load(f)
    version = (rubric or {}).get("rubric_version")
    if not version:
        raise ValueError(f"{rubric_path}: rubric file is missing rubric_version")
    return version


def load_postings(postings_path: Path) -> list[dict]:
    """Read a postings JSONL file from an arbitrary local path.

    Only checks the minimum needed to build packets safely: a stable ID and
    the source text to point evidence offsets into. Everything else about
    the posting schema is the data track's concern
    (see data/postings/README.md), not this track's.
    """
    postings = read_jsonl(postings_path)
    seen_ids: set[str] = set()
    for p in postings:
        pid = p.get("posting_id")
        if not pid:
            raise ValueError(f"{postings_path}: a posting row is missing posting_id")
        if pid in seen_ids:
            raise ValueError(f"{postings_path}: duplicate posting_id {pid!r}")
        seen_ids.add(pid)
        if not p.get("full_text"):
            raise ValueError(f"{postings_path}: posting {pid!r} is missing full_text")
    return postings
