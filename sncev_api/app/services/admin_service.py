# =============================================================================
# SNCEV API — Administración: usuarios, roles, permisos y consulta de auditoría
# =============================================================================

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import Request
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.errors import ApiError
from ..core.security import cifrar, cifrar_nullable, hash_busqueda, hash_password, normalizar_email
from ..middleware.auth import UsuarioActual, registrar_audit
from ..models.models import AuditLog, Rol, Usuario
from ..models.models_extra import Permiso
from ..schemas.schemas import PaginacionParams, total_paginas
from ..schemas.schemas_extra import (
    AuditLogDetalle, AuditLogOut, AuditLogPaginado, PermisoOut, RolOut, UsuarioCreate,
    UsuarioOut, UsuarioPaginado, UsuarioPatch,
)

_TABLA = "sncev_admin.usuario"


def _usuario_out(u: Usuario, email: str | None, nombre: str | None) -> UsuarioOut:
    return UsuarioOut(
        id=u.id, username=u.username, email=email, rol_id=u.rol_id, rol=u.rol.nombre,
        nivel_acceso=u.rol.nivel_acceso, unidad_medica_id=u.unidad_medica_id,
        jurisdiccion_id=u.jurisdiccion_id, estado_clave=u.estado_clave, nombre=nombre,
        cedula_profesional=u.cedula_profesional, especialidad=u.especialidad, activo=u.activo,
        mfa_habilitado=u.mfa_habilitado, email_verificado=u.email_verificado,
        ultimo_acceso=u.ultimo_acceso, requiere_cambio_pwd=u.requiere_cambio_pwd,
        created_at=u.created_at,
    )


