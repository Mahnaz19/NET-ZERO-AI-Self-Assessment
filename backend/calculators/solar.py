from __future__ import annotations

from dataclasses import dataclass, asdict

from .baseline import ELECTRICITY_CO2_FACTOR


@dataclass(frozen=True)
class SolarResult:
    annual_generation: float
    self_consumed_kwh: float
    exported_kwh: float
    annual_savings: float
    carbon_saving: float
    simple_payback: float | None

    def to_dict(self) -> dict:
        return asdict(self)


def calculate_solar(
    system_kwp: float,
    orientation_factor: float = 0.92,
    generation_factor: float = 900.0,
    self_consumption_rate: float = 0.75,
    electricity_rate: float = 0.30,
    export_rate: float = 0.06,
    cost: float | None = None,
    implementation_cost_gbp: float | None = None,
) -> dict:
    """
    Deterministic PV solar generation and savings calculator.

    Args:
        system_kwp: Installed system size in kWp (non-negative).
        orientation_factor: Dimensionless factor capturing orientation / pitch.
        generation_factor: Annual kWh per kWp before orientation adjustment.
        self_consumption_rate: Fraction of generation self-consumed on site (0–1).
        electricity_rate: Import electricity rate in £/kWh.
        export_rate: Export rate in £/kWh.
        cost: Optional project capex in £ for simple payback.
    """
    if system_kwp < 0:
        raise ValueError("system_kwp must be non-negative")
    if orientation_factor < 0 or generation_factor < 0:
        raise ValueError("orientation_factor and generation_factor must be non-negative")
    if not (0.0 <= self_consumption_rate <= 1.0):
        raise ValueError("self_consumption_rate must be between 0 and 1")
    if electricity_rate < 0 or export_rate < 0:
        raise ValueError("electricity_rate and export_rate must be non-negative")
    if cost is not None and cost < 0:
        raise ValueError("cost must be non-negative when provided")
    if implementation_cost_gbp is not None and implementation_cost_gbp < 0:
        raise ValueError("implementation_cost_gbp must be non-negative when provided")

    annual_generation = system_kwp * generation_factor * orientation_factor
    self_consumed_kwh = annual_generation * self_consumption_rate
    exported_kwh = annual_generation - self_consumed_kwh

    annual_savings = self_consumed_kwh * electricity_rate + exported_kwh * export_rate

    # ELECTRICITY_CO2_FACTOR is in kgCO2e/kWh; convert to tonnes.
    carbon_saving_tonnes = (annual_generation * ELECTRICITY_CO2_FACTOR) / 1000.0

    effective_cost = implementation_cost_gbp if implementation_cost_gbp is not None else cost

    simple_payback: float | None = None
    if effective_cost is not None and annual_savings > 0:
        simple_payback = effective_cost / annual_savings

    result = SolarResult(
        annual_generation=annual_generation,
        self_consumed_kwh=self_consumed_kwh,
        exported_kwh=exported_kwh,
        annual_savings=annual_savings,
        carbon_saving=carbon_saving_tonnes,
        simple_payback=simple_payback,
    )
    out = result.to_dict()
    out.update(
        {
            # For solar we treat the self-consumed generation as the effective kWh "saved"
            "estimated_annual_kwh_saved": self_consumed_kwh,
            "estimated_annual_saving_gbp": annual_savings,
            "estimated_implementation_cost_gbp": effective_cost,
            "payback_years": simple_payback,
            "estimated_annual_co2_saved_tonnes": carbon_saving_tonnes,
        }
    )
    return out

