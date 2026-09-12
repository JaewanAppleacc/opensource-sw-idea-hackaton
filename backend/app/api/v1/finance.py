from __future__ import annotations

from fastapi import APIRouter

from ...models.finance import FinancialComparison, FinancialComparisonRequest
from ...services.finance import compare_financials

router = APIRouter()


@router.post("/finance/compare", response_model=FinancialComparison)
def compare(request: FinancialComparisonRequest) -> FinancialComparison:
    return compare_financials(request)
