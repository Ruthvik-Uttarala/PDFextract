

IMPLEMENTATION_PLAN.md
PDFextract — Canonical Implementation Plan
## 1. Document Purpose
This document defines the exact implementation order for PDFextract. It exists to answer
one question clearly:
In what sequence should the system be built so the final product matches the
approved architecture without AI drift, backend confusion, or frontend guesswork?
This is not a generic roadmap. It is not a “sprint ideas” note. It is the operational build order
for the actual product.
This document exists because AI coding tools fail when they are asked to “build the app”
without a locked sequence. They skip foundations, mix infrastructure and UI prematurely,
invent models before schema is defined, and produce impressive-looking but structurally
wrong systems.
This plan prevents that by defining:
- the implementation phases
- the dependency order
- the exact sequence of backend and frontend work
- what must be complete before the next phase starts
- acceptance criteria for each phase
- what not to build early
- how to reach a true MVP instead of a half-finished demo shell
This file must be read together with:
- PRD.md
- APP_FLOW.md
- TECH_STACK.md
- FRONTEND_GUIDELINES.md
- BACKEND_STRUCTURE.md

If a build plan or generated code conflicts with this document, this document wins.

- Non-Negotiable Build Rules
Before any coding starts, the following rules are locked.
2.1 Use Only the Approved Stack
No swapping technologies mid-build. No “helpful” framework substitution.
Allowed only:
## • React + Next.js
## • Python + Flask
## • Gemini
- PostgreSQL
- MinIO + AWS S3
## • Kafka
- AWS Lambda
## • Firebase
- Excel output
2.2 Build the System in Dependency Order
Do not start with polished frontend pages before auth, database, job model, and upload
flow exist.
2.3 Build End-to-End Vertically, But in Controlled Layers
Each phase should contribute to the final upload → process → download loop, but only after
the dependent infrastructure is in place.
## 2.4 No Feature Drift
Do not build:
- chat UI

- analytics dashboards
- settings pages
- schema builder
- billing
- live editing of extracted fields
- multi-tenant admin suite
- direct ERP integration
2.5 Every Phase Must End With a Real Test
A phase is not done because files exist. It is done when the specific flow for that phase
works.

## 3. Delivery Strategy
The correct implementation strategy for PDFextract is:
- establish repository and environment discipline
- establish backend foundations
- establish upload and job persistence
- establish async pipeline wiring
- establish extraction and validation
- establish Excel generation and artifact storage
- establish frontend flows against real APIs
- establish admin retry and operational visibility
- harden, test, and deploy
This order matters.
If the team starts with frontend screens first, the UI will fake states that the backend does
not support. If the team starts with Gemini first, it will lack job structure and operational
traceability. If the team starts with Lambda first, there will be no stable API contract or DB
state model.
The plan below fixes that.


- Definition of MVP Completion
The MVP is complete only when all of the following are true:
- user can authenticate
- user can upload a PDF
- PDF is stored in receiving/
- job is created in PostgreSQL
- Kafka receives the work event
- Lambda processes the job
- Gemini returns structured output
- extraction output is validated
- Excel file is generated
- Excel file is stored in processed/
- job becomes completed
- frontend shows job state correctly
- user can download the Excel output
- admin can inspect and retry failed jobs
Anything less than this is partial infrastructure, not a complete product.

- Phase 0 — Project Initialization and Repo Discipline
## Goal
Create the implementation skeleton and guardrails before feature code begins.
## Step 0.1 — Create Monorepo Structure
Create the root project layout with separated frontend and backend areas. The structure
must reflect the system boundaries already defined in BACKEND_STRUCTURE.md.
## Deliverables:
- /frontend for Next.js app
- /backend for Flask API and worker code

