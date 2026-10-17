from typing import Any, Dict, List

from calculators.boiler import calculate_boiler_upgrade
from calculators.building_fabric import calculate_building_fabric_improvement
from calculators.cooling import calculate_cooling_upgrade
from calculators.energy_management import calculate_energy_management_savings
from calculators.heaters import calculate_heaters_replacement
from calculators.heatpump import calculate_heatpump_replacement
from calculators.lighting import calculate_led_upgrade
from calculators.misc_electric import calculate_misc_electric
from calculators.misc_gas import calculate_misc_gas
from calculators.refrigeration import calculate_refrigeration
from calculators.solar import calculate_solar
from calculators.ventilation import calculate_ventilation_improvement


DEFAULT_TARIFF_P_PER_KWH = 30.0  # fallback tariff in pence/kWh (dev placeholder)
UK_ELECTRICITY_CO2_FACTOR = 0.000233  # tonnes CO2e per kWh (placeholder)
# TODO: Replace with time-series / regional emissions factors once data model is defined.


def compute_baseline(answers: Dict[str, Any]) -> Dict[str, Any]:
    """
    Very simple deterministic baseline calculator.

    This is intentionally a placeholder and should be replaced with the
    proper assessor logic based on the Excel models in /docs.

    TODO: Replace with real baseline energy and carbon calculations derived
    from assessor Excel tools in /docs once the domain model is finalized.
    """
    electricity_kwh = float(answers.get("electricity_kwh_annual", 0) or 0)
    gas_kwh = float(answers.get("gas_kwh_annual", 0) or 0)
    electricity_cost = float(answers.get("electricity_cost_annual_ex_vat", 0) or 0)
    gas_cost = float(answers.get("gas_cost_annual_ex_vat", 0) or 0)

    annual_kwh = float(answers.get("annual_kwh", 0) or (electricity_kwh + gas_kwh))
    annual_cost = float(answers.get("annual_cost_gbp", 0) or (electricity_cost + gas_cost))

    tariff_p_per_kwh: float
    if annual_kwh > 0 and annual_cost > 0:
        # Convert GBP to pence for the tariff figure.
        tariff_p_per_kwh = (annual_cost * 100.0) / annual_kwh
    else:
        # Example default tariff; not domain-accurate.
        tariff_p_per_kwh = DEFAULT_TARIFF_P_PER_KWH

    # Simple carbon intensity factor (kgCO2e per kWh) converted to tonnes.
    annual_co2_tonnes = annual_kwh * UK_ELECTRICITY_CO2_FACTOR

    return {
        "annual_kwh": annual_kwh,
        "annual_cost_gbp": annual_cost,
        "tariff_p_per_kwh": tariff_p_per_kwh,
        "annual_co2_tonnes": annual_co2_tonnes,
    }


