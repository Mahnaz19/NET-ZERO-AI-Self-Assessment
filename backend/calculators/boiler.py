from __future__ import annotations

from dataclasses import dataclass, asdict

from .baseline import GAS_CO2_FACTOR


@dataclass(frozen=True)
class BoilerResult:
    kwh_saved: float
    cost_saved: float
    carbon_saved: float
    simple_payback: float | None

    def to_dict(self) -> dict:
        return asdict(self)


def calculate_boiler_upgrade(
    annual_gas_kwh: float,
    efficiency_improvement: float = 0.20,
    gas_rate: float = 0.06,
    cost: float | None = None,
    implementation_cost_gbp: float | None = None,
) -> dict:
    """
    Deterministic boiler upgrade calculator.

    Args:
        annual_gas_kwh: Baseline annual gas consumption in kWh.
        efficiency_improvement: Fractional reduction in gas use (e.g. 0.2 for 20%).
        gas_rate: Gas rate in £/kWh.
        cost: Optional project capex in £ for simple payback.
    """
    if annual_gas_kwh < 0:
        raise ValueError("annual_gas_kwh must be non-negative")
    if efficiency_improvement < 0:
        raise ValueError("efficiency_improvement must be non-negative")
    if gas_rate < 0:
        raise ValueError("gas_rate must be non-negative")
    if cost is not None and cost < 0:
        raise ValueError("cost must be non-negative when provided")
    if implementation_cost_gbp is not None and implementation_cost_gbp < 0:
        raise ValueError("implementation_cost_gbp must be non-negative when provided")

    kwh_saved = annual_gas_kwh * efficiency_improvement
    cost_saved = kwh_saved * gas_rate
    # GAS_CO2_FACTOR is in kgCO2e/kWh; convert to tonnes.
    carbon_saved_tonnes = (kwh_saved * GAS_CO2_FACTOR) / 1000.0

    effective_cost = implementation_cost_gbp if implementation_cost_gbp is not None else cost

    simple_payback: float | None = None
    if effective_cost is not None and cost_saved > 0:
        simple_payback = effective_cost / cost_saved

    result = BoilerResult(
        kwh_saved=kwh_saved,
        cost_saved=cost_saved,
        carbon_saved=carbon_saved_tonnes,
        simple_payback=simple_payback,
    )
    out = result.to_dict()
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

