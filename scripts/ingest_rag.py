"""
RAG ingestion: read report chunks JSONL, compute embeddings, upsert to vector store,
and persist a local parquet cache.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "backend"))

import numpy as np


def _clean_text(text: str) -> str:
    if not text or not isinstance(text, str):
        return ""
    t = text.strip()
    t = re.sub(r"\s+", " ", t)
    return t


def _deterministic_id(filename: str, section: str, chunk_index: int) -> str:
    """Stable id for idempotent upserts."""
    key = f"{filename}|{section}|{chunk_index}"
    return hashlib.sha256(key.encode("utf-8")).hexdigest()


def _load_jsonl(path: Path) -> list[dict]:
    records = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            records.append(json.loads(line))
    return records


def _prepare_records(
    raw: list[dict],
    chunk_size: int | None,
) -> list[dict]:
    """
    Ensure each record has id, filename, section, chunk_index, text, sector (optional).
    Use deterministic id. Optionally validate or re-chunk by chunk_size (max chars per chunk).
    """
    out = []
    for r in raw:
        filename = str(r.get("filename", "")).strip()
        section = str(r.get("section", "unknown")).strip() or "unknown"
        chunk_index = int(r.get("chunk_index", 0))
        text = _clean_text(str(r.get("text", "")))
        sector = str(r.get("sector", "")).strip()
        report_id = str(r.get("report_id", "")).strip()

        if chunk_size is not None and chunk_size > 0 and len(text) > chunk_size:
            # Re-chunk by splitting on spaces
            start = 0
            idx = 0
            while start < len(text):
                end = min(start + chunk_size, len(text))
                if end < len(text):
                    last_space = text.rfind(" ", start, end + 1)
                    if last_space > start:
                        end = last_space
                chunk_text = text[start:end].strip()
                if chunk_text:
                    rid = _deterministic_id(filename, section, idx)
                    out.append({
                        "id": rid,
                        "filename": filename,
                        "report_id": report_id,
                        "section": section,
                        "chunk_index": idx,
                        "text": chunk_text,
                        "sector": sector,
                        "created_at": datetime.now(timezone.utc).isoformat()
                    })
                    idx += 1
                start = end
            continue

        rid = r.get("id")
        if not rid:
            rid = _deterministic_id(filename, section, chunk_index)
        else:
            rid = str(rid)
        out.append({
            "id": rid,
            "filename": filename,
            "report_id": report_id,
            "section": section,
            "chunk_index": chunk_index,
            "text": text,
            "sector": sector,
            "created_at": datetime.now(timezone.utc).isoformat()
        })
    return out


def run(
    input_path: Path,
    index_name: str,
    provider: str,
    chunk_size: int | None,
    parquet_path: Path,
) -> None:
    from rag.embeddings import get_embedding
    from rag.adapter import PgVectorAdapter, AzureCogSearchAdapter, VectorAdapter

    if not input_path.is_file():
        print(f"Input file not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    raw = _load_jsonl(input_path)
    if not raw:
        print("No records in input.", file=sys.stderr)
        sys.exit(0)

    records = _prepare_records(raw, chunk_size)
    texts = [r["text"] or " " for r in records]

    print(f"Computing embeddings for {len(texts)} chunks...")
    embeddings = get_embedding(texts)
    if embeddings.ndim == 1:
        embeddings = embeddings.reshape(1, -1)

    # Build records with embedding for adapter
    dim = embeddings.shape[1]
    for i, r in enumerate(records):
        r["embedding"] = embeddings[i]

    # Persist parquet cache first so it exists even if vector store upsert fails
    parquet_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        import pyarrow as pa
        import pyarrow.parquet as pq
    except ImportError:
        print("pyarrow not installed; skipping parquet write.", file=sys.stderr)
    else:
        upsert_ts = datetime.now(timezone.utc).isoformat()
        tbl = pa.table({
            "id": [r["id"] for r in records],
            "filename": [r["filename"] for r in records],
            "section": [r["section"] for r in records],
            "chunk_index": pa.array([r["chunk_index"] for r in records], type=pa.int32()),
            "sector": [r["sector"] for r in records],
            "text": [r["text"] for r in records],
            "embedding": [emb.tolist() if hasattr(emb, "tolist") else emb for emb in embeddings],
            "upsert_ts": [upsert_ts] * len(records),
        })
        pq.write_table(tbl, parquet_path)
        print(f"Wrote {parquet_path}")

    # Upsert to vector store (optional: warn on failure but do not fail the run)
    try:
        if provider == "pgvector":
            adapter: VectorAdapter = PgVectorAdapter(index_name=index_name, embedding_dim=dim)
        elif provider == "azure":
            adapter = AzureCogSearchAdapter(index_name=index_name, embedding_dim=dim)
        else:
            print(f"Unknown provider: {provider}. Use pgvector or azure.", file=sys.stderr)
            sys.exit(1)
        print(f"Upserting to {provider} index '{index_name}'...")
        adapter.upsert(records)
    except Exception as e:
        print(f"Warning: vector store upsert failed ({e}). Parquet was still written.", file=sys.stderr)

    print(f"Processed {len(records)} records. Vector index: {index_name} (dim={dim}).")


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest report chunks into RAG vector store.")
    parser.add_argument(
        "--input",
        type=Path,
        default=REPO_ROOT / "data" / "processed" / "reports_chunks.jsonl",
        help="Input JSONL path (default: data/processed/reports_chunks.jsonl)",
    )
    parser.add_argument(
        "--index-name",
        type=str,
        default="beas_reports",
        help="Vector index name (default: beas_reports)",
    )
    parser.add_argument(
        "--provider",
        type=str,
        choices=["pgvector", "azure"],
        default="pgvector",
        help="Vector store provider (default: pgvector)",
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=None,
        metavar="N",
        help="Optional max characters per chunk; re-chunk if exceeded",
    )
    parser.add_argument(
        "--parquet",
        type=Path,
        default=REPO_ROOT / "data" / "processed" / "rag_embeddings.parquet",
        help="Output parquet path (default: data/processed/rag_embeddings.parquet)",
    )
    args = parser.parse_args()
    run(
        input_path=args.input,
        index_name=args.index_name,
        provider=args.provider,
        chunk_size=args.chunk_size,
        parquet_path=args.parquet,
    )


if __name__ == "__main__":
    main()
