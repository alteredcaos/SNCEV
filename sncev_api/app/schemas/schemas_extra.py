# =============================================================================
# SNCEV API — Esquemas adicionales: catálogos, citas, tamizajes, desarrollo,
# cartilla, admin/auditoría, reportes y sync
# =============================================================================

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Annotated, Literal

from pydantic import BaseModel, Field, StringConstraints

from .schemas import CURP_RE, EntradaBase, Texto, TextoLargo, UnidadRef, VacunaRef, _normalizar_curp
from ..core.security import errores_politica_password
from pydantic import field_validator, model_validator

# ── Catálogos ────────────────────────────────────────────────────────────────

class VacunaCatalogoOut(BaseModel):
    id: int
    clave_censia: str
    nombre_generico: str
    nombre_comercial: str | None = None
    via_administracion: str
    tipo_vacuna: str | None = None
    enfermedades: list[str] | None = None
    fhir_cvx_code: str | None = None
    activo: bool


class EsquemaOut(BaseModel):
    id: int
    tipo_cartilla_id: int
    vacuna: VacunaRef
    numero_dosis: int
    serie: str | None = None
    edad_min_dias: int
    edad_max_dias: int | None = None
    edad_optima_dias: int | None = None
    intervalo_min_dias: int | None = None
    es_refuerzo: bool


class TipoCartillaOut(BaseModel):
    id: int
    nombre: str
    descripcion: str | None = None
    edad_min_dias: int
    edad_max_dias: int | None = None
    color_hex: str | None = None


class UnidadMedicaOut(BaseModel):
    id: uuid.UUID
    clues: str
    nombre: str
    tipo: str | None = None
    municipio_id: int
    estado_clave: str
    jurisdiccion_id: int | None = None
    telefono: str | None = None
    domicilio: str | None = None
    latitud: float | None = None
    longitud: float | None = None
    distancia_km: float | None = None


class JurisdiccionOut(BaseModel):
    id: int
    nombre: str
    estado_clave: str


class EstadoOut(BaseModel):
    clave_inegi: str
    nombre: str
    abreviatura: str


class MunicipioOut(BaseModel):
    id: int
    clave_inegi: str
    nombre: str
    estado_clave: str


# ── Citas ────────────────────────────────────────────────────────────────────

class CitaCreate(EntradaBase):
    paciente_id: uuid.UUID
    unidad_medica_id: uuid.UUID
    vacuna_id: int | None = None
    esquema_id: int | None = None
    fecha_programada: datetime
    recordatorio_sms: bool = False
    recordatorio_push: bool = False
    notas: TextoLargo | None = None


class CitaPatch(EntradaBase):
    fecha_programada: datetime | None = None
    estado: Literal["Pendiente", "Confirmada", "Atendida", "Cancelada", "No asistió"] | None = None
    motivo_cancelacion: TextoLargo | None = None
    fecha_real: date | None = None
    vacuna_aplicada_id: uuid.UUID | None = None

    @model_validator(mode="after")
    def _motivo_si_cancela(self) -> "CitaPatch":
        if self.estado == "Cancelada" and not self.motivo_cancelacion:
            raise ValueError("motivo_cancelacion es obligatorio al cancelar")
        return self


class CitaCancelar(EntradaBase):
    motivo: Annotated[str, StringConstraints(strip_whitespace=True, min_length=3, max_length=500)]


class CitaOut(BaseModel):
    id: uuid.UUID
    paciente_id: uuid.UUID
    unidad: UnidadRef | None = None
    vacuna: VacunaRef | None = None
    esquema_id: int | None = None
    fecha_programada: datetime
    fecha_real: date | None = None
    estado: str
    motivo_cancelacion: str | None = None
    recordatorio_sms: bool
    recordatorio_push: bool
    notas: str | None = None
    vacuna_aplicada_id: uuid.UUID | None = None
    created_at: datetime | None = None


class CitaPaginada(BaseModel):
    data: list[CitaOut]
    total: int
    page: int
    pages: int


# ── Tamizajes ────────────────────────────────────────────────────────────────

TipoTamiz = Literal["Metabólico", "Auditivo", "Cardiaco", "Oftalmológico", "Caderas"]
ResultadoTamiz = Literal["Normal", "Anormal", "Pendiente"]


class TamizajeCreate(EntradaBase):
    tipo_tamiz: TipoTamiz
    fecha_toma: date
    numero_muestra: int = Field(1, ge=1, le=3)
    resultado: ResultadoTamiz = "Pendiente"
    detalle_resultado: TextoLargo | None = None
    fecha_resultado: date | None = None
    requiere_seguimiento: bool = False
    observaciones: TextoLargo | None = None
    unidad_medica_id: uuid.UUID | None = None


