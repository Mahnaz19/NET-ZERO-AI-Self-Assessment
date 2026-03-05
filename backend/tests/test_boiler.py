from __future__ import annotations

import math

from backend.calculators.baseline import GAS_CO2_FACTOR
from backend.calculators.boiler import calculate_boiler_upgrade


def _almost_equal(a: float, b: float, rel_tol: float = 1e-9) -> bool:
    return math.isclose(a, b, rel_tol=rel_tol, abs_tol=0.0)


def test_boiler_zero_usage() -> None:
    result = calculate_boiler_upgrade(annual_gas_kwh=0.0)
    assert result["kwh_saved"] == 0.0
    assert result["annual_cost_saved_gbp"] == 0.0
    assert result["annual_carbon_saved_kg"] == 0.0
    assert result["simple_payback_years"] is None


def test_boiler_typical_upgrade_default_params() -> None:
    annual_gas_kwh = 40_000.0
    efficiency_improvement = 0.20
    gas_rate = 0.06

    result = calculate_boiler_upgrade(
        annual_gas_kwh=annual_gas_kwh,
        efficiency_improvement=efficiency_improvement,
        gas_rate=gas_rate,
    )

    kwh_saved_expected = annual_gas_kwh * efficiency_improvement
    annual_cost_saved_expected = kwh_saved_expected * gas_rate
    annual_carbon_saved_expected = kwh_saved_expected * GAS_CO2_FACTOR

    assert _almost_equal(result["kwh_saved"], kwh_saved_expected)
    assert _almost_equal(result["annual_cost_saved_gbp"], annual_cost_saved_expected)
    assert _almost_equal(result["annual_carbon_saved_kg"], annual_carbon_saved_expected)


def test_boiler_upgrade_with_payback() -> None:
    annual_gas_kwh = 60_000.0
    efficiency_improvement = 0.18
    gas_rate = 0.055
    upgrade_cost_gbp = 15_000.0

    result = calculate_boiler_upgrade(
        annual_gas_kwh=annual_gas_kwh,
        efficiency_improvement=efficiency_improvement,
        gas_rate=gas_rate,
        upgrade_cost_gbp=upgrade_cost_gbp,
    )

    kwh_saved_expected = annual_gas_kwh * efficiency_improvement
    annual_cost_saved_expected = kwh_saved_expected * gas_rate
    expected_payback = upgrade_cost_gbp / annual_cost_saved_expected

    assert _almost_equal(result["kwh_saved"], kwh_saved_expected)
    assert _almost_equal(result["annual_cost_saved_gbp"], annual_cost_saved_expected)
    assert result["simple_payback_years"] is not None
    assert _almost_equal(result["simple_payback_years"], expected_payback)

