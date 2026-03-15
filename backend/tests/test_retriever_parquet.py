"""
Test retrieve_text_chunks with parquet (or mock). Asserts >0 hits for query 'lighting upgrade'.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

BACKEND = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND.parent
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

PARQUET = REPO_ROOT / "data" / "processed" / "rag_embeddings.parquet"


@pytest.mark.skipif(not PARQUET.is_file(), reason="rag_embeddings.parquet not present")
def test_retrieve_text_chunks_lighting_returns_hits():
    """With parquet present, retrieve_text_chunks returns >0 hits for 'lighting upgrade'."""
    from rag.retriever_adapter import retrieve_text_chunks

    hits = retrieve_text_chunks(
        "lighting upgrade",
        top_k=5,
        provider="parquet",
        parquet_path=PARQUET,
    )
    assert len(hits) > 0
    for h in hits:
        assert "id" in h
        assert "score" in h
        assert "metadata" in h
        assert "text" in h
        assert "filename" in h["metadata"] or "section" in h["metadata"]


def test_retrieve_text_chunks_mock_returns_structure():
    """With mocked parquet retrieval, return structure is correct."""
    from unittest.mock import patch

    fake_hits = [
        {
            "id": "id1",
            "score": 0.9,
            "metadata": {"filename": "a.pdf", "section": "S", "chunk_index": 0, "sector": ""},
            "text": "Lighting upgrade text",
        }
    ]
    with patch("rag.retriever_adapter._retrieve_from_parquet", return_value=fake_hits):
        from rag.retriever_adapter import retrieve_text_chunks

        hits = retrieve_text_chunks(
            "lighting",
            top_k=5,
            provider="parquet",
            parquet_path=Path("/nonexistent/parquet.parquet"),
        )
    assert hits == fake_hits
