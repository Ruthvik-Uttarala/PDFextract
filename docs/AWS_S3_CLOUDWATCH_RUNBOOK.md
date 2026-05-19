# AWS S3 and CloudWatch Runbook (Current Scope)

This runbook covers the parts that can be completed with current access:

- S3 artifact storage under `receiving/` and `processed/`
- CloudWatch dashboard setup for S3 visibility

This does **not** claim final AWS production completion for backend compute, database, queue, or secrets.

## Required Environment Variables

Backend runtime:

- `AWS_REGION=us-east-2`
- `S3_BUCKET_NAME=pdfextract-artifacts-814117164451-us-east-2`
- `RECEIVING_PREFIX=receiving`
- `PROCESSED_PREFIX=processed`
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`

## Artifact Key Contract

Source upload:

- `receiving/{user_id}/{job_id}/source.pdf`

Processed outputs:

- `processed/{user_id}/{job_id}/output.xlsx`
- `processed/{user_id}/{job_id}/result.json`
- `processed/{user_id}/{job_id}/text.txt`
- `processed/{user_id}/{job_id}/tables/table_1.csv` (and table_n variants)
- `processed/{user_id}/{job_id}/images/image_1.png` (real extracted images only)

## S3 Smoke Test

Command:

```powershell
./scripts/smoke-s3-artifacts.ps1 -Cleanup
```

What it does:

1. Writes a source artifact using `put_source_pdf` under `receiving/{user_id}/{job_id}/source.pdf`.
2. Writes a processed JSON artifact under `processed/{user_id}/{job_id}/result.json`.
3. Verifies both keys exist.
4. Deletes them when `-Cleanup` is passed.

## CloudWatch Dashboard Setup

Command:

```powershell
./scripts/setup-cloudwatch-dashboard.ps1
```

Default dashboard:

- Name: `PDFextract-Storage`
- Region: `us-east-2`
- Widgets:
  - `AWS/S3 NumberOfObjects` (`AllStorageTypes`)
  - `AWS/S3 BucketSizeBytes` (`StandardStorage`)

## Alarm Notes

Current script creates a dashboard only. S3 request-error alarms are optional and require request metrics enabled on the bucket.

Enable request metrics path:

1. AWS Console
2. `S3`
3. `Buckets`
4. `pdfextract-artifacts-814117164451-us-east-2`
5. `Metrics`
6. `Request metrics` -> `Enable`

Then create alarms path:

1. AWS Console
2. `CloudWatch`
3. `Alarms`
4. `Create alarm`
5. Namespace `AWS/S3`
6. Select request metrics (4xx/5xx) for the bucket

## Common Blockers and Exact Fix Path

Missing credentials:

- Symptom: `Unable to locate credentials` or `InvalidClientTokenId`
- Fix:
  - set `AWS_ACCESS_KEY_ID`
  - set `AWS_SECRET_ACCESS_KEY`
  - optionally run `aws sts get-caller-identity --region us-east-2`

Missing CloudWatch dashboard permission:

- Symptom: `AccessDenied` on `cloudwatch:PutDashboard`
- Fix path:
  - AWS Console -> IAM -> Users/Roles -> active principal -> Add permission containing:
    - `cloudwatch:PutDashboard`
    - `cloudwatch:GetDashboard`

Missing S3 write permission:

- Symptom: `AccessDenied` on `s3:PutObject`
- Fix path:
  - AWS Console -> IAM -> Users/Roles -> active principal -> Add permission containing:
    - `s3:PutObject`
    - `s3:GetObject`
    - `s3:HeadObject`
    - `s3:DeleteObject` (for cleanup mode)
  - Resource scope includes bucket:
    - `arn:aws:s3:::pdfextract-artifacts-814117164451-us-east-2/*`
