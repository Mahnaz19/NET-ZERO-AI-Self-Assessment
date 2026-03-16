"""
Tests for background worker wiring: async submission processing and manual worker call.
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

BACKEND = Path(__file__).resolve().parents[1]
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))


def test_submit_returns_received_and_worker_can_persist_report(tmp_path):
    """
    POST /api/submit should return 201 with status='received' and not crash.
    We then simulate the worker by calling process_submission_job directly
    (with run_recommendation_pipeline patched to a lightweight stub that
    calls crud.update_report).
    """
    from app.main import create_app
    from app import crud, schemas
    from app.db import Base, SessionLocal, engine
    from app.worker import process_submission_job

    # Ensure tables exist
    Base.metadata.create_all(bind=engine)

    app = create_app()
    client = TestClient(app)

    submission_in = {
        "business_name": "BG Worker Co",
        "postcode": "ZZ1 2YY",
        "answers": {"annual_kwh": 12345.0, "sector": "Office"},
    }
    resp = client.post("/api/submit", json=submission_in)
    assert resp.status_code == 201
    body = resp.json()
    assert body["status"] == "received"
    submission_id = body["id"]

    # Patch pipeline to avoid heavy external calls; use crud.update_report instead.
    with patch("rag.pipeline.run_recommendation_pipeline") as mock_pipeline:
        def _fake_pipeline(db, submission_id: int, top_k: int = 5, provider: str = "auto"):
            report = {"executive_summary": "bg worker test", "recommendations": [], "baseline": {}, "candidates": []}
            crud.update_report(db, submission_id, report, status="ready")
            return report

        mock_pipeline.side_effect = _fake_pipeline
        process_submission_job(submission_id)

    # Verify report persisted
    db = SessionLocal()
    try:
        sub = crud.get_submission(db, submission_id)
        assert sub is not None
        assert sub.report_json is not None
        assert sub.report_json.get("executive_summary") == "bg worker test"
        assert sub.status == "ready"
    finally:
        db.close()

