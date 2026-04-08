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
    required_fields = {
        "vendor.name": (
            normalized_json.get("vendor", {}).get("name")
            if isinstance(normalized_json.get("vendor"), dict)
            else None
        ),
        "invoice_number": normalized_json.get("invoice_number"),
        "invoice_date": normalized_json.get("invoice_date"),
        "total_amount": normalized_json.get("total_amount"),
    }
    for field, value in required_fields.items():
        if value in (None, "", []):
            errors.append({"field": field, "message": "This field is required."})

    total_amount = normalized_json.get("total_amount")
    if total_amount is not None and not _is_decimal(total_amount):
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
