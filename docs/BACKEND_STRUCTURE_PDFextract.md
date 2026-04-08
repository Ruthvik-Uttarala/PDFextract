

BACKEND_STRUCTURE.md
PDFextract — Canonical Backend Structure
## 1. Document Purpose
This document defines the backend architecture for PDFextract in enough detail that
Codex can build it without guessing.
This is not a loose technical overview. It is the canonical backend blueprint. Its purpose is
to stop AI-generated drift in the exact places where drift causes the most damage:
- random database schema choices
- made-up API endpoints
- hidden backend responsibilities
- inconsistent job states
- storage layouts that do not match the UI
- async pipelines that are only implied, not defined
- worker logic mixed into request/response endpoints
- fake retry logic
- invented processing flows
This document freezes:
- backend service boundaries
- Flask API responsibilities
- PostgreSQL schema structure
- S3/MinIO object layout
- Kafka topic usage
- Lambda worker responsibilities
- Firebase token verification model
- Gemini extraction service boundaries
- job state machine
- retry and failure rules
- endpoint inventory

- backend folder structure
This file must be treated as a canonical implementation contract and must be read
together with:
- PRD.md
- APP_FLOW.md
- TECH_STACK.md
- FRONTEND_GUIDELINES.md
- IMPLEMENTATION_PLAN.md
If generated backend code conflicts with this document, the code is wrong.

- Backend Role in the System
The backend exists to turn an authenticated PDF upload into a traceable processing job
and eventually into a downloadable Excel artifact.
The backend is not a single monolithic process doing everything in one synchronous
request. The backend is a system composed of several controlled layers:
- Flask API layer
- PostgreSQL metadata layer
- Object storage layer using MinIO/S3
- Kafka messaging layer
- AWS Lambda worker layer
- Gemini extraction integration layer
- Excel generation/output layer
The key architectural rule is:
The API accepts work.
The async pipeline performs work.
The database records work.
The storage layer preserves artifacts.
That separation is the foundation of the backend.


## 3. Canonical Backend Architecture
The official backend flow is:
- Authenticated user uploads a PDF through the frontend
- Frontend sends request to Flask API
- Flask verifies Firebase identity token
- Flask validates the file and creates a job record in PostgreSQL
- Flask stores the source PDF in object storage under the receiving/ prefix
- Flask publishes a processing event to Kafka
- A Lambda worker consumes or is triggered into processing flow
- Worker fetches the PDF from storage
- Worker extracts document content and calls Gemini for structured extraction
- Worker validates and normalizes the extraction output
- Worker generates an Excel file
- Worker stores the Excel file in object storage under the processed/ prefix
- Worker updates PostgreSQL job records to completed
- Frontend reads job state through Flask API
- User downloads the Excel output through an authorized backend-mediated path
Kafka exists so the pipeline remains resilient and asynchronous. Lambda exists so
processing can scale without turning the API into a long-running worker service.
PostgreSQL exists so the system has a durable record of job state. S3/MinIO exists so
artifacts are stored properly outside the relational database.

## 4. Backend Design Principles
4.1 Job-Centric Architecture
Every accepted upload becomes a job. Backend design must revolve around jobs as the
primary operational entity.

4.2 Asynchronous by Default
Document extraction is not handled fully inside the upload request. The API must respond
quickly and hand work off to the async processing system.
## 4.3 Durable Metadata, Externalized Files
PostgreSQL stores metadata and state. S3/MinIO stores binary artifacts.
## 4.4 Idempotent Processing
Workers must tolerate retries and duplicate event delivery without corrupting state or
generating conflicting artifacts.
## 4.5 Clear Responsibility Boundaries
Flask is the API layer. Lambda is the processing layer. Kafka is the event transport.
PostgreSQL is the metadata system of record.
4.6 Human-Understandable Operational State
The system should never hide what happened to a job. Status and attempts must be
reconstructable from stored records, not only from logs.

## 5. Backend Component Boundaries
5.1 Flask API Layer
The Flask API handles:
- auth verification
- upload intake
- job creation
- job listing
- job detail retrieval
- admin retry actions

- controlled download access
- health and readiness endpoints
The Flask API does not:
- perform full extraction synchronously
- generate Excel in the upload request
- block while Gemini runs
- act as the primary queue
- embed frontend rendering logic
5.2 PostgreSQL Layer
PostgreSQL stores:
- user-linked backend records
- jobs
- source file metadata
- processing attempts
- extraction result references
- output references
- status transitions
- retry history
- admin actions
PostgreSQL does not store:
- raw PDF binaries
- generated Excel binaries
- entire large document contents as the primary source of truth
## 5.3 Object Storage Layer
MinIO/S3 stores:
- uploaded PDFs
- generated Excel outputs
- optional intermediate structured artifacts if needed later

