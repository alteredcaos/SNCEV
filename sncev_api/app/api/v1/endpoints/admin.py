# =============================================================================
# SNCEV API — Endpoints de administración y auditoría (módulos 9 y 10)
# =============================================================================

from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import APIRouter, Query, Request, Response, status

from ....db.session import DbDep
from ....middleware.auth import UserDep
from ....schemas.schemas import PaginacionParams
from ....schemas.schemas_extra import (
    AuditLogDetalle, AuditLogPaginado, PermisoOut, RolOut, UsuarioCreate, UsuarioOut,
    UsuarioPaginado, UsuarioPatch,
)
from ....services.admin_service import AdminService

router = APIRouter(prefix="/admin", tags=["Administración"])


@router.get("/usuarios", response_model=UsuarioPaginado)
async def listar_usuarios(db: DbDep, usuario: UserDep, page: int = Query(1, ge=1),
                          per_page: int = Query(20, ge=1, le=100), rol_id: int | None = None,
                          activo: bool | None = None, unidad_medica_id: uuid.UUID | None = None,
                          q: str | None = None):
    usuario.requiere_permiso("ADMIN_USUARIOS")
    return await AdminService(db, usuario).listar_usuarios(
        PaginacionParams(page=page, per_page=per_page), rol_id, activo, unidad_medica_id, q)


@router.get("/usuarios/{usuario_id}", response_model=UsuarioOut)
async def obtener_usuario(usuario_id: uuid.UUID, db: DbDep, usuario: UserDep):
    usuario.requiere_permiso("ADMIN_USUARIOS")
    return await AdminService(db, usuario).obtener_usuario(usuario_id)


@router.post("/usuarios", status_code=status.HTTP_201_CREATED)
async def crear_usuario(data: UsuarioCreate, request: Request, db: DbDep, usuario: UserDep):
    usuario.requiere_permiso("ADMIN_USUARIOS")
    usuario_id = await AdminService(db, usuario).crear_usuario(data, request)
    return {"id": str(usuario_id)}


@router.patch("/usuarios/{usuario_id}", response_model=UsuarioOut)
async def actualizar_usuario(usuario_id: uuid.UUID, data: UsuarioPatch, request: Request,
                             db: DbDep, usuario: UserDep):
    usuario.requiere_permiso("ADMIN_USUARIOS")
    return await AdminService(db, usuario).actualizar_usuario(usuario_id, data, request)


@router.post("/usuarios/{usuario_id}/desbloquear", status_code=status.HTTP_204_NO_CONTENT)
async def desbloquear_usuario(usuario_id: uuid.UUID, request: Request, db: DbDep, usuario: UserDep):
    usuario.requiere_permiso("ADMIN_USUARIOS")
    await AdminService(db, usuario).desbloquear_usuario(usuario_id, request)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/roles", response_model=list[RolOut])
async def roles(db: DbDep, usuario: UserDep):
    usuario.requiere_permiso("ADMIN_USUARIOS")
    return await AdminService(db, usuario).roles()


@router.get("/roles/{rol_id}/permisos", response_model=list[PermisoOut])
async def permisos_de_rol(rol_id: int, db: DbDep, usuario: UserDep):
    usuario.requiere_permiso("ADMIN_USUARIOS")
    return await AdminService(db, usuario).permisos_de_rol(rol_id)


@router.get("/permisos", response_model=list[PermisoOut])
async def permisos(db: DbDep, usuario: UserDep):
    usuario.requiere_permiso("ADMIN_USUARIOS")
    return await AdminService(db, usuario).permisos()


router_auditoria = APIRouter(prefix="/auditoria", tags=["Auditoría"])


@router_auditoria.get("", response_model=AuditLogPaginado)
async def listar_auditoria(db: DbDep, usuario: UserDep, page: int = Query(1, ge=1),
                           per_page: int = Query(20, ge=1, le=100), usuario_id: uuid.UUID | None = None,
                           accion: str | None = None, modulo: str | None = None, resultado: str | None = None,
                           desde: datetime | None = None, hasta: datetime | None = None):
    usuario.requiere_permiso("AUDITORIA_VER")
    return await AdminService(db, usuario).auditoria(
        PaginacionParams(page=page, per_page=per_page), usuario_id, accion, modulo, resultado, desde, hasta)


@router_auditoria.get("/{audit_id}", response_model=AuditLogDetalle)
async def detalle_auditoria(audit_id: uuid.UUID, db: DbDep, usuario: UserDep):
    usuario.requiere_permiso("AUDITORIA_VER")
    return await AdminService(db, usuario).auditoria_detalle(audit_id)
