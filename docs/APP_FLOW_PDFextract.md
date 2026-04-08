

APP_FLOW.md
PDFextract — Application Flow Document
## 1. Document Purpose
This document defines the exact application flow for PDFextract. Its job is to remove
ambiguity from the product before implementation starts. This is not a design mood board,
not a loose wireframe summary, and not a list of generic SaaS screens. It is a canonical
navigation and behavior document.
The purpose of APP_FLOW.md is to answer all of the following, in full:
- what pages exist
- what pages do not exist
- what the user sees first
- what happens after sign-in
- how a PDF is uploaded
- how the user experiences asynchronous processing
- how job status is displayed
- how completed outputs are retrieved
- how failures are shown
- how internal admin/operator users inspect and retry failed jobs
This document exists because AI coding tools are highly capable but often guess app
structure when documentation is weak. When app flow is not locked, the build starts
drifting. Navigation becomes inconsistent, random pages appear, state transitions are
unclear, and the frontend begins to imply backend behavior that does not exist. This
document prevents that.
This file must be read together with:
- PRD.md
- TECH_STACK.md
- FRONTEND_GUIDELINES.md
- BACKEND_STRUCTURE.md

- IMPLEMENTATION_PLAN.md
If future code, prompts, or generated UI conflict with this document, this document wins
unless explicitly revised.

## 2. Product Flow Principles
The app flow for PDFextract is built around one core user job:
Upload a PDF → wait while the system processes it asynchronously → download the
resulting Excel output.
Everything in the app must serve that core flow.
This means the application is not:
- a chat application
- a document editor
- a data-cleaning studio
- a workflow builder
- a BI dashboard
- a general-purpose file manager
- a multi-feature admin suite in v1
The MVP app flow must feel focused, operational, and easy to understand. The user should
not need training to know what to do.
The flow principles are:
## 2.1 One Primary Job Per Session
A user comes into the app primarily to process one or more PDFs and review results. The
flow should always make it obvious how to do that.

## 2.2 Async Processing Must Feel Visible
The backend is asynchronous. Files move through storage, queueing, Lambda execution,
Gemini extraction, validation, and output generation. The frontend must reflect that clearly
so users do not think the upload failed or the app froze.
## 2.3 No Hidden State
The system must not silently accept a file and then leave the user uncertain. Every upload
becomes a trackable job.
2.4 Job-Based Mental Model
The user does not think in terms of Kafka topics, Lambda triggers, or Gemini calls. The user
thinks in terms of jobs:
- I uploaded a file
- it is processing
- it completed
- I can download the result
- or it failed
The application flow must reinforce that mental model.
## 2.5 Only Necessary Pages
Pages must exist only if they directly support the product. No profile page, billing page,
theme settings page, analytics suite, or “AI assistant” panel should be added unless later
documented and approved.

- Approved Tech Stack Constraints for App Flow
This application flow is built for the following stack only:
- React + Next.js for frontend page rendering, routing, and authenticated app
experience
- Firebase Auth for authentication and session identity

- Python + Flask APIs for backend application endpoints
- AWS S3 for production file storage
- MinIO for local/dev S3-compatible storage
- AWS Lambda for asynchronous processing execution
- Kafka for queuing, buffering, and resilience when Lambda is unavailable or when
async/batch processing is needed
- PostgreSQL for job metadata, file records, user-linked history, statuses, and result
references
- Gemini for extraction
- Excel output files stored in S3 processed location and downloaded via the web app
This document must not assume or introduce:
## • Firestore
## • Framer
- RabbitMQ
- MySQL
- Vercel serverless Python backend as the core backend model
- generic no-code workflow tools
- direct SAP/ERP integration in MVP

## 4. User Roles
There are only two roles in the MVP app flow.
## 4.1 Standard Authenticated User
This user can:
- sign in
- upload PDFs
- view their jobs
- open a job detail screen
- download completed Excel outputs
- see failed jobs that belong to them
This user cannot:

- retry failed jobs globally
- view all system jobs
- inspect raw backend processing metadata
- view other users’ files
## 4.2 Internal Admin / Operator
This user can do everything a standard user can do, plus:
- view all jobs across users
- inspect system-wide failure states
- open detailed admin job views
- retry failed jobs
- inspect processing stage information needed for operations
The admin/operator role exists to support internal testing, demo readiness, and early
operational troubleshooting.

