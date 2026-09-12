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

_DEFAULT_GOLD_PATH = Path("data/gold/adjudicated_labels.json")
_STATUSES = ("confirmed", "vague", "absent")


def _gold_path() -> Path:
    override = os.environ.get("GOLD_LABELS_PATH")
    return Path(override) if override else _DEFAULT_GOLD_PATH


def _not_ready(message: str) -> GapStatsResponse:
    return GapStatsResponse(ready=False, stats=None, error=APIError(code="data_not_ready", message=message))


def compute_gap_stats() -> GapStatsResponse:
    path = _gold_path()
    if not path.exists():
        return _not_ready(
            f"No adjudicated gold labels are available yet at {path}. "
            "AI-generated suggestions are never substituted for human gold labels."
        )

    try:
        with open(path, "r", encoding="utf-8") as fh:
            payload = json.load(fh)
        rubric_version = payload["rubric_version"]
        records = payload["records"]
    except (json.JSONDecodeError, KeyError, TypeError) as exc:
        return _not_ready(f"gold labels file at {path} is malformed: {exc}")

    counts: Dict[str, Counter] = {field_name: Counter() for field_name in FIELD_NAMES}
    cell_count = 0
    occupations, employment_types, regions = set(), set(), set()

    for record in records:
        occupations.add(record.get("occupation"))
        employment_types.add(record.get("employment_type"))
        regions.add(record.get("region"))
        record_fields = record.get("fields", {})
        for field_name in FIELD_NAMES:
            status = record_fields.get(field_name)
            if status not in _STATUSES:
                continue
            counts[field_name][status] += 1
            cell_count += 1

    proportions: Dict[str, Dict[str, float]] = {}
    for field_name in FIELD_NAMES:
        total = sum(counts[field_name].values())
        proportions[field_name] = {
            status: (counts[field_name][status] / total if total else 0.0) for status in _STATUSES
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
    )
    return GapStatsResponse(ready=True, stats=stats)
