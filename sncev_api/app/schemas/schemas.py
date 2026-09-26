# =============================================================================
# SNCEV API — Esquemas Pydantic v2 (contrato del OpenAPI 05_api_rest_fhir.yaml)
# =============================================================================

from __future__ import annotations

import math
import re
import uuid
from datetime import date, datetime
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator, model_validator

from ..core.security import errores_politica_password
from ..core.utils import hoy

Texto = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]
TextoLargo = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=2000)]

CURP_RE = re.compile(
    r"^[A-Z][AEIOUX][A-Z]{2}\d{2}(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])[HMX]"
    r"(AS|BC|BS|CC|CL|CM|CS|CH|DF|DG|GT|GR|HG|JC|MC|MN|MS|NT|NL|OC|PL|QT|QR|SP|SL|SR|TC|TS|TL|VZ|YN|ZS|NE)"
    r"[B-DF-HJ-NP-TV-Z]{3}[A-Z\d]\d$"
)


class EntradaBase(BaseModel):
    """Base para cuerpos de entrada: recorta espacios, '' -> None y tolera campos extra
    (la app móvil envía campos locales como lat_captura, sync_estado, etc.)."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="ignore")

    @model_validator(mode="before")
    @classmethod
    def _vacios_a_none(cls, datos: Any) -> Any:
        if isinstance(datos, dict):
            return {k: (None if isinstance(v, str) and not v.strip() else v) for k, v in datos.items()}
        return datos


# ── Paginación ───────────────────────────────────────────────────────────────

class PaginacionParams(BaseModel):
    page: int = Field(1, ge=1)
    per_page: int = Field(20, ge=1, le=100)

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.per_page


def total_paginas(total: int, per_page: int) -> int:
    return max(1, math.ceil(total / per_page))


# ── Autenticación ────────────────────────────────────────────────────────────

class LoginRequest(EntradaBase):
    username: str = Field(..., min_length=1, max_length=120)       # usuario o correo
    password: str = Field(..., min_length=1, max_length=200)
    device_id: str | None = Field(None, max_length=100)


class TokenResponse(BaseModel):
    access_token: str
    token_type: Literal["Bearer"] = "Bearer"
    expires_in: int
    refresh_token: str
    mfa_requerido: bool = False
    requiere_cambio_pwd: bool = False


class MfaSessionResponse(BaseModel):
    mfa_requerido: bool = True
    session_token: str


class MfaVerifyRequest(EntradaBase):
    session_token: str = Field(..., min_length=10)
    codigo_totp: str = Field(..., pattern=r"^\d{6}$")
    device_id: str | None = Field(None, max_length=100)


class RefreshRequest(EntradaBase):
    refresh_token: str = Field(..., min_length=10, max_length=500)


def _validar_password_nuevo(nuevo: str, confirm: str) -> None:
    errs = errores_politica_password(nuevo)
    if errs:
        raise ValueError("La contraseña no cumple la política: " + ", ".join(errs))
    if nuevo != confirm:
        raise ValueError("La confirmación no coincide")


class ChangePasswordRequest(EntradaBase):
    password_actual: str = Field(..., min_length=1, max_length=200)
    password_nuevo: str = Field(..., max_length=200)
    password_confirm: str = Field(..., max_length=200)

    @model_validator(mode="after")
    def _politica(self) -> "ChangePasswordRequest":
        _validar_password_nuevo(self.password_nuevo, self.password_confirm)
        return self


class ForgotPasswordRequest(EntradaBase):
    email: str = Field(..., min_length=3, max_length=200)


class ResetPasswordRequest(EntradaBase):
    token: str = Field(..., min_length=10, max_length=200)
    password_nuevo: str = Field(..., max_length=200)
    password_confirm: str = Field(..., max_length=200)

    @model_validator(mode="after")
    def _politica(self) -> "ResetPasswordRequest":
        _validar_password_nuevo(self.password_nuevo, self.password_confirm)
        return self


# ── Pacientes ────────────────────────────────────────────────────────────────

class ResponsableInput(EntradaBase):
    nombre: Texto
    ap_paterno: Texto
    ap_materno: Texto | None = None
    curp: str | None = None
    parentesco: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=50)]
    telefono: Annotated[str, StringConstraints(max_length=30)] | None = None
    telefono2: Annotated[str, StringConstraints(max_length=30)] | None = None
    email: Annotated[str, StringConstraints(max_length=200)] | None = None
    domicilio_calle: TextoLargo | None = None
    municipio_id: int | None = None
    cp: Annotated[str, StringConstraints(pattern=r"^\d{5}$")] | None = None
    es_principal: bool = True

    @field_validator("curp")
    @classmethod
    def _curp(cls, v: str | None) -> str | None:
        return _normalizar_curp(v)


def _normalizar_curp(v: str | None) -> str | None:
    if v is None:
        return None
    v = v.strip().upper()
    if not CURP_RE.match(v):
        raise ValueError("CURP con formato inválido")
    return v


class PacienteCreate(EntradaBase):
    tipo_cartilla_id: int
    nombre: Texto
    ap_paterno: Texto
    ap_materno: Texto | None = None
    curp: str | None = None
    fecha_nacimiento: date
    sexo: Literal["M", "F", "I"]
    municipio_nacimiento_id: int | None = None
    estado_nacimiento: Annotated[str, StringConstraints(pattern=r"^\d{2}$")] | None = None
    pais_nacimiento: Annotated[str, StringConstraints(min_length=3, max_length=3, to_upper=True)] = "MEX"
    grupo_etnico: Texto | None = None
    lengua_indigena: Texto | None = None
    habla_espanol: bool | None = None
    unidad_med_registro_id: uuid.UUID | None = None
    nss_imss: Annotated[str, StringConstraints(max_length=20)] | None = None
    responsable: ResponsableInput | None = None

    @field_validator("curp")
    @classmethod
    def _curp(cls, v: str | None) -> str | None:
        return _normalizar_curp(v)

    @field_validator("fecha_nacimiento")
    @classmethod
    def _fecha(cls, v: date) -> date:
        if v > hoy():
            raise ValueError("La fecha de nacimiento no puede ser futura")
        if v < date(1900, 1, 1):
            raise ValueError("Fecha de nacimiento fuera de rango")
        return v


class PacientePatch(EntradaBase):
    """PATCH semántico: solo se actualizan los campos enviados (null explícito = borrar)."""
    tipo_cartilla_id: int | None = None
    municipio_nacimiento_id: int | None = None
    grupo_etnico: Texto | None = None
    lengua_indigena: Texto | None = None
    habla_espanol: bool | None = None
    unidad_med_registro_id: uuid.UUID | None = None
    # Cifrados (requieren PACIENTE_DATOS_SENSIBLES + PACIENTE_EDITAR)
    nombre: Texto | None = None
    ap_paterno: Texto | None = None
    ap_materno: Texto | None = None
    curp: str | None = None
    nss_imss: Annotated[str, StringConstraints(max_length=20)] | None = None

    @field_validator("curp")
    @classmethod
    def _curp(cls, v: str | None) -> str | None:
        return _normalizar_curp(v)


class TipoCartillaRef(BaseModel):
    id: int
    nombre: str


class MunicipioRef(BaseModel):
    id: int
    nombre: str
    estado: str | None = None


class UnidadRef(BaseModel):
    id: uuid.UUID
    clues: str
    nombre: str


class PacienteResumen(BaseModel):
    id: uuid.UUID
    tipo_cartilla_id: int
    tipo_cartilla: str | None = None
    fecha_nacimiento: date
    sexo: str
    municipio_nacimiento_id: int | None = None
    unidad_med_registro_id: uuid.UUID | None = None
    activo: bool
    created_at: datetime | None = None


class PacientePaginado(BaseModel):
    data: list[PacienteResumen]
    total: int
    page: int
    pages: int


class PacienteDetalle(BaseModel):
    id: uuid.UUID
    tipo_cartilla: TipoCartillaRef
    fecha_nacimiento: date
    sexo: str
    pais_nacimiento: str
    estado_nacimiento: str | None = None
    municipio_nacimiento: MunicipioRef | None = None
    grupo_etnico: str | None = None
    lengua_indigena: str | None = None
    habla_espanol: bool | None = None
    unidad_med_registro: UnidadRef | None = None
    fhir_patient_id: str | None = None
    activo: bool
    # Solo con PACIENTE_DATOS_SENSIBLES
    nombre: str | None = None
    ap_paterno: str | None = None
    ap_materno: str | None = None
    curp: str | None = None
    created_at: datetime
    updated_at: datetime


class ResponsableOut(BaseModel):
    id: uuid.UUID
    parentesco: str
    es_principal: bool
    activo: bool
    municipio_id: int | None = None
    cp: str | None = None
    # Solo con PACIENTE_DATOS_SENSIBLES
    nombre: str | None = None
    ap_paterno: str | None = None
    ap_materno: str | None = None
    curp: str | None = None
    telefono: str | None = None
    telefono2: str | None = None
    email: str | None = None
    domicilio_calle: str | None = None


class ResponsablePatch(EntradaBase):
    nombre: Texto | None = None
    ap_paterno: Texto | None = None
    ap_materno: Texto | None = None
    curp: str | None = None
    parentesco: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=50)] | None = None
    telefono: Annotated[str, StringConstraints(max_length=30)] | None = None
    telefono2: Annotated[str, StringConstraints(max_length=30)] | None = None
    email: Annotated[str, StringConstraints(max_length=200)] | None = None
    domicilio_calle: TextoLargo | None = None
    municipio_id: int | None = None
    cp: Annotated[str, StringConstraints(pattern=r"^\d{5}$")] | None = None
    es_principal: bool | None = None

    @field_validator("curp")
    @classmethod
    def _curp(cls, v: str | None) -> str | None:
        return _normalizar_curp(v)


# ── Vacunación ───────────────────────────────────────────────────────────────

class VacunaRef(BaseModel):
    id: int
    clave_censia: str
    nombre_generico: str


class VacunaAplicadaCreate(EntradaBase):
    vacuna_id: int
    esquema_id: int | None = None
    numero_dosis: int = Field(..., ge=1, le=20)
    serie: Annotated[str, StringConstraints(max_length=10)] | None = None
    fecha_aplicacion: date
    lote: Annotated[str, StringConstraints(max_length=50)] | None = None
    fecha_caducidad_lote: date | None = None
    laboratorio: Annotated[str, StringConstraints(max_length=100)] | None = None
    temperatura_cadena: float | None = Field(None, ge=-99.9, le=99.9)
    unidad_medica_id: uuid.UUID | None = None
    nombre_aplicador: Annotated[str, StringConstraints(max_length=200)] | None = None
    cedula_profesional: Annotated[str, StringConstraints(max_length=20)] | None = None
    observaciones: TextoLargo | None = None


class VacunaEditar(EntradaBase):
    lote: Annotated[str, StringConstraints(max_length=50)] | None = None
    laboratorio: Annotated[str, StringConstraints(max_length=100)] | None = None
    observaciones: TextoLargo | None = None


class InvalidarRequest(EntradaBase):
    motivo: Annotated[str, StringConstraints(strip_whitespace=True, min_length=5, max_length=1000)]


class VacunaRegistrada(BaseModel):
    id: uuid.UUID
    paciente_id: uuid.UUID
    vacuna: VacunaRef
    fecha_aplicacion: date
    edad_dias_aplicacion: int | None = None
    advertencias: list[str] = []


class VacunaAplicadaResponse(BaseModel):
    id: uuid.UUID
    paciente_id: uuid.UUID
    vacuna: VacunaRef
    numero_dosis: int
    serie: str | None = None
    fecha_aplicacion: date
    edad_dias_aplicacion: int | None = None
    lote: str | None = None
    fecha_caducidad_lote: date | None = None
    laboratorio: str | None = None
    temperatura_cadena: float | None = None
    unidad: UnidadRef | None = None
    nombre_aplicador: str | None = None
    cedula_profesional: str | None = None
    es_valida: bool
    motivo_invalidacion: str | None = None
    observaciones: str | None = None
    created_at: datetime | None = None


class VacunaPendiente(BaseModel):
    esquema_id: int
    vacuna: VacunaRef
    numero_dosis: int
    serie: str | None = None
    fecha_optima: date | None = None
    fecha_limite: date | None = None
    dias_para_optima: int | None = None
    vencida: bool


class EsquemaResumen(BaseModel):
    tipo_cartilla: str
    dosis_esquema: int
    dosis_completadas: int
    dosis_pendientes: int
    porcentaje_completo: float


class HistorialVacunacion(BaseModel):
    aplicadas: list[VacunaAplicadaResponse]
    pendientes: list[VacunaPendiente]
    esquema: EsquemaResumen


# ── Clínico: somatometría ────────────────────────────────────────────────────

class SomatometriaCreate(EntradaBase):
    fecha_medicion: date
    edad_dias: int | None = Field(None, ge=0)
    peso_kg: float | None = Field(None, gt=0, le=400)
    talla_cm: float | None = Field(None, gt=0, le=260)
    pc_cm: float | None = Field(None, gt=0, le=100)
    pt_cm: float | None = Field(None, gt=0, le=200)
    percentil_peso: Annotated[str, StringConstraints(max_length=10)] | None = None
    percentil_talla: Annotated[str, StringConstraints(max_length=10)] | None = None
    percentil_imc: Annotated[str, StringConstraints(max_length=10)] | None = None
    percentil_pc: Annotated[str, StringConstraints(max_length=10)] | None = None
    clasificacion_nutricional: Annotated[str, StringConstraints(max_length=50)] | None = None
    unidad_medica_id: uuid.UUID | None = None
    observaciones: TextoLargo | None = None

    @model_validator(mode="after")
    def _alguna_medida(self) -> "SomatometriaCreate":
        if all(v is None for v in (self.peso_kg, self.talla_cm, self.pc_cm, self.pt_cm)):
            raise ValueError("Se requiere al menos una medida (peso, talla, pc o pt)")
        return self


class SomatometriaResponse(BaseModel):
    id: uuid.UUID
    paciente_id: uuid.UUID
    fecha_medicion: date
    edad_dias: int | None = None
    peso_kg: float | None = None
    talla_cm: float | None = None
    pc_cm: float | None = None
    pt_cm: float | None = None
    imc: float | None = None
    percentil_peso: str | None = None
    percentil_talla: str | None = None
    percentil_imc: str | None = None
    percentil_pc: str | None = None
    clasificacion_nutricional: str | None = None
    observaciones: str | None = None
    created_at: datetime | None = None
