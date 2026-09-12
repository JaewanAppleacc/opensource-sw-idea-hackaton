"""Deterministic financial-comparison calculator. No LLM involvement.

The deposit is locked wealth, never counted as consumption or folded
silently into liquid-cash totals. The crossover variable is always
monthly_housing_cost on the option that currently has the lower value
(never income -- varying income is a tautology and gives the user nothing
to go verify). The threshold is rounded to a sensible unit so it reads as
"go check whether housing here could realistically exceed ~X", not a raw
float.
"""
from __future__ import annotations

import math

from ..models.finance import (
    CrossoverResult,
    FinancialAssumptions,
    FinancialComparison,
    FinancialComparisonRequest,
    FinancialOption,
    FinancialOptionResult,
)

DISCLAIMER = (
    "This is a hypothetical, assumption-dependent cash comparison based only on the numbers you entered. "
    "It is not financial advice and does not recommend one option over the other."
)


def _monthly_surplus(option: FinancialOption) -> float:
    return option.monthly_income_after_tax - option.monthly_housing_cost - option.monthly_other_living_cost


def _three_year_liquid_cash(option: FinancialOption, assumptions: FinancialAssumptions) -> float:
    income = option.monthly_income_after_tax
    costs = option.monthly_housing_cost + option.monthly_other_living_cost
    total = 0.0
    for _year in range(3):
        total += (income - costs) * 12
        income *= 1 + assumptions.annual_income_growth_rate
        costs *= 1 + assumptions.annual_cost_growth_rate
    return total


def _round_to_unit(value: float, unit: float) -> float:
    return math.floor(value / unit + 0.5) * unit


def _build_option_result(option: FinancialOption, assumptions: FinancialAssumptions) -> FinancialOptionResult:
    surplus = _monthly_surplus(option)
    one_year = surplus * 12
    three_year = _three_year_liquid_cash(option, assumptions)
    return FinancialOptionResult(
        label=option.label,
        monthly_surplus=round(surplus, 2),
        one_year_liquid_cash=round(one_year, 2),
        three_year_liquid_cash=round(three_year, 2),
        deposit_locked=option.deposit,
        one_year_total_with_deposit=round(one_year + option.deposit, 2),
        three_year_total_with_deposit=round(three_year + option.deposit, 2),
    )


def _compute_crossover(
    metropolitan: FinancialOption, jeonbuk: FinancialOption, assumptions: FinancialAssumptions
) -> CrossoverResult:
    options = {"metropolitan": metropolitan, "jeonbuk": jeonbuk}
    # Lower current housing cost is the option whose headroom is worth checking.
    # Ties resolve to "jeonbuk" (stable, deterministic sort key).
    varied_label = min(options, key=lambda label: (options[label].monthly_housing_cost, label))
    comparison_label = "jeonbuk" if varied_label == "metropolitan" else "metropolitan"

    varied = options[varied_label]
    comparison = options[comparison_label]
    comparison_surplus = _monthly_surplus(comparison)

    # Solve varied.income - x - varied.other == comparison_surplus for x.
    raw_threshold = varied.monthly_income_after_tax - varied.monthly_other_living_cost - comparison_surplus
    threshold = _round_to_unit(raw_threshold, assumptions.rounding_unit_krw)

    held_constant = {
        f"{varied_label}.monthly_income_after_tax": varied.monthly_income_after_tax,
        f"{varied_label}.monthly_other_living_cost": varied.monthly_other_living_cost,
        f"{comparison_label}.monthly_income_after_tax": comparison.monthly_income_after_tax,
        f"{comparison_label}.monthly_housing_cost": comparison.monthly_housing_cost,
        f"{comparison_label}.monthly_other_living_cost": comparison.monthly_other_living_cost,
    }

    return CrossoverResult(
        varied_option=varied_label,
        comparison_option=comparison_label,
        varied_variable="monthly_housing_cost",
        current_value=varied.monthly_housing_cost,
        threshold_value=threshold,
        rounding_unit_krw=assumptions.rounding_unit_krw,
        held_constant=held_constant,
        interpretation=(
            f"If {varied_label}'s monthly housing+maintenance cost rose to about {threshold:,.0f} KRW "
            f"(from {varied.monthly_housing_cost:,.0f} KRW today), its monthly surplus would no longer "
            f"exceed {comparison_label}'s, holding every other entered value constant. Worth verifying "
            "actual housing cost against this threshold before deciding."
        ),
    )


def compare_financials(request: FinancialComparisonRequest) -> FinancialComparison:
    metro_result = _build_option_result(request.metropolitan, request.assumptions)
    jeonbuk_result = _build_option_result(request.jeonbuk, request.assumptions)
    crossover = _compute_crossover(request.metropolitan, request.jeonbuk, request.assumptions)
    return FinancialComparison(
        assumptions=request.assumptions,
        options={"metropolitan": metro_result, "jeonbuk": jeonbuk_result},
        crossover=crossover,
        disclaimer=DISCLAIMER,
    )
