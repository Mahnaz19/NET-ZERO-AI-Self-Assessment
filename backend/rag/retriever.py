"""
Retriever: embed query and run vector search via configured adapter.
"""

from __future__ import annotations

from typing import Any, Dict, List

from .adapter import PgVectorAdapter, AzureCogSearchAdapter, VectorAdapter
from .embeddings import get_embedding


def _adapter_for_provider(provider: str, index_name: str, embedding_dim: int) -> VectorAdapter:
    if provider == "pgvector":
        return PgVectorAdapter(index_name=index_name, embedding_dim=embedding_dim)
    if provider == "azure":
        return AzureCogSearchAdapter(index_name=index_name, embedding_dim=embedding_dim)
    raise ValueError(f"Unknown provider: {provider}. Use 'pgvector' or 'azure'.")


def retrieve(
    query: str,
    top_k: int = 5,
    provider: str = "pgvector",
    index_name: str = "beas_reports",
    filter: Dict[str, Any] | None = None,
) -> List[Dict[str, Any]]:
    """
    Embed the query, run vector search, return list of hits with id, text, metadata, score.
    """
    query_embedding = get_embedding(query)
    adapter = _adapter_for_provider(provider, index_name, embedding_dim=query_embedding.shape[0])
    hits = adapter.query(query_embeddings=query_embedding, top_k=top_k, filter=filter)
    return [{"id": h["id"], "text": h["text"], "metadata": h["metadata"], "score": h["score"]} for h in hits]
