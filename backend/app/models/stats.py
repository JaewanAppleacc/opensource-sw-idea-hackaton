from __future__ import annotations

from typing import Dict, Literal, Optional

from .common import APIError, FieldName, FieldStatus, StrictModel


class GapStatsFilters(StrictModel):
    region: Optional[str] = None
    occupation: Optional[str] = None
    employment_type: Optional[str] = None


class GapStats(StrictModel):
    sample_size_postings: int
    sample_size_cells: int
    filters: GapStatsFilters
    rubric_version: str
    label_proportions: Dict[FieldName, Dict[FieldStatus, float]]
    exploratory: Literal[True] = True


class GapStatsResponse(StrictModel):
    ready: bool
    stats: Optional[GapStats] = None
    error: Optional[APIError] = None
