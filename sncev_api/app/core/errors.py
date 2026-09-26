# =============================================================================
# SNCEV API — Errores y manejadores globales (formato {"error": "..."} del OpenAPI)
# =============================================================================

from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import DBAPIError, IntegrityError
from starlette.exceptions import HTTPException as StarletteHTTPException

log = logging.getLogger("sncev.api")


class ApiError(HTTPException):
    """HTTPException con campos extra en el cuerpo (p. ej. desbloqueada_at, paciente_id)."""

    def __init__(self, status_code: int, mensaje: str, headers: dict[str, str] | None = None, **extra: Any):
        super().__init__(status_code=status_code, detail=mensaje, headers=headers)
        self.extra = extra


class PermisoDenegado(ApiError):
    def __init__(self, permiso: str):
        super().__init__(403, "No tiene permiso para esta operación")
        self.permiso = permiso


def _json(status: int, mensaje: str, extra: dict[str, Any] | None = None,
          headers: dict[str, str] | None = None) -> JSONResponse:
    return JSONResponse({"error": mensaje, **(extra or {})}, status_code=status, headers=headers)


def _sqlstate(exc: DBAPIError) -> str | None:
    orig = getattr(exc, "orig", None)
    # SQLAlchemy envuelve la excepción de asyncpg; el código está en .sqlstate/.pgcode
    for obj in (orig, getattr(orig, "__cause__", None)):
        codigo = getattr(obj, "sqlstate", None) or getattr(obj, "pgcode", None)
        if codigo:
            return codigo
    return None


def registrar_manejadores(app: FastAPI) -> None:
    @app.exception_handler(PermisoDenegado)
    async def _denegado(request: Request, exc: PermisoDenegado):
        # Se audita en una sesión aparte (la de la petición se revierte al fallar).
        from ..middleware.auth import auditar_denegado
        await auditar_denegado(request, exc.permiso)
        return _json(403, str(exc.detail))

    @app.exception_handler(ApiError)
    async def _api(request: Request, exc: ApiError):
        return _json(exc.status_code, str(exc.detail), exc.extra, exc.headers)

    @app.exception_handler(StarletteHTTPException)
    async def _http(request: Request, exc: StarletteHTTPException):
        return _json(exc.status_code, str(exc.detail), None, getattr(exc, "headers", None))

    @app.exception_handler(RequestValidationError)
    async def _validacion(request: Request, exc: RequestValidationError):
        # No se devuelve `input`: podría contener contraseñas o datos personales.
        detalle = [{"campo": ".".join(str(p) for p in e["loc"] if p != "body"), "mensaje": e["msg"]}
                   for e in exc.errors()]
        return _json(400, "Datos inválidos", {"detalle": detalle})

    @app.exception_handler(IntegrityError)
    async def _integridad(request: Request, exc: IntegrityError):
        codigo = _sqlstate(exc)
        if codigo == "23505":
            return _json(409, "Registro duplicado")
        if codigo in ("23503", "23514", "23502"):
            return _json(422, "Datos inconsistentes: referencia inexistente o valor no permitido")
        log.exception("integridad_no_clasificada")
        return _json(500, "Error interno del servidor")

    @app.exception_handler(DBAPIError)
    async def _dbapi(request: Request, exc: DBAPIError):
        codigo = _sqlstate(exc)
        if codigo == "42501":   # insufficient_privilege: incluye violaciones de RLS
            return _json(403, "Sin permiso para esta operación en su ámbito")
        if codigo and codigo.startswith("22"):   # datos con formato inválido
            return _json(400, "Dato con formato inválido")
        log.exception("error_bd")
        return _json(500, "Error interno del servidor", {"request_id": str(getattr(request.state, "request_id", ""))})

    @app.exception_handler(Exception)
    async def _generico(request: Request, exc: Exception):
        log.exception("error_no_controlado")
        return _json(500, "Error interno del servidor", {"request_id": str(getattr(request.state, "request_id", ""))})
