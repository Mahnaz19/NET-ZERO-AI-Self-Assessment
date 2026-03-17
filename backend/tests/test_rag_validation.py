from __future__ import annotations

from backend.rag.validation import validate_recommendations


def test_validate_recommendations_populates_standard_fields_from_deterministic():
    baseline = {"annual_kwh": 50000.0, "annual_cost_gbp": 15000.0, "tariff_p_per_kwh": 30.0, "annual_co2_tonnes": 11.65}
    candidates = [
        {
            "measure_code": "LED_UPGRADE",
            "measure_label": "LED lighting",
            "kwh_saved": 1000.0,
            "cost_saved": 300.0,
            "carbon_saved": 0.25,
            "simple_payback": 3.0,
            "capex_gbp": 5000.0,
            "applicability_hint": "test",
        }
    ]
    llm_recs = [
        {
            "measure_code": "LED_UPGRADE",
            "recommendation_text": "Do LEDs",
            "priority": 1,
            # Deliberately conflicting numeric values; should be ignored in favour of deterministic.
            "estimated_annual_kwh_saved": 9999.0,
            "estimated_annual_saving_gbp": 9999.0,
            "estimated_implementation_cost_gbp": 9999.0,
            "payback_years": 99.0,
            "estimated_annual_co2_saved_tonnes": 9.9,
        }
    ]

    merged = validate_recommendations(baseline, candidates, llm_recs)
    assert len(merged) == 1
    rec = merged[0]

    # Deterministic values should populate legacy fields
    assert rec["kwh_saved"] == 1000.0
    assert rec["cost_saved"] == 300.0
    assert rec["carbon_saved"] == 0.25
    assert rec["simple_payback"] == 3.0

    # And the 5 standard fields, overriding any conflicting LLM values
    assert rec["estimated_annual_kwh_saved"] == 1000.0
    assert rec["estimated_annual_saving_gbp"] == 300.0
    assert rec["estimated_implementation_cost_gbp"] == 5000.0
    assert rec["payback_years"] == 3.0
    assert rec["estimated_annual_co2_saved_tonnes"] == 0.25

