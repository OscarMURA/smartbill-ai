from pathlib import Path

from app.services.parsers.base import parse_invoice
from app.services.pdf_extractor import extract_pdf_text

SAMPLES = Path(__file__).resolve().parents[2] / "samples" / "synthetic_invoices"


def parse_sample(name: str):
    text = extract_pdf_text((SAMPLES / name).read_bytes())
    return parse_invoice(text)


def test_synthetic_november_fields_and_amounts():
    result = parse_sample("factura_2026-11_32m3.pdf")
    invoice = result.invoice
    assert invoice.source == "synthetic"
    assert invoice.billing_period == "Noviembre de 2026"
    assert str(invoice.consumption_m3) == "32"
    assert invoice.total_cop == 88_000
    assert invoice.fixed_charge_cop == 8_000
    assert invoice.variable_charge_cop == 80_000
    assert result.warnings == invoice.warnings == []


def test_generated_history_has_expected_consumptions():
    names = [f"factura_2026-{month:02d}_{consumption}m3.pdf" for month, consumption in
             ((6, 19), (7, 21), (8, 20), (9, 23), (10, 22), (11, 32))]
    assert [parse_sample(name).invoice.consumption_m3 for name in names] == [19, 21, 20, 23, 22, 32]


def test_incomplete_document_returns_null_and_warnings():
    result = parse_sample("factura_incompleta_sintetica.pdf")
    assert result.invoice.consumption_m3 == 18
    assert result.invoice.total_cop is None
    assert result.invoice.issued_on is None
    assert "valor total" in " ".join(result.warnings)
    assert result.warnings == result.invoice.warnings


def test_generic_parser_does_not_invent_missing_fields():
    result = parse_invoice("Consumo: 7 m3\n")
    assert result.invoice.source == "synthetic"
    assert result.invoice.consumption_m3 == 7
    assert result.invoice.total_cop is None
    assert len(result.warnings) >= 6


def test_invalid_sample_is_not_a_pdf():
    data = (SAMPLES / "archivo_invalido_sintetico.pdf").read_bytes()
    assert not data.startswith(b"%PDF-")
