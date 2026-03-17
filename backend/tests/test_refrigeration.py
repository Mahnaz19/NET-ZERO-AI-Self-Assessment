"""Tests for refrigeration calculator."""
from __future__ import annotations

import math
from backend.calculators import defaults
from backend.calculators.refrigeration import calculate_refrigeration


def _close(a: float, b: float) -> bool:
    return math.isclose(a, b, rel_tol=1e-9)


def test_refrigeration_zero_load():
    r = calculate_refrigeration(refrigeration_load_kwh=0, savings_pct=0.15, electricity_rate=0.30)
    assert r["kwh_saved"] == 0
    assert r["cost_saved"] == 0
    assert r["carbon_saved"] == 0
    assert r["simple_payback"] is None
    # Normalised fields
    assert r["estimated_annual_kwh_saved"] == 0
    assert r["estimated_annual_saving_gbp"] == 0
    assert r["estimated_implementation_cost_gbp"] is None
    assert r["payback_years"] is None
    assert r["estimated_annual_co2_saved_tonnes"] == 0


def test_refrigeration_typical_from_total_electric():
    total = 100_000.0
    pct = 0.35
    savings_pct = defaults.DEFAULT_REFRIG_SAVINGS_PCT
    rate = 0.28
    r = calculate_refrigeration(total_electric_kwh=total, assumed_pct_of_electric=pct, savings_pct=savings_pct, electricity_rate=rate)
    load = total * pct
    expect_kwh = load * savings_pct
    expect_cost = expect_kwh * rate
    expect_carbon = (expect_kwh * defaults.ELECTRICITY_CO2_FACTOR_KG_PER_KWH) / 1000.0
    assert _close(r["refrigeration_load_kwh"], load)
    assert _close(r["kwh_saved"], expect_kwh)
    assert _close(r["cost_saved"], expect_cost)
    assert _close(r["carbon_saved"], expect_carbon)
    # Normalised fields
    assert _close(r["estimated_annual_kwh_saved"], expect_kwh)
    assert _close(r["estimated_annual_saving_gbp"], expect_cost)
    assert r["estimated_implementation_cost_gbp"] is None
    assert r["payback_years"] is None
    assert _close(r["estimated_annual_co2_saved_tonnes"], expect_carbon)
