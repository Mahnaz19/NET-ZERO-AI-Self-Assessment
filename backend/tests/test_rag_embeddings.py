"""
Tests for RAG embeddings: fallback path (sentence-transformers) and output shape.
Skip if sentence-transformers not installed or credentials would be required.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import numpy as np
import pytest

# Run from backend so app and rag are importable
BACKEND = Path(__file__).resolve().parents[1]
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

# Unset cloud env vars so we force local fallback
@pytest.fixture(autouse=True)
def _force_local_embeddings(monkeypatch):
    monkeypatch.delenv("AZURE_OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("AZURE_OPENAI_DEPLOYMENT_NAME", raising=False)
    monkeypatch.delenv("AZURE_OPENAI_DEPLOYMENT", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)


@pytest.mark.skipif(
    os.environ.get("SKIP_HEAVY_RAG_TESTS", "").lower() in ("1", "true", "yes"),
    reason="SKIP_HEAVY_RAG_TESTS is set (sentence-transformers may be slow or missing)",
)
def test_get_embedding_fallback_single_text() -> None:
    """Without Azure/OpenAI keys, get_embedding uses sentence-transformers and returns 1d array."""
    try:
        from rag.embeddings import get_embedding
    except ImportError as e:
        if "sentence-transformers" in str(e).lower() or "sentence_transformers" in str(e):
            pytest.skip("sentence-transformers not installed")
        raise

    emb = get_embedding("Hello world")
    assert isinstance(emb, np.ndarray)
    assert emb.ndim == 1
    assert emb.dtype in (np.float32, np.float64)
    # all-MiniLM-L6-v2 has dimension 384
    assert emb.shape[0] == 384


@pytest.mark.skipif(
    os.environ.get("SKIP_HEAVY_RAG_TESTS", "").lower() in ("1", "true", "yes"),
    reason="SKIP_HEAVY_RAG_TESTS is set",
)
def test_get_embedding_fallback_batch() -> None:
    """Batch of texts returns (n, dim) array."""
    try:
        from rag.embeddings import get_embedding
    except ImportError as e:
        if "sentence-transformers" in str(e).lower() or "sentence_transformers" in str(e):
            pytest.skip("sentence-transformers not installed")
        raise

    texts = ["First", "Second chunk", "Third"]
    emb = get_embedding(texts)
    assert isinstance(emb, np.ndarray)
    assert emb.ndim == 2
    assert emb.shape[0] == 3
    assert emb.shape[1] == 384
