from pathlib import Path

import pymupdf as fitz
import pytest

from app.services.pdf_extractor import PDFValidationError, extract_pdf_text

SAMPLES = Path(__file__).resolve().parents[2] / "samples" / "synthetic_invoices"


def test_extracts_valid_synthetic_pdf_text():
    data = (SAMPLES / "factura_2026-11_32m3.pdf").read_bytes()
    text = extract_pdf_text(data, filename="noviembre.pdf", content_type="application/pdf")
    assert "DATOS SINTÉTICOS DE DEMOSTRACIÓN" in text
    assert "Consumo: 32 m3" in text


def test_rejects_non_pdf_signature():
    with pytest.raises(PDFValidationError) as exc:
        extract_pdf_text(b"plain text", filename="fake.pdf", content_type="application/pdf")
    assert exc.value.code == "invalid_file"


def test_rejects_invalid_mime_and_extension():
    pdf = (SAMPLES / "factura_2026-11_32m3.pdf").read_bytes()
    with pytest.raises(PDFValidationError):
        extract_pdf_text(pdf, filename="bill.txt", content_type="application/pdf")
    with pytest.raises(PDFValidationError):
        extract_pdf_text(pdf, filename="bill.pdf", content_type="text/plain")


def test_rejects_file_over_10_mb():
    with pytest.raises(PDFValidationError) as exc:
        extract_pdf_text(b"%PDF-1.4\n" + b"0" * (10 * 1024 * 1024), filename="large.pdf")
    assert exc.value.code == "file_too_large"


def test_temporary_file_is_removed_after_extraction(monkeypatch):
    import app.services.pdf_extractor as extractor

    original = extractor.tempfile.NamedTemporaryFile
    paths = []

    def tracking_tempfile(*args, **kwargs):
        handle = original(*args, **kwargs)
        paths.append(Path(handle.name))
        return handle

    monkeypatch.setattr(extractor.tempfile, "NamedTemporaryFile", tracking_tempfile)
    data = (SAMPLES / "factura_2026-11_32m3.pdf").read_bytes()
    extract_pdf_text(data)
    assert len(paths) == 1
    assert not paths[0].exists()


def test_scanned_or_textless_pdf_returns_empty_text():
    document = fitz.open()
    document.new_page()
    data = document.tobytes()
    document.close()
    assert extract_pdf_text(data) == ""
