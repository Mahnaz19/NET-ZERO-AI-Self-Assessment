from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = REPO_ROOT / "data" / "raw" / "edi_export_20260224_214316.csv.xlsx"
DEFAULT_OUT = REPO_ROOT / "data" / "processed"
SAMPLE_EDI_PATH = REPO_ROOT / "data" / "raw" / "sample_edi.csv"

# Drop columns with at least this fraction of values missing (applied to raw-based cleaned df).
MISSING_PCT_DROP_THRESHOLD = 90.0


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


def _find_groupby_column(columns: list[str]) -> str | None:
    """Use company_primary_business_activity for benchmark grouping only. No extra 'sector' column."""
    return _find_first_column(
        ("company_primary_business_activity", "sector", "business_activity", "industry"),
        columns,
    )


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
        # EDI export has header in row 1 (row 0 is often empty); use header=1 so we get real column names.
        df = pd.read_excel(input_path, header=1)
    else:
        df = pd.read_csv(input_path)
    # Strip BOM from first column name if present, then snake_case all.
    df.columns = [_snake_case(str(c).strip().lstrip("\ufeff")) for c in df.columns]

    # Drop only rows that are exactly identical on every column (full duplicate rows).
    # One company can have many recommendations/steps; those rows differ and are kept.
    n_before = len(df)
    df = df.drop_duplicates()
    n_dupes_removed = n_before - len(df)

    # Trim leading/trailing whitespace on all string columns (leave NaN as NaN).
    for col in df.select_dtypes(include=["object", "string"]).columns:
        df[col] = df[col].apply(lambda x: x.strip() if isinstance(x, str) else x)

    # Uppercase postcode for consistency (find column by common names).
    postcode_col = _find_first_column(
        ("postcode", "post_code", "zip", "postal_code"), list(df.columns)
    )
    if postcode_col:
        df[postcode_col] = df[postcode_col].apply(
            lambda x: x.strip().upper() if isinstance(x, str) else x
        )

    # Group by company_primary_business_activity (no extra 'sector' column created).
    groupby_col = _find_groupby_column(list(df.columns))
    if groupby_col is None:
        df = df.copy()
        df["company_primary_business_activity"] = "unknown"
        groupby_col = "company_primary_business_activity"

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

    # EDA missingness: compute missing count and % per column (on raw-based cleaned df).
    n_rows = len(df)
    missing_count = df.isna().sum()
    missing_pct_per_col = (missing_count / n_rows * 100).round(1)
    # Drop columns with missing % >= threshold (e.g. 90%).
    cols_to_drop = missing_pct_per_col[missing_pct_per_col >= MISSING_PCT_DROP_THRESHOLD].index.tolist()
    columns_dropped_high_missing = list(cols_to_drop)
    df = df.drop(columns=cols_to_drop, errors="ignore")
    # If groupby column was dropped, re-add or re-resolve.
    if groupby_col not in df.columns:
        groupby_col = _find_groupby_column(list(df.columns))
        if groupby_col is None:
            df["company_primary_business_activity"] = "unknown"
            groupby_col = "company_primary_business_activity"

    # Fill empty/NaN in Company Primary Business Activity with "unknown" (in place; no extra sector column).
    mask_unknown = df[groupby_col].isna() | (df[groupby_col].astype(str).str.strip() == "")
    df.loc[mask_unknown, groupby_col] = "unknown"

    # Resolve electricity and gas columns for imputation and benchmarks.
    elec_col = _find_first_column(
        (
            "company_estimated_yearly_electricity_consumption_(kwh)",
            "electricity_kwh",
            "annual_electricity_kwh",
            "electricity_consumption_kwh",
        ),
        list(df.columns),
    )
    gas_col = _find_first_column(
        (
            "company_estimated_yearly_gas_consumption_(kwh)",
            "gas_kwh",
            "annual_gas_kwh",
            "gas_consumption_kwh",
        ),
        list(df.columns),
    )

    # Sector-based median imputation (electricity and gas only; fallback to global median).
    # Grouping uses company_primary_business_activity (now with "unknown" for missing).
    if elec_col:
        sector_median_elec = df.groupby(groupby_col, dropna=False)[elec_col].median()
        global_median_elec = df[elec_col].median()
        missing_elec = df[elec_col].isna()
        df.loc[missing_elec, elec_col] = df.loc[missing_elec, groupby_col].map(sector_median_elec)
        df[elec_col] = df[elec_col].fillna(global_median_elec)
    if gas_col:
        sector_median_gas = df.groupby(groupby_col, dropna=False)[gas_col].median()
        global_median_gas = df[gas_col].median()
        missing_gas = df[gas_col].isna()
        df.loc[missing_gas, gas_col] = df.loc[missing_gas, groupby_col].map(sector_median_gas)
        df[gas_col] = df[gas_col].fillna(global_median_gas)

    # Write cleaned data to CSV (no sector column; company_primary_business_activity has "unknown" where missing).
    clean_path = out_dir / "clean_data.csv"
    df.to_csv(clean_path, index=False, encoding="utf-8")

    # Benchmarks: group by company_primary_business_activity; output column named "sector" in CSV.
    group = df.groupby(groupby_col, dropna=False)
    agg_data: dict = {"count": group.size()}
    if elec_col:
        agg_data["median_electricity_kwh"] = group[elec_col].median()
        agg_data["mean_electricity_kwh"] = group[elec_col].mean()
    if gas_col:
        agg_data["median_gas_kwh"] = group[gas_col].median()
        agg_data["mean_gas_kwh"] = group[gas_col].mean()

    benchmarks = pd.DataFrame(agg_data).reset_index().rename(columns={groupby_col: "sector"})

    benchmarks_path = out_dir / "benchmarks_by_sector.csv"
    benchmarks.to_csv(benchmarks_path, index=False)

    # Missingness: count nulls per column on remaining columns (after dropping >= 90% missing).
    missing = df.isna().sum()
    missing_pct = (missing / len(df) * 100).round(1)
    missing_table = pd.DataFrame({
        "column": missing.index,
        "missing_count": missing.values,
        "missing_pct": missing_pct.values,
    })
    missing_table_sorted = missing_table.sort_values("missing_pct", ascending=False)

    # EDA summary markdown.
    summary_lines: list[str] = []
    summary_lines.append(f"# EDA Summary for {input_path.name}")
    summary_lines.append("")
    summary_lines.append(f"- Input rows (after reading): {n_before}")
    summary_lines.append(f"- Full duplicate rows removed: {n_dupes_removed}")
    summary_lines.append(f"- Columns dropped (missing >= {MISSING_PCT_DROP_THRESHOLD}%): {len(columns_dropped_high_missing)}")
    summary_lines.append(f"- Rows in cleaned data: {len(df)}")
    summary_lines.append(f"- Columns in cleaned data: {len(df.columns)}")
    summary_lines.append(f"- Sectors: {benchmarks['sector'].nunique()}")
    summary_lines.append("")
    summary_lines.append("## Columns dropped (missing >= 90%)")
    summary_lines.append("")
    if columns_dropped_high_missing:
        for c in sorted(columns_dropped_high_missing):
            summary_lines.append(f"- {c}")
    else:
        summary_lines.append("None.")
    summary_lines.append("")
    summary_lines.append("## Top 10 sectors by count")
    summary_lines.append("")

    top10 = benchmarks.sort_values("count", ascending=False).head(10)
    for _, row in top10.iterrows():
        summary_lines.append(f"- {row['sector']}: {int(row['count'])} sites")

    summary_lines.append("")
    summary_lines.append("## Missing % per column (remaining columns)")
    summary_lines.append("")
    summary_lines.append("| Column | Missing count | Missing % |")
    summary_lines.append("|--------|---------------|------------|")
    for _, row in missing_table_sorted.iterrows():
        summary_lines.append(
            f"| {row['column']} | {int(row['missing_count'])} | {row['missing_pct']}% |"
        )

    summary_lines.append("")
    summary_lines.append("## Notes")
    summary_lines.append("")
    summary_lines.append(f"- **Columns dropped:** Any column with missing >= {MISSING_PCT_DROP_THRESHOLD}% was removed before writing clean_data.csv.")
    summary_lines.append("- **Sector median imputation:** Missing values in Company Estimated Yearly Electricity and Gas Consumption (KWh) are filled using the median of the row's sector (from Company Primary Business Activity); if sector median is not available, global median is used. No other columns are imputed.")
    summary_lines.append("- **Other missing data:** No further imputation; other NaNs are left as-is.")
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

