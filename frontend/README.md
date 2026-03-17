## NET-ZERO-AI-Self-Assessment Frontend

This `frontend/` app is a Next.js (App Router) TypeScript application that implements:

- **Multi-step questionnaire UI** driven by the Excel spec in `data/raw/Minimum_Input_Questionnaire.xlsx`
- **Submission flow** to `POST /api/questionnaire/submit` with status polling
- **Report viewer** for `GET /api/reports/{reportId}` with **PDF download** via `GET /api/reports/generate_pdf?report_id={reportId}`
- **Mock backend mode** for local development and Playwright tests

### Install

From the repository root:

```bash
cd frontend
npm install
```

### Run (real backend)

Ensure the FastAPI backend is running on `http://localhost:8000`, then:

```bash
cd frontend
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000 npm run dev
```

Open `http://localhost:3000` in your browser.

### Run (mock backend)

Mock mode uses static assets in `public/data/mock/` (`questionnaire.json`, `report_sample.json`, `report_sample.pdf`) instead of calling the FastAPI API.

```bash
cd frontend
USE_MOCK_BACKEND=true NEXT_PUBLIC_USE_MOCK_BACKEND=true npm run dev
```

In this mode:

- Questionnaire submission is short-circuited to a `mock-submission-id`
- Submission status immediately resolves to `done` with `mock-report-id`
- Report viewer loads `public/data/mock/report_sample.json`
- PDF download can be exercised against `public/data/mock/report_sample.pdf`

### Tests

- **Unit tests** (Jest + React Testing Library):

  ```bash
  cd frontend
  npm run test:unit
  ```

  These cover:

  - Questionnaire conditional logic (show-if and clearing hidden values)
  - `PdfDownloadButton` error handling

- **End-to-end tests** (Playwright):

  ```bash
  cd frontend
  USE_MOCK_BACKEND=true NEXT_PUBLIC_USE_MOCK_BACKEND=true npm run dev
  # in another terminal:
  cd frontend
  npm run test:e2e
  ```

  The `tests/e2e/happy-path.spec.ts` scenario:

  - Opens `/`
  - Walks through the questionnaire in mock mode
  - Submits, waits for status, opens the report
  - Verifies the **Download PDF** button is present

### Environment variables

- **`NEXT_PUBLIC_API_BASE_URL`**: Base URL for the FastAPI backend (default `http://localhost:8000`).
- **`USE_MOCK_BACKEND`**: When set to `true`, enables mock-backend behaviour in dev and tests.
- **`NEXT_PUBLIC_USE_MOCK_BACKEND`**: Client-side flag mirroring `USE_MOCK_BACKEND`; must be set to `true` when running in mock mode so the React app uses mock assets instead of real HTTP calls.