def compute_measure_summaries(answers: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Build deterministic measure candidates by invoking dedicated calculators
    from backend/calculators/*. This keeps recommendation candidates aligned
    with the full project recommendation catalogue.
    """
    def _f(key: str, default: float = 0.0) -> float:
        return float(answers.get(key, default) or default)

    def _is_yes(key: str) -> bool:
        return str(answers.get(key, "")).strip().lower() in {"yes", "true", "1"}

    electricity_kwh = _f("electricity_kwh_annual")
    gas_kwh = _f("gas_kwh_annual")
    electricity_cost = _f("electricity_cost_annual_ex_vat")
    gas_cost = _f("gas_cost_annual_ex_vat")
    floor_area_m2 = _f("floor_area_m2", 100.0)

    electricity_rate = (
        (electricity_cost / electricity_kwh) if electricity_kwh > 0 and electricity_cost > 0 else 0.30
    )
    gas_rate = (gas_cost / gas_kwh) if gas_kwh > 0 and gas_cost > 0 else 0.06

    led = calculate_led_upgrade(
        fittings=int(_f("lighting_fixture_count", max(10.0, floor_area_m2 / 10.0))),
        old_watt=_f("lighting_old_watt", 58.0),
        new_watt=_f("lighting_new_watt", 20.0),
        annual_hours=_f("lighting_annual_hours", _f("weekly_operational_hours", 40.0) * 52.0),
        electricity_rate=electricity_rate,
        implementation_cost_gbp=_f("led_upgrade_cost_gbp", max(500.0, floor_area_m2 * 5.0)),
    )
    cooling = calculate_cooling_upgrade(
        total_electric_kwh=max(electricity_kwh, 0.0),
        electricity_rate=electricity_rate,
        cost=_f("cooling_upgrade_cost_gbp", max(1000.0, floor_area_m2 * 12.0)),
    )
    ventilation = calculate_ventilation_improvement(
        fan_power_kw=_f("ventilation_fan_power_kw", max(1.0, floor_area_m2 / 120.0)),
        annual_hours=_f("ventilation_annual_hours", _f("weekly_operational_hours", 40.0) * 52.0),
        electricity_rate=electricity_rate,
        cost=_f("ventilation_upgrade_cost_gbp", max(800.0, floor_area_m2 * 8.0)),
    )
    refrigeration = calculate_refrigeration(
        total_electric_kwh=max(electricity_kwh, 0.0),
        electricity_rate=electricity_rate,
        implementation_cost_gbp=_f("refrigeration_upgrade_cost_gbp", max(1500.0, floor_area_m2 * 10.0)),
    )
    solar = calculate_solar(
        system_kwp=_f("solar_system_kwp", max(5.0, floor_area_m2 / 40.0)),
        electricity_rate=electricity_rate,
        implementation_cost_gbp=_f("solar_cost_gbp", max(6000.0, floor_area_m2 * 30.0)),
    )
    energy_mgmt = calculate_energy_management_savings(
        total_annual_kwh=max(electricity_kwh, 0.0),
        electricity_rate=electricity_rate,
        cost=_f("energy_management_cost_gbp", max(1000.0, floor_area_m2 * 6.0)),
    )
    misc_e = calculate_misc_electric(
        total_electric_kwh=max(electricity_kwh, 0.0),
        electricity_rate=electricity_rate,
        cost=_f("misc_electric_cost_gbp", max(700.0, floor_area_m2 * 4.0)),
    )

    if gas_kwh > 0:
        boiler = calculate_boiler_upgrade(
            annual_gas_kwh=gas_kwh,
            gas_rate=gas_rate,
            implementation_cost_gbp=_f("boiler_upgrade_cost_gbp", max(2500.0, floor_area_m2 * 18.0)),
        )
        building_fabric = calculate_building_fabric_improvement(
            annual_heating_kwh=gas_kwh,
            fuel_rate=gas_rate,
            cost=_f("building_fabric_cost_gbp", max(3000.0, floor_area_m2 * 22.0)),
        )
        heatpump = calculate_heatpump_replacement(
            annual_gas_kwh=gas_kwh,
            gas_rate=gas_rate,
            electricity_rate=electricity_rate,
            implementation_cost_gbp=_f("heat_pump_cost_gbp", max(6000.0, floor_area_m2 * 40.0)),
        )
        heaters = calculate_heaters_replacement(
            annual_heater_kwh=max(gas_kwh * 0.35, 0.0),
            electricity_rate=electricity_rate,
            cost=_f("heater_upgrade_cost_gbp", max(1200.0, floor_area_m2 * 9.0)),
        )
        misc_g = calculate_misc_gas(
            total_gas_kwh=max(gas_kwh, 0.0),
            gas_rate=gas_rate,
            cost=_f("misc_gas_cost_gbp", max(700.0, floor_area_m2 * 4.0)),
        )
    else:
        boiler = {
            "estimated_annual_kwh_saved": 0.0,
            "estimated_annual_saving_gbp": 0.0,
            "estimated_annual_co2_saved_tonnes": 0.0,
            "estimated_implementation_cost_gbp": 0.0,
            "payback_years": 0.0,
        }
        building_fabric = dict(boiler)
        heatpump = dict(boiler)
        heaters = calculate_heaters_replacement(
            annual_heater_kwh=max(electricity_kwh * 0.20, 0.0),
            electricity_rate=electricity_rate,
            cost=_f("heater_upgrade_cost_gbp", max(1200.0, floor_area_m2 * 9.0)),
        )
        misc_g = dict(boiler)

    candidates: List[Dict[str, Any]] = [
        {"code": "SOLAR_PANELS", "title": "Solar Panels", "result": solar, "hint": "On-site generation opportunity."},
        {"code": "HEAT_PUMPS", "title": "Heat Pumps", "result": heatpump, "hint": "Heating electrification option."},
        {"code": "LED_LIGHTING", "title": "LED Lighting", "result": led, "hint": "Lighting efficiency improvement."},
        {"code": "BUILDING_FABRIC", "title": "Building Fabric", "result": building_fabric, "hint": "Insulation and envelope improvements."},
        {"code": "COOLING", "title": "Cooling", "result": cooling, "hint": "Cooling controls and equipment efficiency."},
        {"code": "BOILER", "title": "Boiler", "result": boiler, "hint": "Boiler efficiency or replacement."},
        {"code": "REFRIGERATION", "title": "Refrigeration", "result": refrigeration, "hint": "Refrigeration efficiency upgrade."},
        {"code": "VENTILATION", "title": "Ventilation", "result": ventilation, "hint": "Fan and ventilation optimisation."},
        {"code": "HEATERS", "title": "Heaters", "result": heaters, "hint": "Heater replacement/controls."},
        {
            "code": "ENERGY_MANAGEMENT_BEHAVIOURAL",
            "title": "Energy Management/Behavioural",
            "result": energy_mgmt,
            "hint": "Controls, schedules, and behavioural measures.",
        },
        {"code": "MISC_ELECTRICITY", "title": "Misc. Electricity", "result": misc_e, "hint": "Cross-cutting electricity measures."},
        {"code": "MISC_GAS", "title": "Misc. Gas", "result": misc_g, "hint": "Cross-cutting gas measures."},
    ]

    measures: List[Dict[str, Any]] = []
    for c in candidates:
        r = c["result"] or {}
        savings = float(r.get("estimated_annual_saving_gbp", 0) or 0)
        kwh = float(r.get("estimated_annual_kwh_saved", 0) or 0)
        co2 = float(r.get("estimated_annual_co2_saved_tonnes", 0) or 0)
        capex = float(r.get("estimated_implementation_cost_gbp", 0) or 0)
        payback = float(r.get("payback_years", 0) or 0)

        # Keep list rich, but avoid clearly inapplicable measures with zero impact.
        if savings <= 0 and kwh <= 0 and co2 <= 0:
            if c["code"] == "SOLAR_PANELS" and not _is_yes("consider_solar_pv"):
                continue
            if c["code"] in {"BOILER", "HEAT_PUMPS", "MISC_GAS"} and gas_kwh <= 0:
                continue
            if c["code"] == "COOLING" and not _is_yes("has_cooling"):
                continue
            if c["code"] == "REFRIGERATION" and not _is_yes("has_refrigeration"):
                continue

        measures.append(
            {
                "code": c["code"],
                "title": c["title"],
                "description": c["title"],
                "capex_gbp": capex,
                "annual_savings_kwh": kwh,
                "annual_savings_gbp": savings,
                "simple_payback_years": payback,
                "estimated_annual_co2_saved_tonnes": co2,
                "applicability_hint": c["hint"],
            }
        )

    return measures

