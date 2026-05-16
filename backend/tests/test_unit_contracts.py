from __future__ import annotations

from io import BytesIO

from openpyxl import load_workbook

from app.core import FailureCode, JobStage, JobStatus, Settings
from app.db import session_scope
from app.db.repositories import (
    create_job,
    create_processing_attempt,
    get_job,
    mark_attempt_failed,
    mark_job_completed,
    mark_job_failed,
    mark_job_processing,
    upsert_user_from_claims,
)
from app.services.excel_service import generate_excel_workbook
from app.services.extraction_service import _mock_extract_invoice
from app.services.firebase_service import verify_token
from app.services.pdf_reader_service import PreparedPdf
from app.services.storage_service import build_processed_key, build_source_key
from app.services.validation_service import validate_normalized_output


def test_verify_token_accepts_deterministic_test_token() -> None:
    settings = Settings(
        app_env="test",
        firebase_project_id="pdfextract-local",
        firebase_test_id_token="unit-test-token",
        firebase_test_uid="unit-user",
        firebase_test_email="unit@example.com",
        firebase_test_name="Unit User",
    )

    claims = verify_token(settings, "unit-test-token")

    assert claims["uid"] == "unit-user"
    assert claims["email"] == "unit@example.com"
    assert claims["aud"] == "pdfextract-local"


def test_storage_key_builders_follow_canonical_contract(settings: Settings) -> None:
    assert (
        build_source_key(settings, "user-123", "job-456") == "receiving/user-123/job-456/source.pdf"
    )
    assert (
        build_processed_key(settings, "user-123", "job-456")
        == "processed/user-123/job-456/output.xlsx"
    )


def test_validation_rejects_invalid_invoice_output() -> None:
    result = validate_normalized_output(
        {
            "document_type": "invoice",
            "vendor": {"name": ""},
            "invoice_number": None,
            "invoice_date": "",
            "total_amount": "not-a-number",
            "line_items": [{"description": "", "quantity": "x"}],
        }
    )

    assert result.valid is False
    assert any(error["field"] == "invoice_number|invoice_date" for error in result.errors)
    assert any(error["field"] == "total_amount" for error in result.errors)


def test_validation_accepts_invoice_with_optional_header_gaps() -> None:
    result = validate_normalized_output(
        {
            "document_type": "invoice",
            "vendor": {"name": None},
            "invoice_number": None,
            "invoice_date": "05/10/2026",
            "total_amount": None,
            "line_items": [
                {
                    "description": "Consulting",
                    "quantity": "1",
                    "unit_price": "1200.00",
                    "line_total": "1200.00",
                }
            ],
        }
    )

    assert result.valid is True


def test_mock_invoice_extraction_handles_split_labels_and_two_column_table() -> None:
    prepared_pdf = PreparedPdf(
        page_count=1,
        pages=[],
        full_text=(
            "INVOICE\n"
            "DATE:\n"
            "July 8, 2011\n"
            "INVOICE #\n"
            "4\n"
            "Vendor Name\n"
            "TOTAL\n"
            "567.50\n"
            "DESCRIPTION\n"
            "Laundry service (Linens) from April, 2011 (42 x $11)\n"
            "Laundry service (towels) from April 2011 (71 pieces x $.50)\n"
            "Laundry service (Aprons) from April 2011 (10 pieces x $7)\n"
        ),
        tables=[
            [
                ["DESCRIPTION", "AMOUNT"],
                [
                    "Laundry service (Linens) from April, 2011 (42 x $11)",
                    "$ 4 62.00\n3 5.50\n7 0.00",
                ],
                ["Laundry service (towels) from April 2011 (71 pieces x $.50)", None],
                ["Laundry service (Aprons) from April 2011 (10 pieces x $7)", None],
            ]
        ],
        document_type="invoice",
    )

    extracted = _mock_extract_invoice(prepared_pdf)
    normalized = {
        "document_type": "invoice",
        "vendor": {"name": extracted.get("vendor_name")},
        "invoice_number": extracted.get("invoice_number"),
        "invoice_date": extracted.get("invoice_date"),
        "total_amount": extracted.get("total_amount"),
        "line_items": extracted.get("line_items"),
    }
    validation = validate_normalized_output(normalized)

    assert extracted["invoice_number"] == "4"
    assert extracted["invoice_date"] == "July 8, 2011"
    assert extracted["total_amount"] == "567.50"
    assert len(extracted["line_items"]) >= 3
    assert validation.valid is True


def test_excel_generation_creates_expected_invoice_workbook() -> None:
    workbook_bytes, sheet_names = generate_excel_workbook(
        job_id="job-123",
        source_filename="invoice.pdf",
        normalized_json={
            "document_type": "invoice",
            "vendor": {"name": "Northwind"},
            "invoice_number": "INV-1001",
            "invoice_date": "2026-04-08",
            "total_amount": "3000.00",
            "line_items": [
                {
                    "description": "Consulting Services",
                    "quantity": "2",
                    "unit_price": "1500.00",
                    "line_total": "3000.00",
                }
            ],
        },
    )

    workbook = load_workbook(BytesIO(workbook_bytes))

    assert "Summary" in sheet_names
    assert "Traceability" in sheet_names
    assert "Line Items" in sheet_names
    assert workbook["Traceability"]["B1"].value == "job-123"


def test_job_state_transitions_follow_canonical_statuses(settings: Settings) -> None:
    with session_scope(settings) as session:
        user = upsert_user_from_claims(
            session,
            claims={"uid": "state-user", "email": "state@example.com", "name": "State User"},
            admin_email_allowlist=set(),
        )
        job = create_job(session, user_id=user.id, source_filename="invoice.pdf")
        attempt = create_processing_attempt(
            session,
            job_id=job.id,
            attempt_number=1,
            trigger_type="initial",
            status=JobStatus.QUEUED,
        )

        mark_job_processing(
            session,
            job=job,
            attempt_id=attempt.id,
            current_stage=JobStage.WORKER_STARTED,
        )
        assert job.job_status == JobStatus.PROCESSING
        assert job.current_stage == JobStage.WORKER_STARTED

        mark_attempt_failed(
            session,
            attempt=attempt,
            failure_code=FailureCode.GEMINI_REQUEST_FAILED,
            failure_message="Gemini failed.",
        )
        mark_job_failed(
            session,
            job=job,
            attempt_id=attempt.id,
            current_stage=JobStage.GEMINI_EXTRACTION,
            failure_code=FailureCode.GEMINI_REQUEST_FAILED,
            failure_message="Gemini failed.",
            retryable=True,
        )
        assert job.job_status == JobStatus.FAILED
        assert job.failure_code == FailureCode.GEMINI_REQUEST_FAILED

        mark_job_completed(
            session,
            job=job,
            attempt_id=attempt.id,
            current_stage=JobStage.COMPLETION_PERSISTED,
        )

    with session_scope(settings) as verification_session:
        persisted_job = get_job(verification_session, job.id)
        assert persisted_job is not None
        assert persisted_job.job_status == JobStatus.COMPLETED
        assert persisted_job.current_stage == JobStage.COMPLETION_PERSISTED