## 5. Route Map
The route map for the MVP is intentionally small.
## Public Routes
## • /
## • /login
## Authenticated User Routes
## • /dashboard
## • /upload
## • /jobs
- /jobs/[jobId]

## Internal Admin Routes
## • /admin/jobs
- /admin/jobs/[jobId]
There are no other MVP routes.
That means there is no:
## • /chat
## • /settings
## • /billing
## • /workspace
## • /team
## • /analytics
## • /schema-builder
## • /profile
## • /notifications-center
Those would create artificial complexity and encourage implementation drift.

## 6. Global Navigation Model
Once authenticated, the app navigation is simple and consistent.
## Primary Navigation
The main app navigation contains:
## • Dashboard
## • Upload
## • Jobs
If the logged-in user has internal admin/operator access, a fourth item appears:
## • Admin

## Header Actions
The top-right header contains:
- signed-in user identity indicator
- sign out action
No extra dropdown options should appear in MVP unless they directly support auth or
internal role context.
## Mobile / Narrow Layout Behavior
On smaller screens, the same navigation collapses into a compact menu. The route
structure remains identical. Functionality does not change.

## 7. Entry Flow
## 7.1 Route /
This is the application entry route.
## Behavior:
- if the user is not authenticated, route to /login
- if the user is authenticated, route to /dashboard
The root route is not a marketing website in the MVP. It is an entry resolver.
## Reason:
PDFextract MVP is an operational product, not a brochure site. The first build should
optimize for actual product flow, not marketing content.


## 8. Authentication Flow
## 8.1 Route /login
## Purpose
This page is used only for sign-in.
UI Content
The login page contains:
- product name and short purpose statement
- Firebase-authenticated sign-in action(s)
- loading state during sign-in
- clear error state for failed login
The login page should not contain:
- feature tour carousel
- animated marketing sections
- pricing tables
- roadmap teaser
- random illustrations that distract from entry
## Flow
- User lands on /login
- User initiates Firebase-authenticated sign-in
- On success, session is established
- User is routed to /dashboard
- On failure, inline error is shown and user remains on page
## Session Persistence
If the session is valid, the user should not repeatedly see /login. The app should preserve
authenticated access until sign-out or session expiry.

## Session Expiry Behavior
If an authenticated route is accessed after session expiry:
- user is redirected to /login
- an informational message indicates the session expired
- after re-authentication, user returns to /dashboard

## 9. Dashboard Flow
## 9.1 Route /dashboard
## Purpose
This is the authenticated home screen. It is not a generic analytics dashboard. It is a
workflow-oriented home page.
## Page Goals
The dashboard answers four questions quickly:
- what can I do right now
- what happened to my latest uploads
- which jobs are still processing
- which outputs are ready to download
## Content Structure
The dashboard contains:
- primary upload call-to-action
- recent jobs section
- status summary section
- completed download-ready jobs section or indicators

## Recommended Information Blocks
- New Upload action block
- Recent Jobs list, newest first
- Processing Jobs count
- Completed Jobs count
- Failed Jobs count
This is enough for the MVP. It should not become a data-heavy executive dashboard.
First-Time User Experience
If the user has no prior jobs:
- show a clean empty state
- explain that the first step is uploading a PDF
- provide a prominent button to go to /upload
## Returning User Experience
If the user has job history:
- show the latest jobs first
- surface status badges clearly
- allow direct navigation to the relevant job detail page
- if completed jobs exist, surface download-ready state visibly
## Primary Actions
From /dashboard, the user can:
- go to /upload
- open /jobs
- open a recent job detail page
## Dashboard Rule
The dashboard must always serve the upload → track → download loop. It must never
become a generic landing page full of unrelated components.


## 10. Upload Flow
## 10.1 Route /upload
## Purpose
This page exists to create a new processing job from a PDF upload.
## Core Principle
The upload page must feel simple and high-confidence. The user should know:
- what file type is supported
- what happens after upload
- that processing is asynchronous
- where results will appear
## Page Content
The upload page contains:
- PDF upload input or dropzone
- brief explanation of supported use cases
- selected file display
- upload button
- validation and error messaging
- success transition behavior
## Supported Input
For MVP:
- PDF only
- one file per upload action

