from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any

from app.core import DocumentType


@dataclass(frozen=True)
class ValidationResult:
    valid: bool
    errors: list[dict[str, object]]


def validate_normalized_output(normalized_json: dict[str, Any]) -> ValidationResult:
    document_type = str(normalized_json.get("document_type") or "")
    if document_type == DocumentType.INVOICE:
        return _validate_invoice(normalized_json)
    return _validate_report(normalized_json)


def _validate_invoice(normalized_json: dict[str, Any]) -> ValidationResult:
    errors: list[dict[str, object]] = []
    total_amount = normalized_json.get("total_amount")
    if total_amount not in (None, "") and not _is_decimal(total_amount):
        errors.append({"field": "total_amount", "message": "Total amount must be numeric."})

    line_items = normalized_json.get("line_items")
    if not isinstance(line_items, list) or not line_items:
        errors.append({"field": "line_items", "message": "At least one line item is required."})
    else:
        for index, item in enumerate(line_items):
            if not isinstance(item, dict):
                errors.append(
                    {"field": f"line_items[{index}]", "message": "Line item must be an object."}
                )
                continue
            if not item.get("description"):
                errors.append(
                    {
                        "field": f"line_items[{index}].description",
                        "message": "Description is required.",
                    }
                )
            for numeric_field in ("quantity", "unit_price", "line_total"):
                value = item.get(numeric_field)
                if value is not None and not _is_decimal(value):
                    errors.append(
                        {
                            "field": f"line_items[{index}].{numeric_field}",
                            "message": "Value must be numeric.",
                        }
                    )

    has_invoice_number = bool(_text(normalized_json.get("invoice_number")))
    has_invoice_date = bool(_text(normalized_json.get("invoice_date")))
    if not has_invoice_number and not has_invoice_date:
        errors.append(
            {
                "field": "invoice_number|invoice_date",
                "message": "Either invoice number or invoice date is required.",
            }
        )

    has_total_amount = total_amount not in (None, "")
    has_line_totals = any(
        isinstance(item, dict) and item.get("line_total") not in (None, "")
        for item in (line_items if isinstance(line_items, list) else [])
    )
    if not has_total_amount and not has_line_totals:
        errors.append(
            {
                "field": "total_amount|line_items.line_total",
                "message": "A total amount or at least one line total is required.",
            }
        )

    return ValidationResult(valid=not errors, errors=errors)


def _validate_report(normalized_json: dict[str, Any]) -> ValidationResult:
    errors: list[dict[str, object]] = []
    if not normalized_json.get("title"):
        errors.append({"field": "title", "message": "Title is required."})

    sections = normalized_json.get("sections")
    if not isinstance(sections, list) or not sections:
        errors.append({"field": "sections", "message": "At least one section is required."})
    else:
        for index, section in enumerate(sections):
            if not isinstance(section, dict):
                errors.append(
                    {"field": f"sections[{index}]", "message": "Section must be an object."}
                )
                continue
            if not section.get("heading"):
                errors.append(
                    {"field": f"sections[{index}].heading", "message": "Heading is required."}
                )

    return ValidationResult(valid=not errors, errors=errors)


def _is_decimal(value: object) -> bool:
    try:
        Decimal(str(value))
    except (InvalidOperation, ValueError):
        return False
    return True


def _text(value: object) -> str:
    return str(value).strip() if value is not None else ""
