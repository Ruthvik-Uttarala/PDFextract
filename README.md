# PDFextract

PDFextract is a focused PDF-to-Excel processing product with a frozen stack:

- Frontend: Next.js 14.2.25, React 18.3.1, TypeScript 5.6.3, Node 22.11.0
- Backend: Flask 3.1.0, Python 3.11.11
- Database: PostgreSQL 16
- Object storage: MinIO locally, AWS S3 in production
- Queue: Kafka only
- Auth: Firebase only
- LLM: Gemini only
- Output: Excel `.xlsx` only

This repository now implements the full repo-side MVP path through **Phases 2 to 15** for local development and validation. The remaining production work is Phase 16 infrastructure provisioning and secret wiring for the approved cloud stack.

## Current State

Implemented in-repo:

- canonical monorepo structure under `frontend/`, `backend/`, `docs/`, and `scripts/`
- canonical SQLAlchemy models, Alembic migration, repositories, auth upsert flow, and shared status/stage constants
- Flask API surface for health, readiness, identity, uploads, jobs, admin jobs, downloads, and retry
- deterministic storage keys and local object persistence through MinIO
- Kafka submit and retry publication flow plus Lambda-compatible worker handlers and local worker execution
- PDF reading with PyMuPDF and pdfplumber
- Gemini extraction wrapper with deterministic mock mode for local/testing runs
- normalization, validation, extraction result persistence, and Excel generation with openpyxl
- Next.js App Router frontend with Firebase Google sign-in shell, route guards, dashboard, upload, jobs, job detail, admin list, and admin retry UI
- backend unit and integration tests plus frontend integration tests
- Docker Compose infrastructure for PostgreSQL 16, MinIO, and Kafka in KRaft mode
- reproducible PowerShell validation scripts for backend and frontend checks

Still blocked on external production access:

- production Flask hosting target and deployment access
- production PostgreSQL credentials
- AWS S3, Lambda, and Kafka-compatible broker provisioning and credentials
- production Firebase admin credentials
- production Gemini / GCP credentials

## Repository Layout

```text
PDFextract/
├── frontend/           Next.js 14.2.25 App Router application
├── backend/            Flask 3.1.0 API, worker, services, migrations, and tests
├── docs/               Canonical project contracts copied into the repo
├── scripts/            Local infra/bootstrap/check scripts
├── docker-compose.yml  PostgreSQL 16, MinIO, Kafka (KRaft)
├── package.json        Root orchestration scripts
└── vercel.json         Root-level Vercel safeguard for the frontend project
```

## Prerequisites

Required:

- Git
- PowerShell
- Docker Desktop with the daemon running

Recommended for direct local development outside Docker:

- Node 22.11.0 with npm 10.9.0
- Python 3.11.11

Validation in this repo is designed to run through Dockerized Node/Python so host drift does not silently change the results.

## Environment Setup

Frontend:

1. Copy `frontend/.env.example` to `frontend/.env.local`
2. Fill in the public Firebase web config values

Backend:

1. Copy `backend/.env.example` to `backend/.env`
2. Keep secrets backend-only
3. For real Firebase token verification, provide either:
   - `GOOGLE_APPLICATION_CREDENTIALS` pointing at a local service-account JSON file, or
   - `FIREBASE_AUTH_EMULATOR_HOST` for emulator-backed development

Default local infra values used by the validation scripts:

- PostgreSQL: `postgresql+psycopg://pdfextract:pdfextract@localhost:54329/pdfextract`
- MinIO API: `http://localhost:9000`
- MinIO console: `http://localhost:9001`
- Kafka bootstrap servers: `localhost:9092`
- MinIO bucket: `pdfextract-local`
- Gemini mock mode: `true`
- Admin allowlist default: `admin@example.com`
- Prefixes:
  - `receiving/{user_id}/{job_id}/source.pdf`
  - `processed/{user_id}/{job_id}/output.xlsx`

## Local Bootstrap

Start infrastructure:

```powershell
./scripts/start-local-infra.ps1
./scripts/wait-local-infra.ps1
```

Run backend validation:

```powershell
./scripts/run-backend-checks.ps1
```

Run frontend validation:

```powershell
./scripts/run-frontend-checks.ps1
```

Run the full foundation bootstrap:

```powershell
./scripts/bootstrap-local.ps1
```

Stop infrastructure:

```powershell
./scripts/stop-local-infra.ps1
```

## Backend Surface

The backend API surface is now:

- `GET /api/health`
- `GET /api/ready`
- `GET /api/me`
- `POST /api/uploads`
- `GET /api/jobs`
- `GET /api/jobs/{job_id}`
- `GET /api/jobs/{job_id}/download`
- `GET /api/admin/jobs`
- `GET /api/admin/jobs/{job_id}`
- `POST /api/admin/jobs/{job_id}/retry`

The backend CLI kept for local checks is:

```powershell
python -m app.cli check-db
python -m app.cli ensure-storage
python -m app.cli check-storage-layout --user-id smoke-user --job-id smoke-job
python -m app.cli ensure-kafka-topics
python -m app.cli smoke-firebase
python -m app.cli smoke-http
```

## Frontend Surface

The approved routes are implemented:

- `/`
- `/login`
- `/dashboard`
- `/upload`
- `/jobs`
- `/jobs/[jobId]`
- `/admin/jobs`
- `/admin/jobs/[jobId]`

The frontend remains Vercel-safe with `frontend/` as the project root, but it now points to the real backend contract rather than scaffold-only placeholders.

## Vercel Compatibility

This repository keeps the root as orchestration only while leaving a deployable Next.js app under `frontend/`.

Current in-repo Vercel safeguards:

- the Vercel project Root Directory is `frontend`
- the Framework Preset is `Next.js`
- the Node.js version is `22.x`
- root `package.json` remains local orchestration only

Recommended project settings for the connected Vercel project:

- Root Directory: `frontend`
- Framework Preset: `Next.js`
- Node.js version: `22.x`

## Canonical Docs

These files are copied into `docs/` and are treated as binding implementation contracts:

- `docs/PRD_PDFextract.md`
- `docs/APP_FLOW_PDFextract.md`
- `docs/TECH_STACK_PDFextract.md`
- `docs/FRONTEND_GUIDELINES_PDFextract.md`
- `docs/BACKEND_STRUCTURE_PDFextract.md`
- `docs/IMPLEMENTATION_PLAN_PDFextract.md`