This is important. The page should not imply drag-in multiple folders, image uploads, ZIP
uploads, or arbitrary document libraries unless later added to scope.
## Upload Validation
Before upload is accepted:
- file type must be PDF
- zero-byte or obviously invalid files must be rejected
- oversize rules, if configured, must be enforced clearly
## Upload Submission Flow
- User enters /upload
- User selects a PDF
- UI validates allowed type
- User clicks upload
- Frontend sends authenticated upload request
- Backend stores the source file in the receiving storage path
- Job metadata is written to PostgreSQL
- Processing is triggered through Lambda / Kafka-backed workflow
- User receives success confirmation
- User is redirected to the new job detail page
## Immediate Status After Upload
The app should show the job in an early state such as:
- uploaded
- queued
or
- processing
The exact backend sub-stage can be more granular internally, but the user-facing app
should remain readable.
Upload Success UX
After a successful upload:

- show success confirmation
- redirect to /jobs/[jobId]
- do not keep the user stranded on the upload page wondering what happened
Upload Failure UX
If upload fails before job creation:
- keep the user on /upload
- show clear inline error
- allow retry without reloading the full app
- do not create fake placeholder jobs

- Job Lifecycle in the App
Every accepted upload becomes a job. This is the core object the user tracks in the app.
User-Facing Statuses
The frontend should use a simple status model:
## • Queued
## • Processing
## • Completed
## • Failed
Internally, the backend may track more detailed states such as:
- file stored
- queue published
- Lambda started
- extraction running
- validation running
- Excel generation running
- output stored
But those should roll up into a small set of statuses for normal users.

Meaning of Each Status
## Queued
The file is accepted, stored, and waiting for processing or has been handed into the async
pipeline.
## Processing
The document is actively moving through extraction and output generation.
## Completed
The Excel output was successfully generated, stored in processed storage, and is available
for download.
## Failed
The job did not complete successfully. A failure exists and needs operator review or a retry
path.

## 12. Jobs List Flow
## 12.1 Route /jobs
## Purpose
This page shows the user’s full processing history.
## Page Content
The jobs page contains a structured list of all jobs belonging to the authenticated user.
Each job row should show:
- file name

- upload timestamp
- current status
- document type if known
- output availability
- action to open job detail
## Sorting
Default sorting is:
- newest first
## Empty State
If the user has no jobs:
- explain that no files have been uploaded yet
- provide a button to go to /upload
## Row Click Behavior
Clicking a job row routes to /jobs/[jobId]
## Why This Page Exists
The dashboard shows a summary. The jobs page is the canonical history view.
This page should not try to become:
- a raw log console
- a full admin table
- a schema inspection surface
It is a user history page.


## 13. Job Detail Flow
13.1 Route /jobs/[jobId]
## Purpose
This is the most important screen after upload. It is where the user understands what
happened to the file.
## Page Content
The job detail page should show:
## A. Job Header
- original file name
- current status badge
- upload time
- job ID reference if needed
- document type if identified
## B. Processing Summary
A readable description of where the job stands:
- queued
- processing
- completed
- failed
C. Timeline or Stage View
A lightweight timeline showing major phases:
- uploaded
- stored
- processing started

- extraction complete
- output generated
- ready for download
For failed jobs, the timeline stops at the relevant stage.
## D. Output Area
If completed:
- clear download button for Excel output
- processed timestamp
- output-ready confirmation
If not completed:
- this area explains that output is not yet available
## E. Failure Area
If failed:
- show simple failure state
- do not expose raw stack traces to standard users
- provide a user-friendly message
- instruct that processing did not complete
Real-Time / Refresh Behavior
The page may update through polling or controlled refresh behavior. The user should not
be forced to repeatedly navigate away and back to see status changes.
Completed-State Behavior
Once a job is completed:
- the download action becomes primary
- the page should feel conclusive and successful

Failed-State Behavior
If a job fails:
- the status badge changes to failed
- the output area does not show a fake download
- the user sees a clear failure message
- only internal admin routes expose retry controls

