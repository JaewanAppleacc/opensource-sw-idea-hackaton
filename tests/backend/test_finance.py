from __future__ import annotations

from app.models.finance import FinancialAssumptions, FinancialComparisonRequest, FinancialOption
from app.services.finance import compare_financials


def _make_request(**overrides) -> FinancialComparisonRequest:
    metro = FinancialOption(
        label="metropolitan",
        monthly_income_after_tax=3_200_000,
        monthly_housing_cost=900_000,
        monthly_other_living_cost=700_000,
        deposit=50_000_000,
    )
    jeonbuk = FinancialOption(
        label="jeonbuk",
        monthly_income_after_tax=2_700_000,
        monthly_housing_cost=400_000,
        monthly_other_living_cost=600_000,
        deposit=10_000_000,
    )
    return FinancialComparisonRequest(
        metropolitan=overrides.get("metropolitan", metro),
        jeonbuk=overrides.get("jeonbuk", jeonbuk),
        assumptions=overrides.get("assumptions", FinancialAssumptions()),
    )


def test_monthly_surplus_is_deterministic_arithmetic():
    result = compare_financials(_make_request())
    assert result.options["metropolitan"].monthly_surplus == 3_200_000 - 900_000 - 700_000
    assert result.options["jeonbuk"].monthly_surplus == 2_700_000 - 400_000 - 600_000


def test_one_year_liquid_cash_is_surplus_times_twelve():
    result = compare_financials(_make_request())
    metro = result.options["metropolitan"]
    assert metro.one_year_liquid_cash == metro.monthly_surplus * 12


def test_repeated_calls_are_deterministic():
    request = _make_request()
    first = compare_financials(request)
    second = compare_financials(request)
    assert first.model_dump() == second.model_dump()


def test_deposit_is_not_counted_as_consumption():
    result = compare_financials(_make_request())
    jeonbuk = result.options["jeonbuk"]
    # Liquid cash must exclude the deposit entirely...
    assert jeonbuk.one_year_liquid_cash == jeonbuk.monthly_surplus * 12
    # ...while the deposit is still surfaced, kept separate, and labeled as locked wealth.
    assert jeonbuk.deposit_locked == 10_000_000
    assert jeonbuk.one_year_total_with_deposit == jeonbuk.one_year_liquid_cash + jeonbuk.deposit_locked


def test_crossover_varies_housing_on_lower_cost_option_not_income():
    result = compare_financials(_make_request())
    crossover = result.crossover
    assert crossover.varied_variable == "monthly_housing_cost"
    # jeonbuk has the lower current housing cost (400,000 < 900,000).
    assert crossover.varied_option == "jeonbuk"
    assert crossover.comparison_option == "metropolitan"


def test_crossover_threshold_is_rounded_to_configured_unit():
    result = compare_financials(_make_request())
    crossover = result.crossover
    # jeonbuk surplus 1,700,000 vs metro surplus 1,600,000 -> raw threshold is exactly 500,000.
    assert crossover.threshold_value == 500_000
    assert crossover.rounding_unit_krw == 100_000
    assert crossover.threshold_value % crossover.rounding_unit_krw == 0


def test_crossover_threshold_actually_equalizes_surplus():
    request = _make_request()
    result = compare_financials(request)
    crossover = result.crossover

    varied_option = request.jeonbuk if crossover.varied_option == "jeonbuk" else request.metropolitan
    comparison_result = result.options[crossover.comparison_option]

    surplus_at_threshold = (
        varied_option.monthly_income_after_tax - crossover.threshold_value - varied_option.monthly_other_living_cost
    )
    assert surplus_at_threshold == comparison_result.monthly_surplus


def test_no_winner_is_declared_anywhere_in_the_response():
    result = compare_financials(_make_request())
    dumped = result.model_dump_json()
    assert "does not recommend" in dumped  # the disclaimer explicitly disclaims a winner
    for banned in ("winner", "better option", "we recommend", "승자", "추천합니다"):
        assert banned not in dumped


def test_three_year_scenario_uses_named_growth_assumptions():
    flat = compare_financials(_make_request())
    growing = compare_financials(
        _make_request(assumptions=FinancialAssumptions(annual_income_growth_rate=0.05, annual_cost_growth_rate=0.0))
    )
    # Same 1-year figure (assumption-light), different 3-year figure (assumption-dependent).
    assert flat.options["jeonbuk"].one_year_liquid_cash == growing.options["jeonbuk"].one_year_liquid_cash
    assert flat.options["jeonbuk"].three_year_liquid_cash != growing.options["jeonbuk"].three_year_liquid_cash
