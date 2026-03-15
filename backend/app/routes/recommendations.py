"""
Recommendations API: trigger RAG→LLM pipeline and return stored report.
"""

import logging
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from .. import crud
from ..db import get_db
from rag.pipeline import run_recommendation_pipeline

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["recommendations"])


class RecommendationRequest(BaseModel):
    submission_id: int
    top_k: Optional[int] = 5


@router.post(
    "/recommendations",
    status_code=status.HTTP_200_OK,
)
def create_recommendations(
    body: RecommendationRequest,
    db: Session = Depends(get_db),
) -> Any:
    """
    Run the RAG→LLM recommendation pipeline for the given submission.
    Returns the generated report (200). Uses parquet fallback if pgvector unavailable.
    """
    try:
        report = run_recommendation_pipeline(
            db,
            submission_id=body.submission_id,
            top_k=body.top_k or 5,
            provider="auto",
        )
        return report
    except ValueError as e:
        if "not found" in str(e).lower():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.exception("Recommendation pipeline failed for submission_id=%s", body.submission_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Recommendation generation failed",
        )


@router.get("/recommendations/{submission_id}")
def get_recommendations(
    submission_id: int,
    db: Session = Depends(get_db),
) -> Any:
    """Return the stored report_json for the submission, or 404."""
    submission = crud.get_submission(db, submission_id)
    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Submission {submission_id} not found",
        )
    if submission.report_json is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No report yet for submission {submission_id}",
        )
    return submission.report_json
