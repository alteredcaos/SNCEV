# =============================================================================
# SNCEV API — Endpoints de reportes y coberturas (módulo 8)
# =============================================================================

from __future__ import annotations

import uuid

from fastapi import APIRouter, Query, Request

from ....db.session import DbDep
from ....middleware.auth import UserDep
from ....schemas.schemas_extra import (
    CoberturaResponse, Dimension, ExportarRequest, ExportJobAceptado, ExportJobEstado,
    LoteResponse, MapaFila, RezagoResponse, TendenciaFila,
)
from ....services.reporte_service import ReporteService

router = APIRouter(prefix="/reportes", tags=["Reportes"])


@router.get("/cobertura", response_model=CoberturaResponse)
async def cobertura(db: DbDep, usuario: UserDep, anio: int, semana_desde: int = Query(1, ge=1, le=53),
                    semana_hasta: int = Query(53, ge=1, le=53), dimension: Dimension = "estado",
                    vacuna_id: int | None = None, numero_dosis: int | None = None,
                    tipo_cartilla_id: int | None = None, ageb_clave: str | None = None,
                    municipio_id: int | None = None, jurisdiccion_id: int | None = None,
                    estado_clave: str | None = None):
    usuario.requiere_permiso("REPORTE_VER")
    return await ReporteService(db, usuario).cobertura(
        anio, semana_desde, semana_hasta, dimension, vacuna_id, numero_dosis, tipo_cartilla_id,
        ageb_clave, municipio_id, jurisdiccion_id, estado_clave)


@router.get("/cobertura/tendencia", response_model=list[TendenciaFila])
async def tendencia(db: DbDep, usuario: UserDep, vacuna_id: int, numero_dosis: int | None = None,
                    estado_clave: str | None = None, municipio_id: int | None = None,
                    anio_desde: int = Query(...), anio_hasta: int = Query(...)):
    usuario.requiere_permiso("REPORTE_VER")
    return await ReporteService(db, usuario).tendencia(
        vacuna_id, numero_dosis, estado_clave, municipio_id, anio_desde, anio_hasta)


@router.get("/cobertura/mapa", response_model=list[MapaFila])
async def mapa(db: DbDep, usuario: UserDep, vacuna_id: int, anio: int, numero_dosis: int | None = None,
              semana: int | None = None, estado_clave: str | None = None, nivel: str = "estado"):
    usuario.requiere_permiso("REPORTE_VER")
    return await ReporteService(db, usuario).mapa(vacuna_id, numero_dosis, anio, semana, estado_clave, nivel)


@router.get("/lotes", response_model=LoteResponse)
async def lotes(db: DbDep, usuario: UserDep, lote: str, vacuna_id: int | None = None):
    usuario.requiere_permiso("REPORTE_VER")
    return await ReporteService(db, usuario).lotes(lote, vacuna_id)


@router.get("/rezago", response_model=RezagoResponse)
async def rezago(db: DbDep, usuario: UserDep, page: int = Query(1, ge=1), per_page: int = Query(20, ge=1, le=100),
                 tipo_cartilla_id: int | None = None, vacuna_id: int | None = None,
                 municipio_id: int | None = None, dias_rezago: int = Query(0, ge=0)):
    usuario.requiere_permiso("REPORTE_VER")
    return await ReporteService(db, usuario).rezago(page, per_page, tipo_cartilla_id, vacuna_id,
                                                     municipio_id, dias_rezago)


@router.post("/exportar", response_model=ExportJobAceptado, status_code=202)
async def exportar(data: ExportarRequest, request: Request, db: DbDep, usuario: UserDep):
    usuario.requiere_permiso("REPORTE_EXPORTAR")
    job_id = await ReporteService(db, usuario).solicitar_exportacion(data, request)
    return ExportJobAceptado(job_id=job_id)


@router.get("/exportar/{job_id}", response_model=ExportJobEstado)
async def estado_exportacion(job_id: uuid.UUID, db: DbDep, usuario: UserDep):
    usuario.requiere_permiso("REPORTE_EXPORTAR")
    job = await ReporteService(db, usuario).estado_exportacion(job_id)
    url = None
    if job.estado == "listo" and job.archivo:
        from ....core.storage import get_almacen
        url = get_almacen().url_temporal(job.archivo, f"export_{job.id}.{job.formato}",
                                         "text/csv" if job.formato == "csv" else
                                         "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    return ExportJobEstado(job_id=job.id, estado=job.estado, url=url, error=job.error)
