"""Build two independent, isolated annotator packets (A and B) from an
arbitrary local postings JSONL file (Phase D2 #1).

Unlike `scripts/data/generate_annotation_templates.py` -- which is
hard-coded to `data/postings/postings.jsonl`, the repo's own synthetic
fixture set -- this CLI takes the postings path as an argument, so a real
posting file that must stay outside the public repo layer (e.g. under
`data/private/**` or `data/intake/**`, neither of which this track may
write to) can be turned into two blank packets without moving or
duplicating the source text: packets reference `posting_id` + `field` only,
never a copy of `full_text`.

Each packet row has the exact shape `scripts/data/validate_dataset.py` and
`scripts/data/adjudicate.py` already expect (see data/annotation/schema.md),
so no change to either script is needed to consume real annotator output
later.

Usage:
  python scripts/annotation_ops/build_packets.py \\
      --postings /path/to/real_postings.jsonl \\
      --rubric data/rubric/rubric.yaml \\
      --out-dir data/private/annotation_run_001

Writes:
  <out-dir>/annotator_A/packet.jsonl
  <out-dir>/annotator_B/packet.jsonl
  <out-dir>/manifest.json
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from common import (
    ANNOTATOR_IDS,
    FIELDS,
    load_postings,
    load_rubric_version,
    sha256_of_file,
    utc_now_iso,
    write_jsonl,
)


def is_synthetic(posting: dict) -> bool:
    """Mirrors scripts/data/generate_annotation_templates.py's own rule so a
    real posting (which will have neither field set) defaults to False --
    never guessed True -- while the repo's synthetic fixtures still round-trip
    correctly if ever pushed through this CLI for a dry run.
    """
    return bool(
        posting.get("synthetic_test_fixture") is True
        or posting.get("source_name") == "synthetic_fixture_v1"
    )


def blank_row(
    posting_id: str,
    field: str,
    annotator_id: str,
    rubric_version: str,
    synthetic_test_fixture: bool,
) -> dict:
    return {
        "posting_id": posting_id,
        "field": field,
        "annotator_id": annotator_id,
        "status": None,
        "evidence_text": None,
        "offsets": None,
        "reason_code": None,
        "disagreement_note": None,
        "rubric_version": rubric_version,
        "synthetic_test_fixture": synthetic_test_fixture,
    }


def build_packet_rows(postings: list[dict], annotator_id: str, rubric_version: str) -> list[dict]:
    rows = []
    for posting in postings:
        synthetic = is_synthetic(posting)
        for field in FIELDS:
            rows.append(blank_row(posting["posting_id"], field, annotator_id, rubric_version, synthetic))
    return rows


def build_packets(postings_path: Path, rubric_path: Path, out_dir: Path) -> dict:
    postings = load_postings(postings_path)
    if not postings:
        raise ValueError(f"{postings_path}: no postings found")
    rubric_version = load_rubric_version(rubric_path)

    out_dir = Path(out_dir)
    packet_paths: dict[str, str] = {}
    for annotator_id in ANNOTATOR_IDS:
        rows = build_packet_rows(postings, annotator_id, rubric_version)
        packet_path = out_dir / f"annotator_{annotator_id}" / "packet.jsonl"
        write_jsonl(packet_path, rows)
        packet_paths[annotator_id] = str(packet_path)

    manifest = {
        "generated_at": utc_now_iso(),
        "input_postings_path": str(Path(postings_path).resolve()),
        "input_postings_sha256": sha256_of_file(postings_path),
        "rubric_path": str(Path(rubric_path).resolve()),
        "rubric_version": rubric_version,
        "posting_count": len(postings),
        "fields_per_posting": FIELDS,
        "cell_count_per_annotator": len(postings) * len(FIELDS),
        "annotator_ids": ANNOTATOR_IDS,
        "packet_paths": packet_paths,
        "notes": [
            "Packets contain no AI suggestions and no evidence from the other annotator.",
            "This manifest is run provenance only -- it is not a gold label and confers no gold status.",
        ],
    }
    manifest_path = out_dir / "manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    manifest["manifest_path"] = str(manifest_path)
    return manifest


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--postings", required=True, type=Path, help="Path to a real postings JSONL file (any local path)")
    ap.add_argument("--rubric", required=True, type=Path, help="Path to data/rubric/rubric.yaml")
    ap.add_argument("--out-dir", required=True, type=Path, help="Directory to write annotator_A/, annotator_B/, manifest.json into")
    args = ap.parse_args()

    manifest = build_packets(args.postings, args.rubric, args.out_dir)
    print(
        f"Wrote packets for {manifest['posting_count']} posting(s), "
        f"{manifest['cell_count_per_annotator']} cells each, to {args.out_dir}"
    )
    for annotator_id, path in manifest["packet_paths"].items():
        print(f"  annotator_{annotator_id}: {path}")
    print(f"  manifest: {manifest['manifest_path']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