class TamizajePatch(EntradaBase):
    resultado: ResultadoTamiz | None = None
    detalle_resultado: TextoLargo | None = None
    fecha_resultado: date | None = None
    requiere_seguimiento: bool | None = None
    observaciones: TextoLargo | None = None


class TamizajeOut(BaseModel):
    id: uuid.UUID
    paciente_id: uuid.UUID
    tipo_tamiz: str
    fecha_toma: date
    numero_muestra: int
    resultado: str
    detalle_resultado: str | None = None
    fecha_resultado: date | None = None
    requiere_seguimiento: bool
    observaciones: str | None = None
    created_at: datetime | None = None


# ── Desarrollo infantil ──────────────────────────────────────────────────────

AreaDesarrollo = Literal["Motor grueso", "Motor fino", "Lenguaje", "Social", "Cognitivo"]
ResultadoDesarrollo = Literal["Adecuado", "Riesgo", "Retraso", "No evaluado"]


class DesarrolloCreate(EntradaBase):
    fecha_evaluacion: date
    area: AreaDesarrollo
    resultado: ResultadoDesarrollo
    habilidades_logradas: list[Texto] | None = None
    habilidades_pendientes: list[Texto] | None = None
    observaciones: TextoLargo | None = None
    unidad_medica_id: uuid.UUID | None = None


class DesarrolloOut(BaseModel):
    id: uuid.UUID
    paciente_id: uuid.UUID
    fecha_evaluacion: date
    area: str
    resultado: str
    habilidades_logradas: list[str] | None = None
    habilidades_pendientes: list[str] | None = None
    observaciones: str | None = None
    created_at: datetime | None = None


# ── Cartilla ─────────────────────────────────────────────────────────────────

SeccionCartilla = Literal["vacunas", "tamizajes", "somatometria", "desarrollo"]


class CartillaGenerarRequest(EntradaBase):
    incluir_secciones: list[SeccionCartilla] | None = None


class CartillaGenerada(BaseModel):
    id: uuid.UUID
    hash_sha256: str
    url_pdf: str
    url_qr: str
    qr_token: uuid.UUID
    fecha_firma: datetime


class CartillaVerificacion(BaseModel):
    valida: bool
    fecha_firma: datetime | None = None
    tipo_cartilla: str | None = None
    estado_emision: str | None = None
    qr_version: str = "1.0"


# ── Admin: usuarios / roles / permisos ───────────────────────────────────────

class UsuarioCreate(EntradaBase):
    username: Annotated[str, StringConstraints(strip_whitespace=True, min_length=3, max_length=60,
                                                pattern=r"^[a-zA-Z0-9._-]+$")]
    email: Annotated[str, StringConstraints(strip_whitespace=True, min_length=5, max_length=200)]
    password_inicial: str = Field(..., max_length=200)
    rol_id: int
    unidad_medica_id: uuid.UUID | None = None
    jurisdiccion_id: int | None = None
    estado_clave: Annotated[str, StringConstraints(pattern=r"^\d{2}$")] | None = None
    nombre: Texto | None = None
    cedula_profesional: Annotated[str, StringConstraints(max_length=20)] | None = None
    especialidad: Texto | None = None
    mfa_habilitado: bool = False

    @field_validator("email")
    @classmethod
    def _email(cls, v: str) -> str:
        if "@" not in v:
            raise ValueError("correo inválido")
        return v.strip().lower()

    @field_validator("password_inicial")
    @classmethod
    def _pwd(cls, v: str) -> str:
        errs = errores_politica_password(v)
        if errs:
            raise ValueError("password_inicial no cumple la política: " + ", ".join(errs))
        return v


class UsuarioPatch(EntradaBase):
    rol_id: int | None = None
    unidad_medica_id: uuid.UUID | None = None
    jurisdiccion_id: int | None = None
    estado_clave: Annotated[str, StringConstraints(pattern=r"^\d{2}$")] | None = None
    activo: bool | None = None
    mfa_habilitado: bool | None = None
    requiere_cambio_pwd: bool | None = None
    nombre: Texto | None = None


class UsuarioOut(BaseModel):
    id: uuid.UUID
    username: str
    email: str | None = None
    rol_id: int
    rol: str
    nivel_acceso: int
    unidad_medica_id: uuid.UUID | None = None
    jurisdiccion_id: int | None = None
    estado_clave: str | None = None
    nombre: str | None = None
    cedula_profesional: str | None = None
    especialidad: str | None = None
    activo: bool
    mfa_habilitado: bool
    email_verificado: bool
    ultimo_acceso: datetime | None = None
    requiere_cambio_pwd: bool
    created_at: datetime | None = None


