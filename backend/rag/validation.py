from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Optional

import logging


logger = logging.getLogger(__name__)


NUMERIC_KEYS_LEGACY = (
    "kwh_saved",
    "cost_saved",
    "carbon_saved",
    "simple_payback",
)

NUMERIC_KEYS_STANDARD = (
    "estimated_annual_kwh_saved",
    "estimated_annual_saving_gbp",
    "estimated_implementation_cost_gbp",
    "payback_years",
    "estimated_annual_co2_saved_tonnes",
)


def _is_close(det: Optional[float], llm_val: Optional[float], *, rel_tol: float, abs_tol: float) -> bool:
    if det is None or llm_val is None:
        return False
    try:
        det_f = float(det)
        llm_f = float(llm_val)
    except (TypeError, ValueError):
        return False
    if abs(det_f - llm_f) <= abs_tol:
        return true
    if det_f == 0:
        return False
    return abs(det_f - llm_f) / abs(det_f) <= rel_tol


def merge_and_validate_recommendations(
    candidates: Iterable[Mapping[str, Any]],
    llm_recommendations: Iterable[Mapping[str, Any]],
    *,
    rel_tol: float = 0.20,
    abs_tol: float = 1e-6,
    _logger: Optional[logging.Logger] = None,
) -> List[Dict[str, Any]]:
    """
    Merge deterministic candidate numbers into LLM recommendations, and validate any
    numeric fields supplied by the LLM against the deterministic ones.

    Deterministic values always win; if the LLM provides a conflicting number for
    a known numeric key, the deterministic value is kept and a warning is logged.
    """
    log = _logger or logger
    candidate_by_code: Dict[str, Mapping[str, Any]] = {}
    for c in candidates:
        code = str(c.get("measure_code") or "")
        if code:
            candidate_by_code[code] = c

    merged: List[Dict[str, Any]] = []
    for idx, r in enumerate(llm_recommendations):
        if not isinstance(r, Mapping):
            continue
        code = str(r.get("measure_code") or "")
        det = candidate_by_code.get(code, {})

        out: Dict[str, Any] = {
            "measure_code": code,
            "score": r.get("score"),
            "recommendation_text": r.get("recommendation_text") or "",
            "priority": r.get("priority"),
            "confidence": r.get("confidence"),
            "applicability_hint": det.get("applicability_hint"),
        }

        # First copy deterministic numeric values
        for key in (*NUMERIC_KEYS_LEGACY, *NUMERIC_KEYS_STANDARD):
            if key in det:
                out[key] = det.get(key)

        # Then inspect any LLM-supplied numeric values for the same keys and validate.
        for key in (*NUMERIC_KEYS_LEGACY, *NUMERIC_KEYS_STANDARD):
            if key not in r:
                continue
            llm_val = r.get(key)
            det_val = out.get(key)
            if det_val is None:
                # If we have no deterministic number for this key, allow the LLM value through.
                out[key] = llm_val
                continue
            if not _is_close(det_val, llm_val, rel_tol=rel_tol, abs_tol=abs_tol):
                log.warning(
                    "LLM value for %s on measure_code=%s (index=%s) differed from deterministic;"
                    " keeping deterministic value. det=%r, llm=%r",
                    key,
                    code,
                    idx,
                    det_val,
                    llm_val,
                )
            # Deterministic value already in out; we intentionally ignore conflicting llm_val.

        merged.append(out)

    return merged

