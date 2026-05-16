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
        return _mock_extract_invoice(prepared_pdf)
    return _mock_extract_report(prepared_pdf)


def _mock_extract_invoice(prepared_pdf: PreparedPdf) -> dict[str, Any]:
    full_text = prepared_pdf.full_text
    lines = [line.strip() for line in full_text.splitlines() if line.strip()]
    line_items: list[dict[str, str]] = []
    line_items.extend(_extract_line_items_from_pipe_lines(lines))
    line_items.extend(_extract_line_items_from_pdf_tables(prepared_pdf.tables))
    line_items.extend(_extract_line_items_from_text_rows(lines))
    line_items = _dedupe_line_items(line_items)

    invoice_number = _search_line_value(lines, ("Invoice Number", "Invoice #", "Invoice No"))
    if not invoice_number:
        invoice_number = _extract_invoice_number(full_text)

    invoice_date = _search_line_value(lines, ("Invoice Date", "Date"))
    if not invoice_date:
        invoice_date = _extract_labeled_date(full_text, ("invoice date", "date"))

    due_date = _search_line_value(lines, ("Due Date",))
    if not due_date:
        due_date = _extract_labeled_date(full_text, ("due date", "payment due"))

    total_amount = _search_line_value(lines, ("Total", "Amount Due", "Balance Due"))
    if not total_amount:
        total_amount = _extract_total_amount(full_text)

    vendor_name = _search_line_value(lines, ("Vendor", "From", "Supplier", "Seller"))
    if not vendor_name:
        vendor_name = _extract_vendor_name(lines)

    return {
        "vendor_name": vendor_name,
        "invoice_number": invoice_number,
        "invoice_date": invoice_date,
        "due_date": due_date,
        "currency": _extract_currency(lines, full_text) or "USD",
        "total_amount": total_amount,
        "line_items": line_items,
    }


def _extract_line_items_from_pipe_lines(lines: list[str]) -> list[dict[str, str]]:
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
    return line_items


def _extract_line_items_from_pdf_tables(
    tables: list[list[list[str | None]]],
) -> list[dict[str, str]]:
    line_items: list[dict[str, str]] = []
    for table in tables:
        if not table:
            continue
        header_row = [str(cell or "").strip().lower() for cell in table[0]]
        description_index = _find_header_index(header_row, ("description", "item", "service"))
        quantity_index = _find_header_index(header_row, ("qty", "quantity"))
        unit_price_index = _find_header_index(header_row, ("unit price", "rate", "price"))
        total_index = _find_header_index(header_row, ("amount", "line total", "total"))
        row_start = 1 if description_index is not None else 0

        for row in table[row_start:]:
            normalized_row = [str(cell or "").strip() for cell in row]
            if not any(normalized_row):
                continue

            description = _cell_at(normalized_row, description_index) or _cell_at(normalized_row, 0)
            quantity = _cell_at(normalized_row, quantity_index)
            unit_price = _cell_at(normalized_row, unit_price_index)
            line_total = _cell_at(normalized_row, total_index) or _cell_at(normalized_row, -1)

            if not description:
                continue
            has_numeric_cell = (
                _looks_numeric(quantity)
                or _looks_numeric(unit_price)
                or _looks_numeric(line_total)
            )
            if not has_numeric_cell:
                continue

            line_items.append(
                {
                    "description": description,
                    "quantity": quantity or "",
                    "unit_price": unit_price or "",
                    "line_total": line_total or "",
                }
            )
        line_items.extend(
            _extract_line_items_from_two_column_amount_table(
                table,
                description_index=description_index,
                total_index=total_index,
                row_start=row_start,
            )
        )
    return line_items


def _extract_line_items_from_two_column_amount_table(
    table: list[list[str | None]],
    *,
    description_index: int | None,
    total_index: int | None,
    row_start: int,
) -> list[dict[str, str]]:
    if not table:
        return []

    description_idx = description_index if description_index is not None else 0
    amount_idx = total_index
    if amount_idx is None:
        amount_idx = 1 if len(table[0]) > 1 else None
    if amount_idx is None:
        return []

    descriptions: list[str] = []
    amount_tokens: list[str] = []

    for row in table[row_start:]:
        normalized_row = [str(cell or "").strip() for cell in row]
        if not any(normalized_row):
            continue

        description = _cell_at(normalized_row, description_idx)
        if description and not _looks_like_summary_line(description):
            descriptions.append(description)

        amount_cell = _cell_at(normalized_row, amount_idx)
        if amount_cell:
            amount_tokens.extend(_extract_amount_tokens(amount_cell))

    if not descriptions or not amount_tokens:
        return []

    mapped_count = min(len(descriptions), len(amount_tokens))
    return [
        {
            "description": descriptions[index],
            "quantity": "",
            "unit_price": "",
            "line_total": amount_tokens[index],
        }
        for index in range(mapped_count)
    ]


def _extract_amount_tokens(value: str) -> list[str]:
    tokens: list[str] = []
    for match in re.finditer(r"\$?\s*\d[\d,\s]*\.\d{2}", value):
        token = match.group(0).replace("$", "")
        token = re.sub(r"(?<=\d)\s+(?=\d)", "", token)
        token = token.replace(",", "").strip()
        if token and _to_decimal_or_none(token):
            tokens.append(token)
    return tokens


