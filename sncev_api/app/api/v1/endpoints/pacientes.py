# =============================================================================
# SNCEV API — Endpoints de pacientes y responsables (módulo 2)
# =============================================================================

from __future__ import annotations

import uuid

from fastapi import APIRouter, Query, Request, Response, status

from ....db.session import DbDep
from ....middleware.auth import UserDep
from ....schemas.schemas import (
    PacienteCreate, PacienteDetalle, PacientePaginado, PacientePatch, PaginacionParams,
    ResponsableInput, ResponsableOut, ResponsablePatch,
)
from ....services.paciente_service import PacienteService

router = APIRouter(prefix="/pacientes", tags=["Pacientes"])


@router.get("", response_model=PacientePaginado)
async def listar(db: DbDep, usuario: UserDep, page: int = Query(1, ge=1), per_page: int = Query(20, ge=1, le=100),
                 q: str | None = None, curp: str | None = None, sexo: str | None = None,
                 tipo_cartilla_id: int | None = None, municipio_id: int | None = None,
                 unidad_med_registro_id: uuid.UUID | None = None, activo: bool = True):
    usuario.requiere_permiso("PACIENTE_VER")
    return await PacienteService(db, usuario).buscar(
        PaginacionParams(page=page, per_page=per_page), q, curp, sexo, tipo_cartilla_id,
        municipio_id, unidad_med_registro_id, activo)


@router.post("", status_code=status.HTTP_201_CREATED)
async def crear(data: PacienteCreate, request: Request, db: DbDep, usuario: UserDep):
    usuario.requiere_permiso("PACIENTE_CREAR")
    paciente_id = await PacienteService(db, usuario).crear(data, request)
    return {"id": str(paciente_id)}


@router.get("/{paciente_id}", response_model=PacienteDetalle)
async def obtener(paciente_id: uuid.UUID, request: Request, db: DbDep, usuario: UserDep):
    usuario.requiere_permiso("PACIENTE_VER")
    return await PacienteService(db, usuario).obtener(paciente_id, request)


@router.patch("/{paciente_id}", status_code=status.HTTP_204_NO_CONTENT)
async def actualizar(paciente_id: uuid.UUID, data: PacientePatch, request: Request, db: DbDep, usuario: UserDep):
    usuario.requiere_permiso("PACIENTE_EDITAR")
    await PacienteService(db, usuario).actualizar(paciente_id, data, request)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete("/{paciente_id}", status_code=status.HTTP_204_NO_CONTENT)
async def desactivar(paciente_id: uuid.UUID, request: Request, db: DbDep, usuario: UserDep):
    usuario.requiere_permiso("PACIENTE_ELIMINAR")
    await PacienteService(db, usuario).desactivar(paciente_id, request)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{paciente_id}/responsables", response_model=list[ResponsableOut])
async def listar_responsables(paciente_id: uuid.UUID, request: Request, db: DbDep, usuario: UserDep):
    usuario.requiere_permiso("PACIENTE_VER")
    return await PacienteService(db, usuario).listar_responsables(paciente_id, request)


@router.post("/{paciente_id}/responsables", status_code=status.HTTP_201_CREATED)
async def crear_responsable(paciente_id: uuid.UUID, data: ResponsableInput, request: Request,
                            db: DbDep, usuario: UserDep):
    usuario.requiere_permiso("PACIENTE_EDITAR")
    responsable_id = await PacienteService(db, usuario).crear_responsable(paciente_id, data, request)
    return {"id": str(responsable_id)}


@router.patch("/{paciente_id}/responsables/{responsable_id}", status_code=status.HTTP_204_NO_CONTENT)
async def actualizar_responsable(paciente_id: uuid.UUID, responsable_id: uuid.UUID, data: ResponsablePatch,
                                 request: Request, db: DbDep, usuario: UserDep):
    usuario.requiere_permiso("PACIENTE_EDITAR")
    await PacienteService(db, usuario).actualizar_responsable(paciente_id, responsable_id, data, request)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete("/{paciente_id}/responsables/{responsable_id}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_responsable(paciente_id: uuid.UUID, responsable_id: uuid.UUID, request: Request,
                               db: DbDep, usuario: UserDep):
    usuario.requiere_permiso("PACIENTE_EDITAR")
    await PacienteService(db, usuario).eliminar_responsable(paciente_id, responsable_id, request)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
