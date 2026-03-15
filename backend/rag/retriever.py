"""
Retriever: embed query and run vector search via configured adapter.
"""

from __future__ import annotations

from typing import Any, Dict, List

from pathlib import Path

from .adapter import PgVectorAdapter, AzureCogSearchAdapter, ParquetAdapter, VectorAdapter
from .embeddings import get_embedding


def _adapter_for_provider(
    provider: str,
    index_name: str,
    embedding_dim: int,
    parquet_path: str | Path | None = None,
) -> VectorAdapter:
    if provider == "pgvector":
        return PgVectorAdapter(index_name=index_name, embedding_dim=embedding_dim)
    if provider == "azure":
        return AzureCogSearchAdapter(index_name=index_name, embedding_dim=embedding_dim)
    if provider == "parquet":
        path = parquet_path or Path("data/processed/rag_embeddings.parquet")
        return ParquetAdapter(parquet_path=path)
    raise ValueError(f"Unknown provider: {provider}. Use 'pgvector', 'azure', or 'parquet'.")


def retrieve(
    query: str,
    top_k: int = 5,
    provider: str = "pgvector",
    index_name: str = "beas_reports",
    filter: Dict[str, Any] | None = None,
    parquet_path: str | Path | None = None,
) -> List[Dict[str, Any]]:
    """
    Embed the query, run vector search, return list of hits with id, text, metadata, score.
    Use provider='parquet' to search over data/processed/rag_embeddings.parquet when Postgres is not available.
    """
    query_embedding = get_embedding(query)
    adapter = _adapter_for_provider(
        provider, index_name, embedding_dim=query_embedding.shape[0], parquet_path=parquet_path
    )
    hits = adapter.query(query_embeddings=query_embedding, top_k=top_k, filter=filter)
    return [{"id": h["id"], "text": h["text"], "metadata": h["metadata"], "score": h["score"]} for h in hits]
