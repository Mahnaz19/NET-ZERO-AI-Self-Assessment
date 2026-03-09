"""Tests for heat pump calculator."""
from __future__ import annotations

import math
from backend.calculators import defaults
from backend.calculators.heatpump import calculate_heatpump_replacement


def _close(a: float, b: float) -> bool:
    return math.isclose(a, b, rel_tol=1e-9)


def test_heatpump_zero_gas():
    r = calculate_heatpump_replacement(annual_gas_kwh=0, cop=3.0)
    assert r["heating_kwh"] == 0
    assert r["heatpump_elec_kwh"] == 0
    assert r["gas_kwh_saved"] == 0
    assert r["electricity_kwh_added"] == 0
    assert r["simple_payback"] is None


def test_heatpump_typical():
    gas = 30_000.0
    cop = 3.0
    gas_rate = 0.06
    elec_rate = 0.28
    r = calculate_heatpump_replacement(annual_gas_kwh=gas, fraction_heating_covered=1.0, cop=cop, gas_rate=gas_rate, electricity_rate=elec_rate)
    heating = gas
    elec_kwh = heating / cop
    expect_cost_delta = elec_kwh * elec_rate - heating * gas_rate
    assert _close(r["heating_kwh"], heating)
    assert _close(r["heatpump_elec_kwh"], elec_kwh)
    assert _close(r["cost_delta"], expect_cost_delta)
