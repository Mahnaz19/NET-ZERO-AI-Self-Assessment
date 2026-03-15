"""
RAG package: embeddings, vector adapters (pgvector, Azure Cognitive Search), and retrieval.
"""

from .adapter import VectorAdapter, PgVectorAdapter, AzureCogSearchAdapter, ParquetAdapter
from .embeddings import get_embedding
from .retriever import retrieve

__all__ = [
    "VectorAdapter",
    "PgVectorAdapter",
    "AzureCogSearchAdapter",
    "get_embedding",
    "retrieve",
]
