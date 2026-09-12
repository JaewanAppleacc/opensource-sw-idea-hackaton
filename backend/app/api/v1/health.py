from __future__ import annotations

from fastapi import APIRouter

from ...config import get_settings
from ...datasets.loader import dataset_is_available
from ...rules.field_rules import rules_version

router = APIRouter()


@router.get("/health")
def health() -> dict:
    settings = get_settings()
    return {
        "status": "ok",
        "provider_mode": settings.llm_provider,
        "dataset_available": dataset_is_available(),
        "rubric_version": rules_version(),
    }
