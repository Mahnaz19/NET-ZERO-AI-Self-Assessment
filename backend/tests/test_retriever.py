"""
Tests for RAG retriever: mock adapter.query and assert return structure.
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

BACKEND = Path(__file__).resolve().parents[1]
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))


@patch("rag.retriever.get_embedding")
@patch("rag.retriever._adapter_for_provider")
def test_retrieve_returns_correct_structure(mock_adapter_factory, mock_get_embedding):
    """Retriever returns list of dicts with id, text, metadata, score."""
    # Avoid importing retriever before patching; patch at use site
    import numpy as np
    mock_get_embedding.return_value = np.zeros(384, dtype=np.float32)
    mock_adapter = MagicMock()
    mock_adapter.query.return_value = [
        {
            "id": "abc123",
            "metadata": {"filename": "x.pdf", "section": "Summary"},
            "text": "Some text",
            "score": 0.92,
        }
    ]
    mock_adapter_factory.return_value = mock_adapter

    from rag.retriever import retrieve

    results = retrieve("energy savings", top_k=5, provider="pgvector")
    assert len(results) == 1
    assert results[0]["id"] == "abc123"
    assert results[0]["text"] == "Some text"
    assert results[0]["metadata"] == {"filename": "x.pdf", "section": "Summary"}
    assert results[0]["score"] == 0.92
    mock_adapter.query.assert_called_once()
