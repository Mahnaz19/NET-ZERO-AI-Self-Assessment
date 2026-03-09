from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from . import models, schemas


def _get_or_create_business(
    db: Session,
    business_name: Optional[str],
    postcode: Optional[str],
) -> Optional[models.Business]:
    """
    Find or create a canonical Business row for (business_name, postcode).
    If either is missing, return None and let the submission stand alone.
    """
    if not business_name or not postcode:
        return None

    existing = (
        db.query(models.Business)
        .filter(
            models.Business.business_name == business_name,
            models.Business.postcode == postcode,
        )
        .first()
    )
    if existing:
        return existing

    business = models.Business(business_name=business_name, postcode=postcode)
    db.add(business)
    db.commit()
    db.refresh(business)
    return business


def create_submission(db: Session, submission_in: schemas.SubmissionCreate) -> models.Submission:
    business = _get_or_create_business(
        db,
        business_name=submission_in.business_name,
        postcode=submission_in.postcode,
    )

    submission = models.Submission(
        business_name=submission_in.business_name,
        postcode=submission_in.postcode,
        business_id=business.id if business else None,
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

