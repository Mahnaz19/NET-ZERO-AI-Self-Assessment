"""Tests for cooling calculator."""
from __future__ import annotations

import math
from backend.calculators import defaults
from backend.calculators.cooling import calculate_cooling_upgrade


def _close(a: float, b: float) -> bool:
    return math.isclose(a, b, rel_tol=1e-9)


def test_cooling_zero_load():
    r = calculate_cooling_upgrade(annual_cooling_kwh=0, savings_pct=0.15, electricity_rate=0.30, cost=None)
    assert r["kwh_saved"] == 0
    assert r["cost_saved"] == 0
    assert r["carbon_saved"] == 0
    assert r["simple_payback"] is None
    assert r["estimated_annual_kwh_saved"] == 0
    assert r["estimated_annual_saving_gbp"] == 0
    assert r["estimated_implementation_cost_gbp"] is None
    assert r["payback_years"] is None
    assert r["estimated_annual_co2_saved_tonnes"] == 0


def test_cooling_typical_from_total():
    total = 50_000.0
    assumed = 0.10
    savings = 0.15
    rate = 0.28
    cost = 3_000.0
    r = calculate_cooling_upgrade(total_electric_kwh=total, assumed_pct=assumed, savings_pct=savings, electricity_rate=rate, cost=cost)
    load = total * assumed
    expect_kwh = load * savings
    expect_cost = expect_kwh * rate
    expect_carbon = (expect_kwh * defaults.ELECTRICITY_CO2_FACTOR_KG_PER_KWH) / 1000.0
    assert _close(r["cooling_load_kwh"], load)
    assert _close(r["kwh_saved"], expect_kwh)
    assert _close(r["cost_saved"], expect_cost)
    assert _close(r["carbon_saved"], expect_carbon)
    assert _close(r["estimated_annual_kwh_saved"], expect_kwh)
    assert _close(r["estimated_annual_saving_gbp"], expect_cost)
    assert _close(r["estimated_implementation_cost_gbp"], cost)
    assert _close(r["payback_years"], cost / expect_cost)
    assert _close(r["estimated_annual_co2_saved_tonnes"], expect_carbon)
