# =============================================================================
# SNCEV API — Seguridad: cifrado AES-256-GCM, contraseñas, JWT RS256, TOTP
# =============================================================================

from __future__ import annotations

import base64
import hashlib
import hmac
import os
import re
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from functools import lru_cache
from typing import Any

import bcrypt
import jwt
import pyotp
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from .config import settings

BCRYPT_COST = 12


# ── Cifrado de columnas *_enc ────────────────────────────────────────────────
# Formato: Base64( IV(12) || CipherText || Tag(16) ), como describe el DDL.

@lru_cache
def _aes() -> AESGCM:
    return AESGCM(bytes.fromhex(settings.aes_key_hex.get_secret_value()))


def cifrar(texto: str) -> str:
    iv = os.urandom(12)
    return base64.b64encode(iv + _aes().encrypt(iv, texto.encode("utf-8"), None)).decode("ascii")


def cifrar_nullable(texto: str | None) -> str | None:
    return cifrar(texto) if texto not in (None, "") else None


def descifrar(token: str) -> str:
    raw = base64.b64decode(token)
    return _aes().decrypt(raw[:12], raw[12:], None).decode("utf-8")


def descifrar_nullable(token: str | None) -> str | None:
    return descifrar(token) if token else None


# ── Hashes ───────────────────────────────────────────────────────────────────

def sha256_hex(texto: str) -> str:
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()


@lru_cache
def _pepper() -> bytes:
    if settings.hash_pepper_hex is not None:
        return bytes.fromhex(settings.hash_pepper_hex.get_secret_value())
    # Derivada de la clave AES con separación de dominio
    clave = bytes.fromhex(settings.aes_key_hex.get_secret_value())
    return hmac.new(clave, b"sncev|hash-busqueda|v1", hashlib.sha256).digest()


def hash_busqueda(texto: str) -> str:
    """HMAC-SHA256 (hex, 64 chars) para curp_hash / email_hash. Un SHA-256 simple de una CURP
    se enumera por fuerza bruta (tiene poca entropía); con clave de servidor no."""
    return hmac.new(_pepper(), texto.encode("utf-8"), hashlib.sha256).hexdigest()


def normalizar_curp(curp: str) -> str:
    return curp.strip().upper()


def normalizar_email(email: str) -> str:
    return email.strip().lower()


# ── Contraseñas (bcrypt cost 12) ─────────────────────────────────────────────

_DUMMY_HASH = bcrypt.hashpw(b"relleno-para-igualar-tiempos", bcrypt.gensalt(BCRYPT_COST)).decode()


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(BCRYPT_COST)).decode("ascii")


def verify_password(password: str, hashed: str | None) -> bool:
    """Ejecuta bcrypt SIEMPRE (con hash de relleno si no hay usuario) para igualar tiempos."""
    try:
        ok = bcrypt.checkpw(password.encode("utf-8")[:72], (hashed or _DUMMY_HASH).encode("ascii"))
    except ValueError:
        return False
    return ok and hashed is not None


verificar_password = verify_password   # alias (el avance usaba ambos nombres)


def errores_politica_password(pw: str) -> list[str]:
    errs: list[str] = []
    if len(pw) < 12:
        errs.append("mínimo 12 caracteres")
    if len(pw.encode("utf-8")) > 72:
        errs.append("máximo 72 bytes")
    if not re.search(r"[A-ZÁÉÍÓÚÑ]", pw):
        errs.append("al menos una mayúscula")
    if not re.search(r"\d", pw):
        errs.append("al menos un número")
    if not re.search(r"[^\w\s]|_", pw):
        errs.append("al menos un carácter especial")
    return errs


# ── Refresh token opaco ──────────────────────────────────────────────────────

def crear_refresh_token() -> tuple[str, str]:
    """(token_plano, sha256). Solo el hash se guarda en BD."""
    plano = secrets.token_urlsafe(48)
    return plano, sha256_hex(plano)


# ── JWT RS256 ────────────────────────────────────────────────────────────────

@lru_cache
def _llaves() -> tuple[bytes, bytes]:
    try:
        return settings.jwt_private_key_path.read_bytes(), settings.jwt_public_key_path.read_bytes()
    except FileNotFoundError as exc:
        raise RuntimeError(
            f"No se encontró la llave JWT: {exc.filename}. Ejecute: python scripts/generar_claves.py"
        ) from exc


def _emitir(claims: dict[str, Any], vigencia: timedelta, typ: str) -> str:
    ahora = datetime.now(timezone.utc)
    payload = {**claims, "typ": typ, "iat": ahora, "exp": ahora + vigencia, "jti": str(uuid.uuid4())}
    return jwt.encode(payload, _llaves()[0], algorithm="RS256")


def crear_access_token(
    usuario_id: uuid.UUID, username: str, rol: str, nivel: int, permisos: list[str],
    unidad_id: str | None = None, jurisdiccion_id: int | None = None,
    estado_clave: str | None = None, requiere_cambio_pwd: bool = False,
) -> str:
    return _emitir(
        {"sub": str(usuario_id), "username": username, "rol": rol, "nivel": nivel,
         "unidad_id": unidad_id, "jurisdiccion": jurisdiccion_id, "estado": estado_clave,
         "permisos": sorted(permisos), "pwd": requiere_cambio_pwd},
        timedelta(minutes=settings.jwt_access_expire_min), "access",
    )


def decodificar_access_token(token: str) -> dict[str, Any]:
    """Lanza jwt.PyJWTError si el token es inválido, expiró o no es de acceso."""
    payload = jwt.decode(token, _llaves()[1], algorithms=["RS256"],
                         options={"require": ["exp", "sub", "iat"]})
    if payload.get("typ") != "access":
        raise jwt.InvalidTokenError("tipo de token incorrecto")
    return payload


def crear_session_token_mfa(usuario_id: uuid.UUID) -> str:
    return _emitir({"sub": str(usuario_id)}, timedelta(minutes=settings.mfa_session_expire_min), "mfa")


def verificar_session_token_mfa(token: str) -> uuid.UUID:
    try:
        payload = jwt.decode(token, _llaves()[1], algorithms=["RS256"],
                             options={"require": ["exp", "sub"]})
        if payload.get("typ") != "mfa":
            raise ValueError("Sesión MFA inválida")
        return uuid.UUID(payload["sub"])
    except jwt.ExpiredSignatureError as exc:
        raise ValueError("La sesión MFA expiró; vuelva a iniciar sesión") from exc
    except (jwt.PyJWTError, ValueError, KeyError) as exc:
        raise ValueError("Sesión MFA inválida") from exc


# ── TOTP (RFC 6238) ──────────────────────────────────────────────────────────

def generar_secreto_totp() -> str:
    return pyotp.random_base32()


def verificar_totp(secreto: str, codigo: str) -> bool:
    """`secreto` debe venir YA descifrado."""
    return bool(re.fullmatch(r"\d{6}", codigo or "")) and pyotp.TOTP(secreto).verify(codigo, valid_window=1)


def uri_totp(secreto: str, username: str) -> str:
    return pyotp.TOTP(secreto).provisioning_uri(name=username, issuer_name="SNCEV")
