"""
Background worker functions for processing submissions asynchronously with RQ.

The main entry point is process_submission_job(submission_id), which can be
run by an rq worker. This calls the existing RAG→LLM pipeline to generate
and persist a report for the submission.
"""

from __future__ import annotations

import logging
from typing import Any

try:
    from redis import Redis
    from rq import Queue
except Exception:  # pragma: no cover - RQ not required for tests/CI import
    Redis = None  # type: ignore[assignment]
    Queue = None  # type: ignore[assignment]

from .config import settings
from .db import SessionLocal

logger = logging.getLogger("app.worker")


def _get_redis_connection() -> Redis | None:
    """
    Return a Redis connection if REDIS_URL is configured, else None.
    """
    if not settings.REDIS_URL or Redis is None or Queue is None:
        logger.warning("REDIS_URL not set; background queue will be disabled")
        return None
    return Redis.from_url(settings.REDIS_URL)


def enqueue_submission(submission_id: int) -> None:
    """
    Enqueue a background job to process the given submission id.
    Uses the default RQ queue named 'default'. If Redis is not configured,
    logs a warning and does nothing (submission remains in 'received' state).
    """
    redis_conn = _get_redis_connection()
    if redis_conn is None:
        logger.warning(
            "Cannot enqueue submission %s: REDIS_URL is not configured",
            submission_id,
        )
        return
    queue = Queue("default", connection=redis_conn)
    queue.enqueue(process_submission_job, submission_id)
    logger.info("Enqueued submission_id=%s on RQ 'default' queue", submission_id)


def process_submission_job(submission_id: int, *_, **__) -> Any:
    """
    Background job entry point: run the recommendation pipeline for a submission.
    Creates its own DB session and ensures it is closed.
    """
    from rag.pipeline import run_recommendation_pipeline

    logger.info("Worker starting processing for submission_id=%s", submission_id)
    db = SessionLocal()
    try:
        report = run_recommendation_pipeline(
            db,
            submission_id=submission_id,
            top_k=5,
            provider="auto",
        )
        logger.info(
            "Worker finished processing submission_id=%s; report keys=%s",
            submission_id,
            list(report.keys()),
        )
        return report
    finally:
        db.close()