The MVP official storage split is:
- receiving/
- processed/
## 5.4 Kafka Layer
Kafka transports processing work and retry events. It decouples API acceptance from
worker execution.
## 5.5 Lambda Worker Layer
Lambda performs:
- source file retrieval
- preprocessing
- Gemini extraction
- normalization
- validation
- Excel generation
- artifact persistence
- job status updates
## 5.6 Gemini Integration Layer
Gemini is wrapped behind a project-owned extraction service module. No direct Gemini
calls should be scattered across endpoint handlers or arbitrary worker files.

## 6. Canonical Repository Structure
The backend codebase should use a structure similar to this:
pdfextract/
├── frontend/                         # Next.js app
├── backend/
│   ├── app/

│   │   ├── api/
│   │   │   ├── routes/
│   │   │   │   ├── auth_routes.py
│   │   │   │   ├── health_routes.py
│   │   │   │   ├── upload_routes.py
│   │   │   │   ├── job_routes.py
│   │   │   │   └── admin_routes.py
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   ├── logging.py
│   │   │   ├── security.py
│   │   │   └── errors.py
│   │   ├── db/
│   │   │   ├── base.py
│   │   │   ├── session.py
│   │   │   ├── models/
│   │   │   │   ├── user.py
│   │   │   │   ├── job.py
│   │   │   │   ├── file_record.py
│   │   │   │   ├── processing_attempt.py
│   │   │   │   ├── extraction_result.py
│   │   │   │   ├── output_artifact.py
│   │   │   │   └── admin_action.py
│   │   │   └── migrations/
│   │   ├── schemas/
│   │   │   ├── job_schema.py
│   │   │   ├── upload_schema.py
│   │   │   ├── admin_schema.py
│   │   │   └── extraction_schema.py
│   │   ├── services/
│   │   │   ├── auth_service.py
│   │   │   ├── upload_service.py
│   │   │   ├── job_service.py
│   │   │   ├── storage_service.py
│   │   │   ├── kafka_service.py
│   │   │   ├── signed_download_service.py
│   │   │   └── status_service.py
│   │   └── main.py
│   ├── worker/

│   │   ├── handlers/
│   │   │   ├── process_document.py
│   │   │   └── retry_document.py
│   │   ├── services/
│   │   │   ├── pdf_reader.py
│   │   │   ├── extraction_service.py
│   │   │   ├── validation_service.py
│   │   │   ├── excel_service.py
│   │   │   ├── storage_service.py
│   │   │   ├── kafka_service.py
│   │   │   └── job_update_service.py
│   │   └── lambda_entrypoints/
│   │       ├── process_job_handler.py
│   │       └── retry_job_handler.py
│   ├── tests/
│   ├── requirements.txt
│   └── alembic.ini
└── docs/
The important structural rule is separation between:
- API code
- database models
- shared services
- worker code
- extraction logic
- output generation logic
Do not place all backend logic into one app.py file.

## 7. Authentication Model
Authentication is handled with Firebase.
## 7.1 Frontend Identity
The frontend signs users in using Firebase Authentication and receives an identity token.

## 7.2 Backend Verification
Every protected Flask endpoint verifies the Firebase token using firebase-admin.
## 7.3 Backend User Mapping
The backend should maintain a local users table keyed by Firebase UID. The first time an
authenticated user interacts with the backend, the system can upsert a local user record.
## 7.4 Auth Rule
The backend trusts Firebase for identity, but it still keeps local user metadata and role
information for application-specific authorization.
## 7.5 Role Model
Supported roles:
- user
- admin
The API must not infer admin status from frontend hints. It must validate role through
backend-controlled records.

## 8. Canonical Database Schema
PostgreSQL is the system of record for metadata. The schema should be explicit and
normalized enough to preserve clarity without becoming overengineered.
8.1 users
Stores application-level user identity and role data.
Suggested columns:
- id UUID PK
- firebase_uid VARCHAR unique not null

- email VARCHAR nullable
- display_name VARCHAR nullable
- role VARCHAR not null default user
- is_active BOOLEAN not null default true
- created_at TIMESTAMP not null
- updated_at TIMESTAMP not null
## Purpose:
- map Firebase identity to backend identity
- attach jobs to users
- enforce admin/operator access
8.2 jobs
This is the central operational table.
Suggested columns:
- id UUID PK
- user_id UUID FK to users
- job_status VARCHAR not null
- document_type VARCHAR nullable
- source_file_id UUID FK
- latest_attempt_id UUID nullable
- current_stage VARCHAR nullable
- failure_code VARCHAR nullable
- failure_message TEXT nullable
- is_retryable BOOLEAN not null default true
- submitted_at TIMESTAMP not null
- processing_started_at TIMESTAMP nullable
- completed_at TIMESTAMP nullable
- failed_at TIMESTAMP nullable
- created_at TIMESTAMP not null
- updated_at TIMESTAMP not null
This table is the main state record shown in the app.

