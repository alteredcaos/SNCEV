from __future__ import annotations

import uuid

from fastapi import APIRouter, Request

from ....db.session import DbDep
from ....middleware.auth import UserDep
from ....schemas.schemas_extra import TamizajeOut, TamizajePatch
from ....services.clinico_service import ClinicoService

router = APIRouter(prefix="/tamizajes", tags=["Clínico"])


@router.patch("/{tamizaje_id}", response_model=TamizajeOut)
async def editar(tamizaje_id: uuid.UUID, data: TamizajePatch, request: Request, db: DbDep, usuario: UserDep):
    usuario.requiere_permiso("CLINICO_REGISTRAR")
    return await ClinicoService(db, usuario).editar_tamizaje(tamizaje_id, data, request)
