

TECH_STACK.md
PDFextract — Canonical Technology Stack
## 1. Document Purpose
This document freezes the technology stack for PDFextract so implementation does not
drift. Its purpose is not to explore options. Its purpose is to eliminate options.
AI coding tools fail most often when the stack is underspecified. If documentation says
“use React” or “use Python backend,” the AI fills in the rest with guesses. It invents state
libraries, changes storage models, swaps queueing systems, introduces different auth
flows, and silently rewrites architecture around whatever defaults it has seen most often.
This document exists to stop that.
TECH_STACK.md defines:
- the exact approved stack for PDFextract
- the exact runtime standards for each layer
- the exact libraries and versions the project should start with
- which technologies are allowed
- which technologies are not allowed
- how the chosen stack components interact
- what local development looks like
- what production architecture looks like
- what should remain configurable versus what is hard-locked
This file must be treated as one of the six canonical project documents. It must be read
together with:
- PRD.md
- APP_FLOW.md
- FRONTEND_GUIDELINES.md
- BACKEND_STRUCTURE.md
- IMPLEMENTATION_PLAN.md

If generated code conflicts with this document, the code is wrong.

## 2. Approved Final Stack
The only approved technology stack for PDFextract is the following:
## • Frontend: React + Next.js
- Backend: Python + Flask APIs
- LLM: Gemini via GCP
- Database: PostgreSQL
- File Storage: MinIO for local/dev, AWS S3 for production
## • Message Queue: Kafka
- Compute: AWS Lambda
## • Authentication: Firebase
- Output Format: Excel files stored in S3 and downloadable via the web app
The core system flow is also fixed:
User uploads PDF → file lands in S3 receiving location → Lambda processing starts →
Gemini extracts structured data → Excel file is generated → Excel file is stored in S3
processed location → user downloads result from frontend
Kafka is part of this flow as the async buffer and resilience layer. If Lambda is unavailable,
delayed, or if async/batch workloads need decoupling, Kafka handles job queueing and
event transport.
That is the stack.
That is the system.
No substitutions unless explicitly re-approved.

## 3. Architecture Philosophy
PDFextract is not being built as a monolith that tries to do everything in one process. It is
being built as a focused document-processing system with clean separation across the
following layers:

## 3.1 Presentation Layer
The web application is built with React + Next.js. This layer handles user-facing workflows:
- sign in
- upload PDF
- view jobs
- inspect job detail
- download completed Excel files
This layer does not do extraction, schema mapping, queue management, or direct
database writes from the browser.
3.2 API Layer
The backend API is written in Python using Flask. It is responsible for:
- authenticated API endpoints
- upload intake
- job creation
- job lookup
- user job history
- admin/operator job views
- secure output access orchestration
This layer is the application contract between the frontend and the backend system.
## 3.3 Async Processing Layer
AWS Lambda is the compute engine for asynchronous processing. Lambda handles:
- retrieval of uploaded PDFs
- extraction pipeline execution
- Gemini calls
- validation
- Excel generation
- metadata updates
- processed artifact persistence

## 3.4 Messaging Layer
Kafka is the queueing and buffering layer. Its job is to decouple upload acceptance from
downstream processing and give the system resilience and throughput flexibility.
## 3.5 Persistence Layer
PostgreSQL stores system metadata and operational records. This includes:
- users
- jobs
- files
- processing status
- extraction metadata
- output references
- retry records
- audit-style operational state
## 3.6 Object Storage Layer
MinIO and AWS S3 are the file storage systems.
MinIO is used for local and development parity.
AWS S3 is used for production.
The storage model is intentionally simple:
- receiving/ for raw uploaded files
- processed/ for generated Excel outputs
## 3.7 Identity Layer
Firebase Authentication handles user identity and session authentication. The frontend
signs users in, and the backend validates Firebase-issued identity tokens before allowing
protected operations.

3.8 AI Extraction Layer
Gemini, accessed through GCP, handles document extraction and structured
interpretation. Gemini is the LLM used for turning PDF content into schema-aligned
structured data.

