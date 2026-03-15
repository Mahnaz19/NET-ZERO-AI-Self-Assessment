"""
Abstract vector store adapter and implementations: PgVector and Azure Cognitive Search.
"""

from __future__ import annotations

import os
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

import numpy as np


# Metadata fields we store and return
RAG_METADATA_KEYS = ("id", "filename", "report_id", "section", "chunk_index", "text", "sector", "created_at")


class VectorAdapter(ABC):
    """Abstract interface for vector store backends."""

    @abstractmethod
    def upsert(self, records: List[Dict[str, Any]]) -> None:
        """Insert or update vector records. Each record must have: id, embedding, and metadata fields."""
        ...

    @abstractmethod
    def query(
        self,
        query_embeddings: np.ndarray,
        top_k: int,
        filter: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Return list of hits with score, id, metadata, text."""
        ...

    @abstractmethod
    def delete_index(self) -> None:
        """Drop the vector index (and table if applicable). Use with care."""
        ...


def _normalize_record(record: Dict[str, Any], embedding: np.ndarray) -> Dict[str, Any]:
    """Ensure record has all required metadata fields for storage."""
    return {
        "id": str(record.get("id", "")),
        "filename": str(record.get("filename", "")),
        "report_id": str(record.get("report_id", "")),
        "section": str(record.get("section", "unknown")),
        "chunk_index": int(record.get("chunk_index", 0)),
        "text": str(record.get("text", "")),
        "sector": str(record.get("sector", "")),
        "created_at": str(record.get("created_at", "")),
        "embedding": embedding,
    }


# ---------------------------------------------------------------------------
# PgVector adapter
# ---------------------------------------------------------------------------

def _get_engine():
    """Lazy import to avoid circular imports and allow running outside app context."""
    from app.db import engine
    return engine


class PgVectorAdapter(VectorAdapter):
    """Vector store using PostgreSQL + pgvector. Uses SQLAlchemy engine from app.db."""

    def __init__(self, index_name: str = "beas_reports", embedding_dim: int = 384):
        self.index_name = index_name
        self.embedding_dim = embedding_dim
        self._table_created = False

    def _ensure_table(self) -> None:
        if self._table_created:
            return
        try:
            from pgvector.sqlalchemy import Vector
        except ImportError:
            raise ImportError("pgvector is required for PgVectorAdapter. Install with: pip install pgvector")
        from sqlalchemy import text, Column, String, Integer, DateTime, MetaData, Table

        engine = _get_engine()
        with engine.begin() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        metadata = MetaData()
        self._table = Table(
            self.index_name,
            metadata,
            Column("id", String(64), primary_key=True),
            Column("filename", String(512)),
            Column("report_id", String(256)),
            Column("section", String(256)),
            Column("chunk_index", Integer),
            Column("text", String(65535)),
            Column("sector", String(256)),
            Column("created_at", String(64)),
            Column("embedding", Vector(self.embedding_dim)),
        )
        metadata.create_all(engine)
        self._table_created = True

    def upsert(self, records: List[Dict[str, Any]]) -> None:
        if not records:
            return
        self._ensure_table()
        from sqlalchemy import text
        import json

        engine = _get_engine()
        # Use ON CONFLICT (id) DO UPDATE for idempotency
        # pgvector expects list for embedding
        with engine.begin() as conn:
            for r in records:
                emb = r["embedding"]
                if hasattr(emb, "tolist"):
                    emb = emb.tolist()
                conn.execute(
                    text(f"""
                    INSERT INTO {self.index_name}
                    (id, filename, report_id, section, chunk_index, text, sector, created_at, embedding)
                    VALUES (:id, :filename, :report_id, :section, :chunk_index, :text, :sector, :created_at, CAST(:embedding AS vector))
                    ON CONFLICT (id) DO UPDATE SET
                    filename = EXCLUDED.filename,
                    report_id = EXCLUDED.report_id,
                    section = EXCLUDED.section,
                    chunk_index = EXCLUDED.chunk_index,
                    text = EXCLUDED.text,
                    sector = EXCLUDED.sector,
                    created_at = EXCLUDED.created_at,
                    embedding = EXCLUDED.embedding
                    """),
                    {
                        "id": r["id"],
                        "filename": r["filename"],
                        "report_id": r["report_id"],
                        "section": r["section"],
                        "chunk_index": r["chunk_index"],
                        "text": r["text"],
                        "sector": r["sector"],
                        "created_at": r["created_at"],
                        "embedding": str(emb),
                    },
                )

    def query(
        self,
        query_embeddings: np.ndarray,
        top_k: int,
        filter: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        self._ensure_table()
        from sqlalchemy import text

        engine = _get_engine()
        qvec = query_embeddings
        if qvec.ndim > 1:
            qvec = qvec.ravel()
        qvec_list = qvec.tolist()

        # Simple cosine distance: 1 - (a . b) / (|a||b|). pgvector uses <=> for cosine.
        with engine.connect() as conn:
            rows = conn.execute(
                text(f"""
                SELECT id, filename, report_id, section, chunk_index, text, sector, created_at,
                       1 - (embedding <=> :qvec::vector) AS score
                FROM {self.index_name}
                ORDER BY embedding <=> :qvec::vector
                LIMIT :top_k
                """),
                {"qvec": str(qvec_list), "top_k": top_k},
            ).fetchall()

        return [
            {
                "id": r[0],
                "metadata": {
                    "filename": r[1],
                    "report_id": r[2],
                    "section": r[3],
                    "chunk_index": r[4],
                    "sector": r[6],
                    "created_at": r[7],
                },
                "text": r[5] or "",
                "score": float(r[8]),
            }
            for r in rows
        ]

    def delete_index(self) -> None:
        from sqlalchemy import text
        engine = _get_engine()
        with engine.begin() as conn:
            conn.execute(text(f"DROP TABLE IF EXISTS {self.index_name}"))
        self._table_created = False


# ---------------------------------------------------------------------------
# Parquet adapter (read-only retrieval from rag_embeddings.parquet)
# ---------------------------------------------------------------------------

from pathlib import Path


class ParquetAdapter(VectorAdapter):
    """Read-only adapter: query via cosine similarity over embeddings in a parquet file."""

    def __init__(self, parquet_path: str | Path):
        self.parquet_path = Path(parquet_path)

    def _load(self) -> tuple[np.ndarray, list[dict]]:
        import pyarrow.parquet as pq
        tbl = pq.read_table(self.parquet_path)
        ids = tbl.column("id")
        filenames = tbl.column("filename")
        sections = tbl.column("section")
        chunk_indices = tbl.column("chunk_index")
        sectors = tbl.column("sector")
        texts = tbl.column("text")
        embeddings = tbl.column("embedding")
        n = len(ids)
        vecs = np.array([list(embeddings[i]) for i in range(n)], dtype=np.float32)
        meta = [
            {
                "filename": str(filenames[i]) if filenames[i] is not None else "",
                "report_id": "",
                "section": str(sections[i]) if sections[i] is not None else "unknown",
                "chunk_index": int(chunk_indices[i]) if chunk_indices[i] is not None else 0,
                "sector": str(sectors[i]) if sectors[i] is not None else "",
                "created_at": "",
            }
            for i in range(n)
        ]
        return vecs, [
            {"id": str(ids[i]), "metadata": meta[i], "text": str(texts[i]) if texts[i] is not None else ""}
            for i in range(n)
        ]

    def upsert(self, records: List[Dict[str, Any]]) -> None:
        """No-op: parquet is read-only for retrieval."""
        pass

    def query(
        self,
        query_embeddings: np.ndarray,
        top_k: int,
        filter: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        vecs, rows = self._load()
        q = query_embeddings.ravel().astype(np.float32)
        q = q / (np.linalg.norm(q) + 1e-12)
        norms = np.linalg.norm(vecs, axis=1) + 1e-12
        scores = (vecs @ q) / norms
        idx = np.argsort(-scores)[:top_k]
        return [
            {"id": rows[i]["id"], "metadata": rows[i]["metadata"], "text": rows[i]["text"], "score": float(scores[i])}
            for i in idx
        ]

    def delete_index(self) -> None:
        """No-op: parquet file is not deleted."""
        pass


# ---------------------------------------------------------------------------
# Azure Cognitive Search adapter
# ---------------------------------------------------------------------------

class AzureCogSearchAdapter(VectorAdapter):
    """Thin wrapper around Azure Cognitive Search REST/SDK for vector index."""

    def __init__(
        self,
        index_name: str = "beas_reports",
        embedding_dim: int = 1536,
        service: Optional[str] = None,
        api_key: Optional[str] = None,
    ):
        self.index_name = index_name
        self.embedding_dim = embedding_dim
        self.endpoint = service or os.environ.get("AZURE_COG_SEARCH_SERVICE", "")
        self.api_key = api_key or os.environ.get("AZURE_COG_SEARCH_API_KEY", "")
        if not self.endpoint or not self.api_key:
            raise ValueError("AZURE_COG_SEARCH_SERVICE and AZURE_COG_SEARCH_API_KEY must be set")

    def _client(self):
        from azure.core.credentials import AzureKeyCredential
        from azure.search.documents import SearchClient
        endpoint = self.endpoint.rstrip("/")
        if not endpoint.startswith("http"):
            endpoint = f"https://{endpoint}.search.windows.net"
        return SearchClient(
            endpoint=endpoint,
            index_name=self.index_name,
            credential=AzureKeyCredential(self.api_key),
        )

    def _ensure_index(self) -> None:
        """Create index if not exists. Requires SearchIndexClient."""
        from azure.core.credentials import AzureKeyCredential
        from azure.search.documents.indexes import SearchIndexClient
        from azure.search.documents.indexes.models import (
            SearchIndex,
            SimpleField,
            SearchableField,
            SearchFieldDataType,
            VectorSearch,
            VectorSearchProfile,
            HnswAlgorithmConfiguration,
        )
        endpoint = self.endpoint.rstrip("/")
        if not endpoint.startswith("http"):
            endpoint = f"https://{endpoint}.search.windows.net"
        idx_client = SearchIndexClient(
            endpoint=endpoint,
            credential=AzureKeyCredential(self.api_key),
        )
        if self.index_name in [i.name for i in idx_client.list_index_names()]:
            return
        index = SearchIndex(
            name=self.index_name,
            fields=[
                SimpleField(name="id", type=SearchFieldDataType.String, key=True),
                SearchableField(name="filename", type=SearchFieldDataType.String),
                SearchableField(name="report_id", type=SearchFieldDataType.String),
                SearchableField(name="section", type=SearchFieldDataType.String),
                SimpleField(name="chunk_index", type=SearchFieldDataType.Int32),
                SearchableField(name="text", type=SearchFieldDataType.String),
                SearchableField(name="sector", type=SearchFieldDataType.String),
                SearchableField(name="created_at", type=SearchFieldDataType.String),
                SearchableField(
                    name="embedding",
                    type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                    vector_search_dimensions=self.embedding_dim,
                    vector_search_profile_name="vector_profile",
                ),
            ],
            vector_search=VectorSearch(
                algorithms=[HnswAlgorithmConfiguration(name="hnsw")],
                profiles=[VectorSearchProfile(name="vector_profile", algorithm_configuration_name="hnsw")],
            ),
        )
        idx_client.create_index(index)

    def upsert(self, records: List[Dict[str, Any]]) -> None:
        if not records:
            return
        self._ensure_index()
        docs = []
        for r in records:
            emb = r["embedding"]
            if hasattr(emb, "tolist"):
                emb = emb.tolist()
            docs.append({
                "id": r["id"],
                "filename": r["filename"],
                "report_id": r["report_id"],
                "section": r["section"],
                "chunk_index": r["chunk_index"],
                "text": r["text"],
                "sector": r["sector"],
                "created_at": r["created_at"],
                "embedding": emb,
            })
        client = self._client()
        # Batch upload (Azure allows up to 1000 per batch)
        batch_size = 1000
        for i in range(0, len(docs), batch_size):
            client.upload_documents(documents=docs[i : i + batch_size])

    def query(
        self,
        query_embeddings: np.ndarray,
        top_k: int,
        filter: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        from azure.search.documents.models import VectorizedQuery
        qvec = query_embeddings
        if qvec.ndim > 1:
            qvec = qvec.ravel()
        vector_query = VectorizedQuery(vector=qvec.tolist(), k_nearest_neighbors=top_k, fields="embedding")
        client = self._client()
        results = client.search(search_text=None, vector_queries=[vector_query], top=top_k)
        hits = []
        for r in results:
            hits.append({
                "id": r["id"],
                "metadata": {
                    "filename": r.get("filename", ""),
                    "report_id": r.get("report_id", ""),
                    "section": r.get("section", ""),
                    "chunk_index": r.get("chunk_index", 0),
                    "sector": r.get("sector", ""),
                    "created_at": r.get("created_at", ""),
                },
                "text": r.get("text", ""),
                "score": float(r.get("@search.score", 0.0)),
            })
        return hits

    def delete_index(self) -> None:
        from azure.core.credentials import AzureKeyCredential
        from azure.search.documents.indexes import SearchIndexClient
        endpoint = self.endpoint.rstrip("/")
        if not endpoint.startswith("http"):
            endpoint = f"https://{endpoint}.search.windows.net"
        idx_client = SearchIndexClient(
            endpoint=endpoint,
            credential=AzureKeyCredential(self.api_key),
        )
        idx_client.delete_index(self.index_name)
