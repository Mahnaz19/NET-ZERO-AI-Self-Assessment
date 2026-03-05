from __future__ import annotations

from dataclasses import dataclass, asdict

from .baseline import ELECTRICITY_CO2_FACTOR


@dataclass(frozen=True)
class LightingResult:
    kwh_saved: float
    annual_cost_saved_gbp: float
    annual_carbon_saved_kg: float
    simple_payback_years: float | None

    def to_dict(self) -> dict:
        return asdict(self)


def calculate_led_upgrade(
    fittings: int,
    old_watt: float,
    new_watt: float,
    annual_hours: float,
    electricity_rate: float,
    upgrade_cost_gbp: float | None = None,
) -> dict:
    """
    Deterministic LED lighting upgrade calculator.
    """
    if fittings < 0:
        raise ValueError("fittings must be non-negative")
    if old_watt < 0 or new_watt < 0:
        raise ValueError("wattages must be non-negative")
    if annual_hours < 0:
        raise ValueError("annual_hours must be non-negative")
    if electricity_rate < 0:
        raise ValueError("electricity_rate must be non-negative")
    if old_watt <= new_watt and fittings > 0 and annual_hours > 0:
        raise ValueError("old_watt must be greater than new_watt for an upgrade")

    watt_delta = max(old_watt - new_watt, 0.0)
    kwh_saved = (watt_delta * fittings * annual_hours) / 1000.0
    annual_cost_saved_gbp = kwh_saved * electricity_rate
    annual_carbon_saved_kg = kwh_saved * ELECTRICITY_CO2_FACTOR

    simple_payback_years: float | None = None
    if upgrade_cost_gbp is not None and annual_cost_saved_gbp > 0:
        simple_payback_years = upgrade_cost_gbp / annual_cost_saved_gbp

    result = LightingResult(
        kwh_saved=kwh_saved,
        annual_cost_saved_gbp=annual_cost_saved_gbp,
        annual_carbon_saved_kg=annual_carbon_saved_kg,
        simple_payback_years=simple_payback_years,
    )
    return result.to_dict()

