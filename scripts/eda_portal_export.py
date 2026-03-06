from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = REPO_ROOT / "data" / "raw" / "edi_export_20260224_214316.csv.xlsx"
DEFAULT_OUT = REPO_ROOT / "data" / "processed"
SAMPLE_EDI_PATH = REPO_ROOT / "data" / "raw" / "sample_edi.csv"


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


def _ensure_input(input_path: Path) -> Path:
    """If input path does not exist, create sample_edi.csv and return its path."""
    if input_path.exists():
        return input_path
    input_path.parent.mkdir(parents=True, exist_ok=True)
    sample = pd.DataFrame([
        {"sector": "Retail", "annual_kwh": 25000, "annual_cost_gbp": 7500, "floor_area_m2": 200, "postcode": "SW1A 1AA"},
        {"sector": "Office", "annual_kwh": 40000, "annual_cost_gbp": 12000, "floor_area_m2": 500, "postcode": "EC1A 1BB"},
        {"sector": "Retail", "annual_kwh": 18000, "annual_cost_gbp": 5400, "floor_area_m2": 150, "postcode": "W1 2CC"},
        {"sector": "Manufacturing", "annual_kwh": 120000, "annual_cost_gbp": 36000, "floor_area_m2": 2000, "postcode": "B1 3DD"},
        {"sector": "Office", "annual_kwh": 35000, "annual_cost_gbp": 10500, "floor_area_m2": 400, "postcode": "M1 4EE"},
        {"sector": "Hospitality", "annual_kwh": 45000, "annual_cost_gbp": 13500, "floor_area_m2": 600, "postcode": "L1 5FF"},
        {"sector": "Retail", "annual_kwh": 22000, "annual_cost_gbp": 6600, "floor_area_m2": 180, "postcode": "S1 6GG"},
        {"sector": "Education", "annual_kwh": 80000, "annual_cost_gbp": 24000, "floor_area_m2": 1200, "postcode": "LS1 7HH"},
        {"sector": "Office", "annual_kwh": 28000, "annual_cost_gbp": 8400, "floor_area_m2": 350, "postcode": "B2 8II"},
        {"sector": "Manufacturing", "annual_kwh": 95000, "annual_cost_gbp": 28500, "floor_area_m2": 1500, "postcode": "CV1 9JJ"},
    ])
    sample.to_csv(SAMPLE_EDI_PATH, index=False)
    return SAMPLE_EDI_PATH


def run(input_path: Path, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)

    input_path = _ensure_input(input_path)
    if input_path.suffix.lower() in (".xlsx", ".xls"):
        df = pd.read_excel(input_path)
    else:
        df = pd.read_csv(input_path)
    df.columns = [_snake_case(str(c)) for c in df.columns]

    # Drop only rows that are exactly identical on every column (full duplicate rows).
    # One company can have many recommendations/steps; those rows differ and are kept.
    n_before = len(df)
    df = df.drop_duplicates()
    n_dupes_removed = n_before - len(df)

    # Trim leading/trailing whitespace on all string columns (leave NaN as NaN).
    for col in df.select_dtypes(include=["object"]).columns:
        df[col] = df[col].apply(lambda x: x.strip() if isinstance(x, str) else x)

    # Uppercase postcode for consistency (find column by common names).
    postcode_col = _find_first_column(
        ("postcode", "post_code", "zip", "postal_code"), list(df.columns)
    )
    if postcode_col:
        df[postcode_col] = df[postcode_col].apply(
            lambda x: x.strip().upper() if isinstance(x, str) else x
        )

    # Identify sector column.
    sector_candidates = ("sector", "business_activity", "industry")
    sector_col = _find_first_column(sector_candidates, list(df.columns))
    if sector_col is None:
        df["sector"] = "unknown"
        sector_col = "sector"

    # Coerce numeric columns: energy-related and cost/area fields.
    numeric_keywords = (
        "kwh", "consumption", "usage", "saving", "cost", "gbp",
        "floor_area", "area", "floor_area_m2", "annual_kwh", "annual_cost"
    )
    for col in df.columns:
        if any(key in col.lower() for key in numeric_keywords):
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Missing data: no imputation (NaNs stay NaN) to avoid introducing bias.
    # Outliers: no automatic removal; review extreme values in key columns if needed.

    # Write cleaned data to CSV for export / reuse.
    clean_path = out_dir / "clean_data.csv"
    df.to_csv(clean_path, index=False, encoding="utf-8")

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

    # Missingness: count nulls per column (for summary).
    missing = df.isna().sum()
    missing_pct = (missing / len(df) * 100).round(1)
    missing_table = pd.DataFrame({
        "column": missing.index,
        "missing_count": missing.values,
        "missing_pct": missing_pct.values,
    })
    missing_table = missing_table[missing_table["missing_count"] > 0].sort_values(
        "missing_count", ascending=False
    )

    # EDA summary markdown.
    summary_lines: list[str] = []
    summary_lines.append(f"# EDA Summary for {input_path.name}")
    summary_lines.append("")
    summary_lines.append(f"- Input rows (after reading): {n_before}")
    summary_lines.append(f"- Full duplicate rows removed: {n_dupes_removed}")
    summary_lines.append(f"- Rows in cleaned data: {len(df)}")
    summary_lines.append(f"- Sectors: {benchmarks['sector'].nunique()}")
    summary_lines.append("")
    summary_lines.append("## Top 10 sectors by count")
    summary_lines.append("")

    top10 = benchmarks.sort_values("count", ascending=False).head(10)
    for _, row in top10.iterrows():
        summary_lines.append(f"- {row['sector']}: {int(row['count'])} sites")

    summary_lines.append("")
    summary_lines.append("## Missingness (columns with at least one null)")
    summary_lines.append("")
    if len(missing_table) == 0:
        summary_lines.append("No missing values in any column.")
    else:
        summary_lines.append("| Column | Missing count | Missing % |")
        summary_lines.append("|--------|---------------|------------|")
        for _, row in missing_table.iterrows():
            summary_lines.append(
                f"| {row['column']} | {int(row['missing_count'])} | {row['missing_pct']}% |"
            )

    summary_lines.append("")
    summary_lines.append("## Notes")
    summary_lines.append("")
    summary_lines.append("- **Missing data:** No imputation applied; NaNs are left as-is.")
    summary_lines.append("- **Outliers:** No automatic detection or removal; review extreme values in key columns if needed.")

    summary_path = out_dir / "eda_summary.md"
    summary_path.write_text("\n".join(summary_lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="EDA for portal export file.")
    parser.add_argument(
        "--input",
        type=Path,
        default=DEFAULT_INPUT,
        help=f"Path to Excel or CSV (default: data/raw/edi_export_20260224_214316.csv.xlsx)",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=DEFAULT_OUT,
        help="Output directory for clean_data.csv, benchmarks, summary (default: data/processed)",
    )
    args = parser.parse_args()
    run(args.input, args.out)


if __name__ == "__main__":
    main()

