import logging
from typing import Any, Dict

from sqlalchemy.orm import Session

from .. import calculators, crud


logger = logging.getLogger("app.services.submission_service")


def process_submission(db: Session, submission_id: int) -> Dict[str, Any]:
    """
    Load a submission, run simple deterministic calculators, and persist a report.

    For now this runs synchronously. In the future, this should be moved to a
    background worker or async task processor.

    TODO: Move processing to an async/background job once infrastructure is ready.
    """
    logger.info("Starting processing for submission_id=%s", submission_id)

    try:
        submission = crud.get_submission(db, submission_id)
        if not submission:
            raise ValueError(f"Submission {submission_id} not found")

        answers: Dict[str, Any] = dict(submission.raw_answers or {})

        baseline = calculators.compute_baseline(answers)
        measures = calculators.compute_measure_summaries(answers)

        report = {
            "baseline": baseline,
            "measures": measures,
        }

        updated = crud.update_report(
            db,
            submission_id=submission_id,
            report_json=report,
            status="ready",
        )
        if not updated:
            raise RuntimeError(f"Failed to update report for submission {submission_id}")

        logger.info(
            "Finished processing submission_id=%s; status=%s",
            submission_id,
            updated.status,
        )
        return report
    except Exception:
        logger.exception("Error processing submission_id=%s", submission_id)
        # Re-raise so callers can decide how to surface the error.
        raise