## 4. Frozen Technology Decisions
This section is the non-negotiable part of the stack.
## 4.1 Frontend
## Approved: React + Next.js
Rejected: Framer as the primary frontend framework, plain React SPA without Next.js,
## Angular, Vue, Svelte, Astro
## 4.2 Backend
## Approved: Python + Flask
Rejected: FastAPI, Express, NestJS, Django, Node-only backend, Go backend
## 4.3 AI / LLM
Approved: Gemini via GCP
Rejected: OpenAI as the default extraction engine, Anthropic as the primary engine, local
open-source model hosting for MVP
## 4.4 Database
Approved: PostgreSQL
Rejected: MySQL, Firestore as the system database, MongoDB, DynamoDB as primary
metadata store

## 4.5 Storage
Approved: MinIO + AWS S3
Rejected: Firestore Storage model, Supabase Storage, local disk-only output storage in
production
## 4.6 Messaging
## Approved: Kafka
Rejected: RabbitMQ, SQS as the core async backbone, Redis queue as the system of
record for jobs
## 4.7 Compute
Approved: AWS Lambda
Rejected: always-on VM backend for processing, ECS-only worker design for MVP, Vercel
serverless Python as the main compute layer
## 4.8 Auth
## Approved: Firebase Authentication
Rejected: custom JWT auth, Auth0 as primary auth, Supabase Auth
## 4.9 Output
Approved: Excel .xlsx output stored in S3
Rejected: JSON-only delivery as the user-facing artifact, CSV-only output as the default
deliverable

## 5. Versioning Strategy
Not every layer of this stack is versioned the same way.
Some parts of the system are project-controlled dependencies. These must be pinned
exactly.
## Examples:

## • React
## • Next.js
## • Python
## • Flask
- SQLAlchemy
- openpyxl
Other parts are managed cloud services. These are not pinned like npm packages.
Instead, they are frozen by:
- product choice
- SDK/API contract
- environment configuration
- infrastructure provisioning
## Examples:
- AWS Lambda
## • AWS S3
## • Firebase Authentication
- PostgreSQL managed hosting
- Kafka broker infrastructure
- Gemini service access via GCP
So this document freezes the stack in two ways:
- Exact package/runtime versions where the team controls installation
- Exact service/vendor choices and API contracts where cloud providers manage
the service runtime
That distinction is important. It prevents false precision while still preventing AI drift.

## 6. Canonical Version Matrix
The following versions are the project baseline versions for the first implementation of
PDFextract.

6.1 Frontend Runtime and Core Dependencies
## • Node.js: 22.11.0
- npm: 10.9.0
- TypeScript: 5.6.3
## • React: 18.3.1
- react-dom: 18.3.1
## • Next.js: 14.2.25
## Frontend Standards
- Next.js uses the App Router
- Frontend is built as a web application, not a static-only export
- Frontend consumes Flask APIs over HTTPS
- Frontend does not directly call Gemini
- Frontend does not directly connect to PostgreSQL
- Frontend does not directly perform privileged S3 operations without backend
authorization
## Why This Frontend Stack
React + Next.js is approved because it gives:
- strong component architecture
- routing structure aligned to the app flow
- server/client rendering flexibility
- production-friendly frontend organization
- good long-term maintainability
Next.js is chosen over a plain React SPA because PDFextract needs structure, route
clarity, authenticated flows, and production-grade page organization rather than a loose
client-only app.

## 7. Frontend Implementation Rules
The frontend stack is not just a framework choice. It also includes behavioral constraints.

## 7.1 Allowed Frontend Patterns
- React components
## • Next.js App Router
- TypeScript everywhere
- native fetch or thin typed API client wrappers
- local component state
- route-based page composition
- Firebase client SDK for sign-in/session acquisition
## 7.2 Rejected Frontend Patterns
- Redux by default
- Zustand by default
- random generated dashboard templates
- direct business logic in UI components
- direct Gemini calls from browser
- direct database reads from browser
- direct privileged object-store writes from browser without backend-controlled flow
The frontend must remain thin, intentional, and workflow-centered.

- Backend Runtime and Core Dependencies
The backend stack is fixed as Python + Flask APIs.
## 8.1 Canonical Backend Versions
## • Python: 3.11.11
## • Flask: 3.1.0
## • Werkzeug: 3.1.3
- SQLAlchemy: 2.0.36
## • Alembic: 1.14.0
- psycopg: 3.2.3
- boto3: 1.35.65

