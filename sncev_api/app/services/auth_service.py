# =============================================================================
# SNCEV API — Servicio de autenticación
# Login, MFA, rotación de refresh tokens, bloqueo por intentos, restablecimiento
#
# Regla de oro: todo lo que deba PERSISTIR antes de responder con error (contador de
# intentos, bloqueo, revocación de familia de tokens, bitácora de fallos) se confirma con
# `await self.db.commit()` ANTES de lanzar la excepción, porque get_db hace rollback
# ante cualquier excepción.
# =============================================================================

from __future__ import annotations

import secrets
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, text, update
from sqlalchemy.ext.asyncio import AsyncSession

from ..core import notificaciones
from ..core.config import settings
from ..core.security import (
    crear_access_token, crear_refresh_token, crear_session_token_mfa, descifrar,
    hash_busqueda, hash_password, normalizar_email, sha256_hex, verificar_session_token_mfa,
    verificar_totp, verify_password,
)
from ..core.utils import ip_valida
from ..db.session import ContextoRLS
from ..middleware.auth import registrar_audit
from ..models.models import PasswordResetToken, RefreshToken, Usuario
from ..schemas.schemas import LoginRequest, MfaSessionResponse, TokenResponse


class AuthException(Exception):
    def __init__(self, mensaje: str, status_code: int = 401, **extra):
        self.mensaje = mensaje
        self.status_code = status_code
        self.extra = extra
        super().__init__(mensaje)


def _ahora() -> datetime:
    return datetime.now(timezone.utc)


