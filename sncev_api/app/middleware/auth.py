# =============================================================================
# SNCEV API — Autenticación por JWT, permisos (RBAC) y bitácora de auditoría
# =============================================================================

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from typing import Annotated, Any

import jwt
from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.config import settings
from ..core.errors import ApiError, PermisoDenegado
from ..core.security import decodificar_access_token
from ..core.utils import ip_valida
from ..db.session import AsyncSessionLocal, ContextoRLS, DbDep, fijar_contexto
from ..models.models import AuditLog

log = logging.getLogger("sncev.auth")
_bearer = HTTPBearer(auto_error=False)

# Claves que nunca deben llegar a la bitácora en claro (datos personales / secretos).
_SENSIBLES = {
    "nombre", "ap_paterno", "ap_materno", "curp", "nss_imss", "telefono", "telefono2", "email",
    "domicilio_calle", "password", "password_actual", "password_nuevo", "password_confirm",
    "refresh_token", "token", "codigo_totp", "session_token",
}


def ip_cliente(request: Request) -> str | None:
    if settings.trust_forwarded_for:
        xff = request.headers.get("x-forwarded-for")
        if xff:
            return ip_valida(xff.split(",")[0])
    return ip_valida(request.client.host if request.client else None)


@dataclass(frozen=True)
class UsuarioActual:
    usuario_id: uuid.UUID
    username: str
    rol: str
    nivel: int
    permisos: frozenset[str] = field(default_factory=frozenset)
    unidad_id: uuid.UUID | None = None
    jurisdiccion_id: int | None = None
    estado_clave: str | None = None
    requiere_cambio_pwd: bool = False
    ip: str | None = None
    user_agent: str | None = None
    request_id: uuid.UUID | None = None

    def tiene_permiso(self, permiso: str) -> bool:
        return permiso in self.permisos

    def requiere_permiso(self, permiso: str) -> None:
        if permiso not in self.permisos:
            raise PermisoDenegado(permiso)

    def requiere_alguno(self, *permisos: str) -> None:
        if not any(p in self.permisos for p in permisos):
            raise PermisoDenegado("|".join(permisos))

    def a_contexto(self) -> ContextoRLS:
        return ContextoRLS(self.usuario_id, self.username, self.nivel, self.unidad_id,
                           self.jurisdiccion_id, self.estado_clave)


def _request_id(request: Request) -> uuid.UUID | None:
    try:
        return uuid.UUID(str(getattr(request.state, "request_id", "")))
    except ValueError:
        return None


async def _autenticar(request: Request, cred: HTTPAuthorizationCredentials | None,
                      db: AsyncSession, permitir_cambio_pwd: bool) -> UsuarioActual:
    cabecera = {"WWW-Authenticate": "Bearer"}
    if cred is None or cred.scheme.lower() != "bearer":
        raise ApiError(401, "Token de acceso ausente", headers=cabecera)
    try:
        p: dict[str, Any] = decodificar_access_token(cred.credentials)
    except jwt.ExpiredSignatureError:
        raise ApiError(401, "Token expirado", headers=cabecera)
    except jwt.PyJWTError:
        raise ApiError(401, "Token inválido", headers=cabecera)

    if p.get("pwd") and not permitir_cambio_pwd:
        raise ApiError(403, "Debe cambiar su contraseña antes de continuar")

    try:
        usuario = UsuarioActual(
            usuario_id=uuid.UUID(p["sub"]), username=p.get("username", ""), rol=p.get("rol", ""),
            nivel=int(p.get("nivel", 1)), permisos=frozenset(p.get("permisos", [])),
            unidad_id=uuid.UUID(p["unidad_id"]) if p.get("unidad_id") else None,
            jurisdiccion_id=p.get("jurisdiccion"), estado_clave=p.get("estado"),
            requiere_cambio_pwd=bool(p.get("pwd")), ip=ip_cliente(request),
            user_agent=request.headers.get("user-agent"), request_id=_request_id(request),
        )
    except (KeyError, ValueError, TypeError):
        raise ApiError(401, "Token inválido", headers=cabecera)

    request.state.usuario = usuario
    await fijar_contexto(db, usuario.a_contexto())      # RLS y triggers de auditoría del DDL
    return usuario


