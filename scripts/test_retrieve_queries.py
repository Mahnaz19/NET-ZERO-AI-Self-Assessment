"""
Run retrieve() on a handful of realistic queries and print metadata + text.
Uses parquet provider so it works without Postgres (data/processed/rag_embeddings.parquet).
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "backend"))

from rag.retriever import retrieve

PARQUET = REPO_ROOT / "data" / "processed" / "rag_embeddings.parquet"

QUERIES = [
    "energy saving recommendations for small business",
    "solar panels and payback period",
    "LED lighting upgrade",
    "carbon footprint and annual consumption",
    "heating and insulation improvements",
]


def main() -> None:
    if not PARQUET.exists():
        print(f"Parquet not found: {PARQUET}. Run ingest_rag.py first.", file=sys.stderr)
        sys.exit(1)
    print(f"Using parquet: {PARQUET}\n")
    for q in QUERIES:
        print("=" * 72)
        print(f"Query: {q!r}")
        print("=" * 72)
        hits = retrieve(q, top_k=3, provider="parquet", parquet_path=PARQUET)
        for i, h in enumerate(hits, 1):
            print(f"\n--- Hit {i} (score={h['score']:.4f}) ---")
            print("id:", h["id"])
            print("metadata:", h["metadata"])
            raw = (h["text"] or "")[:400]
            if len(h["text"] or "") > 400:
                raw += "..."
            # Avoid Windows console Unicode errors
            print("text (first 400 chars):", raw.encode("ascii", errors="replace").decode("ascii"))
        print()
    print("Done.")


if __name__ == "__main__":
    main()