- /docs for the six canonical documents
- root README
- environment template files
## Step 0.2 — Lock Runtime Versions
Freeze the baseline runtime versions from TECH_STACK.md.
## Deliverables:
- Node version file or equivalent
- Python version file or equivalent
- backend requirements file
- frontend package definitions
- version notes in README
## Step 0.3 — Add Code Quality Baselines
Set formatting, linting, and project conventions early.
## Deliverables:
- TypeScript strict mode
- Python formatting and lint config
- import/order conventions
- environment variable naming standards
Step 0.4 — Add Canonical Docs to Repo
The six docs must live inside the project from day one so Codex always has them nearby.
## Acceptance Criteria:
- repo structure exists
- versions are pinned
- docs are committed
- no business logic has been written in the wrong location yet


## 6. Phase 1 — Local Infrastructure Foundation
## Goal
Make the core local environment real before application features begin.
Step 1.1 — Stand Up PostgreSQL Locally
Provision local PostgreSQL and verify connectivity from backend code.
## Deliverables:
- local DB instance
- connection string environment variable
- successful DB connection test
Step 1.2 — Stand Up MinIO Locally
Create the S3-compatible local object storage layer.
## Deliverables:
- local MinIO instance
- bucket creation
- receiving/ and processed/ prefixes standardized
## Step 1.3 — Stand Up Kafka Locally
Provision Kafka locally for event publishing and consumption.
## Deliverables:
- Kafka broker running
- required topics created
- test publish/consume working
## Step 1.4 — Configure Firebase Auth Integration
Set up Firebase project/client/backend verification path for development.

## Deliverables:
- frontend Firebase client configuration
- backend Firebase admin verification configuration
- token verification test
## Step 1.5 — Establish Environment Variable Strategy
Separate environment configuration by local, staging, and production concern.
## Deliverables:
- .env.example files
- backend env loading
- frontend env loading
- secrets excluded from repo
## Acceptance Criteria:
- backend can reach PostgreSQL, MinIO, Kafka
- Firebase tokens can be verified
- environment loading works cleanly
- no production secrets are embedded in code

- Phase 2 — Backend Core Domain and Database
## Schema
## Goal
Create the metadata backbone that every later phase depends on.
Step 2.1 — Implement SQLAlchemy Models
Create the canonical tables:
- users
- jobs

- file_records
- processing_attempts
- extraction_results
- output_artifacts
- admin_actions
## Step 2.2 — Create Alembic Migrations
Schema should be migration-driven, not manually applied ad hoc.
Step 2.3 — Build DB Session and Repository Utilities
Codify clean DB access patterns instead of raw SQL scattering.
Step 2.4 — Implement User Upsert on Authenticated Request
When an authenticated Firebase user hits the backend, ensure a local user record is
created or updated.
Step 2.5 — Implement Job Status Enums and Shared Constants
## Lock:
- queued
- processing
- completed
- failed
and internal stage constants.
## Acceptance Criteria:
- migrations run successfully
- all tables exist
- user creation/upsert works
- jobs can be created and queried in DB
- status constants are centralized


- Phase 3 — Flask API Foundation
## Goal
Create the real API contract before complex worker logic begins.
Step 3.1 — Build Flask App Entry and Blueprint Structure
Implement modular route organization:
- health
- me/auth context
- uploads
- jobs
- admin
## Step 3.2 — Implement Auth Middleware / Decorators
Protect endpoints using Firebase token verification.
Step 3.3 — Implement GET /api/health and GET /api/ready
Health confirms app is alive. Readiness checks core dependency connectivity.
Step 3.4 — Implement GET /api/me
Return authenticated user identity and role.
## Step 3.5 — Add Error Handling Standard
Create canonical JSON error shape so the frontend gets consistent responses.
## Acceptance Criteria:
- protected routes reject invalid tokens
- valid tokens return user context
- health and readiness endpoints work
- Flask API structure is stable enough for the frontend to target


