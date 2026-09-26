# =============================================================================
# SNCEV API — Renderizado de la cartilla electrónica a PDF (WeasyPrint + Jinja2)
# =============================================================================

from __future__ import annotations

import base64
import io
from pathlib import Path
from typing import Any

import qrcode
from jinja2 import Environment, FileSystemLoader, select_autoescape
from weasyprint import HTML

TEMPLATE_DIR = Path(__file__).parent / "templates"

_env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)), autoescape=select_autoescape(["html"]))


def qr_data_uri(texto: str) -> str:
    qr = qrcode.QRCode(box_size=6, border=1)
    qr.add_data(texto)
    qr.make(fit=True)
    buf = io.BytesIO()
    qr.make_image(fill_color="black", back_color="white").save(buf, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode("ascii")


def render_cartilla_pdf(contexto: dict[str, Any]) -> bytes:
    """Renderiza la plantilla con el contexto ya armado (paciente, vacunas, firma, etc.)
    y devuelve los bytes del PDF. `base_url` deja que WeasyPrint resuelva el CSS y el logo
    (rutas relativas de la plantilla) contra la carpeta de templates."""
    html = _env.get_template("cartilla_plantilla.html.j2").render(**contexto)
    return HTML(string=html, base_url=str(TEMPLATE_DIR)).write_pdf()
