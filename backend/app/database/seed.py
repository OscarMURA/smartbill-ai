"""Idempotent synthetic history used by the public demo."""

from decimal import Decimal
from uuid import UUID, uuid5

from sqlalchemy.orm import Session

from app.database.models import InvoiceRecord

SYNTHETIC_COLLECTION_ID = UUID("e96781c4-81e0-4dc1-a7fb-203c00000001")
_NAMESPACE = UUID("e96781c4-81e0-4dc1-a7fb-203c00000002")
_HISTORY = (("2026-06", 19), ("2026-07", 21), ("2026-08", 20), ("2026-09", 23), ("2026-10", 22), ("2026-11", 32))


def seed_synthetic_invoices(db: Session) -> list[InvoiceRecord]:
    """Insert the six demo periods once; return the existing/new rows."""
    result: list[InvoiceRecord] = []
    for period, consumption in _HISTORY:
        invoice_id = uuid5(_NAMESPACE, period)
        record = db.get(InvoiceRecord, str(invoice_id))
        if record is None:
            record = InvoiceRecord(
                id=str(invoice_id),
                collection_id=str(SYNTHETIC_COLLECTION_ID),
                billing_period=period,
                consumption_m3=Decimal(consumption),
                total_cop=consumption * 2500 + 8000,
                fixed_charge_cop=8000,
                variable_charge_cop=consumption * 2500,
                line_items=[
                    {"label": "Cargo fijo ficticio", "amount_cop": 8000},
                    {"label": "Cargo variable ficticio", "amount_cop": consumption * 2500},
                ],
                warnings=[],
                source="synthetic",
            )
            db.add(record)
        result.append(record)
    db.commit()
    for record in result:
        db.refresh(record)
    return result
