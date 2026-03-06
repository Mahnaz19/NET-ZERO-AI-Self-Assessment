"""Tests for building fabric calculator."""
from __future__ import annotations

import math
from backend.calculators import defaults
from backend.calculators.building_fabric import calculate_building_fabric_improvement


def _close(a: float, b: float) -> bool:
    return math.isclose(a, b, rel_tol=1e-9)


def test_building_fabric_zero_heating():
    r = calculate_building_fabric_improvement(annual_heating_kwh=0, improvement_pct=0.12, fuel_rate=0.06)
    assert r["kwh_saved"] == 0
    assert r["cost_saved"] == 0
    assert r["carbon_saved"] == 0
    assert r["simple_payback"] is None


def test_building_fabric_typical():
    heating = 25_000.0
    pct = defaults.DEFAULT_INSULATION_SAVINGS_PCT
    rate = 0.06
    r = calculate_building_fabric_improvement(annual_heating_kwh=heating, improvement_pct=pct, fuel_rate=rate)
    expect_kwh = heating * pct
    expect_cost = expect_kwh * rate
    expect_carbon = (expect_kwh * defaults.GAS_CO2_FACTOR_KG_PER_KWH) / 1000.0
    assert _close(r["kwh_saved"], expect_kwh)
    assert _close(r["cost_saved"], expect_cost)
    assert _close(r["carbon_saved"], expect_carbon)
