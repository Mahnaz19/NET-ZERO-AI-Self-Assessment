"""
RAG→LLM recommendation pipeline: load submission, compute baseline/candidates,
retrieve chunks, build prompt, call LLM, persist and return report.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

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

    # 4) Benchmark row for sector
    benchmark_row: Optional[Dict[str, Any]] = None
    if BENCHMARKS_CSV.is_file() and sector:
        try:
            import pandas as pd
            df = pd.read_csv(BENCHMARKS_CSV)
            if "sector" in df.columns:
                match = df[df["sector"].astype(str).str.contains(sector, case=False, na=False)]
                if not match.empty:
                    benchmark_row = match.iloc[0].to_dict()
        except Exception as e:
            logger.warning("Could not load benchmark for sector %s: %s", sector, e)

    # 5) Build prompt
    prompt = _build_prompt(
        submission_id=submission_id,
        baseline_summary=baseline_summary,
        benchmark_row=benchmark_row,
        candidates=candidates,
        chunks=chunks,
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
        llm_out = client.generate(prompt)
    except Exception as e:
        logger.exception("LLM generate failed for submission_id=%s: %s", submission_id, e)
        raise

    if not isinstance(llm_out, dict):
        raise ValueError("LLM did not return a dict")
    recs = llm_out.get("recommendations")
    if not isinstance(recs, list):
        raise ValueError("LLM response missing or invalid 'recommendations' list")
    exec_summary = llm_out.get("executive_summary")
    if exec_summary is None:
        exec_summary = ""

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

    # 7) Persist
    updated = crud.update_report(db, submission_id, report, status="ready")
    if not updated:
        raise RuntimeError(f"Failed to update report for submission {submission_id}")

    return report


def _build_prompt(
    submission_id: int,
    baseline_summary: Dict[str, Any],
    benchmark_row: Optional[Dict[str, Any]],
    candidates: List[Dict[str, Any]],
    chunks: List[Dict[str, Any]],
) -> str:
    parts = [
        "You are an energy assessor assistant. Do not invent numeric energy calculations; use only the figures provided.",
        "Submission id: " + str(submission_id),
        "",
        "## Baseline (deterministic)",
        f"Annual kWh: {baseline_summary.get('annual_kwh')}",
        f"Annual cost GBP: {baseline_summary.get('annual_cost_gbp')}",
        f"Tariff p/kWh: {baseline_summary.get('tariff_p_per_kwh')}",
        f"Annual CO2 tonnes: {baseline_summary.get('annual_co2_tonnes')}",
        "",
    ]
    if benchmark_row:
        parts.append("## Sector benchmarks (reference)")
        parts.append(str(benchmark_row))
        parts.append("")
    parts.append("## Candidate measures (deterministic numbers)")
    for c in candidates:
        parts.append(
            f"- {c.get('measure_code')}: {c.get('measure_label')} | "
            f"kwh_saved={c.get('kwh_saved')} cost_saved={c.get('cost_saved')} "
            f"carbon_saved={c.get('carbon_saved')} payback={c.get('simple_payback')} | "
            f"{c.get('applicability_hint', '')}"
        )
    parts.append("")
    parts.append("## Assessor context (retrieved report excerpts)")
    for i, ch in enumerate(chunks, 1):
        meta = ch.get("metadata") or {}
        parts.append(f"[{i}] {meta.get('filename', '')} (section: {meta.get('section', '')})")
        parts.append((ch.get("text") or "")[:800])
        parts.append("")
    parts.append(
        "Review the candidate measures and the assessor context. Output a JSON object with exactly: "
        '"recommendations" (array of objects with measure_code, score, recommendation_text, priority, confidence) '
        'and "executive_summary" (short string). Do not recalculate numbers; use the candidate figures.'
    )
    return "\n".join(parts)
