# Azure Docker Deployment Checklist

This project is now containerized for all runtime services:

- `frontend` (Next.js)
- `backend` (FastAPI)
- `worker` (RQ)
- `db` (PostgreSQL)
- `redis`

Use this checklist before deploying.

## 1) Build and run locally with Docker

```bash
docker compose up -d --build
```

Verify:

- Frontend: `http://localhost:3000`
- Backend health: `http://localhost:8000/`

## 2) Production-like local validation

Create `.env.production` from `.env.production.example`, then:

```bash
docker compose --env-file .env.production -f docker-compose.prod.yml up -d --build
```

## 3) Recommended Azure architecture

- Azure Container Apps (or App Service for Containers) for:
  - frontend
  - backend
  - worker
- Azure Database for PostgreSQL (managed) instead of containerized DB
- Azure Cache for Redis (managed) instead of containerized Redis
- Azure Container Registry (ACR) for image storage

## 4) Required environment variables

Backend/worker:

- `DATABASE_URL`
- `REDIS_URL`
- `ENVIRONMENT=production`
- `RAG_PROVIDER`
- `AZURE_OPENAI_ENDPOINT` (if used)
- `AZURE_OPENAI_API_KEY` (if used)
- `AZURE_OPENAI_DEPLOYMENT` (if used)

Frontend:

- `NEXT_PUBLIC_API_BASE_URL` (public URL of deployed backend API)
- `NEXT_PUBLIC_USE_MOCK_BACKEND=false`
- `USE_MOCK_BACKEND=false`

## 5) Production hardening notes

- Keep secrets in Azure Key Vault or service-level secret settings.
- Do not expose DB/Redis publicly when using managed services.
- Ensure backend CORS includes your deployed frontend domain.
- Ensure worker runs as a separate service/replica.
