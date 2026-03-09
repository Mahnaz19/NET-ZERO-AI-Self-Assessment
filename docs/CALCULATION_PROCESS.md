# Calculation Process in the Net Zero AI Self-Assessment Project

This document describes **all calculation-related logic** in the project: where it lives, what each file contains, which formulas are used, and how the pieces fit together. All calculations are **deterministic** (no LLM or ML); they use fixed constants and formulas.

---

## 1. Overview

- **Two entry points for “baseline” and measures:**
  - **API / submission flow:** `backend/app/calculators.py` — used when a questionnaire is submitted; takes a dictionary of answers and returns baseline + example measures (placeholder shape).
  - **Deterministic calculator library:** `backend/calculators/` — used by tests and (when wired in) by real assessor logic; takes explicit numeric arguments and returns structured results.
- **Global constants:** `backend/calculators/defaults.py` — CO₂ factors, default tariffs, and default savings/assumption fractions used by the deterministic calculators.
- **Carbon units:** Where the library uses kg CO₂e per kWh, outputs are converted to **tonnes CO₂e** for cost/savings and carbon results.

---

## 2. Global Defaults: `backend/calculators/defaults.py`

This file defines the numeric constants used across the deterministic calculators. **No calculation logic** — only values.

| Constant | Value | Description |
|----------|--------|-------------|
| `ELECTRICITY_CO2_FACTOR_KG_PER_KWH` | 0.19553 | kg CO₂e per kWh (electricity) |
| `GAS_CO2_FACTOR_KG_PER_KWH` | 0.18296 | kg CO₂e per kWh (gas) |
| `DEFAULT_TARIFF_P_PER_KWH` | 30.0 | Default electricity tariff (p/kWh) when not provided |
| `DEFAULT_LIGHTING_SAVINGS_PCT` | 0.45 | Default LED upgrade savings fraction (not used in current lighting formula; lighting uses explicit wattage delta) |
| `DEFAULT_SOLAR_KWH_PER_KWP` | 900.0 | Annual kWh per kWp (before orientation factor) |
| `DEFAULT_SELF_CONSUMPTION` | 0.75 | Default fraction of solar generation self-consumed on site |
| `DEFAULT_REFRIG_SAVINGS_PCT` | 0.15 | Default refrigeration upgrade savings fraction |
| `DEFAULT_INSULATION_SAVINGS_PCT` | 0.12 | Default building fabric / insulation improvement fraction |
| `DEFAULT_HEAT_PUMP_SAVINGS_PCT` | 0.60 | Default fraction of heating load replaced by heat pump (documented in README; heatpump module uses `fraction_heating_covered` and COP instead) |

---

## 3. API-Level Placeholder: `backend/app/calculators.py`

Used by the **submission service** when storing questionnaire answers. It provides a baseline and a list of example measures so the API can return a consistent shape. **Not** the same as the detailed calculators in `backend/calculators/`.

### 3.1 `compute_baseline(answers: Dict[str, Any]) -> Dict[str, Any]`

- **Inputs (from `answers`):** `annual_kwh`, `annual_cost_gbp` (optional).
- **Logic:**
  - If both `annual_kwh > 0` and `annual_cost_gbp > 0`:  
    `tariff_p_per_kwh = (annual_cost_gbp * 100) / annual_kwh` (GBP → pence).
  - Else: `tariff_p_per_kwh = DEFAULT_TARIFF_P_PER_KWH` (30 p/kWh).
  - Carbon: `annual_co2_tonnes = annual_kwh * UK_ELECTRICITY_CO2_FACTOR`  
    (this file uses `UK_ELECTRICITY_CO2_FACTOR = 0.000233` tonnes/kWh as a placeholder).
- **Returns:** `annual_kwh`, `annual_cost_gbp`, `tariff_p_per_kwh`, `annual_co2_tonnes`.

### 3.2 `compute_measure_summaries(answers: Dict[str, Any]) -> List[Dict[str, Any]]`

- **Inputs (from `answers`):** `floor_area_m2` (default 100), `usage_profile` (e.g. `"office"`).
- **Logic:** Returns a **fixed list of two example measures** (shape only):
  1. **LED_UPGRADE:** `capex_gbp = floor_area_m2 * 5`, `annual_savings_kwh = floor_area_m2 * 3`, `annual_savings_gbp = floor_area_m2 * 3 * 0.30`, `simple_payback_years = 3.0`.
  2. **HEATING_CONTROLS:** Fixed `capex_gbp=500`, `annual_savings_kwh=1500`, `annual_savings_gbp=450`, `simple_payback_years=1.1`, plus an applicability hint using `usage_profile`.
