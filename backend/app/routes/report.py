"""
Report generation API: generate PDF and HTML preview from stored report JSON.
No LLM calls — only reads deterministic report data from the DB.
"""

from __future__ import annotations

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, Response
from pydantic import BaseModel
from sqlalchemy.orm import Session

from .. import crud
from ..db import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["reports"])


class GeneratePdfRequest(BaseModel):
    """Request body for POST /api/reports/generate_pdf."""

    submission_id: int


def _get_report_or_400(db: Session, submission_id: int) -> dict:
    """
    Load submission and return report_json. Raises 404 if submission not found,
    400 if no report_json or report is an error payload.
    """
    submission = crud.get_submission(db, submission_id)
    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Submission {submission_id} not found",
        )
    if submission.report_json is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No report available for submission {submission_id}. Run the recommendations pipeline first.",
        )
    report = submission.report_json
    if isinstance(report, dict) and report.get("error") is True:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=report.get("message", "Report generation previously failed."),
        )
    return report


@router.post(
    "/reports/generate_pdf",
    status_code=status.HTTP_200_OK,
    response_class=Response,
)
def generate_pdf(
    body: GeneratePdfRequest,
    db: Session = Depends(get_db),
) -> Response:
    """
    Generate a PDF from the stored report for the given submission.
    Returns 400 if no report_json exists (run recommendations pipeline first).
    """
    from reportgen import render_report_pdf_bytes

    report = _get_report_or_400(db, body.submission_id)
    try:
        pdf_bytes = render_report_pdf_bytes(report)
    except RuntimeError as e:
        logger.exception("PDF generation failed for submission_id=%s", body.submission_id)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="PDF generation is not available. Install WeasyPrint or Playwright (see backend README).",
        ) from e
    filename = f"report_{body.submission_id}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )


@router.get(
    "/reports/html/{submission_id}",
    response_class=HTMLResponse,
)
def get_report_html(
    submission_id: int,
    db: Session = Depends(get_db),
) -> HTMLResponse:
    """
    Return the rendered HTML for the submission's report (for preview/debugging).
    """
    from reportgen import render_report_html

    report = _get_report_or_400(db, submission_id)
    html = render_report_html(report)
    return HTMLResponse(content=html)
