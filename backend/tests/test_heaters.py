"""Tests for heaters calculator."""
from __future__ import annotations

import math
from backend.calculators import defaults
from backend.calculators.heaters import calculate_heaters_replacement


def _close(a: float, b: float) -> bool:
    return math.isclose(a, b, rel_tol=1e-9)


def test_heaters_zero():
    r = calculate_heaters_replacement(annual_heater_kwh=0, savings_pct=0.20, electricity_rate=0.30)
    assert r["kwh_saved"] == 0
    assert r["cost_saved"] == 0
    assert r["carbon_saved"] == 0
    assert r["simple_payback"] is None


def test_heaters_typical():
    kwh = 8_000.0
    savings = 0.20
    rate = 0.28
    r = calculate_heaters_replacement(annual_heater_kwh=kwh, savings_pct=savings, electricity_rate=rate)
    expect_kwh = kwh * savings
    expect_cost = expect_kwh * rate
    expect_carbon = (expect_kwh * defaults.ELECTRICITY_CO2_FACTOR_KG_PER_KWH) / 1000.0
    assert _close(r["kwh_saved"], expect_kwh)
    assert _close(r["cost_saved"], expect_cost)
    assert _close(r["carbon_saved"], expect_carbon)