- **Returns:** List of measure dicts (code, title, description, capex, savings, payback).

---

## 4. Deterministic Calculator Library: `backend/calculators/`

Each module defines a **single main function** and a **result dataclass** (e.g. `BaselineResult`, `BoilerResult`). Results are converted to a dict via `to_dict()` for JSON. Carbon outputs are in **tonnes CO₂e** (converted from kg using the factors in `defaults.py` or, for `baseline.py`, its own constants).

### 4.1 Baseline: `backend/calculators/baseline.py`

**Function:** `compute_baseline(electricity_kwh, gas_kwh, electricity_rate, gas_rate) -> dict`

- **Purpose:** Annual baseline **costs** and **CO₂** for electricity and gas.
- **Constants (in file):** `ELECTRICITY_CO2_FACTOR = 0.19553` kgCO₂e/kWh, `GAS_CO2_FACTOR = 0.18296` kgCO₂e/kWh.
- **Formulas:**
  - `electricity_cost = electricity_kwh * electricity_rate`
  - `gas_cost = gas_kwh * gas_rate`
  - `total_cost = electricity_cost + gas_cost`
  - `electricity_co2 = electricity_kwh * ELECTRICITY_CO2_FACTOR` (kg; result dict keeps kg for consistency with other calculators that convert to tonnes internally)
  - `gas_co2 = gas_kwh * GAS_CO2_FACTOR`
  - `total_co2 = electricity_co2 + gas_co2`
- **Returns:** `electricity_cost`, `gas_cost`, `total_cost`, `electricity_co2`, `gas_co2`, `total_co2` (costs in £, CO₂ in kg).

### 4.2 Boiler upgrade: `backend/calculators/boiler.py`

**Function:** `calculate_boiler_upgrade(annual_gas_kwh, efficiency_improvement=0.20, gas_rate=0.06, cost=None) -> dict`

- **Purpose:** Gas savings and carbon savings from a boiler efficiency improvement.
- **Formulas:**
  - `kwh_saved = annual_gas_kwh * efficiency_improvement`
  - `cost_saved = kwh_saved * gas_rate`
  - `carbon_saved_tonnes = (kwh_saved * GAS_CO2_FACTOR) / 1000`
  - If `cost` provided and `cost_saved > 0`: `simple_payback = cost / cost_saved`
- **Returns:** `kwh_saved`, `cost_saved`, `carbon_saved`, `simple_payback`.

### 4.3 LED lighting: `backend/calculators/lighting.py`

**Function:** `calculate_led_upgrade(fittings, old_watt, new_watt, annual_hours, electricity_rate) -> dict`

- **Purpose:** Savings from replacing lamps with lower-wattage LEDs.
- **Formulas:**
  - `watt_delta = max(old_watt - new_watt, 0)`
  - `kwh_saved = (watt_delta * fittings * annual_hours) / 1000`
  - `cost_saved = kwh_saved * electricity_rate`
  - `carbon_saved_tonnes = (kwh_saved * ELECTRICITY_CO2_FACTOR) / 1000`
- **Returns:** `kwh_saved`, `cost_saved`, `carbon_saved`.

### 4.4 Solar PV: `backend/calculators/solar.py`

**Function:** `calculate_solar(system_kwp, orientation_factor=0.92, generation_factor=900.0, self_consumption_rate=0.75, electricity_rate=0.30, export_rate=0.06, cost=None) -> dict`

- **Purpose:** Annual PV generation, self-consumption, export, monetary savings, carbon saving, and optional payback.
- **Formulas:**
  - `annual_generation = system_kwp * generation_factor * orientation_factor`
  - `self_consumed_kwh = annual_generation * self_consumption_rate`
  - `exported_kwh = annual_generation - self_consumed_kwh`
  - `annual_savings = self_consumed_kwh * electricity_rate + exported_kwh * export_rate`
  - `carbon_saving_tonnes = (annual_generation * ELECTRICITY_CO2_FACTOR) / 1000`
  - If `cost` and `annual_savings > 0`: `simple_payback = cost / annual_savings`
