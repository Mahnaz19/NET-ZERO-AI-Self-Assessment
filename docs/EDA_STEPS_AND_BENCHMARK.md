# EDA: What the script does (step by step)

This document describes exactly what `scripts/eda_portal_export.py` does to the raw portal export and how the **clean data** and **benchmark** files are created.

---

## Step-by-step pipeline

### 1. Read input

- **Input:** Excel (`.xlsx`/`.xls`) or CSV, default path `data/raw/edi_export_20260224_214316.csv.xlsx`.
- If that file is missing, the script creates `data/raw/sample_edi.csv` (10 sample rows) and uses it.
- The file is read into a pandas DataFrame (all columns preserved).

### 2. Normalise column names to snake_case

**What it is:** We rewrite every column header into a single standard form: only lowercase letters, numbers, and underscores. Spaces, hyphens, and slashes become underscores; everything is lowercased.

**Examples:**
- `Company_Primary Business Activity` → `company_primary_business_activity`
- `Annual Cost (£)` → `annual_cost_(£)` (punctuation can remain)
- `Heard About BEAS (Other)` → `heard_about_beas_(other)`

**Why we do it:**
- Code can refer to columns without worrying about spaces or mixed case (e.g. `df["company_primary_business_activity"]` works the same everywhere).
- No accidental “duplicate” columns that are really the same name with different spacing (e.g. `Sector` vs `sector` vs `SECTOR`).
- Easier to match known names (e.g. “sector”, “postcode”) when we look for them later in the script.

### 3. Remove full-row duplicates only

- Rows that are **identical on every column** are dropped (`df.drop_duplicates()`).
- Rows that differ in at least one column are **kept** (e.g. one company with multiple recommendations).
- **Why:** Removes exact duplicate records without losing valid multi-row records per company.

### 4. Trim whitespace on string columns

**What it is:** For every column that holds text (strings), we remove any spaces or tabs at the **start** and **end** of each cell. We do **not** remove spaces in the middle of text. Empty or missing values (NaN) are left as they are.

**Examples:**
- `"  Retail  "` → `"Retail"`
- `"CV1 4JA "` → `"CV1 4JA"`
- `"Accountants"` (no extra spaces) → unchanged
- NaN → still NaN

**Why we do it:**
- The same category can appear in different forms: `"Retail"`, `" Retail"`, `"Retail "`. After trimming, they all become `"Retail"`, so grouping and counting (e.g. by sector or postcode) are correct.
- Exports from Excel or forms often add invisible spaces; trimming avoids “duplicate” categories that are really the same value.

### 5. Uppercase postcode

**What it is:** We look for a column that holds postcodes (by checking if its name is `postcode`, `post_code`, `zip`, or `postal_code` after snake_casing). If we find it, we convert every **text** value in that column to UPPERCASE. Missing values (NaN) are not changed.

**Examples:**
- `"cv1 4ja"` → `"CV1 4JA"`
- `"SW1A 1AA"` → unchanged (already uppercase)
- `"M1 4ee"` → `"M1 4EE"`
- NaN → still NaN

**Why we do it:**
- UK postcodes are usually written in uppercase in official use. Making them all uppercase gives one consistent format.
- Matching and reporting (e.g. “all sites in CV1”, or grouping by postcode area) work reliably when we don’t mix "cv1" and "CV1" as if they were different.

### 6. Sector column: use existing or add "unknown"

- The script looks for a column whose **exact** name (case-insensitive) is one of:
  - `company_primary_business_activity`
  - `sector`
  - `business_activity`
  - `industry`
- **If such a column exists:** it is used for grouping (no new column is created); the benchmark file will use it and rename it to **`company_primary_business_activity`** in the output.
- **If no such column exists:** a new column **`company_primary_business_activity`** is added and every row is set to **`"unknown"`**.
- **Why:** Downstream steps (benchmarks, summary) need one column for sector-style grouping. The EDI export uses `company_primary_business_activity`, so the script matches it and benchmarks are produced per real sector (e.g. Manufacturing, Retail). Rows with missing sector stay as NaN and appear as one group in the benchmark file.

### 7. Coerce numeric columns

**What it is:** We detect columns that are **meant** to be numbers (energy, cost, area, etc.) by their **names**: if the name contains words like `kwh`, `consumption`, `cost`, `gbp`, `floor_area`, `annual_kwh`, etc., we try to convert every value in that column to a number. If a value cannot be converted (e.g. text like "N/A" or "—"), we turn it into a missing value (NaN) instead of leaving it as text.

**Examples:**
- `"25000"` (text) → `25000` (number)
- `"1,500"` or `"1500"` → `1500`
- `"N/A"` or `""` or `"—"` → NaN
- A cell that is already a number → unchanged

**Why we do it:**
- Averages, sums, and benchmarks (e.g. mean electricity per sector) only make sense for **numeric** columns. If some cells are stored as text, the computer might treat them as non-numeric and skip them or error.
- By **coercing** (forcing) these columns to numbers and turning bad values into NaN, we keep the data usable for maths without deleting whole rows; we only mark the bad cells as missing.

### 8. Drop columns with very high missing (≥ 90%)

- **What it is:** For each column we compute the percentage of missing values (NaNs). Any column with **missing ≥ 90%** is **dropped** from the dataset. No rows are removed.
- **Why:** Columns that are almost entirely empty add little for analysis and can be excluded from clean_data and benchmarks. The threshold (90%) is configurable in the script.
- **Output:** The list of dropped column names is recorded in the EDA summary (see **Columns dropped (missing >= 90%)**).

