# =============================================================================
# SNCEV API — Almacenamiento de archivos (PDF de cartillas, exportaciones)
# Implementación local con URLs temporales firmadas (HMAC + expiración), con la
# misma interfaz que tendría un backend S3 (guardar/leer/url_temporal), para que
# sustituirlo en producción no toque el resto del código.
# =============================================================================

from __future__ import annotations

import asyncio
import base64
import hashlib
import hmac
import json
import time
from functools import lru_cache
from pathlib import Path

from .config import settings


def _firma_urls() -> bytes:
    # Separación de dominio respecto a la clave AES de cifrado de columnas.
    clave = bytes.fromhex(settings.aes_key_hex.get_secret_value())
    return hashlib.sha256(clave + b"|urls-temporales").digest()


class AlmacenLocal:
    def __init__(self, base: Path) -> None:
        self.base = base.resolve()
        self.base.mkdir(parents=True, exist_ok=True)

    def _ruta(self, clave: str) -> Path:
        ruta = (self.base / clave).resolve()
        if self.base not in ruta.parents and ruta != self.base:
            raise ValueError("clave de almacenamiento inválida")
        return ruta

    async def guardar(self, clave: str, datos: bytes) -> None:
        ruta = self._ruta(clave)

        def _escribir() -> None:
            ruta.parent.mkdir(parents=True, exist_ok=True)
            ruta.write_bytes(datos)

        await asyncio.to_thread(_escribir)

    async def leer(self, clave: str) -> bytes:
        return await asyncio.to_thread(self._ruta(clave).read_bytes)

    def url_temporal(self, clave: str, nombre: str, tipo: str, ttl: int | None = None) -> str:
        exp = int(time.time()) + (ttl or settings.url_ttl_segundos)
        cuerpo = base64.urlsafe_b64encode(
            json.dumps({"k": clave, "e": exp, "n": nombre, "t": tipo}).encode()
        ).decode().rstrip("=")
        firma = hmac.new(_firma_urls(), cuerpo.encode(), hashlib.sha256).hexdigest()
        return f"{settings.public_base_url.rstrip('/')}/v1/archivos/{cuerpo}.{firma}"

    def resolver_token(self, token: str) -> dict | None:
        try:
            cuerpo, firma = token.rsplit(".", 1)
            if not hmac.compare_digest(hmac.new(_firma_urls(), cuerpo.encode(), hashlib.sha256).hexdigest(), firma):
                return None
            datos = json.loads(base64.urlsafe_b64decode(cuerpo + "=" * (-len(cuerpo) % 4)))
            return datos if datos["e"] >= time.time() else None
        except Exception:  # noqa: BLE001
            return None

    def ruta_de(self, clave: str) -> Path:
        return self._ruta(clave)


@lru_cache
def get_almacen() -> AlmacenLocal:
    return AlmacenLocal(settings.storage_dir)