- firebase-admin: 6.6.0
- openpyxl: 3.1.5
- PyMuPDF: 1.25.1
- pdfplumber: 0.11.4
- requests: 2.32.3
- google-auth: 2.37.0
## Why Flask
Flask is the approved API layer because the meeting locked Python + Flask, and Flask is
suitable for:
- clean REST API design
- lightweight request handling
- explicit routing
- small operational footprint
- easy Lambda adaptation for API-serving workloads
The project is not using FastAPI even though it is popular. The stack is Flask because that is
the approved decision and the goal here is certainty, not framework churn.
## What Flask Handles
The Flask API layer handles:
- auth-validated endpoints
- upload intake
- job creation
- job list retrieval
- job detail retrieval
- admin retry initiation
- output access orchestration
Flask does not perform all long-running extraction work synchronously in
request/response flow. Heavy processing is offloaded into Lambda-driven async flows.


## 9. Flask + Lambda Execution Model
The project requirement includes both Flask APIs and AWS Lambda. That means the
architecture must support two execution modes:
9.1 API Execution
Flask serves the API contract for frontend requests.
## 9.2 Async Worker Execution
Lambda runs the extraction and processing jobs.
The key architectural rule is:
The user-facing API layer and the document-processing worker layer are both Python,
but they are not the same runtime responsibility.
In practice, the build should separate:
- API entrypoint code
- worker processing code
- shared domain logic
- shared schemas
- shared storage/database access layer
This prevents the API from turning into a blocking processing service and prevents the
worker pipeline from inheriting web-routing concerns.

## 10. Database Standard
## Approved Database
PostgreSQL only

## Database Version Standard
- PostgreSQL: 16.x
- Local dev baseline: PostgreSQL 16
- Production baseline: managed PostgreSQL 16
Why PostgreSQL
PostgreSQL is chosen because:
- it is strong for structured relational metadata
- it supports the job-driven architecture well
- it fits AWS-hosted infrastructure cleanly
- it handles transactional integrity better than schema-loose alternatives
- it is the approved replacement over MySQL
What PostgreSQL Stores
PostgreSQL is the system of record for application metadata, not raw binary PDFs.
It stores:
- user-linked job records
- file metadata
- processing status
- extracted metadata references
- result records
- retry history
- timestamps
- operator-visible failure markers
It does not store:
- raw PDF binaries
- generated Excel binaries
- full raw object content from storage
Those belong in S3/MinIO.


## 11. Object Storage Standard
## Approved Storage
- Local / development: MinIO
- Production: AWS S3
## Storage Topology
The storage model is intentionally minimal and fixed:
- receiving/
- processed/
Meaning of Each Folder
receiving/
Stores source PDF uploads.
processed/
Stores generated Excel output files.
This separation is required because it keeps raw inputs and generated artifacts logically
distinct. It also simplifies retention policies, troubleshooting, and access control.
Why MinIO + S3
MinIO gives local development a storage model that behaves like S3 without requiring
production AWS infrastructure for every local iteration. S3 is the production object store
because it is durable, industry standard, and fits the AWS-centered runtime model.
## Storage Rules
- PDFs are never stored only on local server disk in production
- completed outputs are never left only in temp execution storage

- storage paths must be deterministic and traceable
- download actions should resolve to the processed artifact, not regenerate the file
on demand each time

## 12. Message Queue Standard
## Approved Queue
Kafka only
Kafka Role in This System
Kafka is the async backbone between upload acceptance and downstream processing
reliability.
Kafka is not included for trendiness. It serves very specific roles:
- decouples upload from heavy processing
- prevents user-facing latency from becoming processing latency
- buffers workload when Lambda execution is delayed or unavailable
- supports future batch and retry workflows
- makes failure isolation cleaner than direct chained execution
## Version Standard
- Kafka protocol baseline: 3.8.x compatibility
- Local development: Dockerized Kafka in KRaft mode
- Production direction: managed Kafka-compatible infrastructure on AWS
## Python Client Standard
- confluent-kafka: 2.6.1
Why Kafka Instead of RabbitMQ
The meeting explicitly replaced RabbitMQ with Kafka. That decision is now frozen. The
reasoning is aligned to the system goals:

- better event-stream posture for async processing
- strong industry fit for operational pipelines
- better long-term scaling path for document processing workloads
- cleaner future support for retries, batching, and dead-letter flows
## What Kafka Is Not Used For
Kafka is not the primary data store.
Kafka is not the auth system.
Kafka is not where final job truth lives.
PostgreSQL remains the system of record for job state.

