# NET-ZERO-AI-Self-Assessment
This Repository is for NET ZERO self Assessment project to reduce energy consumption.

## Frontend (Next.js)

The production-ready questionnaire and report UI lives in the `frontend/` directory.

### Run locally (mock backend)

```bash
cd frontend
npm install
USE_MOCK_BACKEND=true NEXT_PUBLIC_USE_MOCK_BACKEND=true npm run dev
```

### Run locally (real backend)

Start the FastAPI backend on `http://localhost:8000`, then:

```bash
cd frontend
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000 npm run dev
```

### Tests

```bash
cd frontend
npm run test:unit
npm run test:e2e
```

### Docker

Build and run the frontend container:

```bash
docker build -t netzero-frontend frontend/
docker run -p 3000:3000 netzero-frontend
```

Then open `http://localhost:3000`.

### Environment variables

- `NEXT_PUBLIC_API_BASE_URL`: Base URL for the FastAPI backend (default `http://localhost:8000`).
- `USE_MOCK_BACKEND`: When `true`, enables mock backend behaviour in dev and tests.
- `NEXT_PUBLIC_USE_MOCK_BACKEND`: Client-side flag mirroring `USE_MOCK_BACKEND` so the React app uses mock assets instead of real HTTP calls.
