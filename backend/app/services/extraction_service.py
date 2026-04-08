from __future__ import annotations

import json
import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any

import google.auth
import requests  # type: ignore[import-untyped]
from google.auth.transport.requests import Request as GoogleAuthRequest

from app.core import DocumentType, FailureCode, Settings
from app.core.errors import ApiError
from app.services.pdf_reader_service import PreparedPdf, extract_headings

SCHEMA_VERSION = "2026-04-08"


@dataclass(frozen=True)
class ExtractionPayload:
    document_type: str
    schema_version: str
    extracted_json: dict[str, Any]
    normalized_json: dict[str, Any]


def extract_document_data(settings: Settings, prepared_pdf: PreparedPdf) -> ExtractionPayload:
    if settings.gemini_mock_mode or not settings.gemini_project_id:
        extracted_json = _mock_extract(prepared_pdf)
    else:
        extracted_json = _call_gemini(settings, prepared_pdf)

    normalized_json = normalize_extraction_output(
        document_type=prepared_pdf.document_type,
        extracted_json=extracted_json,
        prepared_pdf=prepared_pdf,
    )
    return ExtractionPayload(
        document_type=prepared_pdf.document_type,
        schema_version=SCHEMA_VERSION,
        extracted_json=extracted_json,
        normalized_json=normalized_json,
    )


def normalize_extraction_output(
    *,
    document_type: str,
    extracted_json: dict[str, Any],
    prepared_pdf: PreparedPdf,
) -> dict[str, Any]:
    if document_type == DocumentType.INVOICE:
        line_items = extracted_json.get("line_items") or []
        normalized_items = [
            {
                "description": str(item.get("description") or "").strip(),
                "quantity": _to_decimal_or_none(item.get("quantity")),
                "unit_price": _to_decimal_or_none(item.get("unit_price")),
                "line_total": _to_decimal_or_none(item.get("line_total")),
            }
            for item in line_items
            if isinstance(item, dict)
        ]
        return {
            "document_type": DocumentType.INVOICE,
            "vendor": {"name": _clean(extracted_json.get("vendor_name"))},
            "invoice_number": _clean(extracted_json.get("invoice_number")),
            "invoice_date": _clean(extracted_json.get("invoice_date")),
            "due_date": _clean(extracted_json.get("due_date")),
            "currency": _clean(extracted_json.get("currency")) or "USD",
            "total_amount": _to_decimal_or_none(extracted_json.get("total_amount")),
            "line_items": normalized_items,
        }

    sections = extracted_json.get("sections")
    normalized_sections: list[dict[str, str]] = []
    if isinstance(sections, list):
        for section in sections:
            if isinstance(section, dict):
                heading = _clean(section.get("heading"))
                content = _clean(section.get("content"))
                if heading or content:
                    normalized_sections.append(
                        {"heading": heading or "Section", "content": content or ""}
                    )

    if not normalized_sections:
        normalized_sections = [
            {"heading": heading, "content": ""}
            for heading in extract_headings(prepared_pdf.full_text)
        ]

    return {
        "document_type": DocumentType.RESEARCH_REPORT,
        "title": _clean(extracted_json.get("title")),
        "authors": _coerce_string_list(extracted_json.get("authors")),
        "published_date": _clean(extracted_json.get("published_date")),
        "sections": normalized_sections,
        "table_count": len(prepared_pdf.tables),
    }


def _mock_extract(prepared_pdf: PreparedPdf) -> dict[str, Any]:
    if prepared_pdf.document_type == DocumentType.INVOICE:
        return _mock_extract_invoice(prepared_pdf.full_text)
    return _mock_extract_report(prepared_pdf)


def _mock_extract_invoice(full_text: str) -> dict[str, Any]:
    lines = [line.strip() for line in full_text.splitlines() if line.strip()]
    line_items: list[dict[str, str]] = []
    for line in lines:
        if "|" not in line:
            continue
        parts = [part.strip() for part in line.split("|")]
        if len(parts) != 4:
            continue
        description, quantity, unit_price, line_total = parts
        line_items.append(
            {
                "description": description,
                "quantity": quantity,
                "unit_price": unit_price,
                "line_total": line_total,
            }
        )

    return {
        "vendor_name": _search_line_value(lines, ("Vendor", "From", "Supplier")),
        "invoice_number": _search_line_value(lines, ("Invoice Number", "Invoice #")),
        "invoice_date": _search_line_value(lines, ("Invoice Date", "Date")),
        "due_date": _search_line_value(lines, ("Due Date",)),
        "currency": _search_line_value(lines, ("Currency",)) or "USD",
        "total_amount": _search_line_value(lines, ("Total", "Amount Due")),
        "line_items": line_items,
    }


