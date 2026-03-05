from __future__ import annotations

from dataclasses import dataclass, asdict


ELECTRICITY_CO2_FACTOR: float = 0.19553  # kgCO2e per kWh
GAS_CO2_FACTOR: float = 0.18296  # kgCO2e per kWh


@dataclass(frozen=True)
class BaselineResult:
    electricity_cost: float
    gas_cost: float
    total_cost: float
    electricity_co2: float
    gas_co2: float
    total_co2: float

    def to_dict(self) -> dict:
        """Return a JSON-serialisable representation of this baseline result."""
        return asdict(self)


def compute_baseline(
    electricity_kwh: float,
    gas_kwh: float,
    electricity_rate: float,
    gas_rate: float,
) -> dict:
    """
    Compute deterministic baseline annual energy costs and CO2 emissions.

    All inputs are annual values.

    Args:
        electricity_kwh: Annual electricity consumption in kWh.
        gas_kwh: Annual gas consumption in kWh.
        electricity_rate: Electricity unit rate in £/kWh.
        gas_rate: Gas unit rate in £/kWh.

    Returns:
        Dictionary with electricity and gas costs and CO2, ready for JSON serialisation.
    """
    electricity_cost = electricity_kwh * electricity_rate
    gas_cost = gas_kwh * gas_rate
    total_cost = electricity_cost + gas_cost

    electricity_co2 = electricity_kwh * ELECTRICITY_CO2_FACTOR
    gas_co2 = gas_kwh * GAS_CO2_FACTOR
    total_co2 = electricity_co2 + gas_co2

    result = BaselineResult(
        electricity_cost=electricity_cost,
        gas_cost=gas_cost,
        total_cost=total_cost,
        electricity_co2=electricity_co2,
        gas_co2=gas_co2,
        total_co2=total_co2,
    )
    return result.to_dict()

