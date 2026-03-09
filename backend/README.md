## Backend - NetZero AI Self-Assessment

This directory contains the FastAPI-based backend for the NetZero AI Self-Assessment project.
It provides endpoints for accepting questionnaire submissions, persisting them to Postgres,
and returning stored submissions and simple deterministic example reports.

### Requirements

- Python 3.11+ (recommended)
- Local Postgres instance provided via the root `docker-compose.yml`
- A `.env` file in the project root (see `.env.example`)
- Optional: a local virtual environment in `backend/.venv` (not committed to git)

### Setup

1. **Create and activate a virtual environment (recommended)**

   From the project root:

   ```bash
   cd backend
   python -m venv .venv
   # On macOS/Linux
   source .venv/bin/activate
   # On Windows (PowerShell)
   .venv\\Scripts\\Activate.ps1
   ```

2. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

3. **Create your `.env` file**

   From the project root, copy the example:

   ```bash
   cp .env.example .env
   ```

   Ensure `DATABASE_URL` matches the Postgres container. For example:

   ```bash
   DATABASE_URL=postgresql://app:app@localhost:5432/netzero
   ENVIRONMENT=development
   ```

4. **Start Postgres via Docker Compose**

   From the project root:

   ```bash
   docker compose up -d
   ```

### Run the backend

From the project root:

```bash
cd backend
./run.sh
```

Then open the interactive API docs:

- Swagger UI: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/api/health`

### How to test

From the project root:

```bash
# Backend API and calculators
py -m pytest backend/tests -q

# Optional: EDA and PDF script tests (requires pandas, openpyxl, pdfplumber)
py -m pytest backend/tests scripts/script_tests -q
```

### EDA and PDF scripts

From the project root (defaults use `data/raw` and `data/processed`):

```bash
# EDA: clean portal export and benchmarks (default input: data/raw/edi_export_*.xlsx, output: data/processed)
py scripts/eda_portal_export.py
# Or with explicit paths:
py scripts/eda_portal_export.py --input data/raw/your_export.xlsx --out data/processed

# PDF chunks: extract text chunks from PDFs (default: data/raw/reports_sample → data/processed/reports_chunks.jsonl)
py scripts/extract_pdf_chunks.py
# Or: py scripts/extract_pdf_chunks.py --pdf_dir path/to/pdfs --out path/to/reports_chunks.jsonl
```

### Assumptions (calculators)

Deterministic calculators in `backend/calculators/` use these defaults (see `backend/calculators/defaults.py`):

| Constant | Value | Description |
|----------|-------|-------------|
| `ELECTRICITY_CO2_FACTOR_KG_PER_KWH` | 0.19553 | kg CO2e per kWh electricity |
| `GAS_CO2_FACTOR_KG_PER_KWH` | 0.18296 | kg CO2e per kWh gas |
| `DEFAULT_TARIFF_P_PER_KWH` | 30.0 | p/kWh when tariff not provided |
| `DEFAULT_LIGHTING_SAVINGS_PCT` | 0.45 | LED upgrade savings fraction |
| `DEFAULT_SOLAR_KWH_PER_KWP` | 900.0 | kWh per kWp per year |
| `DEFAULT_SELF_CONSUMPTION` | 0.75 | Fraction of solar self-consumed |
| `DEFAULT_REFRIG_SAVINGS_PCT` | 0.15 | Refrigeration upgrade savings |
| `DEFAULT_INSULATION_SAVINGS_PCT` | 0.12 | Building fabric improvement |
| `DEFAULT_HEAT_PUMP_SAVINGS_PCT` | 0.60 | Fraction of heating load replaced by heat pump |

All carbon savings are returned in **tonnes CO2e** (converted from kg in the calculators).

### Notes and TODOs

- Deterministic calculator modules live in `backend/calculators/` (solar, lighting, boiler, refrigeration, heatpump, building fabric, cooling, ventilation, heaters, energy management, misc electric/gas). They use the constants in `backend/calculators/defaults.py`.
- TODO: Replace calculator stubs with real assessor logic based on the Excel tools in `/docs`.
- TODO: Introduce background processing for report generation instead of synchronous processing.
- TODO: Add RAG ingestion and LLM orchestration using Azure OpenAI configuration from environment variables.

