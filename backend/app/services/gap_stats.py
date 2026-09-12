"""Regional gap statistics, computed only from adjudicated human gold labels.

AI-suggested labels are never substituted in here. If the data track has not
produced/adjudicated gold labels yet, this returns a typed not-ready result
rather than fabricating numbers or falling back to model output.
"""
from __future__ import annotations

import json
import os
from collections import Counter
from pathlib import Path
from typing import Dict

from ..models.common import FIELD_NAMES, APIError
from ..models.stats import GapStats, GapStatsFilters, GapStatsResponse

_REPO_ROOT = Path(__file__).resolve().parents[3]
_DEFAULT_GOLD_PATH = _REPO_ROOT / "data" / "gold" / "adjudicated_labels.jsonl"
_DEFAULT_POSTINGS_PATH = _REPO_ROOT / "data" / "postings" / "postings.jsonl"
_STATUSES = ("confirmed", "vague", "absent")


def _gold_path() -> Path:
    override = os.environ.get("GOLD_LABELS_PATH")
    return Path(override) if override else _DEFAULT_GOLD_PATH


def _not_ready(message: str) -> GapStatsResponse:
    return GapStatsResponse(ready=False, stats=None, error=APIError(code="data_not_ready", message=message))


def _read_jsonl(path: Path) -> list[dict]:
    rows: list[dict] = []
    with open(path, "r", encoding="utf-8") as fh:
        for line_number, line in enumerate(fh, start=1):
            if not line.strip():
                continue
            value = json.loads(line)
            if not isinstance(value, dict):
                raise TypeError(f"line {line_number} is not an object")
            rows.append(value)
    return rows


def _postings_path() -> Path:
    override = os.environ.get("POSTINGS_DATASET_PATH")
    return Path(override) if override else _DEFAULT_POSTINGS_PATH


def _records_from_adjudicated_jsonl(rows: list[dict]) -> tuple[str, list[dict]]:
    """Adapt the data track's one-row-per-cell adjudication format."""
    if not rows:
        raise ValueError("adjudication file is empty")
    if any(row.get("synthetic_test_fixture") is not False for row in rows):
        raise ValueError(
            "every human-gold adjudication row must explicitly set synthetic_test_fixture=false"
        )
    if any(row.get("adjudicated_status") not in _STATUSES for row in rows):
        raise ValueError("every cell requires an adjudicated_status")

    rubric_versions = {row.get("rubric_version") for row in rows}
    if None in rubric_versions or len(rubric_versions) != 1:
        raise ValueError("adjudication rows must share one rubric_version")

    metadata = {row["posting_id"]: row for row in _read_jsonl(_postings_path())}
    grouped: dict[str, dict] = {}
    for row in rows:
        posting_id = row["posting_id"]
        meta = metadata.get(posting_id)
        if meta is None:
            raise ValueError(f"missing posting metadata for {posting_id}")
        record = grouped.setdefault(
            posting_id,
            {
                "posting_id": posting_id,
                "region": meta.get("region_group", meta.get("region")),
                "occupation": meta.get("occupation"),
                "employment_type": meta.get("employment_type"),
                "fields": {},
            },
        )
        record["fields"][row["field"]] = row["adjudicated_status"]

    if any(set(record["fields"]) != set(FIELD_NAMES) for record in grouped.values()):
        raise ValueError("every posting requires exactly the six audited fields")
    return str(next(iter(rubric_versions))), list(grouped.values())


def _load_gold(path: Path) -> tuple[str, list[dict]]:
    if path.suffix.lower() == ".jsonl":
        return _records_from_adjudicated_jsonl(_read_jsonl(path))
    with open(path, "r", encoding="utf-8") as fh:
        payload = json.load(fh)
    if payload.get("is_gold") is not True:
        raise ValueError("legacy JSON payload must explicitly set is_gold=true")
    return payload["rubric_version"], payload["records"]


def compute_gap_stats() -> GapStatsResponse:
    path = _gold_path()
    if not path.exists():
        return _not_ready(
            "No adjudicated human gold labels are available yet. "
            "AI-generated suggestions are never substituted for human gold labels."
        )

    try:
        rubric_version, records = _load_gold(path)
    except (json.JSONDecodeError, KeyError, TypeError, ValueError, OSError) as exc:
        return _not_ready(f"The configured gold-label data is not usable: {exc}")

    counts: Dict[str, Counter] = {field_name: Counter() for field_name in FIELD_NAMES}
    counts_by_region: dict[str, Dict[str, Counter]] = {}
    cell_count = 0
    occupations, employment_types, regions = set(), set(), set()

    for record in records:
        occupations.add(record.get("occupation"))
        employment_types.add(record.get("employment_type"))
        regions.add(record.get("region"))
        region = record.get("region") or "unknown"
        region_counts = counts_by_region.setdefault(
            region, {field_name: Counter() for field_name in FIELD_NAMES}
        )
        record_fields = record.get("fields", {})
        for field_name in FIELD_NAMES:
            status = record_fields.get(field_name)
            if status not in _STATUSES:
                continue
            counts[field_name][status] += 1
            region_counts[field_name][status] += 1
            cell_count += 1

    proportions: Dict[str, Dict[str, float]] = {}
    for field_name in FIELD_NAMES:
        total = sum(counts[field_name].values())
        proportions[field_name] = {
            status: (counts[field_name][status] / total if total else 0.0) for status in _STATUSES
        }

    proportions_by_region: dict[str, dict] = {}
    for region, region_counts in counts_by_region.items():
        proportions_by_region[region] = {}
        for field_name in FIELD_NAMES:
            total = sum(region_counts[field_name].values())
            proportions_by_region[region][field_name] = {
                status: (region_counts[field_name][status] / total if total else 0.0)
                for status in _STATUSES
            }

    filters = GapStatsFilters(
        region=next(iter(regions)) if len(regions) == 1 else None,
        occupation=next(iter(occupations)) if len(occupations) == 1 else None,
        employment_type=next(iter(employment_types)) if len(employment_types) == 1 else None,
    )

    stats = GapStats(
        sample_size_postings=len(records),
        sample_size_cells=cell_count,
        filters=filters,
        rubric_version=rubric_version,
        label_proportions=proportions,
        label_proportions_by_region=proportions_by_region,
    )
    return GapStatsResponse(ready=True, stats=stats)
