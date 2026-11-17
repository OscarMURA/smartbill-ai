"""Validate uploaded PDF bytes and extract selectable text with PyMuPDF."""
from __future__ import annotations

import tempfile
from pathlib import Path

import pymupdf as fitz

MAX_PDF_SIZE = 10 * 1024 * 1024
PDF_MIME_TYPE = "application/pdf"


class PDFValidationError(ValueError):
    """A safe-to-display error for invalid or unsupported PDF input."""

    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(message)


def _validate_pdf(data: bytes, filename: str | None = None, content_type: str | None = None) -> None:
    if not isinstance(data, bytes):
        raise PDFValidationError("invalid_file", "El archivo debe ser un PDF válido.")
    if len(data) > MAX_PDF_SIZE:
        raise PDFValidationError("file_too_large", "El archivo supera el máximo permitido de 10 MB.")
    if not data:
        raise PDFValidationError("invalid_file", "El archivo PDF está vacío o no es válido.")
    if filename and Path(filename).suffix.lower() != ".pdf":
        raise PDFValidationError("invalid_file", "La extensión del archivo debe ser .pdf.")
    # The PDF signature is the authoritative MIME sniff; the caller-provided
    # MIME header is untrusted and may be absent or generic.
    if not data.startswith(b"%PDF-"):
        raise PDFValidationError("invalid_file", "El contenido del archivo no tiene formato PDF.")
    if content_type and content_type.split(";", 1)[0].strip().lower() not in (PDF_MIME_TYPE, "application/octet-stream"):
        raise PDFValidationError("invalid_file", "El tipo de contenido del archivo no es PDF.")


def extract_pdf_text(
    data: bytes,
    *,
    filename: str | None = None,
    content_type: str | None = None,
) -> str:
    """Return selectable page text; never retain the uploaded PDF or its text.

    A named temporary file is used for PyMuPDF compatibility and unlinked in
    all success and failure paths. Scanned PDFs naturally return empty text.
    """
    _validate_pdf(data, filename, content_type)
    temp_path: str | None = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp:
            temp.write(data)
            temp_path = temp.name
        with fitz.open(temp_path) as document:
            if document.is_encrypted:
                raise PDFValidationError("invalid_file", "No se pudo leer el documento PDF.")
            return "\n".join(page.get_text("text") for page in document)
    except PDFValidationError:
        raise
    except (fitz.FileDataError, fitz.EmptyFileError, RuntimeError, OSError):
        raise PDFValidationError("invalid_file", "No se pudo leer el documento PDF.") from None
    finally:
        if temp_path:
            Path(temp_path).unlink(missing_ok=True)
