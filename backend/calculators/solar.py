from __future__ import annotations

from dataclasses import dataclass, asdict

ELECTRICITY_CO2_FACTOR: float = 0.19553  # kgCO2e per kWh


@dataclass(frozen=True)
class SolarResult:
    annual_generation_kwh: float
    self_consumed_kwh: float
    exported_kwh: float
    savings_import_gbp: float
    savings_export_gbp: float
    total_savings_gbp: float
    carbon_saving_kg: float

    def to_dict(self) -> dict:
        return asdict(self)


def calculate_solar(
    system_kwp: float,
    orientation_factor: float = 0.92,
    generation_factor: float = 900.0,
    self_consumption_rate: float = 0.75,
    electricity_rate: float = 0.30,
    export_rate: float = 0.06,
) -> dict:
    """
    Deterministic PV solar generation and savings calculator.
    """
    if system_kwp < 0:
        raise ValueError("system_kwp must be non-negative")
    if orientation_factor < 0 or generation_factor < 0:
        raise ValueError("orientation_factor and generation_factor must be non-negative")
    if not (0.0 <= self_consumption_rate <= 1.0):
        raise ValueError("self_consumption_rate must be between 0 and 1")
    if electricity_rate < 0 or export_rate < 0:
        raise ValueError("electricity_rate and export_rate must be non-negative")

    annual_generation_kwh = system_kwp * generation_factor * orientation_factor
    self_consumed_kwh = annual_generation_kwh * self_consumption_rate
    exported_kwh = annual_generation_kwh - self_consumed_kwh

    savings_import_gbp = self_consumed_kwh * electricity_rate
    savings_export_gbp = exported_kwh * export_rate
    total_savings_gbp = savings_import_gbp + savings_export_gbp

    carbon_saving_kg = annual_generation_kwh * ELECTRICITY_CO2_FACTOR

    result = SolarResult(
        annual_generation_kwh=annual_generation_kwh,
        self_consumed_kwh=self_consumed_kwh,
        exported_kwh=exported_kwh,
        savings_import_gbp=savings_import_gbp,
        savings_export_gbp=savings_export_gbp,
        total_savings_gbp=total_savings_gbp,
        carbon_saving_kg=carbon_saving_kg,
    )
    return result.to_dict()