8.3 file_records
Tracks uploaded source files and produced outputs at the metadata level.
Suggested columns:
- id UUID PK
- job_id UUID FK
- file_role VARCHAR not null
Values: source_pdf, processed_excel
- original_filename VARCHAR nullable
- storage_bucket VARCHAR not null
- storage_key VARCHAR not null
- content_type VARCHAR nullable
- size_bytes BIGINT nullable
- etag VARCHAR nullable
- created_at TIMESTAMP not null
This avoids storing object details directly on the job table.
8.4 processing_attempts
Tracks each execution attempt for a job.
Suggested columns:
- id UUID PK
- job_id UUID FK
- attempt_number INTEGER not null
- trigger_type VARCHAR not null
Values: initial, retry
- status VARCHAR not null
- started_at TIMESTAMP not null
- ended_at TIMESTAMP nullable
- worker_request_id VARCHAR nullable
- failure_code VARCHAR nullable
- failure_message TEXT nullable
- created_at TIMESTAMP not null

This is essential for retries and auditability.
8.5 extraction_results
Stores structured extraction metadata for successful or partially successful attempts.
Suggested columns:
- id UUID PK
- job_id UUID FK
- processing_attempt_id UUID FK
- document_type VARCHAR nullable
- schema_version VARCHAR not null
- extracted_json JSONB not null
- normalized_json JSONB nullable
- validation_passed BOOLEAN not null default false
- validation_errors JSONB nullable
- created_at TIMESTAMP not null
This preserves the actual structured result behind the generated Excel.
8.6 output_artifacts
Tracks generated download artifacts.
Suggested columns:
- id UUID PK
- job_id UUID FK
- processing_attempt_id UUID FK
- artifact_type VARCHAR not null default excel
- file_record_id UUID FK
- is_current BOOLEAN not null default true
- created_at TIMESTAMP not null
This supports future re-generation or versioning without corrupting the current user-facing
output reference.

8.7 admin_actions
Tracks admin/operator interventions.
Suggested columns:
- id UUID PK
- job_id UUID FK
- admin_user_id UUID FK to users
- action_type VARCHAR not null
Values: retry_requested, job_inspected
- notes TEXT nullable
- created_at TIMESTAMP not null
This gives visibility into operational intervention.

## 9. Job State Machine
User-facing states must remain simple, but the backend should preserve richer execution
state.
## 9.1 Official Job Status Values
- queued
- processing
- completed
- failed
## 9.2 Optional Internal Stage Values
Stored in current_stage, not necessarily exposed directly:
- upload_received
- source_stored
- event_published
- worker_started

- pdf_reading
- gemini_extraction
- normalization
- validation
- excel_generation
- artifact_storage
- completion_persisted
## 9.3 Transition Rules
- upload accepted → queued
- worker begins execution → processing
- output stored successfully → completed
- unrecoverable failure → failed
No other user-facing top-level statuses should be introduced in MVP.

## 10. Object Storage Structure
The storage layout must stay clean and predictable.
## 10.1 Buckets
For simplicity, the MVP may use:
- one bucket in local/dev MinIO
- one bucket in production S3
Inside that bucket, the object prefixes are fixed.
## 10.2 Prefix Structure
receiving/{user_id}/{job_id}/source.pdf
processed/{user_id}/{job_id}/output.xlsx
Optional variants can preserve original filename metadata, but the canonical storage key
must still be deterministic.

## 10.3 Storage Rules
- source PDFs always go under receiving/
- processed Excel artifacts always go under processed/
- do not mix sources and outputs in one prefix
- do not generate random untraceable object keys without job linkage
- do not rely on object listing alone as the source of truth; PostgreSQL tracks
references

## 11. Kafka Topic Design
Kafka is the async backbone.
## 11.1 Required Topics
At minimum:
- document.jobs.submit
- document.jobs.retry
Optional later:
- document.jobs.deadletter
- document.jobs.events
## 11.2 Topic Purpose
document.jobs.submit
Carries newly created jobs into the processing pipeline.
document.jobs.retry
Carries operator-requested retries.
## 11.3 Event Payload Shape
Kafka payloads should remain small and metadata-driven, for example:

