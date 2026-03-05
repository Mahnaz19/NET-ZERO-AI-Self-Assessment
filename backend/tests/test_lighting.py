from __future__ import annotations

import math

from backend.calculators.baseline import ELECTRICITY_CO2_FACTOR
from backend.calculators.lighting import calculate_led_upgrade


def _almost_equal(a: float, b: float, rel_tol: float = 1e-9) -> bool:
    return math.isclose(a, b, rel_tol=rel_tol, abs_tol=0.0)


def test_lighting_zero_fittings() -> None:
    result = calculate_led_upgrade(
        fittings=0,
        old_watt=60.0,
        new_watt=10.0,
        annual_hours=2000.0,
        electricity_rate=0.30,
    )
    assert result["kwh_saved"] == 0.0
    assert result["annual_cost_saved_gbp"] == 0.0
    assert result["annual_carbon_saved_kg"] == 0.0
    assert result["simple_payback_years"] is None


def test_lighting_typical_upgrade() -> None:
    fittings = 50
    old_watt = 60.0
    new_watt = 10.0
    annual_hours = 2500.0
    electricity_rate = 0.28

    result = calculate_led_upgrade(
        fittings=fittings,
        old_watt=old_watt,
        new_watt=new_watt,
        annual_hours=annual_hours,
        electricity_rate=electricity_rate,
    )

    watt_delta = old_watt - new_watt
    kwh_saved_expected = (watt_delta * fittings * annual_hours) / 1000.0
    annual_cost_saved_expected = kwh_saved_expected * electricity_rate
    annual_carbon_saved_expected = kwh_saved_expected * ELECTRICITY_CO2_FACTOR

    assert _almost_equal(result["kwh_saved"], kwh_saved_expected)
    assert _almost_equal(result["annual_cost_saved_gbp"], annual_cost_saved_expected)
    assert _almost_equal(result["annual_carbon_saved_kg"], annual_carbon_saved_expected)


def test_lighting_upgrade_with_payback() -> None:
    fittings = 40
    old_watt = 50.0
    new_watt = 12.0
    annual_hours = 3000.0
    electricity_rate = 0.30
    upgrade_cost_gbp = 4_000.0

    result = calculate_led_upgrade(
        fittings=fittings,
        old_watt=old_watt,
        new_watt=new_watt,
        annual_hours=annual_hours,
        electricity_rate=electricity_rate,
        upgrade_cost_gbp=upgrade_cost_gbp,
    )

    watt_delta = old_watt - new_watt
    kwh_saved_expected = (watt_delta * fittings * annual_hours) / 1000.0
    annual_cost_saved_expected = kwh_saved_expected * electricity_rate
    expected_payback = upgrade_cost_gbp / annual_cost_saved_expected

    assert _almost_equal(result["kwh_saved"], kwh_saved_expected)
    assert _almost_equal(result["annual_cost_saved_gbp"], annual_cost_saved_expected)
    assert result["simple_payback_years"] is not None
    assert _almost_equal(result["simple_payback_years"], expected_payback)

