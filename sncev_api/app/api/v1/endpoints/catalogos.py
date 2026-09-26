# =============================================================================
# SNCEV API — Endpoints de catálogos (módulo 6, solo lectura)
# =============================================================================

from __future__ import annotations

import uuid

from fastapi import APIRouter, Query

from ....db.session import DbDep
from ....middleware.auth import UserDep
from ....schemas.schemas_extra import (
    EsquemaOut, EstadoOut, JurisdiccionOut, MunicipioOut, TipoCartillaOut, UnidadMedicaOut,
    VacunaCatalogoOut,
)
from ....services.catalogo_service import CatalogoService

router = APIRouter(tags=["Catálogos"])


@router.get("/catalogos/vacunas", response_model=list[VacunaCatalogoOut])
async def vacunas(db: DbDep, usuario: UserDep, tipo_cartilla_id: int | None = None, activo: bool | None = True):
    return await CatalogoService(db).vacunas(tipo_cartilla_id, activo)


@router.get("/catalogos/vacunas/{vacuna_id}", response_model=VacunaCatalogoOut)
async def vacuna(vacuna_id: int, db: DbDep, usuario: UserDep):
    return await CatalogoService(db).vacuna(vacuna_id)


@router.get("/catalogos/vacunas/{vacuna_id}/esquemas", response_model=list[EsquemaOut])
async def esquemas_de_vacuna(vacuna_id: int, db: DbDep, usuario: UserDep):
    return await CatalogoService(db).esquemas_de_vacuna(vacuna_id)


@router.get("/catalogos/esquemas", response_model=list[EsquemaOut])
async def esquemas(db: DbDep, usuario: UserDep, tipo_cartilla_id: int | None = None, vacuna_id: int | None = None):
    return await CatalogoService(db).esquemas(tipo_cartilla_id, vacuna_id)


@router.get("/catalogos/tipos-cartilla", response_model=list[TipoCartillaOut])
async def tipos_cartilla(db: DbDep, usuario: UserDep):
    return await CatalogoService(db).tipos_cartilla()


@router.get("/catalogos/unidades-medicas", response_model=list[UnidadMedicaOut])
async def unidades_medicas(db: DbDep, usuario: UserDep, estado: str | None = None, municipio_id: int | None = None,
                           jurisdiccion_id: int | None = None, tipo: str | None = None, q: str | None = None,
                           lat: float | None = None, lng: float | None = None,
                           radio_km: int | None = Query(None, le=200)):
    return await CatalogoService(db).unidades_medicas(estado, municipio_id, jurisdiccion_id, tipo, q,
                                                       lat, lng, radio_km)


@router.get("/catalogos/unidades-medicas/{unidad_id}", response_model=UnidadMedicaOut)
async def unidad_medica(unidad_id: uuid.UUID, db: DbDep, usuario: UserDep):
    return await CatalogoService(db).unidad_medica(unidad_id)


@router.get("/catalogos/jurisdicciones", response_model=list[JurisdiccionOut])
async def jurisdicciones(db: DbDep, usuario: UserDep, estado: str | None = None):
    return await CatalogoService(db).jurisdicciones(estado)


@router.get("/catalogos/estados", response_model=list[EstadoOut])
async def estados(db: DbDep, usuario: UserDep):
    return await CatalogoService(db).estados()


@router.get("/catalogos/municipios", response_model=list[MunicipioOut])
async def municipios(db: DbDep, usuario: UserDep, estado: str | None = None):
    return await CatalogoService(db).municipios(estado)
