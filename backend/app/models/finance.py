"""Deterministic financial-comparison contract.

Everything here is computed by plain arithmetic in services/finance.py --
never by an LLM. The deposit is locked wealth, kept separate from liquid
cash accumulation per CLAUDE.md. No field here ever ranks or recommends
an option.
"""
from __future__ import annotations

from typing import Dict, Literal

from pydantic import Field

from .common import StrictModel


class FinancialOption(StrictModel):
    label: str = Field(..., min_length=1)
    monthly_income_after_tax: float = Field(..., ge=0)
    monthly_housing_cost: float = Field(..., ge=0, description="Housing cost including maintenance.")
    monthly_other_living_cost: float = Field(..., ge=0)
    deposit: float = Field(..., ge=0, description="Locked wealth, not consumption.")


class FinancialAssumptions(StrictModel):
    annual_income_growth_rate: float = Field(0.0, ge=-0.5, le=1.0)
    annual_cost_growth_rate: float = Field(0.0, ge=-0.5, le=1.0)
    rounding_unit_krw: float = Field(100_000, gt=0)


class FinancialComparisonRequest(StrictModel):
    metropolitan: FinancialOption
    jeonbuk: FinancialOption
    assumptions: FinancialAssumptions = Field(default_factory=FinancialAssumptions)


class FinancialOptionResult(StrictModel):
    label: str
    monthly_surplus: float
    one_year_liquid_cash: float
    three_year_liquid_cash: float = Field(
        ..., description="Secondary, assumption-dependent projection using the named growth-rate assumptions."
    )
    deposit_locked: float
    one_year_total_with_deposit: float
    three_year_total_with_deposit: float


class CrossoverResult(StrictModel):
    varied_option: str
    comparison_option: str
    varied_variable: Literal["monthly_housing_cost"]
    current_value: float
    threshold_value: float
    rounding_unit_krw: float
    held_constant: Dict[str, float]
    interpretation: str


class FinancialComparison(StrictModel):
    assumptions: FinancialAssumptions
    options: Dict[str, FinancialOptionResult]
    crossover: CrossoverResult
    disclaimer: str
