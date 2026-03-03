from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from . import models, schemas


def create_submission(db: Session, submission_in: schemas.SubmissionCreate) -> models.Submission:
    submission = models.Submission(
        business_name=submission_in.business_name,
        postcode=submission_in.postcode,
        raw_answers=submission_in.answers,
        status="received",
    )
    db.add(submission)
    db.commit()
    db.refresh(submission)
    return submission


def get_submission(db: Session, submission_id: int) -> Optional[models.Submission]:
    return db.query(models.Submission).filter(models.Submission.id == submission_id).first()


def update_report(
    db: Session,
    submission_id: int,
    report_json: Dict[str, Any],
    status: str = "ready",
) -> Optional[models.Submission]:
    submission = get_submission(db, submission_id)
    if not submission:
        return None

    submission.report_json = report_json
    submission.status = status
    db.add(submission)
    db.commit()
    db.refresh(submission)
    return submission