### 9. Working column "sector" and sector-based median imputation

- **Sector column:** A working column **`sector`** is created from **Company Primary Business Activity** (`company_primary_business_activity`). If the value is missing or blank, it is set to **`"unknown"`**. No other columns are modified for this step.
- **Imputation (electricity and gas only):** For **Company Estimated Yearly Electricity Consumption (KWh)** and **Company Estimated Yearly Gas Consumption (KWh)**:
  - We compute the **median** of each variable **per sector**.
  - For each row where electricity (or gas) is missing, we fill it with the **median of that row’s sector**.
  - If the sector has no median (e.g. sector has no non-missing values), we use the **global median** (median over all rows) as fallback.
- **Scope:** Only these two consumption columns are imputed. No other columns are filled. No rows are removed. No ML or advanced imputation is used—only sector median with global median fallback.

### 10. Write clean data

- The resulting DataFrame is written to **`data/processed/clean_data.csv`** (or whatever `--out` directory you pass).
- **clean_data.csv** includes: same (snake_cased) columns as after step 8 (minus dropped columns), plus the **sector** column, with electricity and gas consumption missing values filled by sector median (or global median) as above. No other columns are imputed.

---

## How the benchmark file is created

- **File:** `data/processed/benchmarks_by_sector.csv` (same `--out` directory as clean data).
- **Based on:** The **clean data** DataFrame after imputation, grouped by the **sector** column (from Company Primary Business Activity, with missing → "unknown").
- **Columns in the benchmark file:**
  - **sector:** sector label (one per row).
  - **count:** number of rows (sites/records) per sector.
  - **median_electricity_kwh:** median of the electricity consumption column per sector (if the column exists).
  - **mean_electricity_kwh:** mean of the electricity consumption column per sector (if the column exists).
  - **median_gas_kwh:** median of the gas consumption column per sector (if the column exists).
  - **mean_gas_kwh:** mean of the gas consumption column per sector (if the column exists).
- **benchmarks_by_sector.csv** = one row per sector, with **sector**, **count**, **median_electricity_kwh**, **mean_electricity_kwh**, **median_gas_kwh**, **mean_gas_kwh** (when those energy columns exist in the clean data).

---

## Final result (current run)

Based on the latest run of `eda_portal_export.py` on **edi_export_20260224_214316.csv.xlsx**:

| Metric | Value |
|--------|--------|
| Input rows (after reading) | 21,219 |
| Full duplicate rows removed | 266 |
| Columns dropped (missing ≥ 90%) | 11 |
| Rows in cleaned data | 20,953 |
| Columns in cleaned data | 152 (including **sector**) |
| Sectors | 34 |

**Top 10 sectors by count**

| Sector | Sites |
|--------|--------|
| C: Manufacturing | 7,461 |
| S: Other Service Activities | 4,445 |
| N: Admin & Support Service Activities | 1,709 |
| G: Wholesale & Retail Trade; Repair of Motor Vehicles | 1,216 |
| Q: Human Health & Social Work Activities | 977 |
| R: Arts, Entertainment & Recreation | 826 |
| I: Accommodation & Food Services | 771 |
| unknown | 635 |
| J: Information & Communication | 443 |
| P: Education | 425 |

The benchmark file **benchmarks_by_sector.csv** has one row per sector with columns **sector**, **count**, **median_electricity_kwh**, **mean_electricity_kwh**, **median_gas_kwh**, **mean_gas_kwh**. Missing sector in the raw data is mapped to **unknown** and included as one group. Electricity and gas consumption missing values are filled by sector median (fallback to global median) before computing benchmarks.

---

## Legacy note

Previously, if no sector column was matched, **benchmarks_by_sector.csv** had one row: `unknown` / total count. The script now uses **company_primary_business_activity** to build a **sector** column (missing → "unknown"), drops columns with ≥ 90% missing, applies sector median imputation for electricity and gas, and outputs benchmarks with **sector**, **count**, **median_electricity_kwh**, **mean_electricity_kwh**, **median_gas_kwh**, **mean_gas_kwh**.

---

## Summary table

| Step | What is done | Why |
|------|----------------|-----|
| 1 | Read Excel/CSV | Load raw export. |
| 2 | Snake_case column names | Consistent names. |
| 3 | Drop full-row duplicates | Remove exact duplicates only. |
| 4 | Trim whitespace (strings) | Clean categories. |
| 5 | Uppercase postcode | Consistent format. |
| 6 | Use or add sector source column | First match among company_primary_business_activity, sector, business_activity, industry; else "unknown". |
| 7 | Coerce numeric columns | Safe aggregation. |
| 8 | Drop columns with missing ≥ 90% | Remove very sparse columns; no row removal. |
| 9 | Create **sector** column; sector median imputation (elec/gas) | Sector from Company Primary Business Activity (missing → "unknown"); fill missing electricity/gas with sector median (fallback global median). |
| 10 | Write clean_data.csv | Output cleaned rows (with sector and imputed elec/gas). |
| — | Group by sector → count, median/mean electricity, median/mean gas | Build benchmark. |
| — | Write benchmarks_by_sector.csv | One row per sector: **sector**, **count**, **median_electricity_kwh**, **mean_electricity_kwh**, **median_gas_kwh**, **mean_gas_kwh**. |

The script uses **Company Primary Business Activity** for sector; missing becomes **unknown**. It drops columns with ≥ 90% missing, then applies **sector-based median imputation** only for yearly electricity and gas consumption (KWh), and writes benchmarks with sector, count, and median/mean for both energy columns.