- **Returns:** `annual_generation`, `self_consumed_kwh`, `exported_kwh`, `annual_savings`, `carbon_saving`, `simple_payback`.

### 4.5 Refrigeration: `backend/calculators/refrigeration.py`

**Function:** `calculate_refrigeration(refrigeration_load_kwh=None, total_electric_kwh=None, assumed_pct_of_electric=0.35, savings_pct=0.15, electricity_rate=0.30, cost=None) -> dict`

- **Purpose:** Refrigeration load savings (either from given load or estimated from total electricity).
- **Formulas:**
  - If `refrigeration_load_kwh` given: `load = max(0, refrigeration_load_kwh)`.
  - Else if `total_electric_kwh` given: `load = total_electric_kwh * assumed_pct_of_electric`.
  - `kwh_saved = load * savings_pct`
  - `cost_saved = kwh_saved * electricity_rate`
  - `carbon_saved_tonnes = (kwh_saved * ELECTRICITY_CO2_FACTOR_KG_PER_KWH) / 1000`
  - If `cost` and `cost_saved > 0`: `simple_payback = cost / cost_saved`
- **Returns:** `refrigeration_load_kwh` (the load used), `kwh_saved`, `cost_saved`, `carbon_saved`, `simple_payback`, `assumptions` (list of strings describing inputs).

### 4.6 Heat pump replacement: `backend/calculators/heatpump.py`

**Function:** `calculate_heatpump_replacement(annual_gas_kwh, fraction_heating_covered=1.0, cop=3.0, gas_rate=0.06, electricity_rate=0.30, cost=None) -> dict`

- **Purpose:** Impact of replacing part or all of gas heating with a heat pump (cost and carbon delta, optional payback).
- **Formulas:**
  - `heating_kwh = annual_gas_kwh * fraction_heating_covered`
  - `heatpump_elec_kwh = heating_kwh / cop`
  - `gas_kwh_saved = heating_kwh`, `electricity_kwh_added = heatpump_elec_kwh`
  - `cost_gas_saved = gas_kwh_saved * gas_rate`, `cost_elec_added = electricity_kwh_added * electricity_rate`
  - `cost_delta = cost_elec_added - cost_gas_saved` (positive = higher cost with heat pump)
  - `carbon_gas_saved` and `carbon_elec_added` using defaults; `carbon_delta = carbon_elec_added - carbon_gas_saved`
  - If `cost` and `cost_delta > 0`: `simple_payback = cost / cost_delta`
- **Returns:** `heating_kwh`, `heatpump_elec_kwh`, `gas_kwh_saved`, `electricity_kwh_added`, `cost_delta`, `carbon_delta`, `simple_payback`, `assumptions`.

### 4.7 Building fabric / insulation: `backend/calculators/building_fabric.py`

**Function:** `calculate_building_fabric_improvement(annual_heating_kwh, improvement_pct=0.12, cost=None, fuel_rate=0.06) -> dict`

- **Purpose:** Heating savings from fabric/insulation improvement.
- **Formulas:**
  - `kwh_saved = annual_heating_kwh * improvement_pct`
  - `cost_saved = kwh_saved * fuel_rate`
  - `carbon_saved_tonnes = (kwh_saved * GAS_CO2_FACTOR_KG_PER_KWH) / 1000`
  - If `cost` and `cost_saved > 0`: `simple_payback = cost / cost_saved`
- **Returns:** `kwh_saved`, `cost_saved`, `carbon_saved`, `simple_payback`, `assumptions`.

### 4.8 Cooling: `backend/calculators/cooling.py`

**Function:** `calculate_cooling_upgrade(annual_cooling_kwh=None, total_electric_kwh=None, assumed_pct=0.10, savings_pct=0.15, electricity_rate=0.30, cost=None) -> dict`

- **Purpose:** Cooling load savings; load can be given or estimated as a fraction of total electricity.
- **Formulas:**
  - If `annual_cooling_kwh` given: `load = max(0, annual_cooling_kwh)`.
  - Else: `load = total_electric_kwh * assumed_pct`.
  - `kwh_saved = load * savings_pct`
  - `cost_saved`, `carbon_saved_tonnes`, `simple_payback` as in other electric measures.
- **Returns:** `cooling_load_kwh`, `kwh_saved`, `cost_saved`, `carbon_saved`, `simple_payback`, `assumptions`.

