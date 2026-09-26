# =============================================================================
# SNCEV API — Endpoints clínicos: tamizajes, somatometría, desarrollo (módulo 4)
# =============================================================================

from __future__ import annotations

import uuid

from fastapi import APIRouter, Request, status

from ....db.session import DbDep
from ....middleware.auth import UserDep
from ....schemas.schemas import SomatometriaCreate, SomatometriaResponse
from ....schemas.schemas_extra import (
    DesarrolloCreate, DesarrolloOut, TamizajeCreate, TamizajeOut, TamizajePatch,
)
from ....services.clinico_service import ClinicoService

router = APIRouter(prefix="/pacientes/{paciente_id}", tags=["Clínico"])


@router.get("/tamizajes", response_model=list[TamizajeOut])
async def listar_tamizajes(paciente_id: uuid.UUID, db: DbDep, usuario: UserDep):
    usuario.requiere_permiso("PACIENTE_VER")
    return await ClinicoService(db, usuario).listar_tamizajes(paciente_id)


@router.post("/tamizajes", response_model=TamizajeOut, status_code=status.HTTP_201_CREATED)
async def crear_tamizaje(paciente_id: uuid.UUID, data: TamizajeCreate, request: Request, db: DbDep, usuario: UserDep):
    usuario.requiere_permiso("CLINICO_REGISTRAR")
    return await ClinicoService(db, usuario).registrar_tamizaje(paciente_id, data, request)


@router.get("/somatometria", response_model=list[SomatometriaResponse])
async def listar_somatometria(paciente_id: uuid.UUID, db: DbDep, usuario: UserDep):
    usuario.requiere_permiso("PACIENTE_VER")
    return await ClinicoService(db, usuario).listar_somatometria(paciente_id)


@router.post("/somatometria", response_model=SomatometriaResponse, status_code=status.HTTP_201_CREATED)
async def crear_somatometria(paciente_id: uuid.UUID, data: SomatometriaCreate, request: Request,
                             db: DbDep, usuario: UserDep):
    usuario.requiere_permiso("CLINICO_REGISTRAR")
    return await ClinicoService(db, usuario).registrar_somatometria(paciente_id, data, request)


@router.get("/desarrollo", response_model=list[DesarrolloOut])
async def listar_desarrollo(paciente_id: uuid.UUID, db: DbDep, usuario: UserDep):
    usuario.requiere_permiso("PACIENTE_VER")
    return await ClinicoService(db, usuario).listar_desarrollo(paciente_id)


@router.post("/desarrollo", response_model=DesarrolloOut, status_code=status.HTTP_201_CREATED)
async def crear_desarrollo(paciente_id: uuid.UUID, data: DesarrolloCreate, request: Request,
                           db: DbDep, usuario: UserDep):
    usuario.requiere_permiso("CLINICO_REGISTRAR")
    return await ClinicoService(db, usuario).registrar_desarrollo(paciente_id, data, request)
