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
    assert result["cost_saved"] == 0.0
    assert result["carbon_saved"] == 0.0
    # New normalised fields
    assert result["estimated_annual_kwh_saved"] == 0.0
    assert result["estimated_annual_saving_gbp"] == 0.0
    assert result["estimated_implementation_cost_gbp"] is None
    assert result["payback_years"] is None
    assert result["estimated_annual_co2_saved_tonnes"] == 0.0


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
    cost_saved_expected = kwh_saved_expected * electricity_rate
    carbon_saved_expected = (
        kwh_saved_expected * ELECTRICITY_CO2_FACTOR / 1000.0
    )  # tonnes

    assert _almost_equal(result["kwh_saved"], kwh_saved_expected)
    assert _almost_equal(result["cost_saved"], cost_saved_expected)
    assert _almost_equal(result["carbon_saved"], carbon_saved_expected)
    # Normalised fields mirror core values when implementation_cost_gbp is not provided.
    assert _almost_equal(result["estimated_annual_kwh_saved"], kwh_saved_expected)
    assert _almost_equal(result["estimated_annual_saving_gbp"], cost_saved_expected)
    assert result["estimated_implementation_cost_gbp"] is None
    assert result["payback_years"] is None
    assert _almost_equal(result["estimated_annual_co2_saved_tonnes"], carbon_saved_expected)

