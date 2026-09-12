"""Ingest human-supplied real job-posting text files (Phase 3 of
TASK_REAL_DATA_ACQUISITION.md, "User-provided postings" path in
data/sources/source_inventory.yaml).

This is the approved non-API acquisition path: a team member who has
personally confirmed they may share a posting (their own screen-copy of a
real Jeonbuk/metropolitan listing, with source URL and collection date)
pastes it into a small plain-text template — see
docs/acquisition/MANUAL_INTAKE_GUIDE.md for the exact format and the
neutral sampling rule (sort candidates by recency, take from the top,
never cherry-pick by how information-rich a posting looks).

For every parsed record this script:
  1. Validates the required header fields and full-text presence.
  2. Redacts phone numbers / emails from the full text (best-effort).
  3. Always writes the full record (including full text) to
     data/private/intake_raw/<posting_id>.json — gitignored, used only for
     human annotation, never redistributed as-is.
  4. Writes a public-safe record to data/intake/real_postings.jsonl:
     - full_text is included ONLY when redistribution_permission == "yes".
     - Otherwise full_text is null and only source_id_url + a checksum of
       the private full text are kept, so redistribution rights are never
       assumed by omission.
  5. Routes `status: excluded` blocks to data/intake/excluded_postings.jsonl
     with their factual exclusion reason instead of a posting record.

CLI:
  python scripts/acquisition/manual_intake.py --in FILE [FILE ...] \\
      [--out data/intake/real_postings.jsonl] \\
      [--excluded-out data/intake/excluded_postings.jsonl] \\
      [--private-dir data/private/intake_raw] \\
      [--dry-run]

Exit code 0 = all input blocks parsed and written (or dry-run validated) with
no errors. Exit code 1 = at least one error (nothing is written on error).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from acquisition_utils import (  # noqa: E402
    ALLOWED_REDISTRIBUTION_PERMISSIONS,
    ALLOWED_REGION_GROUPS,
    read_jsonl,
    scrub_pii,
    sha256_of_text,
    write_jsonl,
)

REQUIRED_HEADER_FIELDS = [
    "posting_id",
    "region_group",
    "municipality",
    "source_name",
    "source_url",
    "collection_date",
    "occupation",
    "employment_type",
    "company_name",
    "redistribution_permission",
]
FULL_TEXT_MARKER_RE = re.compile(r"^---\s*FULL TEXT\s*---\s*$", re.IGNORECASE)
BLOCK_HEADER_RE = re.compile(r"^=====\s*(.+?)\s*=====\s*$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


class IntakeParseError(Exception):
    def __init__(self, block_label: str, message: str):
        super().__init__(f"[{block_label}] {message}")
        self.block_label = block_label


def split_blocks(text: str) -> list[tuple[str, str]]:
    """Returns [(label, block_text), ...]. A file with no ===== markers is
    treated as a single unlabeled block (the single-posting template).
    """
    lines = text.splitlines()
    marker_indices = [i for i, ln in enumerate(lines) if BLOCK_HEADER_RE.match(ln)]
    if not marker_indices:
        return [("(single record)", text)]

    blocks: list[tuple[str, str]] = []
    for idx, start in enumerate(marker_indices):
        label = BLOCK_HEADER_RE.match(lines[start]).group(1)
        end = marker_indices[idx + 1] if idx + 1 < len(marker_indices) else len(lines)
        blocks.append((label, "\n".join(lines[start + 1 : end])))
    return blocks


def parse_block(label: str, block_text: str) -> dict[str, Any]:
    lines = block_text.splitlines()
    marker_idx = next((i for i, ln in enumerate(lines) if FULL_TEXT_MARKER_RE.match(ln)), None)

    header_lines = lines if marker_idx is None else lines[:marker_idx]
    body_lines = [] if marker_idx is None else lines[marker_idx + 1 :]

    header: dict[str, str] = {}
    for ln in header_lines:
        stripped = ln.strip()
        if not stripped:
            continue
        if ":" not in stripped:
            raise IntakeParseError(label, f"header line is not 'key: value': {stripped!r}")
        key, _, value = stripped.partition(":")
        header[key.strip()] = value.strip()

    status = header.get("status", "active")
    if status not in ("active", "excluded"):
        raise IntakeParseError(label, f"status must be 'active' or 'excluded', got {status!r}")

    if status == "excluded":
        if "excluded_reason" not in header or not header["excluded_reason"]:
            raise IntakeParseError(label, "status: excluded requires a non-empty excluded_reason")
        return {"status": "excluded", "label": label, "header": header}

    missing = [f for f in REQUIRED_HEADER_FIELDS if not header.get(f)]
    if missing:
        raise IntakeParseError(label, f"missing required header field(s): {missing}")

    if header["region_group"] not in ALLOWED_REGION_GROUPS:
        raise IntakeParseError(
            label, f"region_group must be one of {sorted(ALLOWED_REGION_GROUPS)}, got {header['region_group']!r}"
        )
    if header["redistribution_permission"] not in ALLOWED_REDISTRIBUTION_PERMISSIONS:
        raise IntakeParseError(
            label,
            "redistribution_permission must be one of "
            f"{sorted(ALLOWED_REDISTRIBUTION_PERMISSIONS)}, got "
            f"{header['redistribution_permission']!r}",
        )
    if not DATE_RE.match(header["collection_date"]):
        raise IntakeParseError(label, f"collection_date must be YYYY-MM-DD, got {header['collection_date']!r}")

    if marker_idx is None:
        raise IntakeParseError(label, "missing '--- FULL TEXT ---' marker")
    full_text = "\n".join(body_lines).strip("\n").strip()
    if not full_text:
        raise IntakeParseError(label, "full text is empty")

    return {"status": "active", "label": label, "header": header, "full_text": full_text}


def to_posting_record(parsed: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    """Returns (private_record, public_record)."""
    h = parsed["header"]
    scrubbed_text, redaction_count = scrub_pii(parsed["full_text"])
    checksum = sha256_of_text(scrubbed_text)
    redistributable = h["redistribution_permission"] == "yes"

    private_record = {
        "posting_id": h["posting_id"],
        "region_group": h["region_group"],
        "municipality": h["municipality"],
        "occupation": h["occupation"],
        "employment_type": h["employment_type"],
        "collection_date": h["collection_date"],
        "source_name": h["source_name"],
        "source_id_url": h["source_url"],
        "company_name": h["company_name"],
        "redistribution_permission": h["redistribution_permission"],
        "full_text": scrubbed_text,
        "full_text_sha256": checksum,
        "pii_redaction_count": redaction_count,
    }

    public_record = {
        "posting_id": h["posting_id"],
        "region_group": h["region_group"],
        "municipality": h["municipality"],
        "occupation": h["occupation"],
        "employment_type": h["employment_type"],
        "collection_date": h["collection_date"],
        "fixture_build_date": None,
        "source_name": h["source_name"],
        "source_id_url": h["source_url"],
        "company_name": h["company_name"],
        "full_text": scrubbed_text if redistributable else None,
        "full_text_sha256": checksum,
        "full_text_available_privately": True,
        "redistributable": redistributable,
        "synthetic_test_fixture": False,
        "matched_pair_id": None,
        "match_criteria": None,
        "unmatched": None,
        "unmatched_reason": None,
    }
    return private_record, public_record


def run(
    input_paths: list[Path],
    out_path: Path,
    excluded_out_path: Path,
    private_dir: Path,
    dry_run: bool,
) -> int:
    existing_public = read_jsonl(out_path) if out_path.exists() else []
    existing_ids = {r["posting_id"] for r in existing_public}

    new_public: list[dict[str, Any]] = []
    new_private: list[tuple[str, dict[str, Any]]] = []
    new_excluded: list[dict[str, Any]] = []
    seen_in_batch: set[str] = set()
    errors: list[str] = []

    for path in input_paths:
        text = path.read_text(encoding="utf-8")
        for label, block_text in split_blocks(text):
            try:
                parsed = parse_block(label, block_text)
            except IntakeParseError as e:
                errors.append(str(e))
                continue

            if parsed["status"] == "excluded":
                new_excluded.append(
                    {
                        "label": parsed["label"],
                        "excluded_reason": parsed["header"]["excluded_reason"],
                        "posting_id": parsed["header"].get("posting_id"),
                        "region_group": parsed["header"].get("region_group"),
                    }
                )
                continue

            pid = parsed["header"]["posting_id"]
            if pid in existing_ids or pid in seen_in_batch:
                errors.append(f"[{label}] duplicate posting_id: {pid}")
                continue
            seen_in_batch.add(pid)

            private_record, public_record = to_posting_record(parsed)
            new_private.append((pid, private_record))
            new_public.append(public_record)

    if errors:
        for e in errors:
            print(f"error: {e}", file=sys.stderr)
        return 1

    print(
        f"parsed {len(new_public)} active posting(s), {len(new_excluded)} excluded "
        f"record(s) from {len(input_paths)} file(s)"
    )
    if dry_run:
        print("dry-run: nothing written")
        return 0

    private_dir.mkdir(parents=True, exist_ok=True)
    for pid, record in new_private:
        (private_dir / f"{pid}.json").write_text(
            json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    write_jsonl(out_path, existing_public + new_public)

    existing_excluded = read_jsonl(excluded_out_path) if excluded_out_path.exists() else []
    write_jsonl(excluded_out_path, existing_excluded + new_excluded)

    print(f"wrote {len(new_public)} public record(s) to {out_path}")
    print(f"wrote {len(new_private)} private record(s) to {private_dir}/")
    if new_excluded:
        print(f"wrote {len(new_excluded)} excluded record(s) to {excluded_out_path}")
    return 0


def build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--in", dest="input_paths", type=Path, nargs="+", required=True)
    p.add_argument("--out", type=Path, default=Path("data/intake/real_postings.jsonl"))
    p.add_argument("--excluded-out", type=Path, default=Path("data/intake/excluded_postings.jsonl"))
    p.add_argument("--private-dir", type=Path, default=Path("data/private/intake_raw"))
    p.add_argument("--dry-run", action="store_true")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    return run(args.input_paths, args.out, args.excluded_out, args.private_dir, args.dry_run)


if __name__ == "__main__":
    raise SystemExit(main())
