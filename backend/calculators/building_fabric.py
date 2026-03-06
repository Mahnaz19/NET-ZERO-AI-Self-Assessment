"""Deterministic building fabric / insulation improvement calculator."""
from __future__ import annotations

from dataclasses import dataclass, asdict

from . import defaults


@dataclass(frozen=True)
class BuildingFabricResult:
    kwh_saved: float
    cost_saved: float
    carbon_saved: float
    simple_payback: float | None
    assumptions: list[str]

    def to_dict(self) -> dict:
        return asdict(self)


def calculate_building_fabric_improvement(
    annual_heating_kwh: float,
    improvement_pct: float = defaults.DEFAULT_INSULATION_SAVINGS_PCT,
    cost: float | None = None,
    fuel_rate: float = 0.06,
) -> dict:
    """kwh_saved = annual_heating_kwh * improvement_pct; cost_saved, carbon_saved, payback."""
    if annual_heating_kwh < 0:
        raise ValueError("annual_heating_kwh must be non-negative")
    if improvement_pct < 0 or improvement_pct > 1:
        raise ValueError("improvement_pct must be between 0 and 1")
    if fuel_rate < 0:
        raise ValueError("fuel_rate must be non-negative")
    if cost is not None and cost < 0:
        raise ValueError("cost must be non-negative when provided")

    kwh_saved = annual_heating_kwh * improvement_pct
    cost_saved = kwh_saved * fuel_rate
    carbon_saved_tonnes = (kwh_saved * defaults.GAS_CO2_FACTOR_KG_PER_KWH) / 1000.0

    simple_payback: float | None = None
    if cost is not None and cost_saved > 0:
        simple_payback = cost / cost_saved

    return BuildingFabricResult(
        kwh_saved=kwh_saved,
        cost_saved=cost_saved,
        carbon_saved=carbon_saved_tonnes,
        simple_payback=simple_payback,
        assumptions=[f"improvement_pct={improvement_pct:.0%}", f"fuel_rate=£{fuel_rate}/kWh"],
    ).to_dict()
