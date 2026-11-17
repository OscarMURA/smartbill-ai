"""Deterministic analysis for one invoice and its explicitly grouped history."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.api.auth import get_optional_user, require_invoice_access
from app.database.models import InvoiceRecord
from app.database.seed import SYNTHETIC_COLLECTION_ID
from app.database.session import get_db
from app.schemas.analysis import AnalysisOut
from app.services.consumption_analyzer import analyze

router = APIRouter(prefix="/api/invoices", tags=["analysis"])


def ordered_collection(db: Session, collection_id: str, user_id: str | None = None) -> list[InvoiceRecord]:
    statement = select(InvoiceRecord).where(InvoiceRecord.collection_id == collection_id)
    if user_id is None:
        statement = statement.where(InvoiceRecord.source == "synthetic")
    else:
        statement = statement.where(InvoiceRecord.user_id == user_id)
    rows = list(db.scalars(statement))
    return sorted(rows, key=lambda row: (str(row.issued_on or ""), row.billing_period or "", row.id))


def analyze_record(db: Session, record: InvoiceRecord) -> AnalysisOut:
    rows = ordered_collection(db, record.collection_id, record.user_id)
    index = next(i for i, row in enumerate(rows) if row.id == record.id)
    previous = rows[index - 1] if index else None
    return analyze(
        record.consumption_m3,
        previous.consumption_m3 if previous else None,
        [row.consumption_m3 for row in rows[:index]],
    )


@router.get("/{invoice_id}/analysis", response_model=AnalysisOut)
def get_analysis(invoice_id: UUID, user=Depends(get_optional_user), db: Session = Depends(get_db)) -> AnalysisOut:
    record = db.get(InvoiceRecord, str(invoice_id))
    if record is None:
        raise HTTPException(status_code=404, detail={"code": "invoice_not_found", "message": "No se encontró la factura."})
    require_invoice_access(record, user)
    return analyze_record(db, record)
