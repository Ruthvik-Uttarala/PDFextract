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

This repository currently implements **Phase 0** and the **Phase 1 foundation scaffold** only. It does **not** claim the upload, job-processing, extraction, or Excel-generation product flow is complete yet.

## Current State

Implemented in-repo:

- canonical monorepo skeleton under `frontend/`, `backend/`, `docs/`, and `scripts/`
- the six canonical project documents copied into `docs/`
- pinned runtime version files for Node and Python
- a Vercel-safe Next.js frontend scaffold with strict TypeScript and a real Firebase client bootstrap path
- a Flask backend scaffold with structured config, readiness/auth endpoints, and real PostgreSQL/MinIO/Kafka/Firebase integration code paths
- Docker Compose infrastructure for PostgreSQL 16, MinIO, and Kafka in KRaft mode
- deterministic PowerShell scripts to bootstrap infra and run validation

Intentionally not implemented yet:

- upload API
- jobs/history/detail APIs
- admin retry APIs
- Lambda job handlers
- Gemini extraction pipeline
- validation pipeline
- Excel generation
- production auth UX

## Repository Layout

```text
PDFextract/
├── frontend/           Next.js 14.2.25 App Router scaffold
├── backend/            Flask 3.1.0 app, dependency clients, and smoke CLI
├── docs/               Canonical project contracts copied into the repo
├── scripts/            Deterministic local bootstrap and validation scripts
├── docker-compose.yml  PostgreSQL 16, MinIO, Kafka (KRaft)
├── package.json        Root orchestration scripts for the frontend
└── vercel.json         Root-level Vercel-safe install/build commands
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

- PostgreSQL: `postgresql://pdfextract:pdfextract@localhost:54329/pdfextract`
- MinIO API: `http://localhost:9000`
- MinIO console: `http://localhost:9001`
- Kafka bootstrap servers: `localhost:9092`
- MinIO bucket: `pdfextract-local`
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

## Backend Surface in This Phase

Only the minimal Phase 0/1 smoke surface exists:

- `GET /api/health`
- `GET /api/ready`
- `GET /api/me`

The backend CLI used by validation scripts is:

```powershell
python -m app.cli check-db
python -m app.cli ensure-storage
python -m app.cli check-storage-layout --user-id smoke-user --job-id smoke-job
python -m app.cli ensure-kafka-topics
python -m app.cli smoke-firebase
python -m app.cli smoke-http
```

## Frontend Surface in This Phase

The frontend is intentionally minimal:

- `/` redirects to `/login`
- `/login` is a truthful foundation screen, not a marketing page
- Firebase public config loading and browser-side initialization path are real
- no fake upload/jobs/product-complete UI is exposed

## Vercel Compatibility

This repository keeps the root as orchestration only while leaving a deployable Next.js app under `frontend/`.

Current in-repo Vercel safeguards:

- root `vercel.json` points install/build commands at `frontend/`
- root `package.json` exposes orchestration scripts only
- the actual app stays isolated in `frontend/`

Recommended project settings for the connected Vercel project:

- Root Directory: `frontend`
- Framework Preset: `Next.js`
- Node.js version: `22.x`

If the dashboard settings are not yet updated, the root-level Vercel config is the repo-side fallback to keep deployments truthful during the monorepo transition.

## Canonical Docs

These files are copied into `docs/` and are treated as binding implementation contracts:

- `docs/PRD_PDFextract.md`
- `docs/APP_FLOW_PDFextract.md`
- `docs/TECH_STACK_PDFextract.md`
- `docs/FRONTEND_GUIDELINES_PDFextract.md`
- `docs/BACKEND_STRUCTURE_PDFextract.md`
- `docs/IMPLEMENTATION_PLAN_PDFextract.md`
