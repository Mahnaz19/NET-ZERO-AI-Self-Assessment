"""
Validation helpers for LLM-generated recommendations.

- parse_llm_output: safe JSON parsing from raw LLM text.
- compute_deterministic_fields: derive numeric fields from deterministic candidates/baseline.
- validate_recommendations: compare LLM numbers against deterministic ones and adjust confidence.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, ValidationError

from .llm_client import _parse_llm_json


DEFAULT_TOLERANCES: Dict[str, float] = {
    "kwh_saved": 0.05,       # 5%
    "cost_saved": 0.05,      # 5%
    "carbon_saved": 0.05,    # 5%
    "simple_payback": 0.10,  # 10%
}


def parse_llm_output(text: str) -> Dict[str, Any]:
    """
    Parse JSON from LLM text. Returns a dict with at least:
    - executive_summary: str
    - recommendations: list[dict]
    Raises ValueError with an informative message on failure.
    """
    try:
        data = _parse_llm_json(text)
    except Exception as exc:  # noqa: BLE001
        raise ValueError(f"Could not parse LLM JSON: {exc}") from exc

    if not isinstance(data, dict):
        raise ValueError("LLM JSON must be an object at the top level")

    exec_summary = data.get("executive_summary") or ""
    recs = data.get("recommendations")
    if not isinstance(recs, list):
        raise ValueError("LLM JSON missing 'recommendations' list")

    return {
        "executive_summary": str(exec_summary),
        "recommendations": recs,
    }


def compute_deterministic_fields(candidate_spec: Dict[str, Any], baseline: Dict[str, Any]) -> Dict[str, float]:
    """
    Compute deterministic numeric fields for a candidate recommendation.

    In this implementation the pipeline has already called the deterministic calculators
    to produce candidate_spec, so we simply read the numeric fields from there.
    """
    return {
        "kwh_saved": float(candidate_spec.get("kwh_saved", 0) or 0),
        "cost_saved": float(candidate_spec.get("cost_saved", 0) or 0),
        "carbon_saved": float(candidate_spec.get("carbon_saved", 0) or 0),
        "simple_payback": float(candidate_spec.get("simple_payback", 0) or 0),
    }


@dataclass
class _ValidatedRecommendation:
    measure_code: str
    recommendation_text: str
    priority: int
    confidence: str
    kwh_saved: float
    cost_saved: float
    carbon_saved: float
    simple_payback: float
    applicability_hint: str
    validation_notes: Optional[Any]
    score: Optional[float] = None


class RecommendationModel(BaseModel):
    measure_code: str
    recommendation_text: str
    priority: int
    confidence: str = Field(pattern="^(high|medium|low)$")
    kwh_saved: float
    cost_saved: float
    carbon_saved: float
    simple_payback: float
    applicability_hint: str
    validation_notes: Optional[Any] = None
    score: Optional[float] = None


def _within_tolerance(expected: float, reported: float, tolerance: float) -> float:
    """
    Return delta_pct and rely on caller to interpret vs tolerance.
    Handles expected=0 as a special case (0% if both zero, 100% otherwise).
    """
    if expected == 0:
        if reported == 0:
            return 0.0
        return 1.0
    return abs(reported - expected) / abs(expected)


def validate_recommendations(
    baseline: Dict[str, Any],
    candidates: List[Dict[str, Any]],
    llm_recs: List[Dict[str, Any]],
    tolerance: Optional[Dict[str, float]] = None,
) -> List[Dict[str, Any]]:
    """
    Validate LLM recommendations against deterministic candidates.

    - If LLM supplies numbers: compare with deterministic ones using tolerances.
      * All within tolerance → confidence='high', validation_notes=None.
      * Any mismatch → confidence='low', validation_notes['mismatch'] populated.
    - If LLM omits numbers: fill them from deterministic candidates, confidence='high',
      validation_notes='numbers filled by deterministic calculators'.

    Also ensures the five standard measure fields are present in the output, based on
    deterministic numbers rather than any LLM-supplied values:
    - estimated_annual_kwh_saved
    - estimated_annual_saving_gbp
    - estimated_implementation_cost_gbp
    - payback_years
    - estimated_annual_co2_saved_tonnes
    """
    tol = {**DEFAULT_TOLERANCES, **(tolerance or {})}
    candidate_by_code = {c.get("measure_code", ""): c for c in candidates}

    validated: List[Dict[str, Any]] = []

    for raw in llm_recs:
        if not isinstance(raw, dict):
            raise ValueError("Each LLM recommendation must be an object")

        code = (raw.get("measure_code") or "").strip()
        candidate = candidate_by_code.get(code, {})
        det_fields = compute_deterministic_fields(candidate, baseline)

        has_llm_numbers = any(
            raw.get(f) is not None for f in ("kwh_saved", "cost_saved", "carbon_saved", "simple_payback")
        )

        mismatches: Dict[str, Dict[str, float]] = {}

        if has_llm_numbers:
            for field in ("kwh_saved", "cost_saved", "carbon_saved", "simple_payback"):
                reported_val = raw.get(field)
                if reported_val is None:
                    continue
                expected_val = det_fields[field]
                reported_f = float(reported_val)
                delta_pct = _within_tolerance(expected_val, reported_f, tol[field])
                if delta_pct > tol[field]:
                    mismatches[field] = {
                        "expected": expected_val,
                        "reported": reported_f,
                        "delta_pct": delta_pct,
                    }

        if not has_llm_numbers:
            confidence = "high"
            validation_notes: Optional[Any] = "numbers filled by deterministic calculators"
        elif mismatches:
            confidence = "low"
            validation_notes = {"mismatch": mismatches}
        else:
            confidence = "high"
            validation_notes = None

        rec = _ValidatedRecommendation(
            measure_code=code,
            recommendation_text=str(raw.get("recommendation_text") or ""),
            priority=int(raw.get("priority") or 0),
            confidence=confidence,
            kwh_saved=det_fields["kwh_saved"],
            cost_saved=det_fields["cost_saved"],
            carbon_saved=det_fields["carbon_saved"],
            simple_payback=det_fields["simple_payback"],
            applicability_hint=str(candidate.get("applicability_hint") or ""),
            validation_notes=validation_notes,
            score=float(raw["score"]) if raw.get("score") is not None else None,
        )

        try:
            model = RecommendationModel(**asdict(rec))
        except ValidationError as exc:  # pragma: no cover - defensive
            raise ValueError(f"Recommendation failed validation: {exc}") from exc

        out = model.model_dump()

        # Ensure the 5 standard measure fields are present and deterministic.
        out.update(
            {
                "estimated_annual_kwh_saved": det_fields["kwh_saved"],
                "estimated_annual_saving_gbp": det_fields["cost_saved"],
                "estimated_implementation_cost_gbp": float(
                    candidate.get("estimated_implementation_cost_gbp")
                    or candidate.get("capex_gbp")
                    or 0.0
                ),
                "payback_years": det_fields["simple_payback"],
                "estimated_annual_co2_saved_tonnes": det_fields["carbon_saved"],
            }
        )

        validated.append(out)

    return validated

