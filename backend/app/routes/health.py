from fastapi import APIRouter
from sqlalchemy.orm import Session

from ..config import settings
from ..db import SessionLocal

try:
    from redis import Redis
except ImportError:  # pragma: no cover - redis optional in some environments
    Redis = None  # type: ignore[assignment]


router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health")
def health_check() -> dict:
    return {"status": "ok"}


@router.get("/healthz")
def healthz_check() -> dict:
    """
    Health endpoint that checks DB connectivity and, if configured, Redis.
    Always returns 200 but includes component statuses in the payload.
    """
    db_ok = False
    redis_ok = None

    # DB check
    db: Session = SessionLocal()
    try:
        db.execute("SELECT 1")
        db_ok = True
    finally:
        db.close()

    # Redis check (optional)
    if settings.REDIS_URL and Redis is not None:
        try:
            redis_conn = Redis.from_url(settings.REDIS_URL)
            redis_conn.ping()
            redis_ok = True
        except Exception:
            redis_ok = False

    return {
        "status": "ok" if db_ok else "degraded",
        "db_ok": db_ok,
        "redis_ok": redis_ok,
    }

