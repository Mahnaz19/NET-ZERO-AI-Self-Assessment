"""Deterministic heat pump replacement calculator."""
from __future__ import annotations

from dataclasses import dataclass, asdict

from . import defaults


@dataclass(frozen=True)
class HeatpumpResult:
    heating_kwh: float
    heatpump_elec_kwh: float
    gas_kwh_saved: float
    electricity_kwh_added: float
    cost_delta: float
    carbon_delta: float
    simple_payback: float | None
    assumptions: list[str]

    def to_dict(self) -> dict:
        return asdict(self)


def calculate_heatpump_replacement(
    annual_gas_kwh: float,
    fraction_heating_covered: float = 1.0,
    cop: float = 3.0,
    gas_rate: float = 0.06,
    electricity_rate: float = 0.30,
    cost: float | None = None,
) -> dict:
    """
    Estimate impact of replacing gas heating with heat pump. Deterministic.
    heating_kwh = annual_gas_kwh * fraction_heating_covered;
    heatpump_elec_kwh = heating_kwh / cop; cost/carbon delta and payback.
    """
    if annual_gas_kwh < 0:
        raise ValueError("annual_gas_kwh must be non-negative")
    if not (0 < fraction_heating_covered <= 1):
        raise ValueError("fraction_heating_covered must be in (0, 1]")
    if cop <= 0:
        raise ValueError("cop must be positive")
    if gas_rate < 0 or electricity_rate < 0:
        raise ValueError("rates must be non-negative")
    if cost is not None and cost < 0:
        raise ValueError("cost must be non-negative when provided")

    heating_kwh = annual_gas_kwh * fraction_heating_covered
    heatpump_elec_kwh = heating_kwh / cop
    gas_kwh_saved = heating_kwh
    electricity_kwh_added = heatpump_elec_kwh

    cost_gas_saved = gas_kwh_saved * gas_rate
    cost_elec_added = electricity_kwh_added * electricity_rate
    cost_delta = cost_elec_added - cost_gas_saved  # positive = higher cost

    carbon_gas_saved = (gas_kwh_saved * defaults.GAS_CO2_FACTOR_KG_PER_KWH) / 1000.0
    carbon_elec_added = (electricity_kwh_added * defaults.ELECTRICITY_CO2_FACTOR_KG_PER_KWH) / 1000.0
    carbon_delta = carbon_elec_added - carbon_gas_saved  # positive = more carbon

    simple_payback: float | None = None
    if cost is not None and cost_delta > 0:
        simple_payback = cost / cost_delta

    assumptions = [
        f"fraction_heating_covered={fraction_heating_covered:.0%}",
        f"COP={cop}",
    ]

    return HeatpumpResult(
        heating_kwh=heating_kwh,
        heatpump_elec_kwh=heatpump_elec_kwh,
        gas_kwh_saved=gas_kwh_saved,
        electricity_kwh_added=electricity_kwh_added,
        cost_delta=cost_delta,
        carbon_delta=carbon_delta,
        simple_payback=simple_payback,
        assumptions=assumptions,
    ).to_dict()