- Phase 4 — Upload Flow and Source File Persistence
## Goal
Make the first real vertical slice: upload a PDF, persist metadata, persist source file, create
a job.
## Step 4.1 — Implement Upload Validation
Accept only PDF uploads for MVP.
Validation must include:
- file presence
- file type
- non-empty content
- basic filename handling
Step 4.2 — Implement POST /api/uploads
This endpoint must:
- verify auth
- validate file
- create job in PostgreSQL
- store source file in MinIO/S3 under receiving/
- create file_record
- publish async event to Kafka
- return job summary
## Step 4.3 — Standardize Storage Key Builder
Create deterministic storage keys based on user ID and job ID.
## Step 4.4 — Implement Upload Failure Recovery Rules
Do not return false success if Kafka publish fails or storage fails.
## Acceptance Criteria:

- authenticated user can upload a PDF
- job row appears in database
- source file exists in receiving/
- API returns job payload
- frontend or API test can immediately fetch job detail after upload

- Phase 5 — Job Query APIs
## Goal
Make the backend readable before making the worker smarter.
Step 5.1 — Implement GET /api/jobs
Return current user’s jobs in newest-first order.
Step 5.2 — Implement GET /api/jobs/{job_id}
Return one job detail with:
- file name
- status
- timestamps
- document type if known
- output availability
Step 5.3 — Implement Admin Job List and Detail APIs
## Add:
- GET /api/admin/jobs
- GET /api/admin/jobs/{job_id}
## Step 5.4 — Add Access Control Rules
User sees only own jobs. Admin sees all jobs.
## Acceptance Criteria:

- user can query own jobs
- admin can query all jobs
- unauthorized cross-user access is blocked
- upload path now connects to readable history path

- Phase 6 — Kafka Event Flow and Worker Skeleton
## Goal
Make asynchronous job execution real, even before extraction logic is fully finished.
## Step 6.1 — Implement Kafka Producer Service
The upload flow should publish to:
- document.jobs.submit
## Step 6.2 — Define Event Payload Schema
Payload should include:
- job_id
- attempt_type
- requested_at
- correlation_id
Step 6.3 — Create Lambda-Compatible Worker Entry
Build the worker entrypoint that accepts a job event and begins processing.
## Step 6.4 — Add Processing Attempt Record Creation
When a worker begins a job, insert processing_attempts row and update job to
processing.
Step 6.5 — Implement No-Op Worker Path First
Before Gemini is added, make the worker capable of:

- loading the job
- loading the source file
- updating state
- exiting cleanly or with controlled failure
## Acceptance Criteria:
- upload triggers Kafka publish
- worker receives job event
- job transitions to processing
- attempt row is created
- controlled failure path updates DB correctly

- Phase 7 — PDF Reading and Extraction Integration
## Goal
Replace placeholder processing with real document extraction.
Step 7.1 — Build PDF Reader Service
Use approved PDF libraries to:
- read the PDF
- extract raw text
- capture table-oriented context where useful
- normalize page content for extraction input
## Step 7.2 — Build Gemini Extraction Service Wrapper
Create one service module that owns Gemini calls. Do not scatter LLM requests across
handlers.
## Responsibilities:
- prompt assembly
- model invocation
- structured parsing

- error handling
## Step 7.3 — Implement Initial Supported Schemas
Start with:
- invoice extraction
- secondary report/research extraction path
## Step 7.4 — Normalize Extraction Output
Map Gemini response into a predictable JSON structure for downstream validation and
Excel generation.
## Step 7.5 — Persist Extraction Results
Write extraction_results row for each attempt.
## Acceptance Criteria:
- worker reads source PDF
- Gemini is called successfully
- normalized structured JSON is produced
- extraction result is stored in PostgreSQL

## 13. Phase 8 — Validation Layer
## Goal
Ensure output is fit for export before generating user artifacts.
## Step 8.1 — Build Validation Service
Validation checks must cover:
- required fields
- date structure
- amount structure

- line item/table structure where relevant
- missing critical data
## Step 8.2 — Define Validation Outcome Rules
If validation fails:
- mark extraction result accordingly
- mark job failed if output is not usable
- store validation errors
Step 8.3 — Separate Extraction Failure from Validation Failure
Do not collapse all failures into one vague state internally.
## Acceptance Criteria:
- invalid structured output is caught
- validation errors are stored
- jobs do not generate fake Excel files from broken data