## 13. Compute Standard
## Approved Compute
AWS Lambda
## Why Lambda
Lambda is approved because:
- it scales with request and job volume
- it avoids overcommitting early infrastructure
- it fits async document processing well
- it is cost-efficient for an MVP and early user base
- it matches the approved event-driven architecture
## Lambda Responsibility
Lambda runs the heavy document workflow:
- fetch file from receiving storage
- parse/extract source content
- call Gemini
- normalize output

- validate data
- generate Excel file
- store Excel in processed storage
- update job status in PostgreSQL
## Lambda Constraints
Because Lambda is serverless:
- execution logic must be stateless between invocations
- temp file usage must be bounded
- processing code must tolerate retries
- idempotency matters
- long-running assumptions must be avoided
These are not optional design considerations. They are part of why the processing pipeline
must be explicit and disciplined.

## 14. Authentication Standard
## Approved Auth
## Firebase Authentication
## Frontend Auth Library
- firebase: 11.0.2
## Backend Token Verification
- firebase-admin: 6.6.0
## Why Firebase Auth
Firebase Auth is already approved and gives:
- a fast authentication path

- stable token-based identity
- easy frontend integration
- backend-verifiable identity tokens
- reduced need to build auth from scratch
## Auth Model
- frontend signs user in using Firebase Auth
- frontend includes auth token in protected backend requests
- Flask backend verifies Firebase identity token
- protected endpoints reject invalid or missing auth
## Auth Scope
Firebase Auth is used for:
- sign in
- user identity
- route protection
- associating jobs with authenticated users
Firebase Auth is not the main database and is not the document store.

- LLM / AI Standard
Approved LLM
Gemini via GCP
## Access Model
Gemini is accessed through GCP with existing credit support. The application standard is:
- use Gemini through Vertex AI / GCP-backed integration
- keep model name configurable by environment
- keep the extraction interface wrapped behind a project-owned service layer

## Why Gemini
Gemini is chosen because:
- it is already approved in the meeting
- it aligns with available GCP credit
- it fits structured extraction use cases
- it avoids mixing AI vendors during MVP
- it keeps the extraction layer consistent
SDK / API Standard
Because managed model catalogs change over time, the safer lock for this project is:
- Google auth layer: google-auth==2.37.0
- HTTP transport: requests==2.32.3
- API contract: Vertex AI / GCP Gemini integration through a project-owned wrapper
That means the codebase should not scatter Gemini calls everywhere. It should centralize
them inside a dedicated extraction service so model upgrades do not force a system-wide
rewrite.
## Model Selection Rule
The exact Gemini model identifier must be environment-configurable, but the system
architecture is fixed to Gemini only. That allows safe model swapping inside the approved
vendor boundary without changing the overall stack.
This is an important distinction:
- Vendor choice is fixed
- Model string is configurable
- System architecture is unchanged

- PDF Processing Standard
Although Gemini is the extraction engine, the system still needs deterministic PDF
handling before and after the LLM call.

Approved PDF Libraries
- PyMuPDF: 1.25.1
- pdfplumber: 0.11.4
## Why Both
These libraries serve different practical roles:
- PyMuPDF is strong for robust low-level PDF access and page handling
- pdfplumber is useful for text and table-oriented extraction support
The stack uses them as preprocessing and fallback helpers, not as a substitute for Gemini.
PDF Layer Role
The PDF processing layer is responsible for:
- validating PDF readability
- extracting page/text/table context where helpful
- preparing content for Gemini
- supporting traceable extraction behavior
This keeps the LLM input grounded and reduces blind prompt-only extraction.

## 17. Excel Generation Standard
## Approved Output Format
## Microsoft Excel .xlsx
## Library Standard
- openpyxl: 3.1.5

## Why Excel
The product requirement is explicit: users download structured Excel outputs. This is not
optional and not secondary. The application is meant to produce a business-usable
deliverable.
Why openpyxl
openpyxl is chosen because it is reliable for:
- workbook creation
- sheet structuring
- row/column writing
- formatting basic business outputs
- stable Python integration
The MVP does not need a flashy spreadsheet engine. It needs predictable workbook
generation.

