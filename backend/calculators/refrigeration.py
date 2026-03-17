"""Deterministic refrigeration upgrade calculator."""
from __future__ import annotations

from dataclasses import dataclass, asdict

from . import defaults


@dataclass(frozen=True)
class RefrigerationResult:
    refrigeration_load_kwh: float
    kwh_saved: float
    cost_saved: float
    carbon_saved: float
    simple_payback: float | None
    assumptions: list[str]

    def to_dict(self) -> dict:
        return asdict(self)


def calculate_refrigeration(
    refrigeration_load_kwh: float | None = None,
    total_electric_kwh: float | None = None,
    assumed_pct_of_electric: float = 0.35,
    savings_pct: float = defaults.DEFAULT_REFRIG_SAVINGS_PCT,
    electricity_rate: float = 0.30,
    cost: float | None = None,
    implementation_cost_gbp: float | None = None,
) -> dict:
    """
    Estimate refrigeration load savings (e.g. 10% reduction); deterministic.
    If refrigeration_load_kwh not given, estimate from total_electric_kwh * assumed_pct_of_electric.
    """
    if savings_pct < 0 or savings_pct > 1:
        raise ValueError("savings_pct must be between 0 and 1")
    if assumed_pct_of_electric < 0 or assumed_pct_of_electric > 1:
        raise ValueError("assumed_pct_of_electric must be between 0 and 1")
    if electricity_rate < 0:
        raise ValueError("electricity_rate must be non-negative")
    if cost is not None and cost < 0:
        raise ValueError("cost must be non-negative when provided")
    if implementation_cost_gbp is not None and implementation_cost_gbp < 0:
        raise ValueError("implementation_cost_gbp must be non-negative when provided")

    if refrigeration_load_kwh is not None:
        load = max(0.0, refrigeration_load_kwh)
        assumptions = ["refrigeration_load_kwh provided by user"]
    elif total_electric_kwh is not None and total_electric_kwh >= 0:
        load = total_electric_kwh * assumed_pct_of_electric
        assumptions = [
            f"refrigeration estimated as {assumed_pct_of_electric:.0%} of total electricity",
            f"savings_pct={savings_pct:.0%}",
        ]
    else:
        raise ValueError("Provide either refrigeration_load_kwh or total_electric_kwh")

    kwh_saved = load * savings_pct
    cost_saved = kwh_saved * electricity_rate
    carbon_saved_tonnes = (kwh_saved * defaults.ELECTRICITY_CO2_FACTOR_KG_PER_KWH) / 1000.0

    effective_cost = implementation_cost_gbp if implementation_cost_gbp is not None else cost

    simple_payback: float | None = None
    if effective_cost is not None and cost_saved > 0:
        simple_payback = effective_cost / cost_saved

    out = RefrigerationResult(
        refrigeration_load_kwh=load,
        kwh_saved=kwh_saved,
        cost_saved=cost_saved,
        carbon_saved=carbon_saved_tonnes,
        simple_payback=simple_payback,
        assumptions=assumptions,
    ).to_dict()
    out.update(
        {
            "estimated_annual_kwh_saved": kwh_saved,
            "estimated_annual_saving_gbp": cost_saved,
            "estimated_implementation_cost_gbp": effective_cost,
            "payback_years": simple_payback,
            "estimated_annual_co2_saved_tonnes": carbon_saved_tonnes,
        }
    )
    return out
