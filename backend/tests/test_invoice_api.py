from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.invoices import MAX_UPLOAD_BYTES
from app.core.config import settings
from app.database.models import Base, InvoiceRecord
from app.database.seed import SYNTHETIC_COLLECTION_ID, seed_synthetic_invoices
from app.database.session import get_db
from app.main import app

SAMPLES = Path(__file__).resolve().parents[2] / "samples" / "synthetic_invoices"


@pytest.fixture
def client():
    test_engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    TestingSession = sessionmaker(bind=test_engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(test_engine)

    def override_db():
        with TestingSession() as db:
            yield db

    app.dependency_overrides[get_db] = override_db
    old_public_demo = settings.public_demo
    settings.public_demo = False
    try:
        with TestClient(app) as test_client:
            auth = test_client.post("/api/auth/register", json={"email": "invoice-test@example.com", "password": "a-long-test-password"}, headers={"Origin": settings.frontend_origin})
            assert auth.status_code == 201
            test_client.headers.update({"Origin": settings.frontend_origin, "X-CSRF-Token": auth.json()["csrf_token"]})
            yield test_client, TestingSession
    finally:
        settings.public_demo = old_public_demo
        app.dependency_overrides.clear()
        test_engine.dispose()


def test_upload_and_read_only_persist_structured_fields(client):
    test_client, TestingSession = client
    pdf = (SAMPLES / "factura_2026-11_32m3.pdf").read_bytes()
    response = test_client.post(
        "/api/invoices/upload",
        files={"file": ("noviembre.pdf", pdf, "application/pdf")},
    )
    assert response.status_code == 201
    invoice = response.json()
    assert invoice["source"] == "local_upload"
    assert invoice["consumption_m3"] == 32
    assert "32" not in str(invoice["warnings"])
    assert "DATOS SINTÉTICOS" not in str(invoice).upper()
    assert test_client.get(f"/api/invoices/{invoice['id']}").json() == invoice

    with TestingSession() as db:
        record = db.get(InvoiceRecord, invoice["id"])
        assert record is not None
        assert not hasattr(record, "pdf")
        assert not hasattr(record, "raw_text")


def test_uploads_receive_separate_collections_unless_explicitly_associated(client):
    test_client, _ = client
    pdf = (SAMPLES / "factura_2026-10_22m3.pdf").read_bytes()
    responses = [
        test_client.post("/api/invoices/upload", files={"file": ("octubre.pdf", pdf, "application/pdf")})
        for _ in range(2)
    ]
    assert all(response.status_code == 201 for response in responses)
    assert responses[0].json()["collection_id"] != responses[1].json()["collection_id"]

    collection_id = str(uuid4())
    response = test_client.post(
        "/api/invoices/upload",
        files={"file": ("octubre.pdf", pdf, "application/pdf")},
        data={"collection_id": collection_id},
    )
    assert response.status_code == 201
    assert response.json()["collection_id"] == collection_id


def test_invalid_pdf_and_unknown_invoice_have_typed_errors(client):
    test_client, _ = client
    response = test_client.post(
        "/api/invoices/upload", files={"file": ("fake.pdf", b"PRIVATE DOCUMENT TEXT", "application/pdf")}
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "invalid_file"
    assert "PRIVATE DOCUMENT TEXT" not in response.text
    missing = test_client.get(f"/api/invoices/{uuid4()}")
    assert missing.status_code == 404
    assert missing.json()["error"]["code"] == "invoice_not_found"


def test_upload_limit_is_enforced_and_public_demo_blocks_upload_and_local_rows(client):
    test_client, TestingSession = client
    too_large = b"%PDF-1.7\n" + b"x" * MAX_UPLOAD_BYTES
    response = test_client.post(
        "/api/invoices/upload", files={"file": ("large.pdf", too_large, "application/pdf")}
    )
    assert response.status_code == 413

    with TestingSession() as db:
        row = InvoiceRecord(
            id=str(uuid4()), collection_id=str(uuid4()), source="local_upload",
            line_items=[], warnings=[]
        )
        db.add(row)
        db.commit()
        local_id = row.id
        seeded = seed_synthetic_invoices(db)
        assert len(seeded) == 6
        assert len(seed_synthetic_invoices(db)) == 6
        assert db.scalar(select(func.count()).select_from(InvoiceRecord)) == 7

    settings.public_demo = True
    try:
        blocked = test_client.post(
            "/api/invoices/upload", files={"file": ("noviembre.pdf", b"%PDF-x", "application/pdf")}
        )
        assert blocked.status_code == 403
        assert test_client.get(f"/api/invoices/{local_id}").status_code == 404
        synthetic_id = str(seeded[-1].id)
        assert test_client.get(f"/api/invoices/{synthetic_id}").status_code == 200
    finally:
        settings.public_demo = False
