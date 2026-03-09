"""Deterministic cooling upgrade calculator."""
from __future__ import annotations

from dataclasses import dataclass, asdict

from . import defaults


@dataclass(frozen=True)
class CoolingResult:
    cooling_load_kwh: float
    kwh_saved: float
    cost_saved: float
    carbon_saved: float
    simple_payback: float | None
    assumptions: list[str]

    def to_dict(self) -> dict:
        return asdict(self)


def calculate_cooling_upgrade(
    annual_cooling_kwh: float | None = None,
    total_electric_kwh: float | None = None,
    assumed_pct: float = 0.10,
    savings_pct: float = 0.15,
    electricity_rate: float = 0.30,
    cost: float | None = None,
) -> dict:
    """If annual_cooling_kwh not given, estimate as total_electric_kwh * assumed_pct. Then kwh_saved = load * savings_pct."""
    if assumed_pct < 0 or assumed_pct > 1 or savings_pct < 0 or savings_pct > 1:
        raise ValueError("assumed_pct and savings_pct must be between 0 and 1")
    if electricity_rate < 0:
        raise ValueError("electricity_rate must be non-negative")
    if cost is not None and cost < 0:
        raise ValueError("cost must be non-negative when provided")

    if annual_cooling_kwh is not None:
        load = max(0.0, annual_cooling_kwh)
        assumptions = ["annual_cooling_kwh provided"]
    elif total_electric_kwh is not None and total_electric_kwh >= 0:
        load = total_electric_kwh * assumed_pct
        assumptions = [f"cooling estimated as {assumed_pct:.0%} of total electricity", f"savings_pct={savings_pct:.0%}"]
    else:
        raise ValueError("Provide either annual_cooling_kwh or total_electric_kwh")

    kwh_saved = load * savings_pct
    cost_saved = kwh_saved * electricity_rate
    carbon_saved_tonnes = (kwh_saved * defaults.ELECTRICITY_CO2_FACTOR_KG_PER_KWH) / 1000.0

    simple_payback: float | None = None
    if cost is not None and cost_saved > 0:
        simple_payback = cost / cost_saved

    return CoolingResult(
        cooling_load_kwh=load,
        kwh_saved=kwh_saved,
        cost_saved=cost_saved,
        carbon_saved=carbon_saved_tonnes,
        simple_payback=simple_payback,
        assumptions=assumptions,
    ).to_dict()
