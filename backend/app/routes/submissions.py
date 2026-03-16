import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import crud, schemas
from ..db import get_db
from ..worker import enqueue_submission, process_submission_job


router = APIRouter(prefix="/api", tags=["submissions"])


@router.post(
    "/submit",
    response_model=schemas.SubmissionOut,
    status_code=status.HTTP_201_CREATED,
)
def submit_assessment(
    submission_in: schemas.SubmissionCreate,
    db: Session = Depends(get_db),
) -> Any:
    submission = crud.create_submission(db, submission_in)

    logger = logging.getLogger("app.routes.submissions")
    logger.info("Received submission id=%s — enqueuing background processing", submission.id)
    enqueue_submission(submission.id)

    return submission


@router.post(
    "/admin/process_submission",
    status_code=status.HTTP_202_ACCEPTED,
)
def admin_process_submission(
    body: schemas.SubmissionCreate,
    db: Session = Depends(get_db),
) -> Any:
    """
    Admin/dev-only endpoint to manually trigger processing for a submission.
    This calls the same worker function that RQ uses, but inline.
    """
    if not body.answers or "submission_id" not in body.answers:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Body must include answers.submission_id for admin processing",
        )
    submission_id = int(body.answers["submission_id"])
    submission = crud.get_submission(db, submission_id)
    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Submission {submission_id} not found",
        )
    logger = logging.getLogger("app.routes.submissions")
    logger.info("Admin requested manual processing for submission id=%s", submission_id)
    # Call worker job directly with existing DB session to avoid extra connections in tests.
    report = process_submission_job(submission_id)
    db.refresh(submission)
    return {"submission_id": submission.id, "status": submission.status, "report": report}


@router.get(
    "/report/{submission_id}",
    response_model=schemas.SubmissionOut,
)
def get_report(
    submission_id: int,
    db: Session = Depends(get_db),
) -> Any:
    submission = crud.get_submission(db, submission_id)
    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Submission {submission_id} not found",
        )
    return submission

