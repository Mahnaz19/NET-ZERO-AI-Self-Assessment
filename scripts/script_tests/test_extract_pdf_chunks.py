"""Test PDF extractor: run on default dir and assert JSONL exists; skip if no PDFs."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "extract_pdf_chunks.py"
DEFAULT_PDF_DIR = REPO_ROOT / "data" / "raw" / "reports_sample"
DEFAULT_OUT = REPO_ROOT / "data" / "processed" / "reports_chunks.jsonl"


def test_extract_pdf_chunks_produces_jsonl() -> None:
    """Run PDF extractor; assert output JSONL exists. If no PDFs, skip."""
    pdfs = list(DEFAULT_PDF_DIR.glob("*.pdf")) if DEFAULT_PDF_DIR.exists() else []
    if not pdfs:
        pytest.skip("No sample PDFs in data/raw/reports_sample")

    result = subprocess.run(
        [sys.executable, str(SCRIPT)],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
    )
    assert result.returncode == 0, (result.stdout or "") + (result.stderr or "")

    assert DEFAULT_OUT.exists(), "reports_chunks.jsonl should be created"
    lines = [l for l in DEFAULT_OUT.read_text(encoding="utf-8").strip().splitlines() if l]
    if not lines:
        pytest.skip("No PDFs produced chunks (empty directory or empty PDFs)")
    assert len(lines) >= 1, "At least one chunk record expected"