class AuthService:

    def __init__(self, db: AsyncSession):
        self.db = db
        # Flujos sin usuario autenticado (login/refresh/logout): contexto de sistema.
        if db.info.get("rls") is None:
            db.info["rls"] = ContextoRLS.sistema()

    # ─────────────────────────────────────────────────────────────────────────
    # LOGIN
    # ─────────────────────────────────────────────────────────────────────────

    async def login(self, data: LoginRequest, ip_origen: str | None = None,
                    user_agent: str | None = None) -> TokenResponse | MfaSessionResponse:
        usuario = await self._buscar_usuario(data.username)

        if usuario is None:
            verify_password(data.password, None)          # iguala el tiempo de respuesta
            await self._auditar("LOGIN_FALLIDO", None, ip_origen, user_agent,
                                username=data.username, detalle="usuario inexistente")
            await self.db.commit()
            raise AuthException("Credenciales inválidas")

        bloqueo = self._bloqueado_hasta(usuario)
        if bloqueo:
            await self._auditar("LOGIN_FALLIDO", usuario, ip_origen, user_agent, detalle="cuenta bloqueada")
            await self.db.commit()
            raise AuthException("Cuenta bloqueada", 423, desbloqueada_at=bloqueo.isoformat())

        if not verify_password(data.password, usuario.password_hash):
            await self._registrar_fallo(usuario, ip_origen, user_agent, "contraseña incorrecta")
            raise AuthException("Credenciales inválidas")

        if not usuario.activo:      # mensaje genérico: no revelar el estado de la cuenta
            await self._auditar("LOGIN_FALLIDO", usuario, ip_origen, user_agent, detalle="cuenta desactivada")
            await self.db.commit()
            raise AuthException("Credenciales inválidas")

        usuario.intentos_fallidos = 0
        usuario.bloqueado_hasta = None

        if usuario.mfa_habilitado:
            await self.db.commit()
            return MfaSessionResponse(session_token=crear_session_token_mfa(usuario.id))

        return await self._emitir_tokens(usuario, ip_origen, user_agent, data.device_id, auditar_login=True)

    # ─────────────────────────────────────────────────────────────────────────
    # MFA
    # ─────────────────────────────────────────────────────────────────────────

    async def verificar_mfa(self, session_token: str, codigo_totp: str, ip_origen: str | None = None,
                            user_agent: str | None = None, device_id: str | None = None) -> TokenResponse:
        try:
            usuario_id = verificar_session_token_mfa(session_token)
        except ValueError as exc:
            raise AuthException(str(exc)) from exc

        usuario = await self._obtener_por_id(usuario_id)
        if not usuario or not usuario.activo or not usuario.mfa_habilitado or not usuario.mfa_secret_enc:
            raise AuthException("Sesión MFA inválida")

        bloqueo = self._bloqueado_hasta(usuario)
        if bloqueo:
            raise AuthException("Cuenta bloqueada", 423, desbloqueada_at=bloqueo.isoformat())

        # El secreto está cifrado en BD: hay que descifrarlo antes de verificar el código.
        if not verificar_totp(descifrar(usuario.mfa_secret_enc), codigo_totp):
            # Los fallos de TOTP cuentan para el bloqueo (6 dígitos son fáciles de forzar).
            await self._registrar_fallo(usuario, ip_origen, user_agent, "código TOTP inválido")
            raise AuthException("Código TOTP inválido")

        usuario.intentos_fallidos = 0
        usuario.bloqueado_hasta = None
        return await self._emitir_tokens(usuario, ip_origen, user_agent, device_id, auditar_login=True)

    # ─────────────────────────────────────────────────────────────────────────
    # REFRESH (rotación + detección de reutilización)
    # ─────────────────────────────────────────────────────────────────────────

    async def renovar_token(self, refresh_token: str, ip_origen: str | None = None,
                            user_agent: str | None = None) -> TokenResponse:
        res = await self.db.execute(
            select(RefreshToken).where(RefreshToken.token_hash == sha256_hex(refresh_token)).with_for_update()
        )
        rt = res.scalar_one_or_none()
        if rt is None:
            raise AuthException("Token revocado o expirado")

        if rt.revocado:
            # Reutilización de un token ya rotado: posible robo -> se revoca TODA la familia.
            await self._revocar_familia(rt.familia)
            await self._auditar("LOGIN_FALLIDO", None, ip_origen, user_agent, usuario_id=rt.usuario_id,
                                detalle="reutilización de refresh token: familia revocada")
            await self.db.commit()
            raise AuthException("Token revocado o expirado")

        if rt.expira_at < _ahora():
            raise AuthException("Token revocado o expirado")

        usuario = await self._obtener_por_id(rt.usuario_id)
        if not usuario or not usuario.activo or self._bloqueado_hasta(usuario):
            rt.revocado, rt.revocado_at = True, _ahora()
            await self.db.commit()
            raise AuthException("Token revocado o expirado")

        rt.revocado, rt.revocado_at = True, _ahora()
        return await self._emitir_tokens(usuario, ip_origen, user_agent, rt.device_id, familia=rt.familia)

    # ─────────────────────────────────────────────────────────────────────────
    # LOGOUT
    # ─────────────────────────────────────────────────────────────────────────

    async def logout(self, refresh_token: str, ip_origen: str | None = None,
                     user_agent: str | None = None) -> None:
        res = await self.db.execute(
            select(RefreshToken).where(RefreshToken.token_hash == sha256_hex(refresh_token))
        )
        rt = res.scalar_one_or_none()
        if rt is None:
            return                                     # siempre 204: no revelar si existía
        if not rt.revocado:
            rt.revocado, rt.revocado_at = True, _ahora()
            await self._auditar("LOGOUT", None, ip_origen, user_agent, usuario_id=rt.usuario_id)

    async def logout_all(self, usuario_id: uuid.UUID) -> None:
        await self._revocar_todos(usuario_id)

    # ─────────────────────────────────────────────────────────────────────────
    # CONTRASEÑAS
    # ─────────────────────────────────────────────────────────────────────────

    async def cambiar_password(self, usuario_id: uuid.UUID, password_actual: str, password_nuevo: str,
                               ip_origen: str | None = None, user_agent: str | None = None) -> None:
        usuario = await self._obtener_por_id(usuario_id)
        if not usuario:
            raise AuthException("Usuario no encontrado", 404)
        if not verify_password(password_actual, usuario.password_hash):
            raise AuthException("Contraseña actual incorrecta", 400)
        if verify_password(password_nuevo, usuario.password_hash):
            raise AuthException("La nueva contraseña debe ser distinta de la actual", 422)

        usuario.password_hash = hash_password(password_nuevo)
        usuario.requiere_cambio_pwd = False
        usuario.password_cambiado_at = _ahora()
        await self._revocar_todos(usuario_id)          # cierra todas las sesiones
        await self._auditar("UPDATE", usuario, ip_origen, user_agent, detalle="cambio de contraseña")

    async def solicitar_reset(self, email: str, ip_origen: str | None = None,
                              user_agent: str | None = None) -> None:
        """Siempre termina sin error (el endpoint responde 202) para no revelar qué correos existen."""
        res = await self.db.execute(
            select(Usuario).where(Usuario.email_hash == hash_busqueda(normalizar_email(email)),
                                  Usuario.activo.is_(True))
        )
        usuario = res.scalars().first()
        if usuario is None:
            return
        await self.db.execute(
            update(PasswordResetToken)
            .where(PasswordResetToken.usuario_id == usuario.id, PasswordResetToken.usado.is_(False))
            .values(usado=True)
        )
        token = secrets.token_urlsafe(32)
        self.db.add(PasswordResetToken(
            usuario_id=usuario.id, token_hash=sha256_hex(token),
            expira_at=_ahora() + timedelta(minutes=settings.reset_password_minutes),
        ))
        await self._auditar("UPDATE", usuario, ip_origen, user_agent, detalle="solicitud de restablecimiento")
        enlace = f"{settings.frontend_reset_url}?token={token}" if settings.frontend_reset_url else f"token: {token}"
        await notificaciones.enviar(
            normalizar_email(email), "SNCEV — Restablecimiento de contraseña",
            f"Use este enlace en los próximos {settings.reset_password_minutes} minutos:\n{enlace}",
        )

    async def resetear_password(self, token: str, password_nuevo: str, ip_origen: str | None = None,
                                user_agent: str | None = None) -> None:
        res = await self.db.execute(
            select(PasswordResetToken).where(
                PasswordResetToken.token_hash == sha256_hex(token),
                PasswordResetToken.usado.is_(False),
                PasswordResetToken.expira_at > _ahora(),
            ).with_for_update()
        )
        prt = res.scalar_one_or_none()
        if prt is None:
            raise AuthException("Token inválido o expirado", 400)
        usuario = await self._obtener_por_id(prt.usuario_id)
        if not usuario or not usuario.activo:
            raise AuthException("Token inválido o expirado", 400)

        prt.usado = True
        usuario.password_hash = hash_password(password_nuevo)
        usuario.requiere_cambio_pwd = False
        usuario.password_cambiado_at = _ahora()
        usuario.intentos_fallidos = 0
        usuario.bloqueado_hasta = None
        await self._revocar_todos(usuario.id)
        await self._auditar("UPDATE", usuario, ip_origen, user_agent, detalle="restablecimiento de contraseña")

    # ─────────────────────────────────────────────────────────────────────────
    # Helpers
    # ─────────────────────────────────────────────────────────────────────────

    async def _emitir_tokens(self, usuario: Usuario, ip_origen: str | None, user_agent: str | None,
                             device_id: str | None = None, familia: uuid.UUID | None = None,
                             auditar_login: bool = False) -> TokenResponse:
        permisos = await self._permisos_rol(usuario.rol_id)
        access = crear_access_token(
            usuario_id=usuario.id, username=usuario.username,
            rol=usuario.rol.nombre, nivel=usuario.rol.nivel_acceso, permisos=permisos,
            unidad_id=str(usuario.unidad_medica_id) if usuario.unidad_medica_id else None,
            jurisdiccion_id=usuario.jurisdiccion_id, estado_clave=usuario.estado_clave,
            requiere_cambio_pwd=usuario.requiere_cambio_pwd,
        )
        plano, hash_token = crear_refresh_token()
        self.db.add(RefreshToken(
            usuario_id=usuario.id, token_hash=hash_token, familia=familia or uuid.uuid4(),
            expira_at=_ahora() + timedelta(days=settings.jwt_refresh_expire_days),
            ip_origen=ip_valida(ip_origen), user_agent=user_agent, device_id=device_id,
        ))
        usuario.ultimo_acceso = _ahora()
        if auditar_login:
            await self._auditar("LOGIN", usuario, ip_origen, user_agent)
        await self.db.flush()
        return TokenResponse(
            access_token=access, refresh_token=plano, expires_in=settings.jwt_access_expire_min * 60,
            requiere_cambio_pwd=usuario.requiere_cambio_pwd,
        )

    async def _permisos_rol(self, rol_id: int) -> list[str]:
        res = await self.db.execute(
            text("""SELECT p.codigo FROM sncev_admin.rol_permiso rp
                    JOIN sncev_admin.permiso p ON p.id = rp.permiso_id
                    WHERE rp.rol_id = :rol_id AND p.activo = TRUE"""),
            {"rol_id": rol_id},
        )
        return [r[0] for r in res.fetchall()]

    async def _buscar_usuario(self, identificador: str) -> Usuario | None:
        if "@" in identificador:
            cond = Usuario.email_hash == hash_busqueda(normalizar_email(identificador))
        else:
            cond = Usuario.username == identificador
        return (await self.db.execute(select(Usuario).where(cond))).scalars().first()

    async def _obtener_por_id(self, usuario_id: uuid.UUID) -> Usuario | None:
        return (await self.db.execute(select(Usuario).where(Usuario.id == usuario_id))).scalar_one_or_none()

    @staticmethod
    def _bloqueado_hasta(usuario: Usuario) -> datetime | None:
        if usuario.bloqueado_hasta and usuario.bloqueado_hasta > _ahora():
            return usuario.bloqueado_hasta
        return None

    async def _registrar_fallo(self, usuario: Usuario, ip: str | None, ua: str | None, detalle: str) -> None:
        usuario.intentos_fallidos = (usuario.intentos_fallidos or 0) + 1
        if usuario.intentos_fallidos >= settings.max_login_attempts:
            usuario.bloqueado_hasta = _ahora() + timedelta(minutes=settings.lockout_minutes)
            usuario.intentos_fallidos = 0
            detalle += f" — cuenta bloqueada {settings.lockout_minutes} min"
        await self._auditar("LOGIN_FALLIDO", usuario, ip, ua, detalle=detalle)
        await self.db.commit()

    async def _revocar_familia(self, familia: uuid.UUID) -> None:
        await self.db.execute(
            update(RefreshToken)
            .where(RefreshToken.familia == familia, RefreshToken.revocado.is_(False))
            .values(revocado=True, revocado_at=_ahora())
        )

    async def _revocar_todos(self, usuario_id: uuid.UUID) -> None:
        await self.db.execute(
            update(RefreshToken)
            .where(RefreshToken.usuario_id == usuario_id, RefreshToken.revocado.is_(False))
            .values(revocado=True, revocado_at=_ahora())
        )

    async def _auditar(self, accion: str, usuario: Usuario | None, ip: str | None, ua: str | None,
                       *, username: str | None = None, usuario_id: uuid.UUID | None = None,
                       detalle: str | None = None) -> None:
        await registrar_audit(
            self.db, None, accion, modulo="Auth", tabla="sncev_admin.usuario",
            registro_id=usuario.id if usuario else usuario_id,
            usuario_id=usuario.id if usuario else usuario_id,
            username=usuario.username if usuario else username,
            ip=ip, user_agent=ua, detalle_error=detalle,
            resultado="ERROR" if accion == "LOGIN_FALLIDO" else "OK",
        )
