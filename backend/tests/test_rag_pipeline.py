"""
Test RAG→LLM recommendation pipeline with MockLLM and optional test DB.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

BACKEND = Path(__file__).resolve().parents[1]
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))


@pytest.fixture
def _no_azure(monkeypatch):
    monkeypatch.delenv("AZURE_OPENAI_ENDPOINT", raising=False)
    monkeypatch.delenv("AZURE_OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("AZURE_OPENAI_DEPLOYMENT", raising=False)


@pytest.fixture
def db_session():
    """Provide a DB session; uses default engine (e.g. sqlite test.db)."""
    from app.db import SessionLocal
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def test_submission(db_session):
    """Create a minimal test submission and return it."""
    from app import crud, schemas

    # Ensure tables exist
    from app.db import Base, engine
    Base.metadata.create_all(bind=engine)

    submission_in = schemas.SubmissionCreate(
        business_name="Test Co",
        postcode="AB1 2CD",
        answers={
            "annual_kwh": 50000.0,
            "annual_cost_gbp": 15000.0,
            "floor_area_m2": 200,
            "usage_profile": "office",
            "sector": "Office",
        },
    )
    sub = crud.create_submission(db_session, submission_in)
    return sub


def test_run_recommendation_pipeline_returns_report(_no_azure, db_session, test_submission):
    """Pipeline with MockLLM returns report with executive_summary and recommendations."""
    from rag.pipeline import run_recommendation_pipeline

    with patch("rag.retriever_adapter.retrieve_text_chunks", return_value=[
        {"id": "c1", "score": 0.8, "metadata": {"filename": "x.pdf", "section": "S"}, "text": "Context chunk."},
    ]):
        report = run_recommendation_pipeline(
            db_session,
            submission_id=test_submission.id,
            top_k=2,
            provider="parquet",
        )

    assert "executive_summary" in report
    assert "recommendations" in report
    assert len(report["recommendations"]) > 0
    assert "baseline" in report
    assert "candidates" in report
    for r in report["recommendations"]:
        assert "measure_code" in r
        assert "recommendation_text" in r