async def get_current_user(request: Request, db: DbDep,
                           cred: HTTPAuthorizationCredentials | None = Depends(_bearer)) -> UsuarioActual:
    return await _autenticar(request, cred, db, permitir_cambio_pwd=False)


async def get_current_user_cambio_pwd(request: Request, db: DbDep,
                                      cred: HTTPAuthorizationCredentials | None = Depends(_bearer)) -> UsuarioActual:
    """Igual que get_current_user pero permite tokens con cambio de contraseña pendiente."""
    return await _autenticar(request, cred, db, permitir_cambio_pwd=True)


def requiere(*permisos: str):
    """Dependencia: exige TODOS los permisos indicados. Uso: Depends(requiere("PACIENTE_VER"))."""
    async def _dep(usuario: UsuarioActual = Depends(get_current_user)) -> UsuarioActual:
        for p in permisos:
            usuario.requiere_permiso(p)
        return usuario
    return _dep


async def get_request_id(request: Request) -> str:
    return str(getattr(request.state, "request_id", ""))


UserDep = Annotated[UsuarioActual, Depends(get_current_user)]
UserCambioPwdDep = Annotated[UsuarioActual, Depends(get_current_user_cambio_pwd)]
ReqIdDep = Annotated[str, Depends(get_request_id)]


# ── Bitácora ─────────────────────────────────────────────────────────────────

def sanear_audit(datos: dict[str, Any] | None) -> dict[str, Any] | None:
    if datos is None:
        return None
    return {k: ("[REDACTADO]" if k in _SENSIBLES else v) for k, v in datos.items()}


async def registrar_audit(
    db: AsyncSession,
    usuario: UsuarioActual | None,
    accion: str,
    modulo: str | None = None,
    tabla: str | None = None,
    registro_id: uuid.UUID | None = None,
    datos_ant: dict[str, Any] | None = None,
    datos_nue: dict[str, Any] | None = None,
    request: Request | None = None,
    resultado: str = "OK",
    detalle_error: str | None = None,
    *,
    usuario_id: uuid.UUID | None = None,
    username: str | None = None,
    ip: str | None = None,
    user_agent: str | None = None,
    request_id: uuid.UUID | None = None,
) -> None:
    """Agrega un registro a sncev_audit.audit_log en la MISMA transacción del negocio.
    Los valores sensibles (nombre, CURP, contraseñas, tokens...) se redactan siempre."""
    if request is not None:
        ip = ip or ip_cliente(request)
        user_agent = user_agent or request.headers.get("user-agent")
        request_id = request_id or _request_id(request)
    if usuario is not None:
        usuario_id = usuario_id or usuario.usuario_id
        username = username or usuario.username
        ip = ip or usuario.ip
        user_agent = user_agent or usuario.user_agent
        request_id = request_id or usuario.request_id
    db.add(AuditLog(
        usuario_id=usuario_id, username_snapshot=(username or "")[:60] or None, accion=accion,
        modulo=modulo, tabla_afectada=tabla, registro_id=registro_id,
        datos_anteriores=sanear_audit(datos_ant), datos_nuevos=sanear_audit(datos_nue),
        ip_origen=ip_valida(ip), user_agent=user_agent, request_id=request_id,
        resultado=resultado, detalle_error=detalle_error,
    ))
    await db.flush()


_ACCION_POR_METODO = {"POST": "INSERT", "PUT": "UPDATE", "PATCH": "UPDATE", "DELETE": "DELETE"}


async def auditar_denegado(request: Request, permiso: str) -> None:
    """Registra un 403 por falta de permiso, en una sesión propia (nunca propaga errores)."""
    usuario: UsuarioActual | None = getattr(request.state, "usuario", None)
    if usuario is None:
        return
    try:
        async with AsyncSessionLocal() as s:
            await fijar_contexto(s, usuario.a_contexto())
            await registrar_audit(
                s, usuario, _ACCION_POR_METODO.get(request.method, "VIEW_SENSITIVE"), modulo="Seguridad",
                resultado="DENEGADO", request=request,
                detalle_error=f"{request.method} {request.url.path} requiere {permiso}",
            )
            await s.commit()
    except Exception:  # noqa: BLE001
        log.exception("no_se_pudo_auditar_denegado")
