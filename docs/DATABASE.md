## Database: Local Postgres Overview

This project uses a **local PostgreSQL database** running in Docker. It stores
self‑assessment submissions and, via a `businesses` table, a canonical
record for each unique (`business_name`, `postcode`) pair.

- **Database engine**: PostgreSQL 16 (with `pgvector`)  
- **Container name**: `netzero_db`  
- **DB name**: `netzero`  
- **User/password**: `app` / `app`  
- **Port**: `5432` (mapped to `localhost:5432`)  
- **Default connection string (local):**  
  `postgresql://app:app@localhost:5432/netzero`

The backend connects using SQLAlchemy, with connection details loaded from `.env`.

---

## 1. Where the database runs

### 1.1 `docker-compose.yml`

- **File:** `docker-compose.yml`
- **Role:** Defines the **Postgres service** for local development.
- **Key fields:**
  - `image: pgvector/pgvector:pg16` – Postgres 16 with `pgvector` installed.
  - `container_name: netzero_db`
  - `environment`:
    - `POSTGRES_USER=app`
    - `POSTGRES_PASSWORD=app`
    - `POSTGRES_DB=netzero`
  - `ports: "5432:5432"` – exposes Postgres on `localhost:5432`.
  - `volumes: netzero_pgdata:/var/lib/postgresql/data` – persistent DB data.
  - `healthcheck: pg_isready -U app -d netzero` – waits until DB is ready.

**How to start DB locally:**

