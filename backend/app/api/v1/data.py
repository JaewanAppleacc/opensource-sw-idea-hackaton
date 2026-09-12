from __future__ import annotations

from fastapi import APIRouter

from ...models.stats import GapStatsResponse
from ...services.gap_stats import compute_gap_stats

router = APIRouter()


@router.get("/data/gap-stats", response_model=GapStatsResponse)
def gap_stats() -> GapStatsResponse:
    return compute_gap_stats()