def _mock_extract_report(prepared_pdf: PreparedPdf) -> dict[str, Any]:
    lines = [line.strip() for line in prepared_pdf.full_text.splitlines() if line.strip()]
    sections = [
        {"heading": heading, "content": ""} for heading in extract_headings(prepared_pdf.full_text)
    ]
    authors_line = _search_line_value(lines, ("Author", "Authors"))
    authors = [part.strip() for part in authors_line.split(",")] if authors_line else []

    return {
        "title": (
            _search_line_value(lines, ("Title",)) or (lines[0] if lines else "Untitled Report")
        ),
        "authors": [author for author in authors if author],
        "published_date": _search_line_value(lines, ("Published", "Published Date", "Date")),
        "sections": sections,
    }


def _call_gemini(settings: Settings, prepared_pdf: PreparedPdf) -> dict[str, Any]:
    access_token = _get_google_access_token()
    endpoint = (
        f"https://{settings.gemini_location}-aiplatform.googleapis.com/v1/projects/"
        f"{settings.gemini_project_id}/locations/{settings.gemini_location}/publishers/google/models/"
        f"{settings.gemini_model_name}:generateContent"
    )
    prompt = _build_gemini_prompt(prepared_pdf)

    response = requests.post(
        endpoint,
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        },
        json={
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0,
                "responseMimeType": "application/json",
            },
        },
        timeout=60,
    )
    if response.status_code >= 400:
        raise ApiError(
            code=FailureCode.GEMINI_REQUEST_FAILED,
            message="Gemini extraction failed.",
            details={"status_code": response.status_code, "response": response.text[:500]},
        )

    payload = response.json()
    try:
        text = payload["candidates"][0]["content"]["parts"][0]["text"]
        return _parse_json_response(text)
    except Exception as exc:
        raise ApiError(
            code=FailureCode.EXTRACTION_PARSE_FAILED,
            message="Gemini returned an unreadable extraction payload.",
            details={"reason": str(exc)},
        ) from exc


def _build_gemini_prompt(prepared_pdf: PreparedPdf) -> str:
    if prepared_pdf.document_type == DocumentType.INVOICE:
        return (
            "Extract structured invoice data from the following PDF text. "
            "Return JSON with keys vendor_name, invoice_number, invoice_date, due_date, "
            "currency, total_amount, and line_items "
            "(description, quantity, unit_price, line_total).\n\n"
            f"{prepared_pdf.full_text}"
        )

    return (
        "Extract structured research/report data from the following PDF text. "
        "Return JSON with keys title, authors, published_date, and sections "
        "(heading, content).\n\n"
        f"{prepared_pdf.full_text}"
    )


def _get_google_access_token() -> str:
    credentials, _project_id = google.auth.default(
        scopes=["https://www.googleapis.com/auth/cloud-platform"]
    )
    credentials.refresh(GoogleAuthRequest())
    token = getattr(credentials, "token", None)
    if not token:
        raise ApiError(
            code=FailureCode.GEMINI_REQUEST_FAILED,
            message="Gemini credentials are not available.",
        )
    return str(token)


def _parse_json_response(text: str) -> dict[str, Any]:
    fenced = re.search(r"```json\s*(\{.*\})\s*```", text, re.DOTALL)
    raw = fenced.group(1) if fenced else text
    parsed = json.loads(raw)
    if not isinstance(parsed, dict):
        raise ValueError("Gemini response was not a JSON object")
    return parsed


def _search_line_value(lines: list[str], labels: tuple[str, ...]) -> str | None:
    for line in lines:
        for label in labels:
            prefix = f"{label}:"
            if line.lower().startswith(prefix.lower()):
                return line[len(prefix) :].strip()
    return None


def _clean(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _coerce_string_list(value: object) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if value is None:
        return []
    return [part.strip() for part in str(value).split(",") if part.strip()]


def _to_decimal_or_none(value: object) -> str | None:
    if value is None or value == "":
        return None
    try:
        cleaned = str(value).replace("$", "").replace(",", "").strip()
        return format(Decimal(cleaned), "f")
    except (InvalidOperation, ValueError):
        return None