- Phase 9 — Excel Generation and Processed Artifact
## Storage
## Goal
Produce the actual user deliverable.
## Step 9.1 — Build Excel Service
Generate .xlsx output from normalized structured JSON.
## Step 9.2 — Define Workbook Structure
For invoice-like outputs, include:
- summary sheet or top-level metadata section

- structured line-item table
For research/report outputs:
- metadata section
- structured extracted sections as needed
Step 9.3 — Store Excel in processed/
Write the artifact to MinIO/S3 under the deterministic processed key.
## Step 9.4 — Persist Output Artifact Metadata
## Create:
- file_record for processed file
- output_artifact row
- mark current artifact as active
Step 9.5 — Complete the Job
Update job status to completed and set completion timestamp.
## Acceptance Criteria:
- completed worker run produces real Excel file
- file exists in processed/
- DB reflects artifact
- job transitions to completed

## 15. Phase 10 — Download Flow
## Goal
Expose the completed artifact safely to the frontend.

Step 10.1 — Implement GET /api/jobs/{job_id}/download
This endpoint must:
- verify auth
- verify user owns job or is admin
- verify job is completed
- verify output artifact exists
- return authorized download response
## Step 10.2 — Handle Missing Artifact Edge Cases
If DB says completed but artifact is missing, return controlled failure and flag operational
inconsistency.
## Acceptance Criteria:
- user can download completed Excel output
- user cannot download another user’s output
- incomplete jobs do not show valid download response

- Phase 11 — Frontend App Shell and Auth Flow
## Goal
Now that the backend is real, implement the user-facing product shell.
## Step 11.1 — Create Next.js App Shell
## Implement:
- login route
- authenticated layout
- navigation from APP_FLOW.md
Step 11.2 — Integrate Firebase Sign-In
Frontend obtains auth token and uses it on protected API requests.

## Step 11.3 — Implement Route Guards
Authenticated routes must require valid session.
Step 11.4 — Build Shared API Client
Centralize frontend API calls to Flask backend.
## Acceptance Criteria:
- user can sign in
- authenticated layout works
- frontend can call protected backend endpoints successfully

- Phase 12 — Frontend Upload, Jobs, and Detail Flow
## Goal
Connect the frontend to the real backend workflow.
## Step 12.1 — Build Dashboard
## Show:
- upload CTA
- recent jobs
- core summary counts
## Step 12.2 — Build Upload Page
Connect actual file input to POST /api/uploads.
## Step 12.3 — Build Jobs List Page
Render user job history from GET /api/jobs.

## Step 12.4 — Build Job Detail Page
## Render:
- file name
- status
- timestamps
- download button when complete
- failure message when failed
## Step 12.5 — Add Status Refresh Strategy
Use controlled polling or refresh so async state changes become visible.
## Acceptance Criteria:
- user can sign in, upload, see job created, observe status, and download output
- frontend does not fake any state not supported by backend

- Phase 13 — Admin Retry and Operations Flow
## Goal
Make failure operationally manageable.
Step 13.1 — Build Admin Jobs UI
Implement admin-only pages from APP_FLOW.md.
## Step 13.2 — Implement Retry Endpoint
POST /api/admin/jobs/{job_id}/retry
Step 13.3 — Publish Retry Events to Kafka
Retry must create a new processing attempt and republish work.

Step 13.4 — Display Attempt History in Admin View
Let internal operators see what happened without digging through logs first.
## Acceptance Criteria:
- admin can identify failed jobs
- admin can retry failed jobs
- retry creates new attempt without destroying history

- Phase 14 — Hardening and Operational Safety
## Goal
Make the MVP stable enough for repeated demo use and early real usage.
## Step 14.1 — Add Structured Logging
Log with:
- job_id
- attempt_id
- user_id
- failure_code
- correlation_id
## Step 14.2 — Add Idempotency Protections
Ensure duplicate events do not create inconsistent outputs or broken state.
## Step 14.3 — Add Graceful Failure Codes
Standardize internal failure categories.
Step 14.4 — Add Readiness Checks for Dependencies
Backend should expose meaningful readiness.

