from __future__ import annotations

from backend.rag.validation import merge_and_validate_recommendations


def test_merge_and_validate_recommendations_uses_deterministic_values():
    candidates = [
        {
            "measure_code": "LED_UPGRADE",
            "kwh_saved": 1000.0,
            "cost_saved": 300.0,
            "carbon_saved": 0.25,
            "simple_payback": 3.0,
            "estimated_annual_kwh_saved": 1000.0,
            "estimated_annual_saving_gbp": 300.0,
            "estimated_implementation_cost_gbp": 5000.0,
            "payback_years": 3.0,
            "estimated_annual_co2_saved_tonnes": 0.25,
            "applicability_hint": "test",
        }
    ]
    llm_recs = [
        {
            "measure_code": "LED_UPGRADE",
            "recommendation_text": "Do LEDs",
            "priority": 1,
            "confidence": "High",
            # Deliberately conflicting numeric values
            "estimated_annual_kwh_saved": 9999.0,
            "estimated_annual_saving_gbp": 9999.0,
            "estimated_implementation_cost_gbp": 9999.0,
            "payback_years": 99.0,
            "estimated_annual_co2_saved_tonnes": 9.9,
        }
    ]

    merged = merge_and_validate_recommendations(candidates, llm_recs, rel_tol=0.01, abs_tol=1e-6)
    assert len(merged) == 1
    rec = merged[0]

    # Deterministic values should win over LLM-supplied ones
    assert rec["estimated_annual_kwh_saved"] == 1000.0
    assert rec["estimated_annual_saving_gbp"] == 300.0
    assert rec["estimated_implementation_cost_gbp"] == 5000.0
    assert rec["payback_years"] == 3.0
    assert rec["estimated_annual_co2_saved_tonnes"] == 0.25

    # Legacy fields are also populated
    assert rec["kwh_saved"] == 1000.0
    assert rec["cost_saved"] == 300.0
    assert rec["carbon_saved"] == 0.25
    assert rec["simple_payback"] == 3.0

