#!/usr/bin/env python3
"""Generate deterministic, clearly synthetic SmartBill AI invoice PDF samples.

Usage: python scripts/generate_samples.py
No third-party packages are required. Generated PDFs contain selectable text.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "samples" / "synthetic_invoices"

HISTORY = [
    ("2026-06", "Junio", 19),
    ("2026-07", "Julio", 21),
    ("2026-08", "Agosto", 20),
    ("2026-09", "Septiembre", 23),
    ("2026-10", "Octubre", 22),
    ("2026-11", "Noviembre", 32),
]
FIXED_COP = 8_000
VARIABLE_COP_PER_M3 = 2_500


def pdf_escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def make_pdf(lines: list[str]) -> bytes:
    """Build a small one-page PDF with embedded selectable Helvetica text."""
    stream_parts = ["BT", "/F1 11 Tf", "50 790 Td", "14 TL"]
    for index, line in enumerate(lines):
        if index:
            stream_parts.append("T*")
        stream_parts.append(f"({pdf_escape(line)}) Tj")
    stream_parts.append("ET")
    stream = "\n".join(stream_parts).encode("latin-1", errors="replace")
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 842] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>",
        b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"\nendstream",
    ]
    result = bytearray(b"%PDF-1.4\n% Synthetic demo document\n")
    offsets = [0]
    for number, body in enumerate(objects, start=1):
        offsets.append(len(result))
        result.extend(f"{number} 0 obj\n".encode())
        result.extend(body)
        result.extend(b"\nendobj\n")
    xref_offset = len(result)
    result.extend(f"xref\n0 {len(objects) + 1}\n".encode())
    result.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        result.extend(f"{offset:010d} 00000 n \n".encode())
    result.extend(
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF\n".encode()
    )
    return bytes(result)


def money(cop: int) -> str:
    return f"${cop:,.0f} COP".replace(",", ".")


def invoice_lines(period: str, month: str, consumption: int, number: str) -> list[str]:
    fixed = FIXED_COP
    variable = consumption * VARIABLE_COP_PER_M3
    total = fixed + variable
    return [
        "DATOS SINTÉTICOS DE DEMOSTRACIÓN - FACTURA FICTICIA",
        "SmartBill AI | Ejemplo educativo; no corresponde a un proveedor real",
        f"Factura de gas natural: {number}",
        f"Periodo de facturación: {month} de {period[:4]}",
        f"Fecha de emisión: {period}-25",
        f"Fecha límite de pago: {period[:5]}{int(period[5:]) + 1:02d}-10" if int(period[5:]) < 12 else "Fecha límite de pago: 2026-12-10",
        f"Consumo: {consumption} m3",
        f"Cargo fijo ficticio: {money(fixed)}",
        f"Cargo variable ficticio: {money(variable)} ({consumption} m3 x {money(VARIABLE_COP_PER_M3)}/m3)",
        f"TOTAL FICTICIO: {money(total)}",
        "Valores inventados únicamente para pruebas; no son tarifas ni cobros reales.",
    ]


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    generated: list[Path] = []
    for index, (period, month, consumption) in enumerate(HISTORY, start=1):
        path = OUT / f"factura_{period}_{consumption}m3.pdf"
        path.write_bytes(make_pdf(invoice_lines(period, month, consumption, f"SYN-{index:04d}")))
        generated.append(path)

    # Incomplete by design: period and consumption are present, monetary and
    # issue/due-date fields are omitted so a parser can report missing data.
    incomplete = OUT / "factura_incompleta_sintetica.pdf"
    incomplete.write_bytes(make_pdf([
        "DATOS SINTÉTICOS DE DEMOSTRACIÓN - FACTURA FICTICIA INCOMPLETA",
        "SmartBill AI | Ejemplo educativo; no corresponde a un proveedor real",
        "Periodo de facturación: Diciembre de 2026",
        "Consumo: 18 m3",
        "Documento deliberadamente incompleto para probar advertencias de extracción.",
    ]))
    generated.append(incomplete)

    # Deliberately not a PDF (no %PDF signature) while retaining a clear label.
    invalid = OUT / "archivo_invalido_sintetico.pdf"
    invalid.write_text(
        "DATOS SINTÉTICOS DE DEMOSTRACIÓN - ARCHIVO INVÁLIDO\n"
        "Este archivo de texto no es un PDF; sirve para probar el rechazo de formato.\n",
        encoding="utf-8",
    )
    generated.append(invalid)

    print(f"Generados {len(generated)} archivos en {OUT.relative_to(ROOT)}:")
    for path in generated:
        print(f"- {path.name} ({path.stat().st_size} bytes)")
    print("Importes ficticios: cargo fijo COP 8.000 + COP 2.500 por m3.")


if __name__ == "__main__":
    main()