class AdminService:

    def __init__(self, db: AsyncSession, usuario: UsuarioActual):
        self.db = db
        self.u = usuario

    # ─────────────────────────────────────────────────────────────────────────
    # Usuarios
    # ─────────────────────────────────────────────────────────────────────────

    async def listar_usuarios(self, pag: PaginacionParams, rol_id: int | None, activo: bool | None,
                              unidad_medica_id: uuid.UUID | None, q: str | None) -> UsuarioPaginado:
        conds = []
        if rol_id:
            conds.append(Usuario.rol_id == rol_id)
        if activo is not None:
            conds.append(Usuario.activo.is_(activo))
        if unidad_medica_id:
            conds.append(Usuario.unidad_medica_id == unidad_medica_id)
        if q:
            conds.append(Usuario.username.ilike(f"%{q.strip()}%"))

        total = (await self.db.execute(select(func.count()).select_from(Usuario).where(*conds))).scalar_one()
        filas = (await self.db.execute(
            select(Usuario).where(*conds).order_by(Usuario.username)
            .limit(pag.per_page).offset(pag.offset))).scalars().all()
        return UsuarioPaginado(
            data=[_usuario_out(u, None, None) for u in filas],  # datos sensibles no se descifran en listados
            total=total, page=pag.page, pages=total_paginas(total, pag.per_page),
        )

    async def obtener_usuario(self, usuario_id: uuid.UUID) -> UsuarioOut:
        from ..core.security import descifrar_nullable
        u = (await self.db.execute(select(Usuario).where(Usuario.id == usuario_id))).scalar_one_or_none()
        if u is None:
            raise ApiError(404, "Usuario no encontrado")
        self.u.requiere_permiso("ADMIN_USUARIOS")   # ver correo/nombre en claro requiere permiso de admin
        return _usuario_out(u, descifrar_nullable(u.email_enc), descifrar_nullable(u.nombre_enc))

    async def crear_usuario(self, data: UsuarioCreate, request: Request | None = None) -> uuid.UUID:
        rol = await self.db.get(Rol, data.rol_id)
        if rol is None or not rol.activo:
            raise ApiError(422, "rol_id no existe o está inactivo")
        if rol.nivel_acceso > self.u.nivel:
            raise ApiError(403, "No puede crear usuarios con un nivel de acceso mayor al suyo")

        email_hash = hash_busqueda(normalizar_email(data.email))
        if (await self.db.execute(select(Usuario.id).where(
                (Usuario.username == data.username) | (Usuario.email_hash == email_hash)))).first():
            raise ApiError(409, "El username o el correo ya están en uso")

        u = Usuario(
            username=data.username, email_enc=cifrar(normalizar_email(data.email)), email_hash=email_hash,
            password_hash=hash_password(data.password_inicial), rol_id=data.rol_id,
            unidad_medica_id=data.unidad_medica_id, jurisdiccion_id=data.jurisdiccion_id,
            estado_clave=data.estado_clave, nombre_enc=cifrar_nullable(data.nombre),
            cedula_profesional=data.cedula_profesional, especialidad=data.especialidad,
            mfa_habilitado=data.mfa_habilitado, requiere_cambio_pwd=True,
        )
        self.db.add(u)
        await self.db.flush()
        await registrar_audit(self.db, self.u, "INSERT", "Admin", _TABLA, u.id, request=request,
                              datos_nue={"username": data.username, "rol_id": data.rol_id})
        return u.id

    async def actualizar_usuario(self, usuario_id: uuid.UUID, data: UsuarioPatch,
                                 request: Request | None = None) -> UsuarioOut:
        campos = data.model_dump(exclude_unset=True)
        if not campos:
            raise ApiError(400, "No se enviaron campos para actualizar")
        u = (await self.db.execute(select(Usuario).where(Usuario.id == usuario_id))).scalar_one_or_none()
        if u is None:
            raise ApiError(404, "Usuario no encontrado")

        if "rol_id" in campos:
            rol = await self.db.get(Rol, campos["rol_id"])
            if rol is None or not rol.activo:
                raise ApiError(422, "rol_id no existe o está inactivo")
            if rol.nivel_acceso > self.u.nivel or u.rol.nivel_acceso > self.u.nivel:
                raise ApiError(403, "No puede modificar usuarios con nivel de acceso mayor al suyo")

        antes = {}
        for campo, valor in campos.items():
            if campo == "nombre":
                u.nombre_enc = cifrar_nullable(valor)
                continue
            antes[campo] = getattr(u, campo)
            setattr(u, campo, valor)
        await self.db.flush()

        await registrar_audit(self.db, self.u, "UPDATE", "Admin", _TABLA, usuario_id, request=request,
                              datos_ant=antes, datos_nue={k: v for k, v in campos.items() if k != "nombre"})
        return await self.obtener_usuario(usuario_id)

    async def desbloquear_usuario(self, usuario_id: uuid.UUID, request: Request | None = None) -> None:
        res = await self.db.execute(
            update(Usuario).where(Usuario.id == usuario_id)
            .values(bloqueado_hasta=None, intentos_fallidos=0).returning(Usuario.id))
        if res.first() is None:
            raise ApiError(404, "Usuario no encontrado")
        await registrar_audit(self.db, self.u, "UPDATE", "Admin", _TABLA, usuario_id, request=request,
                              datos_nue={"accion": "desbloqueo_manual"})

    # ─────────────────────────────────────────────────────────────────────────
    # Roles y permisos (solo lectura: se administran por migración)
    # ─────────────────────────────────────────────────────────────────────────

    async def roles(self) -> list[RolOut]:
        filas = (await self.db.execute(select(Rol).where(Rol.activo.is_(True))
                                       .order_by(Rol.nivel_acceso.desc()))).scalars().all()
        return [RolOut.model_validate(r, from_attributes=True) for r in filas]

    async def permisos_de_rol(self, rol_id: int) -> list[PermisoOut]:
        from sqlalchemy import text
        if await self.db.get(Rol, rol_id) is None:
            raise ApiError(404, "Rol no encontrado")
        filas = (await self.db.execute(
            text("""SELECT p.id, p.codigo, p.descripcion FROM sncev_admin.rol_permiso rp
                    JOIN sncev_admin.permiso p ON p.id = rp.permiso_id
                    WHERE rp.rol_id = :rol_id AND p.activo ORDER BY p.codigo"""),
            {"rol_id": rol_id},
        )).all()
        return [PermisoOut(id=i, codigo=c, descripcion=d) for i, c, d in filas]

    async def permisos(self) -> list[PermisoOut]:
        filas = (await self.db.execute(select(Permiso).where(Permiso.activo.is_(True))
                                       .order_by(Permiso.codigo))).scalars().all()
        return [PermisoOut.model_validate(p, from_attributes=True) for p in filas]

    # ─────────────────────────────────────────────────────────────────────────
    # Auditoría (solo lectura)
    # ─────────────────────────────────────────────────────────────────────────

    async def auditoria(self, pag: PaginacionParams, usuario_id: uuid.UUID | None, accion: str | None,
                        modulo: str | None, resultado: str | None, desde: datetime | None,
                        hasta: datetime | None) -> AuditLogPaginado:
        conds = []
        if usuario_id:
            conds.append(AuditLog.usuario_id == usuario_id)
        if accion:
            conds.append(AuditLog.accion == accion)
        if modulo:
            conds.append(AuditLog.modulo == modulo)
        if resultado:
            conds.append(AuditLog.resultado == resultado)
        if desde:
            conds.append(AuditLog.created_at >= desde)
        if hasta:
            conds.append(AuditLog.created_at <= hasta)

        total = (await self.db.execute(select(func.count()).select_from(AuditLog).where(*conds))).scalar_one()
        filas = (await self.db.execute(
            select(AuditLog).where(*conds).order_by(AuditLog.created_at.desc())
            .limit(pag.per_page).offset(pag.offset))).scalars().all()
        return AuditLogPaginado(
            data=[AuditLogOut.model_validate(a, from_attributes=True) for a in filas],
            total=total, page=pag.page, pages=total_paginas(total, pag.per_page),
        )

    async def auditoria_detalle(self, audit_id: uuid.UUID) -> AuditLogDetalle:
        a = await self.db.get(AuditLog, audit_id)
        if a is None:
            raise ApiError(404, "Registro de auditoría no encontrado")
        return AuditLogDetalle.model_validate(a, from_attributes=True)
