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
- RAG ingestion and LLM pipeline are implemented under `backend/rag/`; see below.

### Recommendations API (RAG→LLM pipeline)

The recommendations pipeline loads a submission, computes deterministic baseline and candidate measures, retrieves relevant report chunks (RAG), and calls an LLM to produce ranked recommendations and an executive summary. All numeric calculations are deterministic; the LLM only provides natural-language text and ranking.

**Endpoints**

- **POST /api/recommendations** — Body: `{"submission_id": <int>, "top_k": <int, optional, default 5>}`. Runs the pipeline and returns the generated report (200). Creates or overwrites the stored report for that submission.
- **GET /api/recommendations/{submission_id}** — Returns the stored `report_json` for the submission (404 if not found or no report yet).

**Retrieval provider**

- By default the pipeline uses **auto**: if `DATABASE_URL` is set and Postgres is reachable, it uses **pgvector** for RAG retrieval; if the DB connection fails, it falls back to **parquet** (reads `data/processed/rag_embeddings.parquet`) and logs a warning.
- To force parquet-only (e.g. no Postgres), ensure `data/processed/rag_embeddings.parquet` exists (run `python scripts/ingest_rag.py` from repo root) and either do not set `DATABASE_URL` or use a provider that skips DB (the current implementation falls back to parquet on connection failure).

**Azure OpenAI (real LLM)**

- Set these environment variables to use Azure OpenAI instead of the mock LLM:
  - `AZURE_OPENAI_ENDPOINT` — e.g. `https://your-resource.openai.azure.com`
  - `AZURE_OPENAI_API_KEY` — your API key
  - `AZURE_OPENAI_DEPLOYMENT` — deployment name for the chat model
- If any of these are missing, the backend uses **MockLLM**, which returns deterministic example JSON (no API calls). Use this for local development and CI.

**Example: call POST /api/recommendations**

From the repo root (with backend running on port 8000):

```bash
# Create a submission first (POST /api/submit with answers), then:
curl -X POST http://localhost:8000/api/recommendations \
  -H "Content-Type: application/json" \
  -d '{"submission_id": 1, "top_k": 5}'
```

Or with httpie:

```bash
http POST localhost:8000/api/recommendations submission_id:=1 top_k:=5
```

Example response (with MockLLM): `{"executive_summary": "...", "recommendations": [...], "baseline": {...}, "candidates": [...]}`.

