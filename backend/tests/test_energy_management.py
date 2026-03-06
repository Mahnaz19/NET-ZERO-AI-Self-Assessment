"""Tests for energy management calculator."""
from __future__ import annotations

import math
from backend.calculators import defaults
from backend.calculators.energy_management import calculate_energy_management_savings


def _close(a: float, b: float) -> bool:
    return math.isclose(a, b, rel_tol=1e-9)


def test_energy_management_zero():
    r = calculate_energy_management_savings(total_annual_kwh=0, savings_pct=0.05, electricity_rate=0.30)
    assert r["kwh_saved"] == 0
    assert r["cost_saved"] == 0
    assert r["carbon_saved"] == 0
    assert r["simple_payback"] is None


def test_energy_management_typical():
    total = 80_000.0
    savings = 0.05
    rate = 0.28
    r = calculate_energy_management_savings(total_annual_kwh=total, savings_pct=savings, electricity_rate=rate)
    expect_kwh = total * savings
    expect_cost = expect_kwh * rate
    expect_carbon = (expect_kwh * defaults.ELECTRICITY_CO2_FACTOR_KG_PER_KWH) / 1000.0
    assert _close(r["kwh_saved"], expect_kwh)
    assert _close(r["cost_saved"], expect_cost)
    assert _close(r["carbon_saved"], expect_carbon)
