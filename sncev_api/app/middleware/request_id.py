# =============================================================================
# SNCEV API — Middleware de request-id, cabeceras de seguridad y límite de tasa
# (rate limit en memoria; en producción usar el gateway/API management)
# =============================================================================

from __future__ import annotations

import time
import uuid
from collections import defaultdict, deque

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from ..core.config import settings

_LIMITES: dict[str, tuple[int, int]] = {   # prefijo de ruta -> (máximo, ventana_segundos)
    "/v1/auth/login": (10, 60),
    "/v1/auth/refresh": (30, 60),
    "/v1/fhir": (500, 60),
    "/v1/reportes/exportar": (5, 3600),
}
_LIMITE_DEFAULT = (300, 60)
_ventanas: dict[str, deque] = defaultdict(deque)


def _clave_limite(path: str) -> tuple[str, int, int]:
    for prefijo, (maximo, ventana) in _LIMITES.items():
        if path.startswith(prefijo):
            return prefijo, maximo, ventana
    return "__default__", *_LIMITE_DEFAULT


class SeguridadMiddleware(BaseHTTPMiddleware):
    """Agrega X-Request-ID, cabeceras de seguridad y aplica rate limit por IP+ruta."""

    async def dispatch(self, request: Request, call_next):
        request.state.request_id = uuid.uuid4()

        if settings.rate_limit_enabled:
            ip = request.client.host if request.client else "desconocido"
            prefijo, maximo, ventana = _clave_limite(request.url.path)
            clave = f"{ip}:{prefijo}"
            ahora = time.monotonic()
            cola = _ventanas[clave]
            while cola and ahora - cola[0] > ventana:
                cola.popleft()
            if len(cola) >= maximo:
                restante = max(0, ventana - (ahora - cola[0]))
                return Response(
                    content='{"error":"Límite de solicitudes excedido"}', status_code=429,
                    media_type="application/json",
                    headers={"Retry-After": str(int(restante) + 1), "X-Request-ID": str(request.state.request_id)},
                )
            cola.append(ahora)

        respuesta = await call_next(request)
        respuesta.headers["X-Request-ID"] = str(request.state.request_id)
        respuesta.headers["X-Content-Type-Options"] = "nosniff"
        respuesta.headers["X-Frame-Options"] = "DENY"
        if settings.es_produccion:
            respuesta.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        if "/fhir" in request.url.path or request.url.path.startswith("/v1/pacientes") \
                or request.url.path.startswith("/v1/vacunas"):
            respuesta.headers["Cache-Control"] = "no-store"
        return respuesta
