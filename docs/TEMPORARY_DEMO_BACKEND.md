# Temporary Demo Backend

This MVP deployment uses a temporary non-AWS backend host to unblock testing.

## Scope

- Host: separate Vercel project (`pdfextract-backend-demo`)
- Runtime mode: `DEMO_MODE=true`
- Auth: demo identity (`demo-mvp-user`) without Firebase login gate
- Queue: inline (`QUEUE_BACKEND=inline`)
- Storage: local runtime filesystem (`STORAGE_BACKEND=local`, `/tmp/pdfextract-storage`)
- Database: SQLite (`DATABASE_URL=sqlite:////tmp/pdfextract-demo.db`, `AUTO_INIT_DB=true`)
- Extraction ownership: backend only (PDF read, extraction wrapper, validation, result shaping, workbook generation)

## Why Temporary

- The canonical production architecture requires AWS App Runner/ECS + S3 + Kafka + Lambda + PostgreSQL + Gemini credentials.
- This temporary setup is only for MVP unblock and feature validation.

## Known Limitations

- Runtime-local filesystem and SQLite are not durable like managed AWS services.
- Multi-instance consistency is not guaranteed in this temporary mode.
- Final production must migrate to the approved AWS architecture.

## Planned Production Migration

Move backend runtime and dependencies to:

- AWS App Runner or ECS (Flask API)
- Amazon S3 (source and processed artifacts)
- Kafka-compatible managed broker (job events)
- AWS Lambda worker for async processing
- Managed PostgreSQL
- Gemini credentials via secure secret management

