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
REDIS_URL=redis://localhost:6379/0
RAG_PROVIDER=auto        # or parquet / pgvector
AZURE_OPENAI_ENDPOINT=...
AZURE_OPENAI_API_KEY=...
AZURE_OPENAI_DEPLOYMENT=...
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
- RAG ingestion and LLM pipeline are implemented under `backend/rag/`; see below.

### Recommendations API (RAG→LLM pipeline)

The recommendations pipeline loads a submission, computes deterministic baseline and candidate measures, retrieves relevant report chunks (RAG), and calls an LLM to produce ranked recommendations and an executive summary. All numeric calculations are deterministic; the LLM only provides natural-language text and ranking.

**Endpoints**

- **POST /api/recommendations** — Body: `{"submission_id": <int>, "top_k": <int, optional, default 5>}`. Runs the pipeline and returns the generated report (200). Creates or overwrites the stored report for that submission.
- **GET /api/recommendations/{submission_id}** — Returns the stored `report_json` for the submission (404 if not found or no report yet).

**Retrieval provider**

- By default the pipeline uses **auto**: if `DATABASE_URL` is set and Postgres is reachable, it uses **pgvector** for RAG retrieval; if the DB connection fails, it falls back to **parquet** (reads `data/processed/rag_embeddings.parquet`) and logs a warning.
- To force parquet-only (e.g. no Postgres), ensure `data/processed/rag_embeddings.parquet` exists (run `python scripts/ingest_rag.py` from repo root) and either do not set `DATABASE_URL` or use a provider that skips DB (the current implementation falls back to parquet on connection failure).

**Azure OpenAI integration**

- To use a real LLM (Azure OpenAI), set these environment variables (e.g. in `.env` or your shell):
  - `AZURE_OPENAI_ENDPOINT` — e.g. `https://your-resource.openai.azure.com`
  - `AZURE_OPENAI_API_KEY` — your API key
  - `AZURE_OPENAI_DEPLOYMENT` — deployment name for the chat model
- If **any** of these are missing, the backend uses **MockLLM** (no API calls): you can run the pipeline locally and in CI without Azure. MockLLM returns deterministic JSON so tests and development work without real keys.

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

### Background processing and worker

Submissions are now accepted synchronously but processed in the background via an RQ worker.

**Flow**

- **POST /api/submit** — Creates a submission in the DB with `status="received"` and immediately returns `201` with the submission JSON. It enqueues a background job (via Redis/RQ) to run the RAG→LLM pipeline for that submission.
- The RQ worker runs `app.worker.process_submission_job(submission_id)`, which calls `rag.pipeline.run_recommendation_pipeline(...)` and persists the report JSON.
- **Admin**: **POST /api/admin/process_submission** — Body: `{"submission_id": <int>}`. Manually triggers processing for a submission by calling the same worker job inline (intended for dev/testing).

**Health checks**

- **GET /api/health** — Simple `{"status": "ok"}`.
- **GET /api/healthz** — Checks DB connectivity and, if `REDIS_URL` is set, Redis connectivity. Returns `{"status": "ok" | "degraded", "db_ok": bool, "redis_ok": bool | null}`.

**Local Docker stack**

The root `docker-compose.yml` now includes:

- `db` — Postgres with pgvector.
- `redis` — Redis for the RQ queue.
- `backend` — FastAPI app container built from `backend/Dockerfile`.

From the project root:

```bash
docker compose up -d --build
```

This starts Postgres, Redis, and the backend on `http://localhost:8000`.

**Worker commands**

In one terminal (backend API, if not using `command` in compose):

```bash
docker compose exec backend uvicorn app.main:app --host 0.0.0.0 --port 8000
```

In another terminal (RQ worker on the `default` queue):

```bash
docker compose exec backend rq worker default
```

The worker will pick up jobs enqueued by `POST /api/submit`.

**Manual processing via admin endpoint**

```bash
curl -X POST http://localhost:8000/api/admin/process_submission \
  -H "Content-Type: application/json" \
  -d '{"submission_id": 1}'
```

This is useful during development to re-run processing for a given submission without re-submitting answers.

### Report PDF generation

The backend can render the stored report JSON as HTML and PDF (no LLM calls; deterministic only).

**Endpoints**

- **POST /api/reports/generate_pdf** — Body: `{"submission_id": <int>}`. Generates a PDF from the submission’s stored report and returns it as `application/pdf` with `Content-Disposition: attachment; filename="report_{id}.pdf"`. Returns 400 if the submission has no report (run the recommendations pipeline first).
- **GET /api/reports/html/{submission_id}** — Returns the report rendered as HTML for preview or debugging.

**Dependencies**

- **Jinja2** — used for the HTML template (`pip install jinja2`).
- **WeasyPrint** (preferred) — `pip install weasyprint`. On Windows/macOS you may need system libraries (e.g. Pango, GTK). If WeasyPrint fails, the code falls back to Playwright.
- **Playwright** (fallback) — `pip install playwright`, then install a browser: `playwright install chromium`. Use this if WeasyPrint is not available or fails (e.g. missing C dependencies).

**Example: generate PDF**

After a report exists for a submission (from POST /api/recommendations):

```bash
curl -X POST http://localhost:8000/api/reports/generate_pdf \
  -H "Content-Type: application/json" \
  -d '{"submission_id": 1}' \
  --output report_1.pdf
```

To preview HTML: `GET http://localhost:8000/api/reports/html/1`

