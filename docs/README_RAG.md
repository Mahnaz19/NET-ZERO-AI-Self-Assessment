# RAG Ingestion & Retrieval

This document describes how to run the RAG (retrieval-augmented generation) pipeline: ingesting report chunks into a vector store and querying them for LLM use.

## Environment variables

**No production or private cloud keys are used in CI/tooling.** Configure credentials via environment variables:

| Variable | Purpose |
|----------|--------|
| `AZURE_OPENAI_ENDPOINT` | Azure OpenAI endpoint (e.g. `https://xxx.openai.azure.com`) |
| `AZURE_OPENAI_API_KEY` | Azure OpenAI API key |
| `AZURE_OPENAI_DEPLOYMENT_NAME` or `AZURE_OPENAI_DEPLOYMENT` | Embeddings deployment name |
| `OPENAI_API_KEY` | OpenAI API key (optional; used if Azure not set) |
| `AZURE_COG_SEARCH_SERVICE` | Azure Cognitive Search service name (for `--provider azure`) |
| `AZURE_COG_SEARCH_API_KEY` | Azure Cognitive Search API key |
| `DATABASE_URL` | Postgres connection string for pgvector (see below). Example: `postgresql://app:app@localhost:5432/netzero` |

**Local fallback:** If none of the Azure/OpenAI embedding variables are set, the pipeline uses **sentence-transformers** (e.g. `all-MiniLM-L6-v2`) so you can run locally and offline.

## How to run RAG ingest with pgvector

1. **Start Postgres (with pgvector)**  
   From the repository root, start the DB:
   ```bash
   docker compose up -d
   ```
   The repo’s `docker-compose.yml` starts Postgres 16 with the **pgvector** extension. The ingest script runs `CREATE EXTENSION IF NOT EXISTS vector` on first use.

2. **Set `DATABASE_URL`**  
   In the project root `.env` (or in your shell), set the Postgres URL so the backend and ingest script can connect. Example:
   ```bash
   DATABASE_URL=postgresql://app:app@localhost:5432/netzero
   ```
   Adjust `user`, `password`, `host`, `port`, and `dbname` to match your `docker-compose.yml` or local Postgres.

3. **Run ingest**  
   From the **repository root**:
   ```bash
   python scripts/ingest_rag.py --input data/processed/reports_chunks.jsonl --provider pgvector
   ```
   If the input JSONL exists, this creates/updates the `beas_reports` table and writes `data/processed/rag_embeddings.parquet`. If Postgres is unreachable, the script still writes the parquet file and logs a warning.

## Running ingestion (reference)

From the **repository root**:

```bash
python scripts/ingest_rag.py --input data/processed/reports_chunks.jsonl --provider pgvector
```

- **`--input`** – Path to JSONL of report chunks (default: `data/processed/reports_chunks.jsonl`).
- **`--index-name`** – Vector index name (default: `beas_reports`).
- **`--provider`** – `pgvector` (default) or `azure`.
- **`--chunk-size`** – Optional max characters per chunk; re-chunks if exceeded.
- **`--parquet`** – Output path for local parquet cache (default: `data/processed/rag_embeddings.parquet`).

Ingestion is **idempotent**: records are identified by a deterministic id (hash of filename + section + chunk_index), so re-running does not duplicate vectors.

After a successful run you should see:

- Vectors in the chosen store (Postgres/pgvector table or Azure index).
- A local file `data/processed/rag_embeddings.parquet` with columns: `id`, `filename`, `section`, `chunk_index`, `sector`, `text`, `embedding`, `upsert_ts`.

## Switching to Azure in production

1. Set the Azure OpenAI env vars above for embeddings.
2. Set `AZURE_COG_SEARCH_SERVICE` and `AZURE_COG_SEARCH_API_KEY` for the vector index.
3. Run ingestion with `--provider azure`:

   ```bash
   python scripts/ingest_rag.py --input data/processed/reports_chunks.jsonl --provider azure --index-name beas_reports
   ```

4. Use the same `--index-name` when calling the retriever so queries hit the same index.

## Inspecting vectors

- **pgvector:** Query the table (default name `beas_reports`) in your Postgres DB, e.g. in DBeaver or `psql`. Columns: `id`, `filename`, `report_id`, `section`, `chunk_index`, `text`, `sector`, `created_at`, `embedding`.
- **Parquet:** Open `data/processed/rag_embeddings.parquet` in pandas or Arrow to inspect `id`, `filename`, `section`, `chunk_index`, `sector`, `text`, `embedding` (list), `upsert_ts`.

## Retrieval (programmatic)

From Python (with `backend` on `PYTHONPATH` or from the `backend` directory):

```python
from rag.retriever import retrieve

hits = retrieve("energy saving recommendations", top_k=5, provider="pgvector")
# Each hit: {"id", "text", "metadata", "score"}
```

Use `provider="azure"` and the same `index_name` if you ingested into Azure.

## Tests

- **Unit (embeddings fallback):** `cd backend && pytest tests/test_rag_embeddings.py -v`  
  Uses sentence-transformers when Azure/OpenAI env vars are unset. Skip heavy runs with `SKIP_HEAVY_RAG_TESTS=1`.
- **Retriever (mocked):** `cd backend && pytest tests/test_retriever.py -v`
- **Ingest smoke:** `pytest scripts/tests/test_ingest_rag.py -v` from repo root. One test mocks the adapter; another runs real ingestion if `data/processed/reports_chunks.jsonl` exists (skipped otherwise).

CI runs RAG unit tests; tests that require credentials are skipped when env is not configured.
