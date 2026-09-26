# =============================================================================
# SNCEV API — Punto de entrada de la aplicación FastAPI
# =============================================================================

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.v1.router import api_router
from .core.config import settings
from .core.errors import registrar_manejadores
from .db.session import engine
from .middleware.request_id import SeguridadMiddleware

logging.basicConfig(level=settings.log_level, format="%(asctime)s %(levelname)s %(name)s %(message)s")
log = logging.getLogger("sncev.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("sncev_api_iniciando entorno=%s", settings.environment)
    yield
    await engine.dispose()
    log.info("sncev_api_detenida")


app = FastAPI(
    title=settings.app_name, version=settings.app_version, lifespan=lifespan,
    docs_url="/docs" if not settings.es_produccion else None,
    redoc_url="/redoc" if not settings.es_produccion else None,
    openapi_url="/openapi.json" if not settings.es_produccion else None,
)

app.add_middleware(SeguridadMiddleware)

if settings.allowed_origins:
    app.add_middleware(
        CORSMiddleware, allow_origins=settings.allowed_origins, allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"], allow_headers=["*"],
    )

registrar_manejadores(app)
app.include_router(api_router, prefix="/api/v1")


@app.get("/health", tags=["Sistema"])
async def health():
    return {"status": "ok", "version": settings.app_version}


if settings.prometheus_enabled:
    try:
        from prometheus_fastapi_instrumentator import Instrumentator
        # /metrics no lleva autenticación de aplicación: en producción debe protegerse a
        # nivel de red (firewall/gateway), como es práctica estándar de Prometheus — nunca
        # exponerlo directamente a Internet.
        Instrumentator().instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)
    except ImportError:
        log.warning("PROMETHEUS_ENABLED=true pero prometheus-fastapi-instrumentator no está instalado")
