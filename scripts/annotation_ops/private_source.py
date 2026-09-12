"""Join a public postings JSONL (real_postings.jsonl-shaped, `full_text`
always null or redistributable-only) with the private full text that lives
under `data/private/intake_raw/*.json` (gitignored, one JSON object per
posting, keyed by its own `posting_id` field).

This exists because the existing `common.load_postings()` (used by
`build_packets.py`) requires `full_text` to already be populated in the
file it's given -- true for the repo's synthetic fixtures, never true for a
real, rights-gated posting batch where the public JSONL intentionally keeps
`full_text: null`. Nothing here mutates the public file or any private
file; the join happens in memory only, for the current process.

Fail-closed by design, per TASK instructions:
  - every public posting_id must resolve to exactly one private record
    (missing -> explicit error, never silently skipped);
  - two private files must never declare the same posting_id
    (duplicate -> explicit error);
  - a private record with no corresponding public posting is an "orphan":
    strict mode (default) errors, non-strict mode only warns.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Iterable

from common import read_jsonl

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_ACQUISITION = REPO_ROOT / "scripts" / "acquisition"
if str(SCRIPTS_ACQUISITION) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_ACQUISITION))

from acquisition_utils import _EMAIL_RE, _PHONE_RE  # noqa: E402  (reused, not re-implemented)


class PrivateSourceError(Exception):
    """Raised for any public/private join integrity failure. Never caught
    and downgraded to a warning by callers -- only the explicit
    orphan-private-file case has an opt-in non-strict mode.
    """


def _load_private_records(private_dir: Path) -> dict[str, dict]:
    private_dir = Path(private_dir)
    if not private_dir.is_dir():
        raise PrivateSourceError(f"private directory does not exist: {private_dir}")

    by_id: dict[str, dict] = {}
    duplicates: dict[str, list[str]] = {}
    for path in sorted(private_dir.glob("*.json")):
        with path.open(encoding="utf-8") as f:
            record = json.load(f)
        pid = record.get("posting_id")
        if not pid:
            raise PrivateSourceError(f"{path}: private record is missing posting_id")
        if not record.get("full_text"):
            raise PrivateSourceError(f"{path}: private record {pid!r} has empty full_text")
        if pid in by_id:
            duplicates.setdefault(pid, [str(path)]).append(str(path))
            continue
        by_id[pid] = {**record, "_source_path": str(path)}

    if duplicates:
        raise PrivateSourceError(
            "duplicate posting_id across private files: "
            + "; ".join(f"{pid} -> {paths}" for pid, paths in duplicates.items())
        )
    return by_id


def join_public_and_private(
    postings_path: Path,
    private_dir: Path,
    strict: bool = True,
) -> list[dict]:
    """Returns a list of posting dicts shaped like `common.load_postings()`
    output (posting_id, full_text populated, plus every other public
    metadata field carried through unchanged) so it can be fed directly
    into `build_packets.build_packet_rows()` or a validator that needs
    `full_text` to check evidence offsets.
    """
    public_records = read_jsonl(postings_path)
    if not public_records:
        raise PrivateSourceError(f"{postings_path}: no postings found")

    seen_public_ids: set[str] = set()
    for rec in public_records:
        pid = rec.get("posting_id")
        if not pid:
            raise PrivateSourceError(f"{postings_path}: a posting row is missing posting_id")
        if pid in seen_public_ids:
            raise PrivateSourceError(f"{postings_path}: duplicate posting_id {pid!r}")
        seen_public_ids.add(pid)

    private_by_id = _load_private_records(private_dir)

    missing = sorted(seen_public_ids - private_by_id.keys())
    if missing:
        raise PrivateSourceError(
            f"{len(missing)} public posting(s) have no matching private full text "
            f"under {private_dir}: {missing}"
        )

    orphans = sorted(private_by_id.keys() - seen_public_ids)
    if orphans:
        message = f"private file(s) with no matching public posting: {orphans}"
        if strict:
            raise PrivateSourceError(message)
        print(f"WARNING: {message}", file=sys.stderr)

    joined: list[dict] = []
    for rec in public_records:
        private_rec = private_by_id[rec["posting_id"]]
        merged = dict(rec)
        merged["full_text"] = private_rec["full_text"]
        joined.append(merged)
    return joined


def check_expected_posting_count(postings: Iterable[dict], expected: int) -> list[str]:
    n = len(list(postings))
    if n != expected:
        return [f"expected exactly {expected} posting(s), found {n}"]
    return []


def check_no_pii_in_evidence(records: Iterable[dict]) -> list[str]:
    """Defense in depth: an annotator's evidence_text is a verbatim quote of
    real posting text, so it can in principle contain a phone number or
    email if the posting text does. Flag it rather than silently letting it
    propagate into anything shared later (adjudication output, an eventual
    gold export).
    """
    errors = []
    for i, rec in enumerate(records):
        text = rec.get("evidence_text")
        if not text:
            continue
        if _PHONE_RE.search(text) or _EMAIL_RE.search(text):
            errors.append(
                f"row {i} ({rec.get('posting_id')}/{rec.get('field')}): "
                "evidence_text appears to contain a phone number or email"
            )
    return errors


def check_path_is_gitignored(path: Path) -> list[str]:
    """Confirms `path` is actually covered by .gitignore (not just
    conventionally placed under data/private/) using `git check-ignore`,
    so a typo'd --out-dir can't accidentally produce a trackable file full
    of real posting text.
    """
    import subprocess

    path = Path(path)
    try:
        result = subprocess.run(
            ["git", "check-ignore", "-q", str(path)],
            cwd=REPO_ROOT,
            check=False,
            stderr=subprocess.DEVNULL,
        )
    except FileNotFoundError:
        return [f"could not run 'git check-ignore' to verify {path} is ignored (git not found)"]
    if result.returncode != 0:
        return [f"{path} is NOT covered by .gitignore -- refusing to write real posting text there"]
    return []


def assert_output_under_gitignore(path: Path) -> None:
    errors = check_path_is_gitignored(path)
    if errors:
        raise PrivateSourceError("; ".join(errors))
