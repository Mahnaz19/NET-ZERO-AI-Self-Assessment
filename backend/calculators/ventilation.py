"""Deterministic ventilation improvement calculator."""
from __future__ import annotations

from dataclasses import dataclass, asdict

from . import defaults


@dataclass(frozen=True)
class VentilationResult:
    annual_kwh: float
    kwh_saved: float
    cost_saved: float
    carbon_saved: float
    simple_payback: float | None
    assumptions: list[str]

    def to_dict(self) -> dict:
        return asdict(self)


def calculate_ventilation_improvement(
    fan_power_kw: float | None,
    annual_hours: float = 2000,
    savings_pct: float = 0.20,
    electricity_rate: float = 0.30,
    cost: float | None = None,
) -> dict:
    """annual_kwh = fan_power_kw * annual_hours; kwh_saved = annual_kwh * savings_pct."""
    if fan_power_kw is None or fan_power_kw < 0:
        raise ValueError("fan_power_kw must be non-negative")
    if annual_hours < 0:
        raise ValueError("annual_hours must be non-negative")
    if savings_pct < 0 or savings_pct > 1:
        raise ValueError("savings_pct must be between 0 and 1")
    if electricity_rate < 0:
        raise ValueError("electricity_rate must be non-negative")
    if cost is not None and cost < 0:
        raise ValueError("cost must be non-negative when provided")

    annual_kwh = fan_power_kw * annual_hours
    kwh_saved = annual_kwh * savings_pct
    cost_saved = kwh_saved * electricity_rate
    carbon_saved_tonnes = (kwh_saved * defaults.ELECTRICITY_CO2_FACTOR_KG_PER_KWH) / 1000.0

    simple_payback: float | None = None
    if cost is not None and cost_saved > 0:
        simple_payback = cost / cost_saved
    result = VentilationResult(
        annual_kwh=annual_kwh,
        kwh_saved=kwh_saved,
        cost_saved=cost_saved,
        carbon_saved=carbon_saved_tonnes,
        simple_payback=simple_payback,
        assumptions=[f"annual_hours={annual_hours}", f"savings_pct={savings_pct:.0%}"],
    )
    out = result.to_dict()
    out.update(
        {
            "estimated_annual_kwh_saved": kwh_saved,
            "estimated_annual_saving_gbp": cost_saved,
            "estimated_implementation_cost_gbp": cost,
            "payback_years": simple_payback,
            "estimated_annual_co2_saved_tonnes": carbon_saved_tonnes,
        }
    )
    return out
