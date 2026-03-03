from typing import Any, Dict, List


def compute_baseline(answers: Dict[str, Any]) -> Dict[str, Any]:
    """
    Very simple deterministic baseline calculator.

    This is intentionally a placeholder and should be replaced with the
    proper assessor logic based on the Excel models in /docs.

    TODO: Replace with real baseline energy and carbon calculations derived
    from assessor Excel tools in /docs once the domain model is finalized.
    """
    annual_kwh = float(answers.get("annual_kwh", 0) or 0)
    annual_cost = float(answers.get("annual_cost_gbp", 0) or 0)

    tariff_p_per_kwh: float
    if annual_kwh > 0 and annual_cost > 0:
        # Convert GBP to pence for the tariff figure.
        tariff_p_per_kwh = (annual_cost * 100.0) / annual_kwh
    else:
        # Example default tariff; not domain-accurate.
        tariff_p_per_kwh = 30.0

    # Simple carbon intensity factor (kgCO2e per kWh) converted to tonnes.
    annual_co2_tonnes = annual_kwh * 0.000233

    return {
        "annual_kwh": annual_kwh,
        "annual_cost_gbp": annual_cost,
        "tariff_p_per_kwh": tariff_p_per_kwh,
        "annual_co2_tonnes": annual_co2_tonnes,
    }


def compute_measure_summaries(answers: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Return a deterministic example list of potential measures.

    These are placeholders to demonstrate shape only.

    TODO: Replace with real measure selection and impact logic based on
    assessor guidance and Excel models in /docs.
    """
    # Use very simple dummy measures that depend slightly on input size.
    floor_area_m2 = float(answers.get("floor_area_m2", 100) or 100)
    usage_profile = answers.get("usage_profile", "office")

    measures: List[Dict[str, Any]] = [
        {
            "code": "LED_UPGRADE",
            "title": "Upgrade to LED lighting",
            "description": "Replace existing lighting with high-efficiency LED fittings.",
            "capex_gbp": round(floor_area_m2 * 5.0, 2),
            "annual_savings_kwh": round(floor_area_m2 * 3.0, 2),
            "annual_savings_gbp": round(floor_area_m2 * 3.0 * 0.30, 2),
            "simple_payback_years": 3.0,
        },
        {
            "code": "HEATING_CONTROLS",
            "title": "Heating controls optimisation",
            "description": "Improve control schedules and setpoints for heating system.",
            "capex_gbp": 500.0,
            "annual_savings_kwh": 1500.0,
            "annual_savings_gbp": 450.0,
            "simple_payback_years": 1.1,
            "applicability_hint": f"Especially relevant for {usage_profile} spaces.",
        },
    ]

    return measures

