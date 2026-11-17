"""Conservative generic invoice parser; missing data remains null."""
from __future__ import annotations

import re
from datetime import date
from decimal import Decimal
from uuid import UUID

from app.schemas.invoice import InvoiceOut, LineItem
from .base import ParseResult

_MONEY = r"(?:COP\s*)?\$?\s*([\d.]+(?:,\d{1,2})?)"


def _amount(value: str) -> int | None:
    normalized = value.replace(".", "").replace(",", ".")
    try:
        return int(Decimal(normalized).quantize(Decimal("1")))
    except Exception:
        return None


def _first(patterns: tuple[str, ...], text: str, flags: int = re.IGNORECASE) -> str | None:
    for pattern in patterns:
        match = re.search(pattern, text, flags)
        if match:
            return match.group(1).strip()
    return None


def parse_generic(text: str, *, invoice_id: UUID, collection_id: UUID, source: str = "local_upload") -> ParseResult:
    warnings: list[str] = []
    period = _first((r"(?:periodo|per[ií]odo)(?:\s+de\s+facturaci[oó]n)?\s*[:\-]\s*([^\n]+)",), text)
    issued_raw = _first((r"fecha\s+de\s+emisi[oó]n\s*[:\-]\s*(\d{4}-\d{2}-\d{2})",), text)
    due_raw = _first((r"fecha\s+l[ií]mite\s+de\s+pago\s*[:\-]\s*(\d{4}-\d{2}-\d{2})",), text)
    consumption_raw = _first((r"consumo(?:\s+del\s+periodo)?\s*[:\-]\s*([\d.,]+)\s*(?:m[³3])",), text)
    total_raw = _first((rf"(?:total(?:\s+(?:facturado|ficticio))?|valor\s+total)\s*[:\-]?\s*{_MONEY}",), text)
    fixed_raw = _first((rf"cargo\s+fijo(?:\s+ficticio)?\s*[:\-]?\s*{_MONEY}",), text)
    variable_raw = _first((rf"cargo\s+(?:variable|por\s+consumo)(?:\s+ficticio)?\s*[:\-]?\s*{_MONEY}",), text)

    def parsed_date(raw: str | None) -> date | None:
        try:
            return date.fromisoformat(raw) if raw else None
        except ValueError:
            return None

    try:
        consumption = Decimal(consumption_raw.replace(",", ".")) if consumption_raw else None
    except Exception:
        consumption = None
    total, fixed, variable = (_amount(v) if v else None for v in (total_raw, fixed_raw, variable_raw))
    items = []
    if fixed is not None:
        items.append(LineItem(label="Cargo fijo", amount_cop=fixed))
    if variable is not None:
        items.append(LineItem(label="Cargo variable", amount_cop=variable))
    issued_on, due_on = parsed_date(issued_raw), parsed_date(due_raw)
    for label, value in (("periodo de facturación", period), ("fecha de emisión", issued_on),
                         ("fecha límite de pago", due_on), ("consumo", consumption),
                         ("valor total", total_raw), ("cargo fijo", fixed_raw), ("cargo variable", variable_raw)):
        if value is None:
            warnings.append(f"No se pudo identificar {label} en el documento.")
    invoice = InvoiceOut(
        id=invoice_id, collection_id=collection_id, billing_period=period,
        issued_on=issued_on, due_on=due_on, consumption_m3=consumption,
        total_cop=total, fixed_charge_cop=fixed, variable_charge_cop=variable,
        line_items=items, warnings=warnings, source=source,
    )
    return ParseResult(invoice=invoice, warnings=warnings)
