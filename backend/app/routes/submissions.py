import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import crud, schemas
from ..db import get_db
from ..services import submission_service


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

    # For MVP we run processing synchronously.
    logger = logging.getLogger("app.routes.submissions")
    logger.info(
        "Received submission id=%s — starting synchronous processing (dev only)",
        submission.id,
    )
    # TODO: Move processing to background worker (Celery / Azure Function / Azure Queue + Function)

    try:
        submission_service.process_submission(db, submission.id)
        logger.info("Completed processing for submission id=%s", submission.id)
    except Exception:  # noqa: BLE001
        # In MVP we still return 201 with 'received' status; we just log the error.
        # TODO: Plug in structured logging/monitoring for processing failures.
        logger.exception(
            "Error processing submission id=%s; returning current submission object",
            submission.id,
        )

    db.refresh(submission)
    return submission


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

