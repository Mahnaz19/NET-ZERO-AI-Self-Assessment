"""Test EDA script: run on sample data and assert output files exist."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "eda_portal_export.py"


def test_eda_creates_clean_data_and_benchmarks(tmp_path: Path) -> None:
    """Run EDA script on a small CSV; assert clean_data.csv and benchmarks_by_sector.csv exist."""
    sample_csv = tmp_path / "sample.csv"
    sample_csv.write_text(
        "sector,annual_kwh,annual_cost_gbp,floor_area_m2,postcode\n"
        "Retail,25000,7500,200,SW1A 1AA\n"
        "Office,40000,12000,500,EC1A 1BB\n"
    )
    out_dir = tmp_path / "out"
    out_dir.mkdir()

    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--input", str(sample_csv), "--out", str(out_dir)],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
    )
    assert result.returncode == 0, (result.stdout or "") + (result.stderr or "")

    assert (out_dir / "clean_data.csv").exists(), "clean_data.csv should be created"
    assert (out_dir / "benchmarks_by_sector.csv").exists(), "benchmarks_by_sector.csv should be created"
    assert (out_dir / "eda_summary.md").exists(), "eda_summary.md should be created"
