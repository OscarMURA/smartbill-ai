"""Shared parser result and adapter selection."""
from dataclasses import dataclass
from uuid import UUID, uuid4

from app.schemas.invoice import InvoiceOut


@dataclass
class ParseResult:
    invoice: InvoiceOut
    warnings: list[str]


def parse_invoice(
    text: str,
    *,
    invoice_id: UUID | None = None,
    collection_id: UUID | None = None,
    source: str = "synthetic",
) -> ParseResult:
    """Choose the synthetic template parser when its explicit marker exists."""
    from .generic import parse_generic
    from .synthetic import parse_synthetic

    parser = parse_synthetic if "DATOS SINTÉTICOS DE DEMOSTRACIÓN" in text.upper() else parse_generic
    return parser(
        text,
        invoice_id=invoice_id or uuid4(),
        collection_id=collection_id or uuid4(),
        source=source,
    )