Step 14.5 — Add Storage and Artifact Consistency Checks
Protect against cases where DB and object store diverge.
## Acceptance Criteria:
- repeated tests do not create corrupt state
- failure handling is structured
- operational visibility is good enough for internal troubleshooting

## 20. Phase 15 — Test Plan Execution
## Goal
Prove the system end to end.
## Step 15.1 — Backend Unit Tests
## Cover:
- auth verification helpers
- storage key builders
- validation logic
- Excel generation logic
- job state transitions
## Step 15.2 — Integration Tests
## Cover:
- upload to DB + storage
- Kafka event production
- worker processing flow
- artifact creation
- download flow

## Step 15.3 — Frontend Integration Tests
## Cover:
- sign in
- upload flow
- jobs list rendering
- completed job download state
Step 15.4 — End-to-End Smoke Tests
Run a true user-path smoke test:
- sign in
- upload valid invoice PDF
- confirm job queued
- confirm job processing
- confirm completed state
- download Excel
- open Excel and verify structure
## Step 15.5 — Failure Tests
## Run:
- invalid PDF upload
- forced Gemini failure
- validation failure
- missing artifact
- retry flow
## Acceptance Criteria:
- all critical user paths pass
- failure paths are understandable
- admin recovery path works


## 21. Phase 16 — Deployment Preparation
## Goal
Move from local build to deployable MVP.
## Step 16.1 — Prepare Production Environment Variables
Separate frontend, backend, AWS, Firebase, Kafka, and Gemini config cleanly.
Step 16.2 — Provision Production PostgreSQL
Apply migrations in production-like environment.
Step 16.3 — Provision S3 Buckets and Prefix Rules
Ensure correct bucket policy and object path discipline.
Step 16.4 — Provision Kafka in Production
Create required topics and connectivity.
## Step 16.5 — Provision Lambda Execution
Deploy worker package and verify permission to reach storage, DB, Kafka, and Gemini.
Step 16.6 — Deploy Flask API
Deploy API in its approved runtime environment.
## Step 16.7 — Deploy Next.js Frontend
Deploy frontend and point it to the backend API.
## Acceptance Criteria:
- production-like stack is wired
- frontend can talk to backend
- worker can process real uploaded jobs

- download path works in deployed environment

## 22. Implementation Order Summary
Codex must implement in this exact order:
## Foundation
- repo structure
- local infra
- database schema
- Flask API skeleton
Core workflow
- upload endpoint
- job retrieval endpoints
- Kafka producer + worker skeleton
- PDF reader + Gemini extraction
- validation
- Excel generation
- download endpoint
User-facing system
- frontend auth shell
- frontend upload/jobs/detail flow
Operations and quality
- admin retry
- hardening
- test execution
- deployment preparation
This is the official build sequence.


## 23. What Must Not Happen During Implementation
To keep the build sane, the following are explicitly forbidden:
- building dashboard charts before upload works
- building admin pages before job model exists
- integrating Gemini before source file flow works
- generating Excel before validation exists
- building fake frontend states disconnected from backend
- skipping Kafka and calling workers ad hoc from upload request
- storing binary files in PostgreSQL
- exposing direct client-side privileged storage logic
- adding random pages outside APP_FLOW.md
- swapping Flask for another framework because it “feels easier”
If any of these happen, the build has drifted from the canonical plan.

## 24. Final Execution Standard
The correct implementation mindset for PDFextract is:
Build the real system, in the real order, with the real dependencies, and refuse to
decorate incomplete infrastructure with fake UI polish.
The product is complete only when the full chain works:
- authenticated upload
- source storage
- job creation
- async processing
- Gemini extraction
- validation
- Excel generation
- processed storage
- status visibility
- download

- retry for failures
That is what this implementation plan protects.
