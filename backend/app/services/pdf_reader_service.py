from __future__ import annotations

import io
import re
from dataclasses import dataclass

import fitz
import pdfplumber

from app.core import DocumentType, FailureCode
from app.core.errors import ApiError


@dataclass(frozen=True)
class PreparedPdf:
    page_count: int
    pages: list[str]
    full_text: str
    tables: list[list[list[str | None]]]
    document_type: str


def read_pdf_document(pdf_bytes: bytes, *, source_filename: str | None = None) -> PreparedPdf:
    try:
        document = fitz.open(stream=pdf_bytes, filetype="pdf")
    except Exception as exc:
        raise ApiError(
            code=FailureCode.PDF_READ_FAILED,
            message="The PDF could not be opened for processing.",
            details={"reason": str(exc)},
        ) from exc

    pages: list[str] = []
    try:
        for page in document:
            text = page.get_text("text").strip()
            pages.append(text)
    finally:
        document.close()

    full_text = "\n\n".join(filter(None, pages)).strip()
    if not full_text:
        raise ApiError(
            code=FailureCode.PDF_READ_FAILED,
            message="The PDF does not contain readable text.",
        )

    tables = _extract_tables(pdf_bytes)
    document_type = classify_document_type(full_text=full_text, source_filename=source_filename)
    return PreparedPdf(
        page_count=len(pages),
        pages=pages,
        full_text=full_text,
        tables=tables,
        document_type=document_type,
    )


def classify_document_type(*, full_text: str, source_filename: str | None) -> str:
    haystack = f"{source_filename or ''}\n{full_text}".lower()

    invoice_signals = (
        "invoice",
        "invoice number",
        "bill to",
        "due date",
        "line item",
        "subtotal",
        "total",
    )
    report_signals = (
        "abstract",
        "executive summary",
        "introduction",
        "conclusion",
        "references",
        "research report",
    )

    invoice_score = sum(1 for signal in invoice_signals if signal in haystack)
    report_score = sum(1 for signal in report_signals if signal in haystack)

    if invoice_score >= report_score:
        return DocumentType.INVOICE
    return DocumentType.RESEARCH_REPORT


def extract_headings(full_text: str) -> list[str]:
    headings: list[str] = []
    for line in full_text.splitlines():
        candidate = line.strip()
        if not candidate:
            continue
        if candidate.isupper() or re.match(r"^\d+(\.\d+)*\s+[A-Z]", candidate):
            headings.append(candidate)
    return headings


def _extract_tables(pdf_bytes: bytes) -> list[list[list[str | None]]]:
    tables: list[list[list[str | None]]] = []
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for page in pdf.pages:
            extracted = page.extract_tables() or []
            for table in extracted:
                if table:
                    tables.append(table)
    return tables
