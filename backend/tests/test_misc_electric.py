"""Tests for misc electric calculator."""
from __future__ import annotations

import math
from backend.calculators import defaults
from backend.calculators.misc_electric import calculate_misc_electric


def _close(a: float, b: float) -> bool:
    return math.isclose(a, b, rel_tol=1e-9)


def test_misc_electric_zero_total():
    r = calculate_misc_electric(total_electric_kwh=0, estimated_pct_of_total=0.10, savings_pct=0.15, electricity_rate=0.30, cost=None)
    assert r["estimated_load_kwh"] == 0
    assert r["kwh_saved"] == 0
    assert r["cost_saved"] == 0
    assert r["carbon_saved"] == 0
    assert r["simple_payback"] is None
    assert r["estimated_annual_kwh_saved"] == 0
    assert r["estimated_annual_saving_gbp"] == 0
    assert r["estimated_implementation_cost_gbp"] is None
    assert r["payback_years"] is None
    assert r["estimated_annual_co2_saved_tonnes"] == 0


def test_misc_electric_typical():
    total = 60_000.0
    pct_est = 0.10
    pct_sav = 0.15
    rate = 0.28
    cost = 1_500.0
    r = calculate_misc_electric(total_electric_kwh=total, estimated_pct_of_total=pct_est, savings_pct=pct_sav, electricity_rate=rate, cost=cost)
    load = total * pct_est
    expect_kwh = load * pct_sav
    expect_cost = expect_kwh * rate
    expect_carbon = (expect_kwh * defaults.ELECTRICITY_CO2_FACTOR_KG_PER_KWH) / 1000.0
    assert _close(r["estimated_load_kwh"], load)
    assert _close(r["kwh_saved"], expect_kwh)
    assert _close(r["cost_saved"], expect_cost)
    assert _close(r["carbon_saved"], expect_carbon)
    assert _close(r["estimated_annual_kwh_saved"], expect_kwh)
    assert _close(r["estimated_annual_saving_gbp"], expect_cost)
    assert _close(r["estimated_implementation_cost_gbp"], cost)
    assert _close(r["payback_years"], cost / expect_cost)
    assert _close(r["estimated_annual_co2_saved_tonnes"], expect_carbon)
