from tempfile import NamedTemporaryFile
from typing import Annotated
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.core.config import settings
from app.api.auth import get_current_session, get_optional_user, require_csrf, require_invoice_access
from app.database.models import InvoiceRecord
from app.database.seed import SYNTHETIC_COLLECTION_ID
from app.database.session import get_db
from app.schemas.invoice import InvoiceOut
from app.services.pdf_extractor import PDFValidationError, extract_pdf_text
from app.services.parsers.base import parse_invoice

router = APIRouter(prefix="/api/invoices", tags=["invoices"])
MAX_UPLOAD_BYTES = 10 * 1024 * 1024
CHUNK_BYTES = 64 * 1024


def _as_output(record: InvoiceRecord) -> InvoiceOut:
    return InvoiceOut.model_validate(
        {
            "id": record.id,
            "collection_id": record.collection_id,
            "billing_period": record.billing_period,
            "issued_on": record.issued_on,
            "due_on": record.due_on,
            "consumption_m3": record.consumption_m3,
            "total_cop": record.total_cop,
            "fixed_charge_cop": record.fixed_charge_cop,
            "variable_charge_cop": record.variable_charge_cop,
            "line_items": record.line_items or [],
            "warnings": record.warnings or [],
            "source": record.source,
        }
    )


@router.post("/upload", response_model=InvoiceOut, status_code=201)
async def upload_invoice(
    file: Annotated[UploadFile, File(...)],
    collection_id: Annotated[UUID | None, Form()] = None,
    auth=Depends(require_csrf),
    db: Session = Depends(get_db),
) -> InvoiceOut:
    if settings.public_demo:
        raise HTTPException(status_code=403, detail={"code": "upload_disabled", "message": "La demo pública solo permite consultar facturas sintéticas."})

    user, _ = auth
    invoice_id = uuid4()
    target_collection = collection_id or uuid4()
    if str(target_collection) == str(SYNTHETIC_COLLECTION_ID):
        raise HTTPException(status_code=409, detail={"code": "collection_reserved", "message": "Ese identificador está reservado para la demo pública."})
    existing_owners = set(db.scalars(select(InvoiceRecord.user_id).where(InvoiceRecord.collection_id == str(target_collection))))
    if existing_owners and existing_owners != {user.id}:
        raise HTTPException(status_code=404, detail={"code": "collection_not_found", "message": "No se encontró la colección."})
    try:
        total = 0
        # Keep the upload on disk while enforcing the limit; only read the bounded file
        # into memory after it has passed the size check and before extraction.
        with NamedTemporaryFile(prefix="smartbill-upload-", suffix=".pdf") as temp_file:
            while chunk := await file.read(CHUNK_BYTES):
                total += len(chunk)
                if total > MAX_UPLOAD_BYTES:
                    raise HTTPException(status_code=413, detail={"code": "file_too_large", "message": "El PDF supera el límite de 10 MB."})
                temp_file.write(chunk)
            temp_file.flush()
            temp_file.seek(0)
            payload = temp_file.read()
        text = extract_pdf_text(payload, filename=file.filename, content_type=file.content_type)
        parsed = parse_invoice(
            text,
            invoice_id=invoice_id,
            collection_id=target_collection,
            source="local_upload",
        )
        invoice = parsed.invoice
        record = InvoiceRecord(
            id=str(invoice.id),
            collection_id=str(invoice.collection_id),
            billing_period=invoice.billing_period,
            issued_on=invoice.issued_on,
            due_on=invoice.due_on,
            consumption_m3=invoice.consumption_m3,
            total_cop=invoice.total_cop,
            fixed_charge_cop=invoice.fixed_charge_cop,
            variable_charge_cop=invoice.variable_charge_cop,
            line_items=[item.model_dump() for item in invoice.line_items],
            warnings=parsed.warnings,
            source="local_upload",
            user_id=user.id,
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return _as_output(record)
    except PDFValidationError as exc:
        raise HTTPException(status_code=400, detail={"code": exc.code, "message": exc.message}) from exc
    finally:
        await file.close()


@router.get("/{invoice_id}", response_model=InvoiceOut)
def get_invoice(invoice_id: UUID, user=Depends(get_optional_user), db: Session = Depends(get_db)) -> InvoiceOut:
    record = db.get(InvoiceRecord, str(invoice_id))
    if record is None:
        raise HTTPException(status_code=404, detail={"code": "invoice_not_found", "message": "No se encontró la factura."})
    require_invoice_access(record, user)
    return _as_output(record)
