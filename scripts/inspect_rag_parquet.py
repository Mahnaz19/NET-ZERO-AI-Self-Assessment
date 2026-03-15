"""
Inspect data/processed/rag_embeddings.parquet: schema, row count, sample.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PATH = REPO_ROOT / "data" / "processed" / "rag_embeddings.parquet"


def main() -> None:
    path = DEFAULT_PATH
    if not path.exists():
        print(f"File not found: {path}", file=sys.stderr)
        sys.exit(1)
    try:
        import pyarrow.parquet as pq
    except ImportError:
        print("pyarrow not installed", file=sys.stderr)
        sys.exit(1)
    tbl = pq.read_table(path)
    print("Path:", path)
    print("Rows:", tbl.num_rows)
    print("Columns:", tbl.column_names)
    for name in tbl.column_names:
        col = tbl.column(name)
        print(f"  - {name}: {col.type}")
    if tbl.num_rows > 0:
        print("\nSample row (first):")
        for name in tbl.column_names:
            val = tbl.column(name)[0]
            if name == "embedding":
                val = f"<list len={len(val) if val is not None else 0}>"
            elif isinstance(val, (str, bytes)) and len(str(val)) > 80:
                val = (str(val)[:80] + "...") if val else val
            print(f"  {name}: {val}")
    print()
    return None


if __name__ == "__main__":
    main()
