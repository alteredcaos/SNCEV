# =============================================================================
# SNCEV API — Router raíz de la versión v1
# =============================================================================

from __future__ import annotations

from fastapi import APIRouter

from .endpoints import (
    admin, archivos, auth, cartilla, catalogos, citas, clinico, fhir, pacientes, reportes,
    sync, tamizajes, vacunas,
)

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(pacientes.router)
api_router.include_router(vacunas.router)
api_router.include_router(clinico.router)
api_router.include_router(tamizajes.router)
api_router.include_router(citas.router)
api_router.include_router(catalogos.router)
api_router.include_router(cartilla.router)
api_router.include_router(cartilla.router_publico)
api_router.include_router(sync.router)
api_router.include_router(admin.router)
api_router.include_router(admin.router_auditoria)
api_router.include_router(reportes.router)
api_router.include_router(archivos.router)
api_router.include_router(fhir.router)