### 4.9 Ventilation: `backend/calculators/ventilation.py`

**Function:** `calculate_ventilation_improvement(fan_power_kw, annual_hours=2000, savings_pct=0.20, electricity_rate=0.30, cost=None) -> dict`

- **Purpose:** Ventilation fan energy and savings from an efficiency improvement.
- **Formulas:**
  - `annual_kwh = fan_power_kw * annual_hours`
  - `kwh_saved = annual_kwh * savings_pct`
  - `cost_saved = kwh_saved * electricity_rate`
  - `carbon_saved_tonnes = (kwh_saved * ELECTRICITY_CO2_FACTOR_KG_PER_KWH) / 1000`
  - If `cost` and `cost_saved > 0`: `simple_payback = cost / cost_saved`
- **Returns:** `annual_kwh`, `kwh_saved`, `cost_saved`, `carbon_saved`, `simple_payback`, `assumptions`.

### 4.10 Heaters (electric): `backend/calculators/heaters.py`

**Function:** `calculate_heaters_replacement(annual_heater_kwh, savings_pct=0.20, electricity_rate=0.30, cost=None) -> dict`

- **Purpose:** Savings from replacing or improving electric heaters.
- **Formulas:**
  - `kwh_saved = annual_heater_kwh * savings_pct`
  - `cost_saved`, `carbon_saved_tonnes`, `simple_payback` as in other electric measures.
- **Returns:** `kwh_saved`, `cost_saved`, `carbon_saved`, `simple_payback`, `assumptions`.

### 4.11 Energy management / BMS: `backend/calculators/energy_management.py`

**Function:** `calculate_energy_management_savings(total_annual_kwh, savings_pct=0.05, electricity_rate=0.30, cost=None) -> dict`

- **Purpose:** Site-wide savings from BMS/controls (percentage of total electricity).
- **Formulas:**
  - `kwh_saved = total_annual_kwh * savings_pct`
  - `cost_saved = kwh_saved * electricity_rate`
  - `carbon_saved_tonnes = (kwh_saved * ELECTRICITY_CO2_FACTOR_KG_PER_KWH) / 1000`
  - If `cost` and `cost_saved > 0`: `simple_payback = cost / cost_saved`
- **Returns:** `kwh_saved`, `cost_saved`, `carbon_saved`, `simple_payback`, `assumptions`.

### 4.12 Misc electric: `backend/calculators/misc_electric.py`

**Function:** `calculate_misc_electric(total_electric_kwh, estimated_pct_of_total=0.10, savings_pct=0.15, electricity_rate=0.30, cost=None) -> dict`

- **Purpose:** Generic electric measure — estimate a share of total consumption and apply a savings fraction.
- **Formulas:**
  - `estimated_load_kwh = total_electric_kwh * estimated_pct_of_total`
  - `kwh_saved = estimated_load_kwh * savings_pct`
  - Then `cost_saved`, `carbon_saved_tonnes`, `simple_payback` as usual.
- **Returns:** `estimated_load_kwh`, `kwh_saved`, `cost_saved`, `carbon_saved`, `simple_payback`, `assumptions`.

### 4.13 Misc gas: `backend/calculators/misc_gas.py`

**Function:** `calculate_misc_gas(total_gas_kwh, estimated_pct_of_total=0.10, savings_pct=0.15, gas_rate=0.06, cost=None) -> dict`

- **Purpose:** Generic gas measure — estimate a share of total gas and apply a savings fraction.
- **Formulas:**
  - `estimated_load_kwh = total_gas_kwh * estimated_pct_of_total`
  - `kwh_saved = estimated_load_kwh * savings_pct`
  - `cost_saved = kwh_saved * gas_rate`
  - `carbon_saved_tonnes = (kwh_saved * GAS_CO2_FACTOR_KG_PER_KWH) / 1000`
  - If `cost` and `cost_saved > 0`: `simple_payback = cost / cost_saved`
- **Returns:** `estimated_load_kwh`, `kwh_saved`, `cost_saved`, `carbon_saved`, `simple_payback`, `assumptions`.

---

## 5. Where Calculations Are Used

