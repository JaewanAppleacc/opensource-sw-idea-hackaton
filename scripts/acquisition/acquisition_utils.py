"""Shared helpers for the real-data acquisition scripts (Parallel task D1).

Standard library only, plus a re-export of the data/evaluation track's
JSONL/checksum helpers (`scripts/data/utils.py`) so the two tracks share one
implementation instead of duplicating it. This module must never import
anything from `backend/**` or `contracts/**` (those belong to other tracks).
"""
from __future__ import annotations

import importlib.util
import re
from pathlib import Path
from typing import Iterable

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DATA = REPO_ROOT / "scripts" / "data"


def _load_data_track_utils():
    # Load the data-track helper by file path so each CLI remains runnable
    # without turning the scripts directories into installed packages.
    spec = importlib.util.spec_from_file_location("data_track_utils", SCRIPTS_DATA / "utils.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_data_track_utils = _load_data_track_utils()
read_jsonl = _data_track_utils.read_jsonl
write_jsonl = _data_track_utils.write_jsonl
sha256_of_records = _data_track_utils.sha256_of_records

__all__ = [
    "read_jsonl",
    "write_jsonl",
    "sha256_of_records",
    "sha256_of_text",
    "scrub_pii",
    "AcquisitionError",
    "CredentialOrConfigUnavailableError",
    "NetworkError",
    "ALLOWED_REGION_GROUPS",
    "ALLOWED_REDISTRIBUTION_PERMISSIONS",
]

ALLOWED_REGION_GROUPS = {"jeonbuk", "metro"}
# "yes"/"no" are an explicit human decision; "unknown" is the safe default
# used by the manual-intake template until someone confirms redistribution
# rights for that specific posting.
ALLOWED_REDISTRIBUTION_PERMISSIONS = {"yes", "no", "unknown"}


class AcquisitionError(Exception):
    """Base class for typed acquisition errors (never a bare Exception)."""


class CredentialOrConfigUnavailableError(AcquisitionError):
    """Raised when a live API call is requested but the service key and/or
    the verified endpoint config are not available. Never attempt the network
    call in this case — fail closed with a precise, actionable message that
    never includes the key value itself.
    """


class NetworkError(AcquisitionError):
    """Raised for transport-level failures (timeout, connection, HTTP 5xx),
    kept distinct from CredentialOrConfigUnavailableError (HTTP 401/403 or
    missing config) so callers/tests can tell the two apart.
    """


def sha256_of_text(text: str) -> str:
    import hashlib

    return hashlib.sha256(text.encode("utf-8")).hexdigest()


# Conservative Korean/international phone patterns and emails. This is a
# best-effort scrub, not a guarantee — annotators handling data/private raw
# text should still avoid quoting contact details in evidence spans.
_PHONE_RE = re.compile(
    r"(?:\+?82[-.\s]?)?0?1[016789][-.\s]?\d{3,4}[-.\s]?\d{4}"
    r"|(?:\+?82[-.\s]?)?0\d{1,2}[-.\s]?\d{3,4}[-.\s]?\d{4}"
)
_EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")


def scrub_pii(text: str) -> tuple[str, int]:
    """Redact phone numbers and email addresses. Returns (scrubbed_text,
    count_of_redactions). Contact-person names are NOT auto-detected (no
    reliable regex for Korean names without false positives on company/role
    text) — the manual-intake guide asks the human supplier to drop those
    themselves before pasting.
    """
    count = 0

    def _sub(pattern: re.Pattern[str], label: str, s: str) -> str:
        nonlocal count
        def repl(_m: re.Match[str]) -> str:
            nonlocal count
            count += 1
            return f"[REDACTED_{label}]"
        return pattern.sub(repl, s)

    text = _sub(_EMAIL_RE, "EMAIL", text)
    text = _sub(_PHONE_RE, "PHONE", text)
    return text, count


def dedupe_check(existing_ids: Iterable[str], new_id: str) -> None:
    if new_id in set(existing_ids):
        raise AcquisitionError(f"duplicate posting_id already present: {new_id}")
