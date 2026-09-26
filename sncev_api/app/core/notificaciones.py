"""Envío de correos. Por defecto solo escribe en el log; sustituir `enviar` por SMTP / el servicio
de correo institucional para operar en producción."""
from __future__ import annotations

import logging

from .config import settings

log = logging.getLogger("sncev.notif")


async def enviar(destinatario: str, asunto: str, cuerpo: str) -> None:
    if settings.es_produccion:
        log.warning("correo_no_enviado: notificador sin configurar (asunto=%r)", asunto)
        return
    # Solo en desarrollo se imprime el cuerpo (contiene enlaces/tokens de un solo uso).
    log.info("CORREO [DEV] a=%s asunto=%r\n%s", destinatario, asunto, cuerpo)
