# NET-ZERO Self-Assessment

Web application that helps organisations complete an energy self-assessment questionnaire, generate prioritised energy-saving recommendations, and download a PDF report.

The system combines:

- a multi-step questionnaire (Next.js)
- deterministic savings calculators (Python)
- optional retrieval-augmented context from previous assessment reports
- LLM-assisted recommendation wording and ranking (Azure OpenAI when configured; deterministic mock mode for local/CI)

---

## Repository structure

| Path | Purpose |
|------|---------|
| `frontend/` | Next.js questionnaire UI, submission status, report viewer, PDF download |
| `backend/` | FastAPI API, worker jobs, calculators, RAG pipeline, PDF/HTML report generation |
| `scripts/` | Offline tools (EDA, PDF chunking, RAG ingest) |
| `docs/` | Technical notes (RAG, EDA, validation, Azure checklist) |
| `docker-compose.yml` | Local full-stack Docker (db, redis, backend, worker, frontend) |
| `docker-compose.prod.yml` | Production-style Docker compose |
| `infra/` | Placeholder for future infrastructure definitions |

---

## Architecture (runtime)

```text
Browser (frontend :3000)
    → FastAPI backend (:8000)
        → PostgreSQL (submissions + reports)
        → Redis + RQ worker (async recommendation pipeline)
        → Deterministic calculators
        → Optional RAG retrieval + LLM wording
        → PDF generation (WeasyPrint, Playwright fallback)
```

---

## Quick start (Docker — recommended)

Prerequisites: Docker Desktop (or Docker Engine + Compose).

From the repository root:

```bash
docker compose up -d --build
```

Then open:

- Frontend: http://localhost:3000
- Backend API docs: http://localhost:8000/docs
- Health: http://localhost:8000/api/health

Stop:

```bash
docker compose down
```

Remove containers and the database volume:

```bash
docker compose down -v
```

---

## Local development (without full Docker frontend)

### 1. Start data services + API + worker

```bash
docker compose up -d --build db redis backend worker
```

### 2. Frontend

```bash
cd frontend
npm ci
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000 npm run dev
```

Open http://localhost:3000.

### 3. Backend only (optional, for API work)

```bash
cd backend
python -m venv .venv
# Windows PowerShell: .\.venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
cp ../.env.example ../.env
# edit .env if needed
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

In another terminal, run the worker (same env / Redis):

```bash
cd backend
rq worker default
```

---

## Environment variables

Copy examples, then fill secrets locally (never commit real secrets):

```bash
cp .env.example .env
cp .env.production.example .env.production   # for production-style compose
```

### Backend / worker

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | Postgres connection string |
| `REDIS_URL` | Redis URL for RQ (e.g. `redis://localhost:6379/0`) |
| `ENVIRONMENT` | `development` / `local` / `production` |
| `RAG_PROVIDER` | `auto`, `parquet`, or `pgvector` |
| `AZURE_OPENAI_ENDPOINT` | Azure OpenAI endpoint (optional) |
| `AZURE_OPENAI_API_KEY` | Azure OpenAI key (optional) |
| `AZURE_OPENAI_DEPLOYMENT` | Deployment name (optional) |

If Azure OpenAI vars are unset, the backend uses a deterministic mock LLM suitable for local demos and CI.

### Frontend

| Variable | Description |
|----------|-------------|
| `NEXT_PUBLIC_API_BASE_URL` | Backend base URL (default `http://localhost:8000`) |
| `NEXT_PUBLIC_USE_MOCK_BACKEND` | `true` to use static mock assets instead of the API |
| `USE_MOCK_BACKEND` | Server-side companion flag for mock mode |

Mock assets live under `frontend/public/data/mock/` (`report_sample.json`, and optional PDF/questionnaire fixtures).

---

## Production-style Docker

```bash
docker compose --env-file .env.production -f docker-compose.prod.yml up -d --build
```

For real cloud deployments, prefer managed PostgreSQL and Redis, and inject connection URLs via environment variables / secret stores. See `docs/AZURE_DOCKER_DEPLOY_CHECKLIST.md`.

---

## How recommendations are produced

1. User submits questionnaire answers via the frontend.
2. Backend stores the submission and enqueues a background job.
3. Deterministic calculators estimate savings for applicable measure types (lighting, solar, cooling, refrigeration, etc.).
4. Optional RAG retrieval adds context from processed report excerpts.
5. The LLM ranks/selects from calculator candidates and writes recommendation text (it does **not** invent the numeric savings).
6. Validation merges LLM text with calculator numbers; the report is marked ready.
7. User downloads PDF via `POST /api/reports/generate_pdf`.

---

## Data files

| Location | Tracked in Git? | Notes |
|----------|-----------------|-------|
| `/data/raw`, `/data/processed`, `/data/mock` (repo root) | **No** (gitignored) | Local/raw exports, embeddings, generated PDFs — keep off GitHub |
| `frontend/public/data/mock/` | **Yes** | Small fixtures for frontend mock mode |
| Calculators / code | **Yes** | Source of truth for measure logic |

Do **not** commit portal exports, large parquet/JSONL embeddings, or generated assessment PDFs.

Offline scripts under `scripts/` can regenerate processed artefacts when you have local source data.

---

## Tests

### Backend

```bash
cd backend
pytest -q
```

### Frontend

```bash
cd frontend
npm run test:unit
# optional E2E (mock mode):
USE_MOCK_BACKEND=true NEXT_PUBLIC_USE_MOCK_BACKEND=true npm run test:e2e
```

CI runs via `.github/workflows/ci.yml`.

---

## Main API endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/api/health` | Health check |
| `POST` | `/api/submit` | Create submission |
| `GET` | `/api/report/{submission_id}` | Submission + report status/payload |
| `POST` | `/api/reports/generate_pdf` | Download PDF (`{"submission_id": <id>}`) |
| `GET` | `/api/reports/html/{submission_id}` | HTML preview |
| `POST` | `/api/admin/process_submission` | Dev helper to process a submission |

Interactive docs: http://localhost:8000/docs

---

## Further documentation

- `backend/README.md` — backend setup and API detail  
- `frontend/README.md` — frontend mock/real modes and tests  
- `docs/README_RAG.md` — RAG indexing and retrieval  
- `docs/EDA_STEPS_AND_BENCHMARK.md` — portal export cleaning / benchmarks  
- `docs/CALCULATION_PROCESS.md` — calculator overview  
- `docs/AZURE_DOCKER_DEPLOY_CHECKLIST.md` — container deployment checklist  

---

## Licence / contribution

This repository is under active development for the NET ZERO self-assessment pilot. Open an issue or pull request if you want to propose changes.
