"""
Safe prompt template for the recommendation LLM. Instructs the model to use provided
numbers only and to output JSON with executive_summary and recommendations.
"""

from __future__ import annotations

from typing import Any, Dict, List


def build_recommendation_prompt(
    baseline: Dict[str, Any],
    candidates: List[Dict[str, Any]],
    retrieved_context: List[Dict[str, Any]],
) -> str:
    """
    Build a single prompt string for the LLM. Instructs to NEVER compute numeric values
    (numbers are provided), to write an executive summary and rank candidates (1..N)
    with short reasoning, and to output JSON only with executive_summary and
    recommendations (measure_code, recommendation_text, priority, confidence).
    """
    parts = [
        "You are an energy assessor. NEVER compute numeric values; all numbers below are provided.",
        "",
        "## Baseline (use as-is)",
        f"Annual kWh: {baseline.get('annual_kwh')}",
        f"Annual cost GBP: {baseline.get('annual_cost_gbp')}",
        f"Tariff p/kWh: {baseline.get('tariff_p_per_kwh')}",
        f"Annual CO2 tonnes: {baseline.get('annual_co2_tonnes')}",
        "",
        "## Candidate measures (use provided numbers only)",
    ]
    for c in candidates:
        parts.append(
            f"- {c.get('measure_code')}: {c.get('measure_label')} | "
            f"kwh_saved={c.get('kwh_saved')} cost_saved={c.get('cost_saved')} "
            f"carbon_saved={c.get('carbon_saved')} payback={c.get('simple_payback')} | "
            f"{c.get('applicability_hint', '')}"
        )
    parts.append("")
    parts.append("## Context (retrieved excerpts)")
    for i, ch in enumerate(retrieved_context, 1):
        meta = ch.get("metadata") or {}
        parts.append(f"[{i}] {meta.get('filename', '')} (section: {meta.get('section', '')})")
        parts.append((ch.get("text") or "")[:800])
        parts.append("")
    parts.append(
        "Using only the numbers above, write a short executive_summary and rank the candidates 1..N "
        "with brief reasoning. Output JSON only with keys: executive_summary (string), recommendations "
        "(array of objects with measure_code, recommendation_text, priority, confidence)."
    )
    return "\n".join(parts)
