# =============================================================================
# SNCEV API — Endpoints de vacunación (módulo 3)
# =============================================================================

from __future__ import annotations

import uuid

from fastapi import APIRouter, Request, Response, status

from ....db.session import DbDep
from ....middleware.auth import UserDep
from ....schemas.schemas import (
    HistorialVacunacion, InvalidarRequest, VacunaAplicadaCreate, VacunaAplicadaResponse,
    VacunaEditar, VacunaPendiente, VacunaRegistrada,
)
from ....services.vacuna_service import VacunaService

router = APIRouter(tags=["Vacunación"])


@router.get("/pacientes/{paciente_id}/vacunas", response_model=HistorialVacunacion)
async def historial(paciente_id: uuid.UUID, db: DbDep, usuario: UserDep):
    usuario.requiere_permiso("PACIENTE_VER")
    return await VacunaService(db, usuario).historial(paciente_id)


@router.get("/pacientes/{paciente_id}/vacunas/pendientes", response_model=list[VacunaPendiente])
async def pendientes(paciente_id: uuid.UUID, db: DbDep, usuario: UserDep):
    usuario.requiere_permiso("PACIENTE_VER")
    return await VacunaService(db, usuario).pendientes(paciente_id)


@router.post("/pacientes/{paciente_id}/vacunas", response_model=VacunaRegistrada, status_code=status.HTTP_201_CREATED)
async def aplicar(paciente_id: uuid.UUID, data: VacunaAplicadaCreate, db: DbDep, usuario: UserDep):
    usuario.requiere_permiso("VACUNA_APLICAR")
    return await VacunaService(db, usuario).aplicar(paciente_id, data)


@router.get("/vacunas/{vacuna_aplicada_id}", response_model=VacunaAplicadaResponse)
async def obtener(vacuna_aplicada_id: uuid.UUID, db: DbDep, usuario: UserDep):
    usuario.requiere_permiso("PACIENTE_VER")
    return await VacunaService(db, usuario).obtener(vacuna_aplicada_id)


@router.patch("/vacunas/{vacuna_aplicada_id}", response_model=VacunaAplicadaResponse)
async def editar(vacuna_aplicada_id: uuid.UUID, data: VacunaEditar, db: DbDep, usuario: UserDep):
    usuario.requiere_permiso("VACUNA_APLICAR")
    return await VacunaService(db, usuario).editar(vacuna_aplicada_id, data)


@router.post("/vacunas/{vacuna_aplicada_id}/invalidar", status_code=status.HTTP_204_NO_CONTENT)
async def invalidar(vacuna_aplicada_id: uuid.UUID, data: InvalidarRequest, db: DbDep, usuario: UserDep):
    usuario.requiere_permiso("VACUNA_INVALIDAR")
    await VacunaService(db, usuario).invalidar(vacuna_aplicada_id, data.motivo)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
