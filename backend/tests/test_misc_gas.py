"""Tests for misc gas calculator."""
from __future__ import annotations

import math
from backend.calculators import defaults
from backend.calculators.misc_gas import calculate_misc_gas


def _close(a: float, b: float) -> bool:
    return math.isclose(a, b, rel_tol=1e-9)


def test_misc_gas_zero_total():
    r = calculate_misc_gas(total_gas_kwh=0, estimated_pct_of_total=0.10, savings_pct=0.15, gas_rate=0.06)
    assert r["estimated_load_kwh"] == 0
    assert r["kwh_saved"] == 0
    assert r["cost_saved"] == 0
    assert r["carbon_saved"] == 0
    assert r["simple_payback"] is None


def test_misc_gas_typical():
    total = 40_000.0
    pct_est = 0.10
    pct_sav = 0.15
    rate = 0.06
    r = calculate_misc_gas(total_gas_kwh=total, estimated_pct_of_total=pct_est, savings_pct=pct_sav, gas_rate=rate)
    load = total * pct_est
    expect_kwh = load * pct_sav
    expect_cost = expect_kwh * rate
    expect_carbon = (expect_kwh * defaults.GAS_CO2_FACTOR_KG_PER_KWH) / 1000.0
    assert _close(r["estimated_load_kwh"], load)
    assert _close(r["kwh_saved"], expect_kwh)
    assert _close(r["cost_saved"], expect_cost)
    assert _close(r["carbon_saved"], expect_carbon)
