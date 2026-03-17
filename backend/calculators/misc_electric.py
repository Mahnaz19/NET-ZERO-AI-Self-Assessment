"""Generic misc electric measure estimator (estimated_pct_of_total * savings_pct)."""
from __future__ import annotations

from dataclasses import dataclass, asdict

from . import defaults


@dataclass(frozen=True)
class MiscElectricResult:
    estimated_load_kwh: float
    kwh_saved: float
    cost_saved: float
    carbon_saved: float
    simple_payback: float | None
    assumptions: list[str]

    def to_dict(self) -> dict:
        return asdict(self)


def calculate_misc_electric(
    total_electric_kwh: float,
    estimated_pct_of_total: float = 0.10,
    savings_pct: float = 0.15,
    electricity_rate: float = 0.30,
    cost: float | None = None,
) -> dict:
    """estimated_load = total_electric_kwh * estimated_pct_of_total; kwh_saved = load * savings_pct."""
    if total_electric_kwh < 0:
        raise ValueError("total_electric_kwh must be non-negative")
    if not (0 <= estimated_pct_of_total <= 1) or not (0 <= savings_pct <= 1):
        raise ValueError("estimated_pct_of_total and savings_pct must be in [0, 1]")
    if electricity_rate < 0:
        raise ValueError("electricity_rate must be non-negative")
    if cost is not None and cost < 0:
        raise ValueError("cost must be non-negative when provided")

    estimated_load_kwh = total_electric_kwh * estimated_pct_of_total
    kwh_saved = estimated_load_kwh * savings_pct
    cost_saved = kwh_saved * electricity_rate
    carbon_saved_tonnes = (kwh_saved * defaults.ELECTRICITY_CO2_FACTOR_KG_PER_KWH) / 1000.0

    simple_payback: float | None = None
    if cost is not None and cost_saved > 0:
        simple_payback = cost / cost_saved
    result = MiscElectricResult(
        estimated_load_kwh=estimated_load_kwh,
        kwh_saved=kwh_saved,
        cost_saved=cost_saved,
        carbon_saved=carbon_saved_tonnes,
        simple_payback=simple_payback,
        assumptions=[
            f"estimated_pct_of_total={estimated_pct_of_total:.0%}",
            f"savings_pct={savings_pct:.0%}",
        ],
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
