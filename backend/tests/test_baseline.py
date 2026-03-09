from __future__ import annotations

import math

from backend.calculators.baseline import (
    ELECTRICITY_CO2_FACTOR,
    GAS_CO2_FACTOR,
    compute_baseline,
)


def _almost_equal(a: float, b: float, rel_tol: float = 1e-9) -> bool:
    return math.isclose(a, b, rel_tol=rel_tol, abs_tol=0.0)


def test_baseline_zero_consumption() -> None:
    result = compute_baseline(0.0, 0.0, 0.30, 0.05)
    assert result["electricity_cost"] == 0.0
    assert result["gas_cost"] == 0.0
    assert result["total_cost"] == 0.0
    assert result["electricity_co2"] == 0.0
    assert result["gas_co2"] == 0.0
    assert result["total_co2"] == 0.0


def test_baseline_electricity_only() -> None:
    electricity_kwh = 10_000.0
    electricity_rate = 0.30

    result = compute_baseline(electricity_kwh, 0.0, electricity_rate, 0.05)

    expected_elec_cost = electricity_kwh * electricity_rate
    expected_elec_co2 = electricity_kwh * ELECTRICITY_CO2_FACTOR

    assert _almost_equal(result["electricity_cost"], expected_elec_cost)
    assert result["gas_cost"] == 0.0
    assert _almost_equal(result["total_cost"], expected_elec_cost)
    assert _almost_equal(result["electricity_co2"], expected_elec_co2)
    assert result["gas_co2"] == 0.0
    assert _almost_equal(result["total_co2"], expected_elec_co2)


def test_baseline_gas_only() -> None:
    gas_kwh = 20_000.0
    gas_rate = 0.06

    result = compute_baseline(0.0, gas_kwh, 0.30, gas_rate)

    expected_gas_cost = gas_kwh * gas_rate
    expected_gas_co2 = gas_kwh * GAS_CO2_FACTOR

    assert result["electricity_cost"] == 0.0
    assert _almost_equal(result["gas_cost"], expected_gas_cost)
    assert _almost_equal(result["total_cost"], expected_gas_cost)
    assert result["electricity_co2"] == 0.0
    assert _almost_equal(result["gas_co2"], expected_gas_co2)
    assert _almost_equal(result["total_co2"], expected_gas_co2)


def test_baseline_mixed_consumption() -> None:
    electricity_kwh = 12_500.0
    gas_kwh = 30_000.0
    electricity_rate = 0.28
    gas_rate = 0.07

    result = compute_baseline(electricity_kwh, gas_kwh, electricity_rate, gas_rate)

    expected_elec_cost = electricity_kwh * electricity_rate
    expected_gas_cost = gas_kwh * gas_rate
    expected_total_cost = expected_elec_cost + expected_gas_cost

    expected_elec_co2 = electricity_kwh * ELECTRICITY_CO2_FACTOR
    expected_gas_co2 = gas_kwh * GAS_CO2_FACTOR
    expected_total_co2 = expected_elec_co2 + expected_gas_co2

    assert _almost_equal(result["electricity_cost"], expected_elec_cost)
    assert _almost_equal(result["gas_cost"], expected_gas_cost)
    assert _almost_equal(result["total_cost"], expected_total_cost)
    assert _almost_equal(result["electricity_co2"], expected_elec_co2)
    assert _almost_equal(result["gas_co2"], expected_gas_co2)
    assert _almost_equal(result["total_co2"], expected_total_co2)


def test_baseline_realistic_small_site() -> None:
    """
    A simple realistic scenario for a small SME site.
    """
    electricity_kwh = 8_000.0
    gas_kwh = 15_000.0
    electricity_rate = 0.32
    gas_rate = 0.055

    result = compute_baseline(electricity_kwh, gas_kwh, electricity_rate, gas_rate)

    # Spot-check some key ratios rather than exact pennies.
    assert result["total_cost"] > 0.0
    assert result["total_co2"] > 0.0
    assert result["electricity_co2"] > result["gas_co2"] * 0.5
    assert _almost_equal(
        result["electricity_cost"] + result["gas_cost"],
        result["total_cost"],
    )

