"""Utilidades comunes."""
from __future__ import annotations

import ipaddress
from datetime import date, datetime
from zoneinfo import ZoneInfo

from .config import settings


def hoy() -> date:
    """Fecha actual en la zona horaria de la operación (no la del servidor)."""
    return datetime.now(ZoneInfo(settings.timezone)).date()


def ip_valida(valor: str | None) -> str | None:
    """Devuelve la IP normalizada o None (columnas INET rechazan textos como 'testclient')."""
    if not valor:
        return None
    try:
        return str(ipaddress.ip_address(valor.strip()))
    except ValueError:
        return None
