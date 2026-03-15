"""
Retriever adapter: retrieve_text_chunks with optional sector and auto fallback (pgvector -> parquet).
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Default parquet path relative to repo root (backend/rag -> repo = parents[2])
_REPO_ROOT = Path(__file__).resolve().parents[2]
_DEFAULT_PARQUET = _REPO_ROOT / "data" / "processed" / "rag_embeddings.parquet"


def retrieve_text_chunks(
    query: str,
    top_k: int = 5,
    sector: Optional[str] = None,
    provider: str = "auto",
    parquet_path: Optional[Path] = None,
) -> List[Dict[str, Any]]:
    """
    Retrieve top_k RAG chunks for the query. Each hit has keys:
    id, score, metadata (filename, section, chunk_index, sector), text.

    - If provider == "pgvector" or (provider == "auto" and DATABASE_URL present):
      attempt DB retrieval; on connection failure, fall back to parquet with a log warning.
    - Otherwise use parquet (load rag_embeddings.parquet, cosine similarity).
    """
    if sector and query.strip():
        query = f"{query} sector {sector}"
    elif sector:
        query = f"sector {sector} energy assessment"

    parquet_path = parquet_path or _DEFAULT_PARQUET

    if provider in ("pgvector", "auto") and os.environ.get("DATABASE_URL", "").strip():
        try:
            from .retriever import retrieve
            hits = retrieve(
                query,
                top_k=top_k,
                provider="pgvector",
                parquet_path=None,
            )
            return _hits_to_chunk_dicts(hits)
        except Exception as e:
            logger.warning(
                "pgvector retrieval failed (%s), falling back to parquet: %s",
                type(e).__name__,
                e,
            )
            provider = "parquet"

    if provider == "azure":
        from .retriever import retrieve
        hits = retrieve(query, top_k=top_k, provider="azure")
        return _hits_to_chunk_dicts(hits)

    # parquet (default or fallback)
    return _retrieve_from_parquet(query, top_k=top_k, parquet_path=parquet_path)


def _hits_to_chunk_dicts(hits: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    out = []
    for h in hits:
        meta = h.get("metadata") or {}
        out.append({
            "id": h.get("id"),
            "score": float(h.get("score", 0)),
            "metadata": {
                "filename": meta.get("filename", ""),
                "section": meta.get("section", ""),
                "chunk_index": meta.get("chunk_index", 0),
                "sector": meta.get("sector", ""),
            },
            "text": h.get("text") or "",
        })
    return out


def _retrieve_from_parquet(query: str, top_k: int, parquet_path: Path) -> List[Dict[str, Any]]:
    """Load parquet, embed query, compute cosine similarity, return top_k chunks."""
    if not parquet_path.is_file():
        logger.warning("Parquet file not found: %s; returning empty chunks", parquet_path)
        return []

    from .embeddings import get_embedding
    from .adapter import ParquetAdapter

    adapter = ParquetAdapter(parquet_path=parquet_path)
    query_embedding = get_embedding(query)
    hits = adapter.query(query_embeddings=query_embedding, top_k=top_k)
    return _hits_to_chunk_dicts(hits)
