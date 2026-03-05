from __future__ import annotations

from dataclasses import dataclass, asdict

from .baseline import GAS_CO2_FACTOR


@dataclass(frozen=True)
class BoilerResult:
    kwh_saved: float
    annual_cost_saved_gbp: float
    annual_carbon_saved_kg: float
    simple_payback_years: float | None

    def to_dict(self) -> dict:
        return asdict(self)


def calculate_boiler_upgrade(
    annual_gas_kwh: float,
    efficiency_improvement: float = 0.20,
    gas_rate: float = 0.06,
    upgrade_cost_gbp: float | None = None,
) -> dict:
    """
    Deterministic boiler upgrade calculator.
    """
    if annual_gas_kwh < 0:
        raise ValueError("annual_gas_kwh must be non-negative")
    if efficiency_improvement < 0:
        raise ValueError("efficiency_improvement must be non-negative")
    if gas_rate < 0:
        raise ValueError("gas_rate must be non-negative")

    kwh_saved = annual_gas_kwh * efficiency_improvement
    annual_cost_saved_gbp = kwh_saved * gas_rate
    annual_carbon_saved_kg = kwh_saved * GAS_CO2_FACTOR

    simple_payback_years: float | None = None
    if upgrade_cost_gbp is not None and annual_cost_saved_gbp > 0:
        simple_payback_years = upgrade_cost_gbp / annual_cost_saved_gbp

    result = BoilerResult(
        kwh_saved=kwh_saved,
        annual_cost_saved_gbp=annual_cost_saved_gbp,
        annual_carbon_saved_kg=annual_carbon_saved_kg,
        simple_payback_years=simple_payback_years,
    )
    return result.to_dict()

