# =============================================================================
# SNCEV API — Configuración (variables de entorno / .env)
# =============================================================================

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )

    # ── Aplicación ───────────────────────────────────────────────────────────
    app_name:    str = "SNCEV API"
    app_version: str = "1.0.0"
    public_base_url: str = "http://localhost:8000"   # base para armar url_qr/url_pdf
    environment: str = "development"          # development | staging | production
    debug:       bool = False
    log_level:   str = "INFO"
    timezone:    str = "America/Mexico_City"
    allowed_origins: list[str] = []           # JSON: '["http://localhost:3000"]'
    trust_forwarded_for: bool = False         # true solo detrás de un proxy/gateway de confianza
    prometheus_enabled: bool = False
    sentry_dsn: str | None = None

    # ── Base de datos ────────────────────────────────────────────────────────
    database_url: str = Field(..., description="postgresql://usuario:clave@host/sncev_db")
    db_ssl: str = ""                          # '' | 'require' | 'verify-full'
    db_pool_size: int = 10
    db_max_overflow: int = 10

    # ── Claves ───────────────────────────────────────────────────────────────
    aes_key_hex: SecretStr = Field(..., description="64 hex = 32 bytes (AES-256)")
    hash_pepper_hex: SecretStr | None = None  # si falta, se deriva de la clave AES
    jwt_private_key_path: Path = Path("/app/certs/private.pem")
    jwt_public_key_path:  Path = Path("/app/certs/public.pem")
    firma_private_key_path: Path = Path("/app/certs/firma_private.pem")   # llave del profesional/institución
    firma_public_key_path:  Path = Path("/app/certs/firma_public.pem")
    storage_dir: Path = Path("storage")
    url_ttl_segundos: int = 3600
    umbral_alerta_pct: float = 80.0
    meta_cobertura_pct_default: float = 95.0
    export_max_filas: int = 200_000

    # ── Sesiones ─────────────────────────────────────────────────────────────
    jwt_access_expire_min:   int = 15
    jwt_refresh_expire_days: int = 8
    mfa_session_expire_min:  int = 5
    max_login_attempts:      int = 5
    lockout_minutes:         int = 30
    reset_password_minutes:  int = 30
    frontend_reset_url:      str = ""      # p. ej. https://portal.sncev.gob.mx/restablecer

    @field_validator("database_url")
    @classmethod
    def _driver_asyncpg(cls, v: str) -> str:
        for prefijo in ("postgresql://", "postgres://"):
            if v.startswith(prefijo):
                return "postgresql+asyncpg://" + v[len(prefijo):]
        return v

    @field_validator("aes_key_hex")
    @classmethod
    def _validar_aes(cls, v: SecretStr) -> SecretStr:
        try:
            raw = bytes.fromhex(v.get_secret_value())
        except ValueError as exc:
            raise ValueError("AES_KEY_HEX debe ser hexadecimal") from exc
        if len(raw) != 32:
            raise ValueError("AES_KEY_HEX debe tener 64 caracteres hex (32 bytes)")
        return v

    @property
    def es_produccion(self) -> bool:
        return self.environment.lower() == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]


settings = get_settings()
