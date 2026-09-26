# =============================================================================
# SNCEV API — Endpoints de sincronización offline (módulo 11)
# =============================================================================

from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import APIRouter, Query

from ....db.session import DbDep
from ....middleware.auth import UserDep
from ....schemas.schemas_extra import SyncPullResponse, SyncPushRequest, SyncPushResponse
from ....services.sync_service import SyncService

router = APIRouter(prefix="/sync", tags=["Sincronización"])


@router.post("/push", response_model=SyncPushResponse)
async def push(data: SyncPushRequest, db: DbDep, usuario: UserDep):
    usuario.requiere_permiso("VACUNA_APLICAR")
    return await SyncService(db, usuario).push(data.device_id, data.registros)


@router.get("/pull", response_model=SyncPullResponse)
async def pull(db: DbDep, usuario: UserDep, last_sync_at: datetime | None = Query(None),
              unidad_medica_id: uuid.UUID | None = None):
    usuario.requiere_permiso("PACIENTE_VER")
    return await SyncService(db, usuario).pull(last_sync_at, unidad_medica_id)
