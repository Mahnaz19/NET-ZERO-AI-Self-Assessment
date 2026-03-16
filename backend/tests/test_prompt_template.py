"""Tests for build_recommendation_prompt."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

BACKEND = Path(__file__).resolve().parents[1]
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))


def test_build_recommendation_prompt_contains_required_tokens():
    from rag.prompt_templates import build_recommendation_prompt

    baseline = {"annual_kwh": 100, "annual_cost_gbp": 50, "tariff_p_per_kwh": 25, "annual_co2_tonnes": 0.5}
    candidates = [
        {
            "measure_code": "LED",
            "measure_label": "LED lighting",
            "kwh_saved": 10,
            "cost_saved": 5,
            "carbon_saved": 0.05,
            "simple_payback": 2,
            "applicability_hint": "Good for offices",
        },
    ]
    retrieved_context = [{"metadata": {"filename": "a.pdf", "section": "S1"}, "text": "Some context."}]
    prompt = build_recommendation_prompt(baseline=baseline, candidates=candidates, retrieved_context=retrieved_context)
    assert isinstance(prompt, str)
    assert "NEVER compute" in prompt
    assert "executive_summary" in prompt
    assert "recommendations" in prompt
