from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import settings
from app.database.models import Base, InvoiceRecord, SessionRecord
from app.database.seed import seed_synthetic_invoices
from app.database.session import get_db
from app.main import app

SAMPLES = Path(__file__).resolve().parents[2] / "samples" / "synthetic_invoices"
ORIGIN = {"Origin": settings.frontend_origin}


@pytest.fixture
def auth_client():
    test_engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    TestingSession = sessionmaker(bind=test_engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(test_engine)

    def override_db():
        with TestingSession() as db:
            yield db

    app.dependency_overrides[get_db] = override_db
    previous = settings.public_demo
    settings.public_demo = False
    try:
        with TestClient(app) as client:
            yield client, TestingSession
    finally:
        settings.public_demo = previous
        app.dependency_overrides.clear()
        test_engine.dispose()


def register(client, email):
    response = client.post("/api/auth/register", json={"email": email, "password": "long-test-password"}, headers=ORIGIN)
    assert response.status_code == 201
    client.headers.update({"X-CSRF-Token": response.json()["csrf_token"]})
    return response.json()


def test_register_me_logout_cookie_and_origin(auth_client):
    client, TestingSession = auth_client
    bad_origin = client.post("/api/auth/register", json={"email": "bad@example.com", "password": "long-test-password"}, headers={"Origin": "https://attacker.invalid"})
    assert bad_origin.status_code == 403
    registration = client.post("/api/auth/register", json={"email": "One@Example.com", "password": "long-test-password"}, headers=ORIGIN)
    assert registration.status_code == 201
    user = registration.json()
    cookie_header = registration.headers["set-cookie"].lower()
    assert "httponly" in cookie_header and "samesite=lax" in cookie_header and "max-age=1209600" in cookie_header
    client.headers.update({"X-CSRF-Token": user["csrf_token"]})
    assert user["email"] == "one@example.com"
    cookie = client.cookies.get("smartbill_session")
    assert cookie
    assert client.get("/api/auth/me").json() == user
    with TestingSession() as db:
        session = db.query(SessionRecord).one()
        assert session.id != cookie
    login_client = TestClient(app)
    wrong = login_client.post("/api/auth/login", json={"email": "one@example.com", "password": "wrong-password"}, headers=ORIGIN)
    assert wrong.status_code == 401
    login = login_client.post("/api/auth/login", json={"email": "ONE@example.com", "password": "long-test-password"}, headers=ORIGIN)
    assert login.status_code == 200
    assert login_client.get("/api/auth/me").json()["email"] == "one@example.com"
    response = client.post("/api/auth/logout", headers={"X-CSRF-Token": "wrong", **ORIGIN})
    assert response.status_code == 403
    response = client.post("/api/auth/logout", headers=ORIGIN)
    assert response.status_code == 200
    assert client.get("/api/auth/me").status_code == 401


def test_owner_isolation_and_private_csrf(auth_client):
    client_a, _ = auth_client
    user_a = register(client_a, "a@example.com")
    pdf = (SAMPLES / "factura_2026-11_32m3.pdf").read_bytes()
    upload = client_a.post("/api/invoices/upload", files={"file": ("invoice.pdf", pdf, "application/pdf")}, headers={**ORIGIN, "X-CSRF-Token": user_a["csrf_token"]})
    assert upload.status_code == 201
    invoice = upload.json()
    assert client_a.get("/api/dashboard").json()["collection_id"] == invoice["collection_id"]
    bad_csrf = client_a.post("/api/invoices/upload", files={"file": ("invoice.pdf", pdf, "application/pdf")}, headers={**ORIGIN, "X-CSRF-Token": "wrong"})
    assert bad_csrf.status_code == 403

    client_b = TestClient(app)
    user_b = register(client_b, "b@example.com")
    assert client_b.get(f"/api/invoices/{invoice['id']}").status_code == 404
    assert client_b.get(f"/api/invoices/{invoice['id']}/analysis").status_code == 404
    assert client_b.get(f"/api/dashboard?collection_id={invoice['collection_id']}").status_code == 404
    assert client_b.post("/api/chat", json={"invoice_id": invoice["id"], "question": "¿Cuánto consumí?"}, headers={**ORIGIN, "X-CSRF-Token": user_b["csrf_token"]}).status_code == 404


def test_synthetic_dashboard_is_public(auth_client):
    client, TestingSession = auth_client
    with TestingSession() as db:
        synthetic = seed_synthetic_invoices(db)
        invoice_id = synthetic[-1].id
    assert client.get("/api/dashboard").status_code == 200
    assert client.get(f"/api/invoices/{invoice_id}").status_code == 200
