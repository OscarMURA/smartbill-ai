from decimal import Decimal
from uuid import uuid4

import pytest
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.chat import router
from app.core.config import settings
from app.database.models import Base, InvoiceRecord
from app.database.seed import SYNTHETIC_COLLECTION_ID
from app.database.session import get_db


@pytest.fixture
def client(monkeypatch):
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)
    collection = str(SYNTHETIC_COLLECTION_ID)
    earlier = InvoiceRecord(
        id=str(uuid4()), collection_id=collection, billing_period="2026-10",
        consumption_m3=Decimal("22"), total_cop=63000, fixed_charge_cop=8000,
        variable_charge_cop=55000, line_items=[], warnings=[], source="synthetic",
    )
    current = InvoiceRecord(
        id=str(uuid4()), collection_id=collection, billing_period="2026-11",
        consumption_m3=Decimal("32"), total_cop=88000, fixed_charge_cop=8000,
        variable_charge_cop=80000, line_items=[], warnings=[], source="synthetic",
    )
    current_id = current.id
    with TestingSession() as db:
        db.add_all([earlier, current])
        db.commit()
    app = FastAPI()
    app.include_router(router)

    @app.exception_handler(HTTPException)
    async def error_envelope(_: Request, exc: HTTPException):
        return JSONResponse(status_code=exc.status_code, content={"error": exc.detail})

    def override_db():
        with TestingSession() as db:
            yield db

    app.dependency_overrides[get_db] = override_db
    monkeypatch.setattr(settings, "llm_api_key", None)
    monkeypatch.setattr(settings, "public_demo", False)
    with TestClient(app) as test_client:
        yield test_client, current_id
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


def test_chat_without_key_answers_from_invoice_and_analysis(client):
    test_client, invoice_id = client
    response = test_client.post("/api/chat", json={"invoice_id": invoice_id, "question": "¿Por qué aumentó?"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["mode"] == "demo"
    assert "32 m³" in payload["answer"]
    assert "45,45 %" in payload["answer"]
    assert any("variation_percentage=45.45" in evidence for evidence in payload["evidence"])


def test_chat_returns_not_found_for_unknown_invoice(client):
    test_client, _ = client
    response = test_client.post("/api/chat", json={"invoice_id": str(uuid4()), "question": "¿Cuánto consumí?"})
    assert response.status_code == 404


def test_emergency_response_is_safe_and_bypasses_provider(client, monkeypatch):
    from app.services import ai_service

    test_client, invoice_id = client
    monkeypatch.setattr(settings, "llm_api_key", "fake-key")
    monkeypatch.setattr(ai_service, "_call_llm", lambda *args: pytest.fail("provider should be bypassed"))
    response = test_client.post("/api/chat", json={"invoice_id": invoice_id, "question": "Siento olor a gas en casa"})
    assert response.status_code == 200
    answer = response.json()["answer"].casefold()
    assert "aléjate" in answer
    assert "interruptores" in answer
    assert "lugar seguro" in answer


def test_provider_failure_returns_controlled_503(client, monkeypatch):
    from app.services import ai_service

    test_client, invoice_id = client
    monkeypatch.setattr(settings, "llm_api_key", "fake-key")
    monkeypatch.setattr(ai_service, "_call_llm", lambda *args: (_ for _ in ()).throw(ai_service.AIProviderError("El servicio de IA no está disponible en este momento.")))
    response = test_client.post("/api/chat", json={"invoice_id": invoice_id, "question": "¿Cuánto consumí?"})
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "ai_unavailable"
    assert "disponible" in response.json()["error"]["message"]


def test_question_with_personal_data_is_rejected_before_provider(client, monkeypatch):
    from app.services import ai_service

    test_client, invoice_id = client
    monkeypatch.setattr(settings, "llm_api_key", "fake-key")
    monkeypatch.setattr(ai_service, "_call_llm", lambda *args: pytest.fail("PII question reached provider"))
    response = test_client.post("/api/chat", json={"invoice_id": invoice_id, "question": "Explícame mi consumo, correo ana@example.com"})
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "personal_data_in_question"
