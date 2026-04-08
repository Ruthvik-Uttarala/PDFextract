. "$PSScriptRoot\\common.ps1"

Assert-DockerDaemon
$repoRoot = Get-RepoRoot
$mount = "${repoRoot}:/repo"

$backendCommand = "python -m pip install --upgrade pip && pip install -r requirements.txt && python -m ruff check . && python -m black --check . && python -m mypy app && python -m app.cli check-db && python -m app.cli ensure-storage && python -m app.cli check-storage-layout --user-id smoke-user --job-id smoke-job && python -m app.cli ensure-kafka-topics && python -m app.cli smoke-firebase && python -m app.cli smoke-http"

docker run --rm `
  --network pdfextract_default `
  -v $mount `
  -w /repo/backend `
  -e APP_ENV=local `
  -e DATABASE_URL=postgresql://pdfextract:pdfextract@postgres:5432/pdfextract `
  -e S3_BUCKET_NAME=pdfextract-local `
  -e S3_ENDPOINT_URL=http://minio:9000 `
  -e AWS_ACCESS_KEY_ID=minioadmin `
  -e AWS_SECRET_ACCESS_KEY=minioadmin `
  -e KAFKA_BOOTSTRAP_SERVERS=kafka:29092 `
  -e FIREBASE_PROJECT_ID=pdfextract-local `
  -e RECEIVING_PREFIX=receiving `
  -e PROCESSED_PREFIX=processed `
  -e GEMINI_MODEL_NAME=gemini-1.5-pro `
  python:3.11.11-slim sh -lc $backendCommand
