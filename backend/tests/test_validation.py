"""
Tests for rag.validation: numeric matching, mismatching, and missing numbers.
"""

from __future__ import annotations

from typing import Any, Dict, List


def _baseline() -> Dict[str, Any]:
    return {"annual_kwh": 50000.0, "annual_cost_gbp": 15000.0, "tariff_p_per_kwh": 30.0, "annual_co2_tonnes": 11.65}


def _candidates() -> List[Dict[str, Any]]:
    return [
        {
            "measure_code": "LED_UPGRADE",
            "measure_label": "LED lighting",
            "kwh_saved": 1000.0,
            "cost_saved": 300.0,
            "carbon_saved": 0.233,
            "simple_payback": 2.5,
            "applicability_hint": "Good for offices",
        }
    ]


def test_llm_numbers_match(monkeypatch):
    """When LLM numbers match deterministic ones within tolerance, confidence is 'high'."""
    from rag import validation

    def _fake_det_fields(candidate_spec, baseline):
        return {
            "kwh_saved": 1000.0,
            "cost_saved": 300.0,
            "carbon_saved": 0.233,
            "simple_payback": 2.5,
        }

    monkeypatch.setattr(validation, "compute_deterministic_fields", _fake_det_fields)

    llm_recs = [
        {
            "measure_code": "LED_UPGRADE",
            "recommendation_text": "Upgrade to LED lighting.",
            "priority": 1,
            "kwh_saved": 990.0,  # within 5%
            "cost_saved": 295.0,
            "carbon_saved": 0.23,
            "simple_payback": 2.6,  # within 10%
        }
    ]

    out = validation.validate_recommendations(_baseline(), _candidates(), llm_recs)
    assert len(out) == 1
    rec = out[0]
    assert rec["confidence"] == "high"
    assert rec["validation_notes"] is None


def test_llm_numbers_mismatch(monkeypatch):
    """When LLM numbers differ beyond tolerance, confidence is 'low' and validation_notes is populated."""
    from rag import validation

    def _fake_det_fields(candidate_spec, baseline):
        return {
            "kwh_saved": 1000.0,
            "cost_saved": 300.0,
            "carbon_saved": 0.233,
            "simple_payback": 2.5,
        }

    monkeypatch.setattr(validation, "compute_deterministic_fields", _fake_det_fields)

    llm_recs = [
        {
            "measure_code": "LED_UPGRADE",
            "recommendation_text": "Upgrade to LED lighting.",
            "priority": 1,
            "kwh_saved": 2000.0,  # 100% off
            "cost_saved": 600.0,
            "carbon_saved": 0.5,
            "simple_payback": 10.0,
        }
    ]

    out = validation.validate_recommendations(_baseline(), _candidates(), llm_recs)
    rec = out[0]
    assert rec["confidence"] == "low"
    notes = rec["validation_notes"]
    assert isinstance(notes, dict)
    assert "mismatch" in notes
    assert "kwh_saved" in notes["mismatch"]


def test_llm_no_numbers(monkeypatch):
    """When LLM omits numbers, validation fills them deterministically and marks confidence 'high'."""
    from rag import validation

    def _fake_det_fields(candidate_spec, baseline):
        return {
            "kwh_saved": 123.0,
            "cost_saved": 45.0,
            "carbon_saved": 0.01,
            "simple_payback": 3.0,
        }

    monkeypatch.setattr(validation, "compute_deterministic_fields", _fake_det_fields)

    llm_recs = [
        {
            "measure_code": "LED_UPGRADE",
            "recommendation_text": "Upgrade to LED lighting.",
            "priority": 1,
        }
    ]

    out = validation.validate_recommendations(_baseline(), _candidates(), llm_recs)
    rec = out[0]
    assert rec["confidence"] == "high"
    assert rec["kwh_saved"] == 123.0
    assert rec["cost_saved"] == 45.0
    assert rec["validation_notes"] == "numbers filled by deterministic calculators"

