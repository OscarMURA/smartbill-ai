"""Dashboard data for a single explicit invoice collection."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.analysis import analyze_record, ordered_collection
from app.api.invoices import _as_output
from app.core.config import settings
from app.api.auth import get_optional_user
from app.database.models import InvoiceRecord
from app.database.seed import SYNTHETIC_COLLECTION_ID
from app.database.session import get_db

router = APIRouter(prefix="/api", tags=["dashboard"])


@router.get("/dashboard")
def get_dashboard(
    collection_id: UUID | None = Query(default=None), user=Depends(get_optional_user), db: Session = Depends(get_db)
) -> dict:
    target = collection_id
    if target is None and user is not None:
        latest = db.query(InvoiceRecord).filter(InvoiceRecord.user_id == user.id).order_by(
            InvoiceRecord.issued_on.desc(), InvoiceRecord.billing_period.desc(), InvoiceRecord.id.desc()
        ).first()
        if latest is None:
            return {"collection_id": None, "invoices": [], "latest_analysis": None, "series": []}
        target = UUID(latest.collection_id)
    if target is None:
        target = SYNTHETIC_COLLECTION_ID
    if settings.public_demo and target != SYNTHETIC_COLLECTION_ID:
        raise HTTPException(status_code=404, detail={"code": "collection_not_found", "message": "No se encontró la colección."})
    if target != SYNTHETIC_COLLECTION_ID:
        if user is None:
            raise HTTPException(status_code=401, detail={"code": "authentication_required", "message": "Inicia sesión para continuar."})
        owned = db.query(InvoiceRecord.id).filter(InvoiceRecord.collection_id == str(target), InvoiceRecord.user_id == user.id).first()
        if owned is None:
            raise HTTPException(status_code=404, detail={"code": "collection_not_found", "message": "No se encontró la colección."})
        rows = ordered_collection(db, str(target), user.id)
    else:
        rows = ordered_collection(db, str(target))
    latest = rows[-1] if rows else None
    return {
        "collection_id": str(target),
        "invoices": [_as_output(row) for row in rows],
        "latest_analysis": analyze_record(db, latest) if latest else None,
        "series": [
            {"period": row.billing_period or str(row.issued_on or "Sin período"),
             "consumption_m3": float(row.consumption_m3) if row.consumption_m3 is not None else None,
             "total_cop": row.total_cop}
            for row in rows
        ],
    }