```bash
docker compose up -d

2. Configuration and connection
2.1 .env.example / .env
Files: .env.example (template), .env (your real config).
Key settings:
# Database (local via docker compose)
DATABASE_URL=postgresql://app:app@localhost:5432/netzero

# App settings
ENVIRONMENT=local
Purpose: Provide the connection string used by the backend and an ENVIRONMENT flag (local, development, etc.).
2.2 backend/app/config.py
File: backend/app/config.py

Class: Settings(BaseSettings)

Key fields:

DATABASE_URL: str = "sqlite:///./test.db" (default) – overridden by .env.
ENVIRONMENT: str = "development".
model_config.env_file = PROJECT_ROOT / ".env" – tells Pydantic to load .env at the repo root.
Exports: settings = get_settings()
All other modules read settings.DATABASE_URL and settings.ENVIRONMENT.

2.3 backend/app/db.py
File: backend/app/db.py
What it does:
Creates the SQLAlchemy engine:

engine = create_engine(settings.DATABASE_URL, future=True)
Creates a session factory:

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    future=True,
)
Declares the base for ORM models:

Base = declarative_base()
Provides a FastAPI dependency get_db() that yields a Session and ensures it is closed after each request:

def get_db() -> Session:
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()
3. How tables are created
3.1 backend/app/main.py
On startup (dev/local only):
if env in ("development", "local"):
    Base.metadata.create_all(bind=engine)
Effect: When you run the backend in local / development, it will auto‑create all tables defined in backend/app/models.py. There is no migrations system yet; table changes are applied by updating the models and re‑creating the schema in dev.
4. ORM models and tables (backend/app/models.py)
This file defines all database tables via SQLAlchemy ORM.

4.1 Business table
class Business(Base):
    __tablename__ = "businesses"
    id = Column(Integer, primary_key=True, index=True)
    business_name = Column(String, nullable=False)
    postcode = Column(String, nullable=False)
    __table_args__ = (
        UniqueConstraint("business_name", "postcode", name="uq_business_name_postcode"),
    )
    submissions = relationship("Submission", back_populates="business")
Table name: businesses
Columns:
id – integer, primary key, indexed. Canonical business ID.
business_name – text (string), required.
postcode – text (string), required.
Constraint:
uq_business_name_postcode – enforces one row per unique (business_name, postcode) pair.
Relationship:
submissions – a list of related Submission rows. One Business can have many Submissions.
Purpose:

Provide a stable business identity per (business_name, postcode).
Allow multiple submissions for the same business/site while reusing the same business_id.
Allow a business to appear multiple times with different postcodes (multiple sites).
4.2 Submission table
class Submission(Base):
    __tablename__ = "submissions"
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=dt.datetime.utcnow)
    business_name = Column(String, nullable=True)
    postcode = Column(String, nullable=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=True, index=True)
    business = relationship("Business", back_populates="submissions")
    raw_answers = Column(JSONB, nullable=False)
    status = Column(String, nullable=False, default="received")
    report_json = Column(JSONB, nullable=True)
Table name: submissions

Columns:

id – integer, primary key, indexed. Unique per submission.
created_at – timezone‑aware timestamp, default now.
business_name – nullable string. Kept for compatibility / reporting.
postcode – nullable string. Kept for compatibility / reporting.
business_id – nullable integer foreign key to businesses.id; indexed.
raw_answers – Postgres JSONB, required. Full questionnaire as submitted.
status – string, required, default "received" (e.g. "ready" after processing).
report_json – Postgres JSONB, optional; stores computed baseline/measures.
Relationships:

business – links each submission to a single Business row (or None if name/postcode were missing at submit time).
Purpose:

Store each form submission from the portal.
Link submissions back to a canonical business via business_id.
Keep both the raw input (raw_answers) and the processed report (report_json) alongside status and timestamps.
5. How data flows into the database
5.1 Request and validation: backend/app/schemas.py
SubmissionCreate

Fields:
business_name: Optional[str]
postcode: Optional[str]
answers: Dict[str, Any] (the full questionnaire).
Used as the input model for /api/submit.
SubmissionOut

Fields:
id
business_name
postcode
raw_answers
status
created_at
report_json
Used as the output model when returning a submission/report.
ReportOut

Fields: id, report_json.
Used when you want just the report.
5.2 API routes: backend/app/routes/submissions.py
POST /api/submit

Accepts SubmissionCreate.
Gets a DB session via Depends(get_db).
Calls crud.create_submission(db, submission_in) to insert into DB.
Immediately triggers processing via submission_service.process_submission.
Returns the refreshed Submission row (now possibly with report_json).
GET /api/report/{submission_id}

Loads a submission by id using crud.get_submission.
Returns it as SubmissionOut or 404 if not found.
5.3 CRUD operations: backend/app/crud.py
Key functions:

_get_or_create_business(db, business_name, postcode)

If either value is missing, returns None.
Otherwise:
Looks for an existing Business row where business_name == business_name and postcode == postcode.
If found, returns it.
If not, creates a new Business row, commits, and returns it.
create_submission(db, submission_in)

Calls _get_or_create_business to get a Business row (or None).
Inserts a new Submission with:
business_name, postcode copied from request.
business_id set to business.id if a Business was found/created.
raw_answers from submission_in.answers.
status="received".
Commits and refreshes, then returns the Submission.
get_submission(db, submission_id)

Simple lookup by primary key.
update_report(db, submission_id, report_json, status="ready")

Loads the Submission by ID, sets report_json and status, commits, refreshes.
5.4 Submission processing: backend/app/services/submission_service.py
Function: process_submission(db, submission_id)
Steps:
Load the submission via crud.get_submission.
Extract answers from submission.raw_answers.
Call app‑level calculators (backend/app/calculators.py) to compute:
baseline = calculators.compute_baseline(answers)
measures = calculators.compute_measure_summaries(answers)
Build report = {"baseline": baseline, "measures": measures}.
Call crud.update_report(db, submission_id, report_json=report, status="ready").
Return the report.
The database layer itself does not run complex calculation logic; it just stores inputs (raw_answers) and outputs (report_json).

6. DB helper utilities
6.1 backend/app/utils.py
Useful with ORM instances:

orm_to_dict(instance) – converts a SQLAlchemy ORM object into a plain dict using its mapped columns.
commit_and_refresh(db, instance) – helper to add, commit, and refresh an ORM instance.
7. Summary of DB‑related files
Root level

docker-compose.yml – runs local Postgres (netzero_db).
.env.example / .env – define DATABASE_URL and ENVIRONMENT.
Backend app

backend/app/config.py – loads settings (including DATABASE_URL).
backend/app/db.py – SQLAlchemy engine, session, and Base, plus get_db.
backend/app/models.py – ORM models (Business, Submission) defining tables and columns.
backend/app/schemas.py – Pydantic models that mirror DB fields for input/output.
backend/app/crud.py – DB operations, business lookup/creation, submission CRUD.
backend/app/services/submission_service.py – orchestrates DB reads/writes + calculations.
backend/app/routes/submissions.py – HTTP endpoints that use DB sessions and CRUD.
backend/app/main.py – application startup, including dev Base.metadata.create_all.
backend/app/utils.py – small ORM helper utilities.