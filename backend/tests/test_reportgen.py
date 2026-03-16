"""
Tests for reportgen (HTML/PDF rendering) and report API endpoints.
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

BACKEND = Path(__file__).resolve().parents[1]
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))


# Minimal report shape matching pipeline output (no LLM calls in tests)
def _sample_report():
    return {
        "executive_summary": "Test summary for PDF generation.",
        "recommendations": [
            {
                "measure_code": "LED_UPGRADE",
                "recommendation_text": "Upgrade to LED lighting.",
                "priority": 1,
                "confidence": "high",
                "kwh_saved": 1000,
                "carbon_saved": 0.233,
                "simple_payback": 2.5,
            },
        ],
        "baseline": {
            "annual_kwh": 50000,
            "annual_cost_gbp": 15000,
            "tariff_p_per_kwh": 30,
            "annual_co2_tonnes": 9.77,
        },
        "candidates": [],
    }


def test_render_report_html_returns_string_with_sections():
    """render_report_html returns HTML containing executive_summary and recommendations."""
    from reportgen import render_report_html

    html = render_report_html(_sample_report())
    assert isinstance(html, str)
    assert "executive_summary" in html or "Executive summary" in html
    assert "recommendations" in html or "Recommendations" in html
    assert "Test summary for PDF generation" in html
    assert "LED_UPGRADE" in html


def test_render_report_html_handles_missing_fields():
    """Template receives defaults for missing baseline/recommendations."""
    from reportgen import render_report_html

    html = render_report_html({"executive_summary": "Only summary."})
    assert isinstance(html, str)
    assert "Only summary" in html


def test_api_reports_generate_pdf_returns_pdf():
    """POST /api/reports/generate_pdf returns 200 and application/pdf with %PDF header."""
    from fastapi.testclient import TestClient

    from app.main import create_app

    app = create_app()
    client = TestClient(app)

    # Create submission and set report_json (simulate pipeline already run)
    from app import crud, schemas
    from app.db import Base, SessionLocal, engine

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        sub_in = schemas.SubmissionCreate(
            business_name="PDF Test",
            postcode="XY1 2AB",
            answers={"annual_kwh": 10000, "sector": "Office"},
        )
        sub = crud.create_submission(db, sub_in)
        crud.update_report(db, sub.id, _sample_report(), status="ready")

        with patch("reportgen.render_report_pdf_bytes") as mock_pdf:
            mock_pdf.return_value = b"%PDF-1.4\nfake pdf content"
            resp = client.post("/api/reports/generate_pdf", json={"submission_id": sub.id})
    finally:
        db.close()

    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/pdf"
    assert resp.content.startswith(b"%PDF")
    assert "attachment" in resp.headers.get("content-disposition", "")
    assert "report_%s.pdf" % sub.id in resp.headers.get("content-disposition", "")


def test_api_reports_generate_pdf_400_when_no_report():
    """POST /api/reports/generate_pdf returns 400 when submission has no report_json."""
    from fastapi.testclient import TestClient

    from app.main import create_app
    from app import crud, schemas
    from app.db import Base, SessionLocal, engine

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        sub_in = schemas.SubmissionCreate(
            business_name="No Report",
            postcode="AB1 2CD",
            answers={},
        )
        sub = crud.create_submission(db, sub_in)
        # do not call update_report — report_json stays None

        app = create_app()
        client = TestClient(app)
        resp = client.post("/api/reports/generate_pdf", json={"submission_id": sub.id})
    finally:
        db.close()

    assert resp.status_code == 400
    assert "No report" in resp.json().get("detail", "")


def test_api_reports_html_returns_html():
    """GET /api/reports/html/{submission_id} returns HTML for a submission with report."""
    from fastapi.testclient import TestClient

    from app.main import create_app
    from app import crud, schemas
    from app.db import Base, SessionLocal, engine

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        sub_in = schemas.SubmissionCreate(
            business_name="HTML Test",
            postcode="CD3 4EF",
            answers={},
        )
        sub = crud.create_submission(db, sub_in)
        crud.update_report(db, sub.id, _sample_report(), status="ready")

        app = create_app()
        client = TestClient(app)
        resp = client.get(f"/api/reports/html/{sub.id}")
    finally:
        db.close()

    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]
    assert "Test summary for PDF generation" in resp.text
    assert "executive_summary" in resp.text or "Executive summary" in resp.text
