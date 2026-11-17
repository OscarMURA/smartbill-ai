"""Invoice-scoped chat endpoint using structured records only."""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.config import settings
from app.api.auth import get_optional_user, require_invoice_access, verify_authenticated_mutation
from app.database.models import InvoiceRecord
from app.database.seed import SYNTHETIC_COLLECTION_ID
from app.database.session import get_db
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.ai_service import AIProviderError, UserQueryPrivacyError, answer_question
from app.api.analysis import analyze_record

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
def chat(payload: ChatRequest, request: Request, user=Depends(get_optional_user), db: Session = Depends(get_db)) -> ChatResponse:
    invoice = db.get(InvoiceRecord, str(payload.invoice_id))
    if invoice is None:
        raise HTTPException(status_code=404, detail={"code": "invoice_not_found", "message": "No se encontró la factura."})
    require_invoice_access(invoice, user)
    if invoice.collection_id != str(SYNTHETIC_COLLECTION_ID):
        user, _ = verify_authenticated_mutation(request, db)

    analysis = analyze_record(db, invoice)

    # Build the shared response schema from structured database columns. Text
    # from source PDFs is never stored or read for chat.
    from app.schemas.invoice import InvoiceOut

    invoice_out = InvoiceOut.model_validate({
        "id": UUID(invoice.id),
        "collection_id": UUID(invoice.collection_id),
        "billing_period": invoice.billing_period,
        "issued_on": invoice.issued_on,
        "due_on": invoice.due_on,
        "consumption_m3": invoice.consumption_m3,
        "total_cop": invoice.total_cop,
        "fixed_charge_cop": invoice.fixed_charge_cop,
        "variable_charge_cop": invoice.variable_charge_cop,
        "line_items": invoice.line_items or [],
        "warnings": invoice.warnings or [],
        "source": invoice.source,
    })
    try:
        return answer_question(payload.question, invoice_out, analysis)
    except UserQueryPrivacyError as exc:
        raise HTTPException(status_code=400, detail={"code": "personal_data_in_question", "message": str(exc)}) from exc
    except AIProviderError as exc:
        raise HTTPException(status_code=503, detail={"code": "ai_unavailable", "message": str(exc)}) from exc
