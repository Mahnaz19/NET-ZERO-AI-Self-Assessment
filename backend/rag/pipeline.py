"""
RAG→LLM recommendation pipeline: load submission, compute baseline/candidates,
retrieve chunks, build prompt, call LLM, persist and return report.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parents[2]
BENCHMARKS_CSV = REPO_ROOT / "data" / "processed" / "benchmarks_by_sector.csv"
UK_ELECTRICITY_CO2_FACTOR = 0.000233  # tonnes CO2e per kWh (match app/calculators)


def run_recommendation_pipeline(
    db: Session,
    submission_id: int,
    top_k: int = 5,
    provider: str = "auto",
) -> Dict[str, Any]:
    """
    Load submission, compute deterministic baseline and candidates, retrieve RAG chunks,
    call LLM for ranking and recommendation text, persist report and return it.
    """
    from app import calculators, crud
    from .llm_client import get_llm_client
    from .prompt_templates import build_recommendation_prompt
    from .retriever_adapter import retrieve_text_chunks

    submission = crud.get_submission(db, submission_id)
    if not submission:
        raise ValueError(f"Submission {submission_id} not found")

    answers: Dict[str, Any] = dict(submission.raw_answers or {})

    # 1) Deterministic baseline
    baseline = calculators.compute_baseline(answers)
    baseline_summary = {
        "annual_kwh": baseline.get("annual_kwh", 0),
        "annual_cost_gbp": baseline.get("annual_cost_gbp", 0),
        "tariff_p_per_kwh": baseline.get("tariff_p_per_kwh", 0),
        "annual_co2_tonnes": baseline.get("annual_co2_tonnes", 0),
    }

    # 2) Deterministic candidate measures
    measure_summaries = calculators.compute_measure_summaries(answers)
    candidates: List[Dict[str, Any]] = []
    for m in measure_summaries:
        kwh = float(m.get("annual_savings_kwh", 0) or 0)
        candidates.append({
            "measure_code": m.get("code", ""),
            "measure_label": m.get("title", ""),
            "kwh_saved": kwh,
            "cost_saved": float(m.get("annual_savings_gbp", 0) or 0),
            "carbon_saved": round(kwh * UK_ELECTRICITY_CO2_FACTOR, 4),
            "simple_payback": float(m.get("simple_payback_years", 0) or 0),
            "applicability_hint": m.get("applicability_hint", "") or "",
        })

    # 3) RAG retrieval
    sector = (answers.get("sector") or "").strip() or None
    query = "energy saving recommendations baseline consumption"
    chunks = retrieve_text_chunks(query, top_k=top_k, sector=sector, provider=provider)
    if not chunks:
        logger.info("No RAG chunks retrieved for submission_id=%s", submission_id)

    # 4) Build prompt
    prompt = build_recommendation_prompt(
        baseline=baseline_summary,
        candidates=candidates,
        retrieved_context=chunks,
    )

    # 6) Call LLM and parse
    settings = None
    try:
        from app.config import settings as app_settings
        settings = app_settings
    except Exception:
        pass
    client = get_llm_client(settings)
    try:
        raw = client.generate(prompt, max_tokens=512, temperature=0.0)
    except Exception as e:
        logger.exception("LLM generate failed for submission_id=%s: %s", submission_id, e)
        return {"error": True, "message": f"LLM generate failed: {e}"}

    # Azure returns {text, raw_response}; MockLLM returns {executive_summary, recommendations}
    if isinstance(raw.get("text"), str):
        import json
        try:
            llm_out = json.loads(raw["text"])
        except json.JSONDecodeError as e:
            logger.warning("LLM response was not valid JSON for submission_id=%s: %s", submission_id, e)
            return {"error": True, "message": f"LLM response was not valid JSON: {e}"}
    else:
        llm_out = raw

    if not isinstance(llm_out, dict):
        logger.warning("LLM did not return a dict for submission_id=%s", submission_id)
        return {"error": True, "message": "LLM did not return a dict"}
    recs = llm_out.get("recommendations")
    if not isinstance(recs, list):
        logger.warning("LLM response missing or invalid 'recommendations' for submission_id=%s", submission_id)
        return {"error": True, "message": "LLM response missing or invalid 'recommendations' list"}
    exec_summary = llm_out.get("executive_summary")
    if exec_summary is None:
        exec_summary = ""
    # Validate each recommendation has required fields (allow extras)
    required_rec_keys = {"measure_code", "recommendation_text", "priority", "confidence"}
    for i, r in enumerate(recs):
        if not isinstance(r, dict) or not required_rec_keys.issubset(r.keys()):
            logger.warning(
                "LLM recommendation[%s] missing required keys for submission_id=%s",
                i, submission_id,
            )
            return {"error": True, "message": "LLM recommendation(s) missing required fields"}

    # Merge deterministic numbers into recommendations by measure_code
    candidate_by_code = {c["measure_code"]: c for c in candidates}
    merged_recs = []
    for r in recs:
        code = r.get("measure_code") or ""
        det = candidate_by_code.get(code, {})
        merged_recs.append({
            "measure_code": code,
            "score": r.get("score"),
            "recommendation_text": r.get("recommendation_text") or "",
            "priority": r.get("priority"),
            "confidence": r.get("confidence"),
            "kwh_saved": det.get("kwh_saved"),
            "cost_saved": det.get("cost_saved"),
            "carbon_saved": det.get("carbon_saved"),
            "simple_payback": det.get("simple_payback"),
            "applicability_hint": det.get("applicability_hint"),
        })

    report = {
        "executive_summary": exec_summary,
        "recommendations": merged_recs,
        "baseline": baseline_summary,
        "candidates": candidates,
    }

    # 6) Persist
    updated = crud.update_report(db, submission_id, report, status="ready")
    if not updated:
        raise RuntimeError(f"Failed to update report for submission {submission_id}")

    return report