- job_id
- attempt_type
- requested_at
- requested_by
- correlation_id
Do not send large raw file content through Kafka.
## 11.4 Kafka Rule
Kafka is transport, not truth. Job truth lives in PostgreSQL.

## 12. Lambda Worker Responsibilities
Lambda should be split conceptually into purpose-driven handlers rather than one all-
knowing mega-handler.
12.1 process_job_handler
Handles normal job execution:
- load job metadata
- mark job processing
- read source PDF
- run extraction pipeline
- validate result
- generate Excel
- store output
- update job to completed
12.2 retry_job_handler
Handles retries:
- validate retry eligibility
- create new processing attempt

- route job back into the same core pipeline
- preserve prior failed attempts
## 12.3 Worker Rule
Both handlers should share underlying service logic. Retry should not duplicate all
processing code.

## 13. Extraction Pipeline Structure
The extraction layer should follow a controlled service pattern.
13.1 PDF Reader Service
Reads and prepares the source PDF.
## Responsibilities:
- fetch object from storage
- validate readable PDF
- extract raw text and table-oriented context where useful
- prepare normalized input package for Gemini
## 13.2 Extraction Service
Wraps Gemini calls.
## Responsibilities:
- document-type-aware prompting
- schema-constrained extraction
- consistent response parsing
- structured JSON return shape
## 13.3 Validation Service
Validates extraction output.
## Responsibilities:

- required field checks
- format checks
- structural checks for line items or sections
- completeness checks for output generation
## 13.4 Excel Service
Generates .xlsx output from normalized structured data.
## 13.5 Job Update Service
Persists status changes, attempt outcomes, and final artifact references.

- API Endpoint Inventory
These are the canonical Flask API endpoints.
## 14.1 Health Endpoints
GET /api/health
Basic health response.
GET /api/ready
Readiness response verifying critical dependencies at a high level.
## 14.2 Auth / Session Endpoint
GET /api/me
Returns the authenticated user profile and role context after Firebase token verification.

## 14.3 Upload Endpoint
POST /api/uploads
Accepts PDF upload, creates job, stores source file, publishes Kafka event.
## Behavior:
- requires auth
- validates file type
- creates jobs record
- creates source file_record
- writes file to storage
- publishes to Kafka
- returns job summary
## 14.4 Job Endpoints
GET /api/jobs
Returns the authenticated user’s jobs, newest first.
GET /api/jobs/{job_id}
Returns detail for one user-owned job.
GET /api/jobs/{job_id}/download
Returns authorized download access to the current Excel artifact if the job is completed.
## 14.5 Admin Endpoints
GET /api/admin/jobs
Returns all jobs across users for admin/operator role.

GET /api/admin/jobs/{job_id}
Returns detailed admin view including attempts and failure context.
POST /api/admin/jobs/{job_id}/retry
Creates retry action and republishes job to Kafka retry topic.
These are the official MVP endpoints. Do not invent extra endpoints unless another
canonical doc requires them.

## 15. Upload Request Lifecycle
The upload endpoint is one of the most critical backend paths.
## 15.1 Required Steps
- verify Firebase token
- validate uploaded file exists
- validate PDF MIME/type expectations
- create job record with queued
- write source PDF to storage
- write file_record for source file
- publish document.jobs.submit event
- return job response
## 15.2 Failure Rules
- if auth fails, reject immediately
- if file validation fails, reject before job creation
- if DB write fails, no success response
- if storage write fails, mark request failed and do not pretend success
- if Kafka publish fails after storage and job creation, preserve backend integrity and
set a recoverable failure path rather than lying to the frontend
The API must never return a success message for a job that cannot be tracked.


## 16. Download Access Model
Downloads should not be exposed by guessing S3 paths from the frontend.
16.1 Backend-Controlled Download
The frontend calls:
GET /api/jobs/{job_id}/download
The backend:
- verifies auth
- verifies ownership or admin access
- verifies job is completed
- verifies artifact exists
- returns a secure download path or stream response
## 16.2 Rule
The frontend should never derive object keys itself.

## 17. Retry Model
Retry is admin-only in MVP.
## 17.1 Retry Eligibility
A job is retryable if:
- current status is failed
- source file exists
- retry limit has not been exceeded
- failure is not marked permanently non-retryable

## 17.2 Retry Flow
- admin calls retry endpoint
- backend creates admin_action
- backend inserts new processing_attempt
- backend republishes retry event to Kafka
- job returns to queued
- worker reprocesses
## 17.3 Retry Rule
Retries create new attempts. They do not overwrite historical failure records.

