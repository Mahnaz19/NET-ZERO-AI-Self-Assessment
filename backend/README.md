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

To run the minimal test suite (health endpoint check):

```bash
cd backend
pytest app/tests
```

### Notes and TODOs

- This backend currently includes **dummy, deterministic** calculator functions in `app/calculators.py`.
  These are **not** production formulas and are placeholders only.
- TODO: Replace calculator stubs with real assessor logic based on the Excel tools in `/docs`.
- TODO: Introduce background processing for report generation instead of synchronous processing.
- TODO: Add RAG ingestion and LLM orchestration using Azure OpenAI configuration from environment variables.

