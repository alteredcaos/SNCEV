# =============================================================================
# SNCEV Jobs — Configuración centralizada
# Todas las variables vienen de .env o variables de entorno del contenedor
# =============================================================================

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, SecretStr
from functools import lru_cache


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        case_sensitive=False,
    )

    # ── Base de datos ────────────────────────────────────────────────────────
    db_host:     str       = Field('localhost',    description='Host PostgreSQL')
    db_port:     int       = Field(5432,           description='Puerto PostgreSQL')
    db_name:     str       = Field('sncev_db',     description='Nombre de la BD')
    db_user:     str       = Field('sncev_app',    description='Usuario de BD')
    db_password: SecretStr = Field(...,             description='Contraseña de BD')
    db_pool_min: int       = Field(2,              description='Conexiones mínimas en pool')
    db_pool_max: int       = Field(10,             description='Conexiones máximas en pool')

    @property
    def db_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.db_user}:"
            f"{self.db_password.get_secret_value()}@"
            f"{self.db_host}:{self.db_port}/{self.db_name}"
        )

    # ── Scheduler ───────────────────────────────────────────────────────────
    timezone:               str  = Field('America/Mexico_City', description='Zona horaria')
    # Hora de ejecución del job nocturno principal (formato HH:MM)
    hora_job_cobertura:     str  = Field('02:00', description='Hora del job de cobertura')
    hora_job_mv_refresh:    str  = Field('03:30', description='Hora del refresh de vistas materializadas')
    hora_job_alertas:       str  = Field('07:00', description='Hora del envío de alertas')
    hora_job_limpieza:      str  = Field('04:00', description='Hora del job de limpieza')

    # ── Parámetros de negocio ────────────────────────────────────────────────
    meta_cobertura_pct:     float = Field(95.0,  description='Meta nacional de cobertura %')
    umbral_alerta_pct:      float = Field(80.0,  description='Umbral de alerta de cobertura %')
    semanas_recalcular:     int   = Field(4,     description='Semanas hacia atrás a recalcular')

    # ── Notificaciones ───────────────────────────────────────────────────────
    webhook_alertas_url:    str | None = Field(None, description='Webhook Slack/Teams para alertas')
    email_alertas:          str | None = Field(None, description='Email para reporte de alertas')
    api_base_url:           str        = Field('https://api.sncev.salud.gob.mx/v1')

    # ── Observabilidad ───────────────────────────────────────────────────────
    log_level:              str  = Field('INFO',  description='Nivel de log')
    prometheus_port:        int  = Field(9090,    description='Puerto de métricas Prometheus')
    environment:            str  = Field('production', description='production | staging | development')


@lru_cache
def get_settings() -> Settings:
    return Settings()
