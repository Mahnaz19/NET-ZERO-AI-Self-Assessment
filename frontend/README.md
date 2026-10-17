## Frontend — NET-ZERO Self-Assessment

Next.js (App Router) TypeScript app for:

- multi-step energy questionnaire
- submission to the FastAPI backend with status polling
- report viewing and PDF download

### Install

```bash
cd frontend
npm ci
```

### Run against the real backend

Ensure the API is available on `http://localhost:8000`, then:

```bash
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000 npm run dev
```

Open http://localhost:3000.

### Run in mock mode (no backend)

Uses static fixtures under `public/data/mock/`:

```bash
USE_MOCK_BACKEND=true NEXT_PUBLIC_USE_MOCK_BACKEND=true npm run dev
```

### Tests

```bash
npm run test:unit
USE_MOCK_BACKEND=true NEXT_PUBLIC_USE_MOCK_BACKEND=true npm run test:e2e
```

### Docker

From the repository root (preferred):

```bash
docker compose up -d --build frontend
```

Or build this directory alone:

```bash
docker build -t netzero-frontend .
docker run -p 3000:3000 netzero-frontend
```

### Environment variables

- `NEXT_PUBLIC_API_BASE_URL` — FastAPI base URL (default `http://localhost:8000`)
- `USE_MOCK_BACKEND` / `NEXT_PUBLIC_USE_MOCK_BACKEND` — enable mock fixtures when `true`