class UsuarioPaginado(BaseModel):
    data: list[UsuarioOut]
    total: int
    page: int
    pages: int


class RolOut(BaseModel):
    id: int
    nombre: str
    descripcion: str | None = None
    nivel_acceso: int


class PermisoOut(BaseModel):
    id: int
    codigo: str
    descripcion: str | None = None


# ── Auditoría ────────────────────────────────────────────────────────────────

class AuditLogOut(BaseModel):
    id: uuid.UUID
    usuario_id: uuid.UUID | None = None
    username_snapshot: str | None = None
    accion: str
    modulo: str | None = None
    tabla_afectada: str | None = None
    registro_id: uuid.UUID | None = None
    ip_origen: str | None = None
    resultado: str
    created_at: datetime

    @field_validator("ip_origen", mode="before")
    @classmethod
    def _ip_a_texto(cls, v):
        # asyncpg devuelve INET como ipaddress.IPv4Address/IPv6Address, no como str.
        return str(v) if v is not None else None


class AuditLogDetalle(AuditLogOut):
    user_agent: str | None = None
    request_id: uuid.UUID | None = None
    datos_anteriores: dict | None = None
    datos_nuevos: dict | None = None
    detalle_error: str | None = None


class AuditLogPaginado(BaseModel):
    data: list[AuditLogOut]
    total: int
    page: int
    pages: int


# ── Reportes ─────────────────────────────────────────────────────────────────

Dimension = Literal["ageb", "municipio", "jurisdiccion", "estado", "nacional"]


class CoberturaFila(BaseModel):
    dimension_id: str
    dimension_nombre: str
    vacuna: VacunaRef
    numero_dosis: int
    dosis_aplicadas: int
    poblacion_objetivo: int
    cobertura_pct: float
    concordancia_pct: float
    dosis_invalidas: int


class CoberturaResponse(BaseModel):
    periodo: dict
    dimension: str
    datos: list[CoberturaFila]
    meta_nacional_pct: float


class TendenciaFila(BaseModel):
    anio: int
    semana: int
    dosis_aplicadas: int
    poblacion_objetivo: int
    cobertura_pct: float


class MapaFila(BaseModel):
    clave: str
    nombre: str
    cobertura_pct: float
    geom_wkt: str | None = None
    alerta: bool


class LoteUnidad(BaseModel):
    clues: str
    nombre: str
    municipio: str | None = None
    estado: str | None = None
    dosis_aplicadas: int


class LoteResponse(BaseModel):
    lote: str
    vacuna: VacunaRef
    total_dosis: int
    unidades: list[LoteUnidad]
    fecha_primera: date | None = None
    fecha_ultima: date | None = None
    alertas: int


class RezagoFila(BaseModel):
    paciente_id: uuid.UUID
    fecha_nacimiento: date
    vacuna: VacunaRef
    serie: str | None = None
    fecha_limite: date | None = None
    dias_rezago: int
    unidad_registro: str | None = None
    municipio: str | None = None


class RezagoResponse(BaseModel):
    data: list[RezagoFila]
    total: int


class ExportarRequest(EntradaBase):
    tipo: Literal["cobertura", "vacunas_aplicadas", "rezago", "auditoria"]
    formato: Literal["csv", "xlsx"]
    filtros: dict = Field(default_factory=dict)
    incluir_datos_sensibles: bool = False


class ExportJobAceptado(BaseModel):
    job_id: uuid.UUID
    estado: Literal["procesando"] = "procesando"


class ExportJobEstado(BaseModel):
    job_id: uuid.UUID
    estado: Literal["procesando", "listo", "error"]
    url: str | None = None
    error: str | None = None


# ── Sync (modo offline) ──────────────────────────────────────────────────────

TipoSync = Literal["paciente", "vacuna_aplicada", "cita", "somatometria"]
AccionSync = Literal["INSERT", "UPDATE"]


class RegistroSync(EntradaBase):
    tipo: TipoSync
    accion: AccionSync
    datos: dict
    local_id: str = Field(..., min_length=1, max_length=100)
    ts_local: datetime | None = None


class SyncPushRequest(EntradaBase):
    device_id: str = Field(..., min_length=1, max_length=100)
    last_sync_at: datetime | None = None
    registros: list[RegistroSync] = Field(..., max_length=500)


class SyncPushError(BaseModel):
    local_id: str
    error: str


class SyncPushResponse(BaseModel):
    procesados: int
    errores: list[SyncPushError]
    id_mapping: dict[str, str]


class SyncPullResponse(BaseModel):
    hasta: datetime
    pacientes: list
    vacunas: list
    citas: list
    catalogos: dict
