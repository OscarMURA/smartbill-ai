"""Parser for the project's explicitly marked synthetic invoice template."""
from __future__ import annotations

from uuid import UUID

from app.schemas.invoice import InvoiceOut
from .base import ParseResult
from .generic import parse_generic


def parse_synthetic(text: str, *, invoice_id: UUID, collection_id: UUID, source: str = "synthetic") -> ParseResult:
    # The generated fixtures use the conservative generic field recognizers;
    # this adapter is the explicit template hook for future synthetic changes.
    parsed = parse_generic(text, invoice_id=invoice_id, collection_id=collection_id, source=source)
    if parsed.invoice.billing_period is None:
        warning = "No se pudo identificar el período de facturación en el documento."
        if warning not in parsed.warnings:
            parsed.warnings.append(warning)
    if parsed.invoice.warnings != parsed.warnings:
        parsed.invoice = InvoiceOut(**{**parsed.invoice.model_dump(), "warnings": parsed.warnings})
    return parsed
