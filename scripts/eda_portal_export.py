from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable

import pandas as pd


def _snake_case(name: str) -> str:
    return (
        name.strip()
        .replace(" ", "_")
        .replace("-", "_")
        .replace("/", "_")
        .lower()
    )


def _find_first_column(candidates: Iterable[str], columns: list[str]) -> str | None:
    cols_lower = {c.lower(): c for c in columns}
    for candidate in candidates:
        if candidate.lower() in cols_lower:
            return cols_lower[candidate.lower()]
    return None


def run(input_path: Path, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_excel(input_path)
    df.columns = [_snake_case(str(c)) for c in df.columns]
    df = df.drop_duplicates()

    # Identify sector column.
    sector_candidates = ("sector", "business_activity", "industry")
    sector_col = _find_first_column(sector_candidates, list(df.columns))
    if sector_col is None:
        df["sector"] = "unknown"
        sector_col = "sector"

    # Coerce numeric columns we care about.
    for col in df.columns:
        if any(key in col for key in ("kwh", "consumption", "usage", "saving")):
            df[col] = pd.to_numeric(df[col], errors="coerce")

    elec_col = _find_first_column(
        ("electricity_kwh", "annual_electricity_kwh", "electricity_consumption_kwh"),
        list(df.columns),
    )
    gas_col = _find_first_column(
        ("gas_kwh", "annual_gas_kwh", "gas_consumption_kwh"),
        list(df.columns),
    )

    group = df.groupby(sector_col, dropna=False)
    agg_data = {
        "count": group.size(),
    }
    if elec_col:
        agg_data["mean_electricity_kwh"] = group[elec_col].mean()
    if gas_col:
        agg_data["mean_gas_kwh"] = group[gas_col].mean()

    benchmarks = pd.DataFrame(agg_data).reset_index().rename(
        columns={sector_col: "sector"},
    )

    benchmarks_path = out_dir / "benchmarks_by_sector.csv"
    benchmarks.to_csv(benchmarks_path, index=False)

    # EDA summary markdown.
    summary_lines: list[str] = []
    summary_lines.append(f"# EDA Summary for {input_path.name}")
    summary_lines.append("")
    summary_lines.append(f"- Input rows: {len(df)}")
    summary_lines.append(f"- Sectors: {benchmarks['sector'].nunique()}")
    summary_lines.append("")
    summary_lines.append("## Top 10 sectors by count")
    summary_lines.append("")

    top10 = benchmarks.sort_values("count", ascending=False).head(10)
    for _, row in top10.iterrows():
        summary_lines.append(f"- {row['sector']}: {int(row['count'])} sites")

    summary_path = out_dir / "eda_summary.md"
    summary_path.write_text("\n".join(summary_lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="EDA for portal export file.")
    parser.add_argument(
        "--input",
        type=Path,
        required=True,
        help="Path to edi_export_*.xlsx file",
    )
    parser.add_argument(
        "--out",
        type=Path,
        required=True,
        help="Output directory for benchmarks and summary",
    )
    args = parser.parse_args()
    run(args.input, args.out)


if __name__ == "__main__":
    main()

