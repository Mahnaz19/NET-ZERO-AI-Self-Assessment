from __future__ import annotations

import math

from backend.calculators.baseline import GAS_CO2_FACTOR
from backend.calculators.boiler import calculate_boiler_upgrade


def _almost_equal(a: float, b: float, rel_tol: float = 1e-9) -> bool:
    return math.isclose(a, b, rel_tol=rel_tol, abs_tol=0.0)


def test_boiler_zero_usage() -> None:
    result = calculate_boiler_upgrade(annual_gas_kwh=0.0)
    assert result["kwh_saved"] == 0.0
    assert result["cost_saved"] == 0.0
    assert result["carbon_saved"] == 0.0
    assert result["simple_payback"] is None


def test_boiler_upgrade_with_cost_and_defaults() -> None:
    annual_gas_kwh = 40_000.0
    efficiency_improvement = 0.20
    gas_rate = 0.06
    cost = 20_000.0

    result = calculate_boiler_upgrade(
        annual_gas_kwh=annual_gas_kwh,
        efficiency_improvement=efficiency_improvement,
        gas_rate=gas_rate,
        cost=cost,
    )

    kwh_saved_expected = annual_gas_kwh * efficiency_improvement
    cost_saved_expected = kwh_saved_expected * gas_rate
    carbon_saved_expected = kwh_saved_expected * GAS_CO2_FACTOR / 1000.0
    simple_payback_expected = cost / cost_saved_expected

    assert _almost_equal(result["kwh_saved"], kwh_saved_expected)
    assert _almost_equal(result["cost_saved"], cost_saved_expected)
    assert _almost_equal(result["carbon_saved"], carbon_saved_expected)
    assert result["simple_payback"] is not None
    assert _almost_equal(result["simple_payback"], simple_payback_expected)

