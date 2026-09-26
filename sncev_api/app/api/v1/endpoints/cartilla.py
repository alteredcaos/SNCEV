# =============================================================================
# SNCEV API — Endpoints de cartilla electrónica: consulta, generación y
# verificación pública por QR (módulo 7)
# =============================================================================

from __future__ import annotations

import uuid

from fastapi import APIRouter, Request

from ....db.session import DbDep
from ....middleware.auth import UserDep
from ....schemas.schemas_extra import CartillaGenerada, CartillaGenerarRequest, CartillaVerificacion
from ....services.cartilla_service import CartillaService

router = APIRouter(tags=["Cartilla"])


@router.get("/pacientes/{paciente_id}/cartilla")
async def obtener(paciente_id: uuid.UUID, db: DbDep, usuario: UserDep):
    usuario.requiere_permiso("PACIENTE_VER")
    return await CartillaService(db, usuario).obtener_completa(paciente_id)


@router.post("/pacientes/{paciente_id}/cartilla/generar", response_model=CartillaGenerada)
async def generar(paciente_id: uuid.UUID, data: CartillaGenerarRequest, request: Request,
                  db: DbDep, usuario: UserDep):
    usuario.requiere_permiso("CARTILLA_FIRMAR")
    return await CartillaService(db, usuario).generar(paciente_id, data, request)


# PÚBLICO: sin autenticación, no expone datos personales (ver CartillaService.verificar_qr)
router_publico = APIRouter(tags=["Cartilla"])


@router_publico.get("/cartilla/verificar/{qr_token}", response_model=CartillaVerificacion)
async def verificar(qr_token: uuid.UUID, db: DbDep):
    from ....db.session import ContextoRLS, fijar_contexto

    await fijar_contexto(db, ContextoRLS.sistema())
    return await CartillaService(db, usuario=None).verificar_qr(qr_token)  # type: ignore[arg-type]
