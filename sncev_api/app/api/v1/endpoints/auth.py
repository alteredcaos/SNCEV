# =============================================================================
# SNCEV API — Endpoints de autenticación (módulo 1 del OpenAPI)
# =============================================================================

from __future__ import annotations

from fastapi import APIRouter, Response, status

from ....core.errors import ApiError
from ....db.session import DbDep
from ....middleware.auth import UserCambioPwdDep, UserDep, ip_cliente
from ....schemas.schemas import (
    ChangePasswordRequest, ForgotPasswordRequest, LoginRequest, MfaSessionResponse,
    MfaVerifyRequest, RefreshRequest, ResetPasswordRequest, TokenResponse,
)
from ....services.auth_service import AuthException, AuthService
from fastapi import Request

router = APIRouter(prefix="/auth", tags=["Autenticación"])


def _levantar(exc: AuthException):
    raise ApiError(exc.status_code, exc.mensaje, **exc.extra)


@router.post("/login", response_model=TokenResponse | MfaSessionResponse)
async def login(data: LoginRequest, request: Request, db: DbDep):
    try:
        return await AuthService(db).login(data, ip_cliente(request), request.headers.get("user-agent"))
    except AuthException as exc:
        _levantar(exc)


@router.post("/mfa/verify", response_model=TokenResponse)
async def mfa_verify(data: MfaVerifyRequest, request: Request, db: DbDep):
    try:
        return await AuthService(db).verificar_mfa(
            data.session_token, data.codigo_totp, ip_cliente(request),
            request.headers.get("user-agent"), data.device_id)
    except AuthException as exc:
        _levantar(exc)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(data: RefreshRequest, request: Request, db: DbDep):
    try:
        return await AuthService(db).renovar_token(
            data.refresh_token, ip_cliente(request), request.headers.get("user-agent"))
    except AuthException as exc:
        _levantar(exc)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(data: RefreshRequest, request: Request, db: DbDep):
    await AuthService(db).logout(data.refresh_token, ip_cliente(request), request.headers.get("user-agent"))
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/logout-all", status_code=status.HTTP_204_NO_CONTENT)
async def logout_all(db: DbDep, usuario: UserDep):
    await AuthService(db).logout_all(usuario.usuario_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/change-password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(data: ChangePasswordRequest, request: Request, db: DbDep,
                          usuario: UserCambioPwdDep):
    try:
        await AuthService(db).cambiar_password(
            usuario.usuario_id, data.password_actual, data.password_nuevo,
            ip_cliente(request), request.headers.get("user-agent"))
    except AuthException as exc:
        _levantar(exc)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/forgot-password", status_code=status.HTTP_202_ACCEPTED)
async def forgot_password(data: ForgotPasswordRequest, request: Request, db: DbDep):
    await AuthService(db).solicitar_reset(data.email, ip_cliente(request), request.headers.get("user-agent"))
    return {"mensaje": "Si el correo existe, se enviaron instrucciones de restablecimiento"}


@router.post("/reset-password", status_code=status.HTTP_204_NO_CONTENT)
async def reset_password(data: ResetPasswordRequest, request: Request, db: DbDep):
    try:
        await AuthService(db).resetear_password(
            data.token, data.password_nuevo, ip_cliente(request), request.headers.get("user-agent"))
    except AuthException as exc:
        _levantar(exc)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
