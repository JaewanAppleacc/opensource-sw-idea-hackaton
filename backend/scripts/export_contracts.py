"""Regenerate contracts/schema.json and contracts/openapi.json from the
backend's canonical Pydantic models and FastAPI app.

Run from the backend/ directory:

    python -m scripts.export_contracts
"""
from __future__ import annotations

import json
from pathlib import Path

from app.main import app
from app.models.common import APIError, EvidenceSpan
from app.models.external import ExternalContext
from app.models.finance import (
    CrossoverResult,
    FinancialAssumptions,
    FinancialComparison,
    FinancialComparisonRequest,
    FinancialOption,
    FinancialOptionResult,
)
from app.models.listing import AnalyzeByIdRequest, HomeRegionMatchRequest, PostingListItem, PostingListResponse
from app.models.match import MatchCandidate, MatchRequest, MatchResponse
from app.models.posting import AuditedField, PostingAnalysis, PostingInput, ValidationWarning, VerificationAction
from app.models.stats import GapStats, GapStatsFilters, GapStatsResponse

CONTRACTS_DIR = Path(__file__).resolve().parents[2] / "contracts"

MODELS = [
    PostingInput,
    PostingAnalysis,
    AuditedField,
    EvidenceSpan,
    VerificationAction,
    ValidationWarning,
    ExternalContext,
    MatchRequest,
    MatchCandidate,
    MatchResponse,
    FinancialOption,
    FinancialAssumptions,
    FinancialComparisonRequest,
    FinancialComparison,
    FinancialOptionResult,
    CrossoverResult,
    GapStats,
    GapStatsFilters,
    GapStatsResponse,
    APIError,
    PostingListItem,
    PostingListResponse,
    HomeRegionMatchRequest,
    AnalyzeByIdRequest,
]


def main() -> None:
    schema = {model.__name__: model.model_json_schema() for model in MODELS}
    CONTRACTS_DIR.mkdir(exist_ok=True)
    (CONTRACTS_DIR / "schema.json").write_text(
        json.dumps(schema, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    (CONTRACTS_DIR / "openapi.json").write_text(
        json.dumps(app.openapi(), indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(f"Wrote {CONTRACTS_DIR / 'schema.json'} and {CONTRACTS_DIR / 'openapi.json'}")


if __name__ == "__main__":
    main()
