"""
Global default constants for deterministic energy calculators.
All numeric logic uses these; no LLM-computed values.
"""

# CO2 emission factors (kg CO2e per kWh)
ELECTRICITY_CO2_FACTOR_KG_PER_KWH: float = 0.19553
GAS_CO2_FACTOR_KG_PER_KWH: float = 0.18296

# Tariff / rate defaults (placeholders when not provided)
DEFAULT_TARIFF_P_PER_KWH: float = 30.0

# Measure-specific default savings or assumptions (fractions)
DEFAULT_LIGHTING_SAVINGS_PCT: float = 0.45
DEFAULT_SOLAR_KWH_PER_KWP: float = 900.0
DEFAULT_SELF_CONSUMPTION: float = 0.75
DEFAULT_REFRIG_SAVINGS_PCT: float = 0.15
DEFAULT_INSULATION_SAVINGS_PCT: float = 0.12
DEFAULT_HEAT_PUMP_SAVINGS_PCT: float = 0.60  # fraction of heating load replaced
