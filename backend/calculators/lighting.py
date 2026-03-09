from __future__ import annotations

from dataclasses import dataclass, asdict

from .baseline import ELECTRICITY_CO2_FACTOR


@dataclass(frozen=True)
class LightingResult:
    kwh_saved: float
    cost_saved: float
    carbon_saved: float

    def to_dict(self) -> dict:
        return asdict(self)


def calculate_led_upgrade(
    fittings: int,
    old_watt: float,
    new_watt: float,
    annual_hours: float,
    electricity_rate: float,
) -> dict:
    """
    Deterministic LED lighting upgrade calculator.

    Args:
        fittings: Number of luminaires.
        old_watt: Pre-upgrade lamp wattage.
        new_watt: Post-upgrade lamp wattage.
        annual_hours: Annual operating hours.
        electricity_rate: Import rate in £/kWh.
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
    cost_saved = kwh_saved * electricity_rate
    # ELECTRICITY_CO2_FACTOR is in kgCO2e/kWh; convert to tonnes.
    carbon_saved_tonnes = (kwh_saved * ELECTRICITY_CO2_FACTOR) / 1000.0

    result = LightingResult(
        kwh_saved=kwh_saved,
        cost_saved=cost_saved,
        carbon_saved=carbon_saved_tonnes,
    )
    return result.to_dict()

