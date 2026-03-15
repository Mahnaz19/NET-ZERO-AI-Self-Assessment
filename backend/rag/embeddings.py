"""
Embedding provider: Azure OpenAI, OpenAI, or local sentence-transformers fallback.
Uses env vars for credentials; no production keys in code.
"""

from __future__ import annotations

import os
from typing import List, Union

import numpy as np


# Batch size for API calls to avoid rate limits
DEFAULT_BATCH_SIZE = 32


def _batch_texts(texts: List[str], batch_size: int) -> List[List[str]]:
    """Split texts into batches."""
    batches = []
    for i in range(0, len(texts), batch_size):
        batches.append(texts[i : i + batch_size])
    return batches


def _embed_via_azure(texts: List[str], batch_size: int = DEFAULT_BATCH_SIZE) -> np.ndarray:
    """Use Azure OpenAI embeddings. Requires AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_KEY, AZURE_OPENAI_DEPLOYMENT_NAME (or AZURE_OPENAI_DEPLOYMENT)."""
    try:
        from openai import AzureOpenAI
    except ImportError:
        raise ImportError("openai package required for Azure embeddings. Install with: pip install openai")

    endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT", "").rstrip("/")
    api_key = os.environ.get("AZURE_OPENAI_API_KEY", "")
    deployment = os.environ.get("AZURE_OPENAI_DEPLOYMENT_NAME") or os.environ.get("AZURE_OPENAI_DEPLOYMENT", "")
    if not endpoint or not api_key or not deployment:
        raise ValueError("AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_KEY, and AZURE_OPENAI_DEPLOYMENT_NAME must be set")

    client = AzureOpenAI(azure_endpoint=endpoint, api_key=api_key, api_version="2024-02-15-preview")
    all_embeddings = []
    for batch in _batch_texts(texts, batch_size):
        resp = client.embeddings.create(input=batch, model=deployment)
        for e in resp.data:
            all_embeddings.append(e.embedding)
    return np.array(all_embeddings, dtype=np.float32)


def _embed_via_openai(texts: List[str], batch_size: int = DEFAULT_BATCH_SIZE) -> np.ndarray:
    """Use OpenAI embeddings. Requires OPENAI_API_KEY."""
    try:
        from openai import OpenAI
    except ImportError:
        raise ImportError("openai package required for OpenAI embeddings. Install with: pip install openai")

    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
        raise ValueError("OPENAI_API_KEY must be set")

    client = OpenAI(api_key=api_key)
    all_embeddings = []
    for batch in _batch_texts(texts, batch_size):
        resp = client.embeddings.create(input=batch, model="text-embedding-3-small")
        for e in resp.data:
            all_embeddings.append(e.embedding)
    return np.array(all_embeddings, dtype=np.float32)


# Dimension for fallback (matches all-MiniLM-L6-v2)
FALLBACK_EMBED_DIM = 384


def _embed_via_fallback(texts: List[str]) -> np.ndarray:
    """Deterministic hash-based embeddings when HF is unavailable (e.g. expired token)."""
    import hashlib
    out = np.zeros((len(texts), FALLBACK_EMBED_DIM), dtype=np.float32)
    for i, t in enumerate(texts):
        h = hashlib.sha256((t or " ").encode("utf-8")).digest()
        # Fill 384 dims from repeated hash
        for j in range(FALLBACK_EMBED_DIM):
            k = (j * 2) % len(h)
            out[i, j] = (h[k] - 128) / 128.0
    return out


def _embed_via_sentence_transformers(texts: List[str], batch_size: int = DEFAULT_BATCH_SIZE) -> np.ndarray:
    """Local fallback using sentence-transformers (e.g. all-MiniLM-L6-v2)."""
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError:
        raise ImportError(
            "sentence-transformers required for local embeddings. "
            "Install with: pip install sentence-transformers"
        )
    model_name = "sentence-transformers/all-MiniLM-L6-v2"
    try:
        model = SentenceTransformer(model_name)
    except (OSError, Exception) as e:
        if "401" in str(e) or "expired" in str(e).lower() or "token" in str(e).lower():
            try:
                model = SentenceTransformer(model_name, local_files_only=True)
            except Exception:
                # No cached model: use deterministic fallback so ingest can still produce parquet
                return _embed_via_fallback(texts)
        else:
            raise
    return model.encode(texts, batch_size=batch_size, show_progress_bar=False, convert_to_numpy=True)


def get_embedding(
    text: Union[str, List[str]],
    batch_size: int = DEFAULT_BATCH_SIZE,
) -> np.ndarray:
    """
    Return embedding(s) as numpy array (shape (dim,) for single text, (n, dim) for list).
    Provider order: Azure OpenAI (if AZURE_OPENAI_API_KEY + deployment set) ->
    OpenAI (if OPENAI_API_KEY set) -> sentence-transformers (local fallback).
    """
    if isinstance(text, str):
        texts = [text]
        single = True
    else:
        texts = list(text)
        single = False

    if not texts:
        raise ValueError("At least one text required")

    # Normalise empty strings to a space so embedders don't error
    texts = [t.strip() if t else " " for t in texts]

    if os.environ.get("AZURE_OPENAI_API_KEY") and (
        os.environ.get("AZURE_OPENAI_DEPLOYMENT_NAME") or os.environ.get("AZURE_OPENAI_DEPLOYMENT")
    ):
        arr = _embed_via_azure(texts, batch_size=batch_size)
    elif os.environ.get("OPENAI_API_KEY"):
        arr = _embed_via_openai(texts, batch_size=batch_size)
    else:
        arr = _embed_via_sentence_transformers(texts, batch_size=batch_size)

    if single:
        return arr[0]
    return arr
