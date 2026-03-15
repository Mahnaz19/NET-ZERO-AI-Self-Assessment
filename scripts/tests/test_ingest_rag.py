"""
Smoke test for RAG ingestion: run on sample JSONL or mock adapter; skip if file absent.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "ingest_rag.py"
DEFAULT_JSONL = REPO_ROOT / "data" / "processed" / "reports_chunks.jsonl"
DEFAULT_PARQUET = REPO_ROOT / "data" / "processed" / "rag_embeddings.parquet"


def test_ingest_rag_smoke_with_mock_adapter() -> None:
    """Run ingestion with mocked adapter; assert upsert called and parquet path can be set."""
    sys.path.insert(0, str(REPO_ROOT / "backend"))
    # Create a minimal JSONL in a temp dir so we don't depend on real file
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        jsonl = tmp_path / "chunks.jsonl"
        parquet = tmp_path / "rag_embeddings.parquet"
        with jsonl.open("w", encoding="utf-8") as f:
            f.write(json.dumps({
                "id": "a1",
                "filename": "test.pdf",
                "chunk_index": 0,
                "text": "Short text for embedding.",
            }, ensure_ascii=False) + "\n")

        mock_upsert = MagicMock()
        import numpy as np
        with patch("rag.adapter.PgVectorAdapter") as MockPg:
            MockPg.return_value.upsert = mock_upsert
            with patch("rag.embeddings.get_embedding") as mock_embed:
                mock_embed.return_value = np.random.randn(1, 384).astype(np.float32)
                # Load and run after patches so run() sees mocked get_embedding and PgVectorAdapter
                import importlib.util
                spec = importlib.util.spec_from_file_location("ingest_rag", SCRIPT)
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                mod.run(
                    input_path=jsonl,
                    index_name="test_index",
                    provider="pgvector",
                    chunk_size=None,
                    parquet_path=parquet,
                )

        mock_upsert.assert_called_once()
        call_args = mock_upsert.call_args[0][0]
        assert len(call_args) == 1
        assert call_args[0]["id"] == "a1"
        assert call_args[0]["filename"] == "test.pdf"
        assert "embedding" in call_args[0]
        if parquet.exists():
            assert parquet.stat().st_size > 0


def _has_sentence_transformers() -> bool:
    try:
        __import__("sentence_transformers")
        return True
    except ImportError:
        return False


@pytest.mark.skipif(
    not DEFAULT_JSONL.exists(),
    reason="reports_chunks.jsonl not present",
)
@pytest.mark.skipif(
    not _has_sentence_transformers(),
    reason="sentence-transformers not installed (optional for real ingest smoke)",
)
def test_ingest_rag_produces_parquet() -> None:
    """If sample JSONL exists, run real ingest and assert parquet created (smoke)."""
    result = __import__("subprocess").run(
        [sys.executable, str(SCRIPT), "--input", str(DEFAULT_JSONL), "--provider", "pgvector", "--parquet", str(DEFAULT_PARQUET)],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
        timeout=300,
    )
    assert result.returncode == 0, (result.stdout or "") + (result.stderr or "")
    assert DEFAULT_PARQUET.exists(), "rag_embeddings.parquet should be created"