## 18. Local Development Stack
The local development environment must mirror production behavior as closely as
practical without forcing full cloud infrastructure for every edit.
## Local Baseline
- Next.js app runs locally
- Flask API runs locally
- PostgreSQL runs locally
- MinIO runs locally
- Kafka runs locally
- Firebase Auth integration is used, with emulator support allowed in dev
- Gemini integration can be mocked or routed through controlled dev credentials
- Excel generation runs locally
- Lambda worker logic runs through local invocation harnesses or task runners

Local Ports and Service Baseline
These can be standardized in implementation, but the typical layout should be:
## • Next.js: 3000
- Flask API: 8000
- PostgreSQL: 5432
- MinIO API: 9000
- MinIO console: 9001
- Kafka broker: 9092
## Dev Rule
Local development should not force developers to upload to production S3 or mutate
production PostgreSQL. MinIO and local PostgreSQL exist specifically to preserve velocity
and safety.

## 19. Production Stack
The production stack remains exactly the same in technology choice, but swaps local
components for managed equivalents:
- Next.js frontend deployed as the production web app
- Flask APIs exposed as the production backend API surface
- PostgreSQL on managed production infrastructure
- AWS S3 for object storage
- Kafka-compatible production messaging on AWS
- AWS Lambda for document processing
- Firebase Auth for production identity
- Gemini via GCP for extraction
- Excel artifacts stored in S3 processed path
The critical principle is environment parity by architecture, not by pretending local and
production are identical binaries for every service.


- Security and Secrets Standard
Secrets are never hardcoded into frontend or backend code.
## Secret Categories
- Firebase config and verification configuration
- PostgreSQL connection credentials
- S3 / MinIO credentials
- Kafka connection credentials
- Gemini / GCP authentication credentials
- signing and service integration values
## Security Rule
Frontend receives only the configuration necessary for browser-side auth and public client
initialization. Privileged credentials remain backend-only.
## Explicitly Rejected
- hardcoded keys in repo
- committing service-account JSON into source control
- embedding database credentials in client code
- direct privileged Gemini secrets in the browser

## 21. Explicitly Rejected Stack Additions
To prevent scope drift, the following technologies are explicitly out of the project unless the
canonical docs are revised:
- Firestore as the primary system database
- Framer as the primary frontend build platform
- RabbitMQ as async backbone
- MySQL as metadata database
- Supabase replacing Firebase/PostgreSQL/S3
- Express or Node replacing Flask

- FastAPI replacing Flask
- Redis as primary queue
- local filesystem as production output storage
- browser-to-Gemini direct calls
- browser-to-PostgreSQL direct access
If AI-generated code introduces any of those, that code should be treated as hallucinated
implementation.

- Cross-Document Role of This File
This document answers what technology is allowed.
It does not fully define:
- page design
- user flow details
- API endpoint list
- table schema
- retry logic
- exact job state machine
- build sequence
Those belong in the remaining docs:
- FRONTEND_GUIDELINES.md defines how the frontend should look and behave
visually
- BACKEND_STRUCTURE.md defines tables, endpoints, storage paths, queue behavior,
and worker boundaries
- IMPLEMENTATION_PLAN.md defines execution sequence
This separation matters. Stack certainty must come before implementation detail.


## 23. Final Frozen Stack Summary
The canonical technology stack for PDFextract is now locked as:
## Frontend
## • React 18.3.1
- react-dom 18.3.1
## • Next.js 14.2.25
- TypeScript 5.6.3
## • Node.js 22.11.0
## Backend
## • Python 3.11.11
## • Flask 3.1.0
- SQLAlchemy 2.0.36
## • Alembic 1.14.0
- psycopg 3.2.3
## Auth
## • Firebase Auth
- firebase 11.0.2
- firebase-admin 6.6.0
## Database
- PostgreSQL 16.x
## Storage
- MinIO for local/dev
- AWS S3 for production
- receiving/ and processed/ as the fixed storage split

## Messaging
- Kafka 3.8.x compatibility
- confluent-kafka 2.6.1
## Compute
- AWS Lambda
## AI
- Gemini via GCP
- google-auth 2.37.0
- requests 2.32.3
- model string configurable, vendor fixed
PDF / Output Tooling
- PyMuPDF 1.25.1
- pdfplumber 0.11.4
- openpyxl 3.1.5
This is the only approved stack for the MVP implementation of PDFextract.