## 14. Download Flow
There is no dedicated /downloads page in the MVP. Download is handled from:
- /dashboard surfaced completed jobs
## • /jobs
- /jobs/[jobId]
## Download Path
- Job reaches completed state
- Processed Excel file exists in S3 processed location
- Backend exposes authorized access to the output
- User clicks download
- File is downloaded through the app flow
UX Rules
- the download button appears only when the output is real and available
- download should not be visible for queued, processing, or failed states
- if access fails unexpectedly, show an error and preserve context on the same page
This prevents false confidence and broken user behavior.


## 15. Admin / Operator Flow
## 15.1 Route /admin/jobs
## Purpose
This page is for internal operational visibility across all jobs in the system.
## Access Control
Only internal admin/operator users may access this route.
## Page Content
This page includes:
- all jobs across users
- status visibility
- failure visibility
- ability to open admin detail
This is not a user-facing page and should not be linked for non-admin users.
15.2 Route /admin/jobs/[jobId]
## Purpose
This is the operator troubleshooting view.
## Content
This page can show more detail than the standard user detail screen, including:
- full job status history
- failure reason summary
- storage references
- backend stage markers
- retry action

## Retry Flow
- Admin opens failed job
- Confirms failure state
- Initiates retry
- Job re-enters queue/processing pipeline
- Status updates reflect the new attempt
Retry must exist only here, not on standard user pages.

- End-to-End User Paths
16.1 First-Time User Path
- User visits /
- Redirected to /login
- Signs in with Firebase
- Lands on /dashboard
- Sees empty state
## 6. Clicks Upload
- Goes to /upload
- Uploads PDF
- Redirected to /jobs/[jobId]
- Watches status move from queued/processing
- Returns later or stays on page
- Sees completed state
- Downloads Excel file
## 16.2 Returning User Path
- User visits /
- Redirected to /dashboard
- Sees recent jobs
- Opens latest completed job
- Downloads output

- Starts a new upload if needed
## 16.3 Failed Job Path
- User uploads valid PDF
- Job is created
- Job enters processing
- Extraction or validation fails
- Job status becomes failed
- User sees failed state on dashboard/jobs/detail
- User cannot self-retry in MVP
- Internal operator reviews in admin route
## 16.4 Admin Recovery Path
- Admin signs in
- Goes to /admin/jobs
- Filters or identifies failed job
- Opens /admin/jobs/[jobId]
- Reviews failure context
- Clicks retry
- Job returns to queued/processing state
- On success, output becomes downloadable

- Backend-Aware Flow Mapping
Even though this document is app-focused, the app flow must mirror actual backend
reality.
## Upload Phase
- user uploads PDF
- backend stores source file in S3 receiving folder
- PostgreSQL records job
- Lambda/Kafka pipeline begins

## Processing Phase
- Lambda retrieves source file
- Gemini extraction runs
- structured data is validated
- Excel output is generated
## Completion Phase
- Excel file is stored in S3 processed folder
- PostgreSQL job record is updated
- frontend sees completed state
- user downloads output
## Queue Resilience
Kafka exists so processing does not collapse when Lambda is unavailable or when async
backlog/batch handling is needed. The frontend should still show job-oriented status
rather than exposing infrastructure wording.

- What the App Must Not Do
To prevent implementation drift, the app flow must not imply any of the following:
- manual field editing before download
- document annotation
- chat with document
- model selection by end user
- arbitrary workflow builder
- schema designer UI
- public sharing links
- billing/subscription management
- multi-organization tenant administration
- custom report designer
- direct ERP push in MVP

If any of those appear in code generation, they should be treated as hallucinated scope.

## 19. Final Flow Definition
The official MVP app flow for PDFextract is:
## Entry → Login → Dashboard → Upload → Job Detail → Completed Download
with supporting history at /jobs and internal recovery through /admin/jobs.
That is the system.
Not a random SaaS shell.
Not a generic AI playground.
Not a feature buffet.
A user signs in, uploads a PDF, tracks a job, and downloads a structured Excel output
when processing completes. The UI exists to make that flow obvious, trustworthy, and
operationally usable.