| Location | What runs |
|----------|-----------|
| **Submission flow** | `backend/app/services/submission_service.py` calls `backend/app/calculators.compute_baseline(answers)` and `compute_measure_summaries(answers)` when persisting a submission and building the response. |
| **Tests** | `backend/tests/test_*.py` import and call the **deterministic** functions in `backend/calculators/` (e.g. `compute_baseline`, `calculate_boiler_upgrade`, `calculate_solar`, etc.) with explicit arguments to assert outputs. |
| **Backend README** | `backend/README.md` summarises defaults from `defaults.py` and lists the calculator modules (solar, lighting, boiler, refrigeration, heatpump, building fabric, cooling, ventilation, heaters, energy management, misc electric/gas). |

---

## 6. File Summary

| File | Role | Contains |
|------|------|----------|
| `backend/calculators/defaults.py` | Global constants | CO₂ factors (electricity, gas), default tariff, default savings/assumption fractions. |
| `backend/app/calculators.py` | API placeholder | `compute_baseline(answers)`, `compute_measure_summaries(answers)` — dict in, baseline + example measures out. |
| `backend/calculators/baseline.py` | Baseline (library) | `compute_baseline(elec_kwh, gas_kwh, elec_rate, gas_rate)` → costs and CO₂. |
| `backend/calculators/boiler.py` | Boiler upgrade | `calculate_boiler_upgrade(...)` → kwh/cost/carbon saved, payback. |
| `backend/calculators/lighting.py` | LED upgrade | `calculate_led_upgrade(...)` → kwh/cost/carbon saved from wattage reduction. |
| `backend/calculators/solar.py` | Solar PV | `calculate_solar(...)` → generation, self-consumption, export, savings, carbon, payback. |
| `backend/calculators/refrigeration.py` | Refrigeration | `calculate_refrigeration(...)` → load (or estimated), kwh/cost/carbon saved, payback. |
| `backend/calculators/heatpump.py` | Heat pump | `calculate_heatpump_replacement(...)` → heating load, elec/gas deltas, cost/carbon delta, payback. |
| `backend/calculators/building_fabric.py` | Insulation/fabric | `calculate_building_fabric_improvement(...)` → kwh/cost/carbon saved, payback. |
| `backend/calculators/cooling.py` | Cooling | `calculate_cooling_upgrade(...)` → cooling load (or estimated), kwh/cost/carbon saved, payback. |
| `backend/calculators/ventilation.py` | Ventilation | `calculate_ventilation_improvement(...)` → annual kwh, kwh/cost/carbon saved, payback. |
| `backend/calculators/heaters.py` | Electric heaters | `calculate_heaters_replacement(...)` → kwh/cost/carbon saved, payback. |
| `backend/calculators/energy_management.py` | BMS/controls | `calculate_energy_management_savings(...)` → kwh/cost/carbon saved, payback. |
| `backend/calculators/misc_electric.py` | Misc electric | `calculate_misc_electric(...)` → estimated load, kwh/cost/carbon saved, payback. |
| `backend/calculators/misc_gas.py` | Misc gas | `calculate_misc_gas(...)` → estimated load, kwh/cost/carbon saved, payback. |
| `backend/app/services/submission_service.py` | Submission API | Calls `app/calculators.compute_baseline` and `compute_measure_summaries` for stored submissions. |
| `backend/tests/test_baseline.py` … `test_misc_gas.py` | Unit tests | Call the corresponding calculator functions and assert on returned dicts. |

---

## 7. Carbon Conversion Convention

- **Storage in code:** CO₂ emission factors are in **kg CO₂e per kWh** (`ELECTRICITY_CO2_FACTOR_KG_PER_KWH`, `GAS_CO2_FACTOR_KG_PER_KWH` in `defaults.py`; `baseline.py` defines its own matching constants).
- **Returned to caller:** The deterministic calculators in `backend/calculators/` convert to **tonnes CO₂e** for carbon outputs using:
  - `carbon_tonnes = (kwh * FACTOR_KG_PER_KWH) / 1000`
- **Exception:** `baseline.py`’s `compute_baseline` returns `electricity_co2` and `gas_co2` in **kg** (no division by 1000 in that file).

---

## 8. Notes and TODOs (from codebase)

- The API layer (`app/calculators.py`) is a **placeholder**; real assessor logic should be driven by the deterministic calculators in `backend/calculators/` and/or Excel models in `/docs`.
- Defaults in `defaults.py` (and in each module) may be updated to align with official factors and assessor guidance.
- Future work may introduce time-varying or regional emission factors and wire the full calculator library into the submission/report flow.
