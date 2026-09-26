# =============================================================================
# SNCEV API — Endpoints de citas de vacunación (módulo 5)
# =============================================================================

from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import APIRouter, Query, Request, status

from ....db.session import DbDep
from ....middleware.auth import UserDep
from ....schemas.schemas import PaginacionParams
from ....schemas.schemas_extra import CitaCancelar, CitaCreate, CitaOut, CitaPaginada, CitaPatch
from ....services.cita_service import CitaService

router = APIRouter(prefix="/citas", tags=["Citas"])


@router.get("", response_model=CitaPaginada)
async def listar(db: DbDep, usuario: UserDep, page: int = Query(1, ge=1), per_page: int = Query(20, ge=1, le=100),
                 paciente_id: uuid.UUID | None = None, unidad_medica_id: uuid.UUID | None = None,
                 estado: str | None = None, fecha_desde: datetime | None = None,
                 fecha_hasta: datetime | None = None):
    usuario.requiere_permiso("CITA_VER")
    return await CitaService(db, usuario).listar(
        PaginacionParams(page=page, per_page=per_page), paciente_id, unidad_medica_id, estado,
        fecha_desde, fecha_hasta)


@router.post("", status_code=status.HTTP_201_CREATED)
async def crear(data: CitaCreate, request: Request, db: DbDep, usuario: UserDep):
    usuario.requiere_permiso("CITA_CREAR")
    cita_id = await CitaService(db, usuario).crear(data, request)
    return {"id": str(cita_id)}


@router.get("/{cita_id}", response_model=CitaOut)
async def obtener(cita_id: uuid.UUID, db: DbDep, usuario: UserDep):
    usuario.requiere_permiso("CITA_VER")
    return await CitaService(db, usuario).obtener(cita_id)


@router.patch("/{cita_id}", response_model=CitaOut)
async def actualizar(cita_id: uuid.UUID, data: CitaPatch, request: Request, db: DbDep, usuario: UserDep):
    usuario.requiere_permiso("CITA_EDITAR")
    return await CitaService(db, usuario).actualizar(cita_id, data, request)


@router.post("/{cita_id}/cancelar", response_model=CitaOut)
async def cancelar(cita_id: uuid.UUID, data: CitaCancelar, request: Request, db: DbDep, usuario: UserDep):
    usuario.requiere_permiso("CITA_EDITAR")
    await CitaService(db, usuario).cancelar(cita_id, data.motivo, request)
    return await CitaService(db, usuario).obtener(cita_id)
