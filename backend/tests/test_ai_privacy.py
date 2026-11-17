import json
from decimal import Decimal
from uuid import uuid4

from app.schemas.analysis import AnalysisOut
from app.schemas.invoice import InvoiceOut
from app.services import ai_service


def invoice():
    return InvoiceOut(
        id=uuid4(), collection_id=uuid4(), billing_period="2026-11",
        consumption_m3=Decimal("32"), total_cop=88000, fixed_charge_cop=8000,
        variable_charge_cop=80000, line_items=[{"label": "cargo fijo", "amount_cop": 8000}],
        warnings=["fake name: Ada Example, address: Calle Inventada 1"], source="synthetic",
    )


def analysis():
    return AnalysisOut(current_consumption_m3=Decimal("32"), previous_consumption_m3=Decimal("22"),
                       variation_percentage=Decimal("45.45"), status="high_variation", message="subió")


def test_context_is_an_allowlist_without_ids_line_items_or_warnings():
    inv = invoice()
    context = ai_service.build_ai_context(inv, analysis())
    serialized = json.dumps(context)
    assert "Ada Example" not in serialized
    assert "Calle Inventada" not in serialized
    assert str(inv.id) not in serialized
    assert str(inv.collection_id) not in serialized
    assert "warnings" not in context
    assert "line_items" not in context
    assert context["consumption_m3"] == "32"


def test_billing_period_rejects_arbitrary_extracted_text():
    inv = invoice()
    inv.billing_period = "2026-11 Ada Example"
    assert ai_service.build_ai_context(inv, analysis())["billing_period"] is None


def test_digitalocean_request_contains_only_user_question_and_allowlisted_context(monkeypatch):
    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self):
            return b'{"choices":[{"message":{"content":"El consumo fue 32 m3."}}]}'

    captured = {}

    def fake_urlopen(request, timeout):
        captured["body"] = json.loads(request.data)
        captured["timeout"] = timeout
        captured["url"] = request.full_url
        captured["api_key_header"] = request.get_header("Authorization")
        return FakeResponse()

    monkeypatch.setattr(ai_service.settings, "llm_api_key", "unit-test-key")
    monkeypatch.setattr(ai_service.urllib.request, "urlopen", fake_urlopen)
    inv = invoice()
    response = ai_service.answer_question("¿Cuánto consumí?", inv, analysis())
    payload_text = json.dumps(captured["body"], ensure_ascii=False)
    assert response.mode == "digitalocean"
    assert response.answer == "El consumo fue 32 m3."
    assert "Ada Example" not in payload_text
    assert "Calle Inventada" not in payload_text
    assert str(inv.id) not in payload_text
    assert str(inv.collection_id) not in payload_text
    assert "warnings" not in payload_text and "line_items" not in payload_text
    assert captured["timeout"] > 0
    assert "unit-test-key" not in captured["url"]
    assert captured["api_key_header"] == "Bearer unit-test-key"
    assert captured["url"] == "https://inference.do-ai.run/v1/chat/completions"
    assert captured["body"]["model"] == "glm-5.3"
    assert [message["role"] for message in captured["body"]["messages"]] == ["system", "user"]