- Idempotency and Duplicate Safety
This is essential in async systems.
## 18.1 Why It Matters
Kafka and Lambda can create at-least-once style behavior. Duplicate processing must not
produce inconsistent job outcomes.
## 18.2 Required Protections
- processing attempts should be uniquely tracked
- worker should check current job state before writing final output
- completed jobs should not generate multiple “current” outputs accidentally
- retries should explicitly create new attempts, not masquerade as the initial one
## 18.3 Artifact Rule
Only one output artifact should be flagged as current for a job at a time.


- Error Handling and Failure Codes
Failure should be structured, not improvised.
## 19.1 Example Failure Codes
## • AUTH_INVALID
## • UPLOAD_INVALID_TYPE
## • STORAGE_WRITE_FAILED
## • KAFKA_PUBLISH_FAILED
## • PDF_READ_FAILED
## • GEMINI_REQUEST_FAILED
## • EXTRACTION_PARSE_FAILED
## • VALIDATION_FAILED
## • EXCEL_GENERATION_FAILED
## • OUTPUT_STORAGE_FAILED
19.2 User vs Admin Error Visibility
Standard users see a readable failure message.
Admins can see the stored failure code and more detailed attempt context.
Do not expose raw Python tracebacks to standard users.

## 20. Environment Variables
The backend needs controlled configuration, not hardcoded values.
Required categories:
- Flask environment
- PostgreSQL connection URL
- Firebase admin configuration
- S3/MinIO endpoint and credentials
- Kafka bootstrap/server settings
- Gemini/GCP credentials

- bucket names
- prefix names
- admin retry limits
- download signing configuration if used
Examples of environment keys
## • APP_ENV
## • DATABASE_URL
## • FIREBASE_PROJECT_ID
## • GOOGLE_APPLICATION_CREDENTIALS
## • S3_BUCKET_NAME
## • S3_ENDPOINT_URL
## • AWS_ACCESS_KEY_ID
## • AWS_SECRET_ACCESS_KEY
## • KAFKA_BOOTSTRAP_SERVERS
## • GEMINI_MODEL_NAME
## • RECEIVING_PREFIX
## • PROCESSED_PREFIX
The exact naming can be standardized in implementation, but these concerns must exist.

## 21. Local Development Topology
Local development mirrors the same architecture with local substitutes where
appropriate.
- Next.js frontend runs locally
- Flask API runs locally
- PostgreSQL runs locally
- MinIO replaces S3
- Kafka runs locally
- Firebase auth uses dev project or emulator support
- Lambda logic is invoked via local runner or test harness
The architecture should remain the same even if the infrastructure is lighter.


## 22. Production Topology
Production uses:
- Next.js web app
- Flask API deployment
- managed PostgreSQL
## • AWS S3
- Kafka-compatible production broker setup
- AWS Lambda workers
## • Firebase Authentication
- Gemini via GCP
The key point is that production is still the same backend architecture, not a different
application model.

- Logging and Observability
The backend must log in a structured way.
Required logging context
- job_id
- user_id where relevant
- attempt_id
- correlation_id
- status
- failure_code
## Rule
Logs support debugging, but PostgreSQL remains the operational source of truth for job
history.


## 24. Security Rules
- Firebase tokens must be verified on protected endpoints
- object storage credentials stay server-side only
- Gemini credentials stay server-side only
- PostgreSQL credentials stay server-side only
- admin routes enforce backend role checks
- user download access must verify ownership
- no client-side direct privileged write access to storage without backend control

- Explicit Anti-Patterns
The backend must not drift into any of the following:
- storing PDFs in PostgreSQL blobs
- synchronous extraction during upload request
- direct browser calls to Gemini
- using Firestore instead of PostgreSQL
- using RabbitMQ instead of Kafka
- mixing API and worker code into one mega-module
- skipping attempt records
- exposing raw storage paths directly to the client without authorization
- inventing undocumented endpoints
- collapsing all job states into an untraceable boolean success flag
These are exactly the types of AI-generated shortcuts that break real systems.

## 26. Final Backend Definition
The official backend for PDFextract is a job-based, async, traceable document-processing
system built on Flask APIs, PostgreSQL, MinIO/S3 object storage, Kafka messaging,

Lambda workers, Firebase auth verification, Gemini extraction services, and Excel artifact
generation.
Its structure is intentionally disciplined:
- Flask accepts and exposes application actions
- PostgreSQL records state and history
- S3/MinIO stores files
- Kafka transports work
- Lambda performs work
- Gemini extracts structure
- Excel becomes the final deliverable
That is the backend.
Nothing more.
Nothing else.
No substituted infrastructure.
No guessed schema.
No invented API surface.