def _extract_line_items_from_text_rows(lines: list[str]) -> list[dict[str, str]]:
    line_items: list[dict[str, str]] = []
    for line in lines:
        if "|" in line:
            continue
        if _looks_like_summary_line(line):
            continue
        match = re.search(
            r"^(?P<description>.+?)\s+(?P<quantity>\d+(?:\.\d+)?)\s+"
            r"(?P<unit_price>\$?\d[\d,]*(?:\.\d{1,2})?)\s+"
            r"(?P<line_total>\$?\d[\d,]*(?:\.\d{1,2})?)$",
            line,
        )
        if not match:
            continue
        groups = match.groupdict()
        line_items.append(
            {
                "description": groups["description"].strip(),
                "quantity": groups["quantity"].strip(),
                "unit_price": groups["unit_price"].strip(),
                "line_total": groups["line_total"].strip(),
            }
        )
    return line_items


def _dedupe_line_items(items: list[dict[str, str]]) -> list[dict[str, str]]:
    seen: set[tuple[str, str, str, str]] = set()
    deduped: list[dict[str, str]] = []
    for item in items:
        key = (
            str(item.get("description") or "").strip().lower(),
            str(item.get("quantity") or "").strip(),
            str(item.get("unit_price") or "").strip(),
            str(item.get("line_total") or "").strip(),
        )
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)
    return deduped


def _find_header_index(header_row: list[str], options: tuple[str, ...]) -> int | None:
    for index, value in enumerate(header_row):
        for option in options:
            if option in value:
                return index
    return None


def _cell_at(values: list[str], index: int | None) -> str | None:
    if index is None:
        return None
    if index < 0:
        index = len(values) + index
    if index < 0 or index >= len(values):
        return None
    value = values[index].strip()
    return value or None


def _extract_invoice_number(full_text: str) -> str | None:
    labeled_match = re.search(
        r"\binvoice\s*(?:number|no\.?|#|id)\s*[:#-]?\s*([A-Z0-9][A-Z0-9\-\/]{0,})",
        full_text,
        flags=re.IGNORECASE,
    )
    if labeled_match:
        candidate = labeled_match.group(1).strip()
        if re.search(r"\d", candidate):
            return candidate

    token_match = re.search(r"\bINV[-/ ]?\d[\w/-]*\b", full_text, flags=re.IGNORECASE)
    return token_match.group(0).strip() if token_match else None


def _extract_labeled_date(full_text: str, labels: tuple[str, ...]) -> str | None:
    month_pattern = (
        r"(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|"
        r"aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)"
    )
    date_pattern = (
        rf"(\d{{4}}-\d{{1,2}}-\d{{1,2}}|\d{{1,2}}[/-]\d{{1,2}}[/-]\d{{2,4}}|"
        rf"{month_pattern}\s+\d{{1,2}},?\s+\d{{4}})"
    )
    for label in labels:
        match = re.search(
            rf"{re.escape(label)}\s*[:#-]?\s*{date_pattern}",
            full_text,
            flags=re.IGNORECASE,
        )
        if match:
            return match.group(1).strip()
    return None


def _extract_total_amount(full_text: str) -> str | None:
    match = re.search(
        r"(?:total|amount due|balance due)\s*[:#-]?\s*([$]?\d[\d,]*(?:\.\d{1,2})?)",
        full_text,
        flags=re.IGNORECASE,
    )
    return match.group(1).strip() if match else None


def _extract_currency(lines: list[str], full_text: str) -> str | None:
    declared = _search_line_value(lines, ("Currency", "Curr"))
    if declared:
        return declared.strip().upper()

    currency_match = re.search(
        r"\b(USD|EUR|GBP|INR|CAD|AUD|JPY)\b",
        full_text,
        flags=re.IGNORECASE,
    )
    return currency_match.group(1).upper() if currency_match else None


def _extract_vendor_name(lines: list[str]) -> str | None:
    for line in lines[:6]:
        lowered = line.lower()
        if any(
            token in lowered
            for token in ("invoice", "bill to", "invoice no", "invoice number", "date", "due")
        ):
            continue
        if len(line.split()) >= 2:
            return line.strip()
    return None


def _looks_numeric(value: str | None) -> bool:
    if value is None:
        return False
    return _to_decimal_or_none(value) is not None


def _looks_like_summary_line(line: str) -> bool:
    lowered = line.lower()
    summary_tokens = ("total", "subtotal", "tax", "amount due", "balance due")
    return any(token in lowered for token in summary_tokens)


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
    for index, line in enumerate(lines):
        normalized = line.strip()
        if not normalized:
            continue
        lowered = normalized.lower()

        for label in labels:
            label_lower = label.lower()
            if lowered.startswith(label_lower):
                suffix = normalized[len(label) :].strip()
                suffix = re.sub(r"^[:#\-\s]+", "", suffix).strip()
                if suffix:
                    return suffix

                for next_index in range(index + 1, len(lines)):
                    candidate = lines[next_index].strip()
                    if not candidate:
                        continue
                    if _looks_like_label_line(candidate):
                        break
                    return candidate
                break
    return None


def _looks_like_label_line(line: str) -> bool:
    return bool(re.match(r"^[A-Za-z][A-Za-z0-9\s/#-]{0,40}:?$", line.strip()))


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
