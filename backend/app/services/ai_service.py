"""Grounded demo/DigitalOcean responses using an OpenAI-compatible API."""
from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from decimal import Decimal
from typing import Any

from app.core.config import settings
from app.schemas.analysis import AnalysisOut
from app.schemas.invoice import InvoiceOut
from app.schemas.chat import ChatResponse
from app.services.prompts.v1 import SYSTEM_INSTRUCTION


class AIProviderError(RuntimeError):
    """Provider failure without upstream response details or invoice content."""


class UserQueryPrivacyError(ValueError):
    """The question appears to contain personal contact or identity details."""


def _contains_basic_pii(question: str) -> bool:
    patterns = (
        r"\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b",
        r"(?<!\d)(?:\+?57[\s.-]?)?(?:3\d{2}|60\d)[\s.-]?\d{3}[\s.-]?\d{4}(?!\d)",
        r"\b(?:c[eé]dula|documento|identificaci[oó]n|nit)\s*(?:n[uú]mero|nro\.?|#|:)?\s*\d{5,}\b",
        r"\b(?:calle|carrera|cra\.?|avenida|av\.?|diagonal|transversal)\s+\d",
        r"(?<!\d)\d{8,}(?!\d)",
    )
    return any(re.search(pattern, question, flags=re.IGNORECASE) for pattern in patterns)


def is_emergency_question(question: str) -> bool:
    q = question.casefold()
    return any(term in q for term in ("olor a gas", "huele a gas", "fuga de gas", "emergencia de gas", "escape de gas"))


def _decimal(value: Decimal | None) -> str | None:
    return format(value.normalize(), "f") if value is not None else None


def _display_decimal(value: Decimal) -> str:
    return format(value.normalize(), "f").replace(".", ",")


def build_ai_context(invoice: InvoiceOut, analysis: AnalysisOut) -> dict[str, Any]:
    """Explicit allowlist: no UUIDs, names, address, paths, or source text."""
    period = invoice.billing_period
    # Billing period should be a short period label, never arbitrary extracted text.
    known_month = r"(?:enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)"
    if period is not None and not re.fullmatch(
        rf"(?:20\d{{2}}[-/](?:0[1-9]|1[0-2])|{known_month}\s+de\s+20\d{{2}})",
        period.strip(),
        flags=re.IGNORECASE,
    ):
        period = None
    return {
        "billing_period": period,
        "consumption_m3": _decimal(invoice.consumption_m3),
        "previous_consumption_m3": _decimal(analysis.previous_consumption_m3),
        "variation_percentage": _decimal(analysis.variation_percentage),
        "analysis_status": analysis.status,
        "total_cop": invoice.total_cop,
        "fixed_charge_cop": invoice.fixed_charge_cop,
        "variable_charge_cop": invoice.variable_charge_cop,
    }


def _demo_answer(question: str, invoice: InvoiceOut, analysis: AnalysisOut) -> tuple[str, list[str]]:
    q = question.casefold()
    evidence: list[str] = []
    if invoice.consumption_m3 is not None:
        evidence.append(f"consumption_m3={invoice.consumption_m3}")
    if invoice.total_cop is not None:
        evidence.append(f"total_cop={invoice.total_cop}")
    if analysis.variation_percentage is not None:
        evidence.append(f"variation_percentage={analysis.variation_percentage}")
    if any(term in q for term in ("por qué", "porque", "aument", "variación", "cambió", "subió")):
        if analysis.variation_percentage is None:
            return "No hay datos suficientes para calcular la variación frente al período anterior.", evidence
        return (
            f"El consumo fue de {_display_decimal(invoice.consumption_m3)} m³ y cambió {_display_decimal(analysis.variation_percentage)} % frente al período anterior. "
            "La factura no permite determinar la causa del cambio.", evidence,
        )
    if any(term in q for term in ("consum", "metros", "m3", "m³")):
        if invoice.consumption_m3 is None:
            return "La factura no incluye un consumo identificable.", evidence
        return f"El consumo registrado es {_display_decimal(invoice.consumption_m3)} m³.", evidence
    if any(term in q for term in ("total", "costo", "cobro", "valor", "pagu")):
        if invoice.total_cop is None:
            return "La factura no incluye un valor total identificable.", evidence
        return f"El valor total registrado es COP {invoice.total_cop:,}.".replace(",", "."), evidence
    if any(term in q for term in ("concept", "cargo", "fijo", "variable")):
        parts = []
        if invoice.fixed_charge_cop is not None:
            parts.append(f"cargo fijo COP {invoice.fixed_charge_cop:,}".replace(",", "."))
        if invoice.variable_charge_cop is not None:
            parts.append(f"cargo variable COP {invoice.variable_charge_cop:,}".replace(",", "."))
        if parts:
            return "Los conceptos identificados son " + " y ".join(parts) + ".", evidence
        return "No se identificaron conceptos de cobro en la factura.", evidence
    return "Puedo ayudarte con el consumo, la variación y los valores que aparecen en la factura.", evidence


def _call_llm(question: str, context: dict[str, Any]) -> str:
    api_key = settings.llm_api_key
    if not api_key:
        raise AIProviderError("Proveedor de IA no configurado.")
    model = settings.llm_model
    try:
        timeout = float(os.getenv("LLM_TIMEOUT_SECONDS", "12"))
    except ValueError:
        timeout = 12.0
    if timeout <= 0 or timeout > 60:
        timeout = 12.0
    base_url = settings.llm_base_url.rstrip("/")
    if not base_url.endswith("/v1"):
        base_url += "/v1"
    url = f"{base_url}/chat/completions"
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_INSTRUCTION},
            {"role": "user", "content": json.dumps({"question": question, "invoice_data": context}, ensure_ascii=False)},
        ],
        "temperature": 0.2,
        "max_completion_tokens": 300,
    }
    request = urllib.request.Request(
        url,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            result = json.loads(response.read())
        answer = result["choices"][0]["message"]["content"].strip()
        if not answer:
            raise ValueError("empty response")
        return answer
    except (urllib.error.URLError, TimeoutError, OSError, ValueError, KeyError, IndexError, TypeError, json.JSONDecodeError):
        raise AIProviderError("El servicio de IA no está disponible en este momento.") from None


def answer_question(question: str, invoice: InvoiceOut, analysis: AnalysisOut) -> ChatResponse:
    if is_emergency_question(question):
        return ChatResponse(
            answer=("Si percibes olor a gas, aléjate del lugar. Evita interruptores y cualquier fuente de ignición. "
                    "Desde un lugar seguro, contacta los canales oficiales de emergencia de tu proveedor o las autoridades locales."),
            mode="demo",
            evidence=[],
        )
    if _contains_basic_pii(question):
        raise UserQueryPrivacyError(
            "Por privacidad, elimina teléfonos, correos, números de documento o direcciones de la pregunta e inténtalo de nuevo."
        )
    if not settings.llm_api_key:
        answer, evidence = _demo_answer(question, invoice, analysis)
        return ChatResponse(answer=answer, mode="demo", evidence=evidence)
    context = build_ai_context(invoice, analysis)
    answer = _call_llm(question, context)
    return ChatResponse(answer=answer, mode="digitalocean", evidence=[])
