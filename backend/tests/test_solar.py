from __future__ import annotations

import math

from backend.calculators.baseline import ELECTRICITY_CO2_FACTOR
from backend.calculators.solar import calculate_solar


def _almost_equal(a: float, b: float, rel_tol: float = 1e-9) -> bool:
    return math.isclose(a, b, rel_tol=rel_tol, abs_tol=0.0)


def test_solar_zero_system_kwp() -> None:
    result = calculate_solar(system_kwp=0.0)
    assert result["annual_generation"] == 0.0
    assert result["self_consumed_kwh"] == 0.0
    assert result["exported_kwh"] == 0.0
    assert result["annual_savings"] == 0.0
    assert result["carbon_saving"] == 0.0
    assert result["simple_payback"] is None


def test_solar_typical_system_defaults_with_cost() -> None:
    system_kwp = 10.0
    cost = 12_000.0

    result = calculate_solar(system_kwp=system_kwp, cost=cost)

    annual_generation_expected = system_kwp * 900 * 0.92
    self_consumed_expected = annual_generation_expected * 0.75
    exported_expected = annual_generation_expected - self_consumed_expected

    annual_savings_expected = (
        self_consumed_expected * 0.30 + exported_expected * 0.06
    )
    carbon_tonnes_expected = (
        annual_generation_expected * ELECTRICITY_CO2_FACTOR / 1000.0
    )
    simple_payback_expected = cost / annual_savings_expected

    assert _almost_equal(result["annual_generation"], annual_generation_expected)
    assert _almost_equal(result["self_consumed_kwh"], self_consumed_expected)
    assert _almost_equal(result["exported_kwh"], exported_expected)
    assert _almost_equal(result["annual_savings"], annual_savings_expected)
    assert _almost_equal(result["carbon_saving"], carbon_tonnes_expected)
    assert result["simple_payback"] is not None
    assert _almost_equal(result["simple_payback"], simple_payback_expected)


def test_solar_custom_rates_and_parameters_no_cost() -> None:
    system_kwp = 5.0
    orientation_factor = 0.85
    generation_factor = 950
    self_consumption_rate = 0.8
    electricity_rate = 0.27
    export_rate = 0.07

    result = calculate_solar(
        system_kwp=system_kwp,
        orientation_factor=orientation_factor,
        generation_factor=generation_factor,
        self_consumption_rate=self_consumption_rate,
        electricity_rate=electricity_rate,
        export_rate=export_rate,
    )

    annual_generation_expected = system_kwp * generation_factor * orientation_factor
    self_consumed_expected = annual_generation_expected * self_consumption_rate
    exported_expected = annual_generation_expected - self_consumed_expected

    annual_savings_expected = (
        self_consumed_expected * electricity_rate + exported_expected * export_rate
    )
    carbon_tonnes_expected = (
        annual_generation_expected * ELECTRICITY_CO2_FACTOR / 1000.0
    )

    assert _almost_equal(result["annual_generation"], annual_generation_expected)
    assert _almost_equal(result["self_consumed_kwh"], self_consumed_expected)
    assert _almost_equal(result["exported_kwh"], exported_expected)
    assert _almost_equal(result["annual_savings"], annual_savings_expected)
    assert _almost_equal(result["carbon_saving"], carbon_tonnes_expected)
    assert result["simple_payback"] is None

