# =============================================================================
# SNCEV API — Modelos SQLAlchemy 2.0 (espejo de los DDL 01–04 y 06)
# Las columnas calculadas por la BD (edad_dias_aplicacion, imc) usan FetchedValue:
# el ORM no las inserta y las recupera con RETURNING.
# =============================================================================

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean, Date, DateTime, FetchedValue, ForeignKey, Integer, Numeric, SmallInteger,
    String, Text, func, text,
)
from sqlalchemy.dialects.postgresql import ARRAY, ENUM, INET, JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

PG_UUID = UUID(as_uuid=True)
TS = DateTime(timezone=True)
UUID_DEFAULT = text("uuid_generate_v4()")

SexoEnum = ENUM("M", "F", "I", name="tipo_sexo", schema="sncev", create_type=False)
AccionEnum = ENUM(
    "INSERT", "UPDATE", "DELETE", "LOGIN", "LOGOUT", "LOGIN_FALLIDO", "EXPORT", "PRINT",
    "VIEW_SENSITIVE", name="tipo_accion", schema="sncev_admin", create_type=False,
)


class Base(DeclarativeBase):
    pass


# ─────────────────────────────── Geografía ───────────────────────────────────

class Estado(Base):
    __tablename__ = "estado"
    __table_args__ = {"schema": "sncev_geo"}
    clave_inegi: Mapped[str] = mapped_column(String(2), primary_key=True)
    nombre: Mapped[str] = mapped_column(String(60))
    abreviatura: Mapped[str] = mapped_column(String(6))
    activo: Mapped[bool] = mapped_column(Boolean, default=True)


class Municipio(Base):
    __tablename__ = "municipio"
    __table_args__ = {"schema": "sncev_geo"}
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    clave_inegi: Mapped[str] = mapped_column(String(5))
    nombre: Mapped[str] = mapped_column(String(100))
    estado_clave: Mapped[str] = mapped_column(String(2), ForeignKey("sncev_geo.estado.clave_inegi"))
    activo: Mapped[bool] = mapped_column(Boolean, default=True)


class UnidadMedica(Base):
    __tablename__ = "unidad_medica"
    __table_args__ = {"schema": "sncev"}
    id: Mapped[uuid.UUID] = mapped_column(PG_UUID, primary_key=True, default=uuid.uuid4)
    clues: Mapped[str] = mapped_column(String(11))
    nombre: Mapped[str] = mapped_column(String(200))
    municipio_id: Mapped[int] = mapped_column(Integer)
    estado_clave: Mapped[str] = mapped_column(String(2))
    jurisdiccion_id: Mapped[int | None] = mapped_column(Integer)
    activo: Mapped[bool] = mapped_column(Boolean, default=True)


# ─────────────────────────────── Catálogos ───────────────────────────────────

class TipoCartilla(Base):
    __tablename__ = "tipo_cartilla"
    __table_args__ = {"schema": "sncev"}
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre: Mapped[str] = mapped_column(String(80))
    descripcion: Mapped[str | None] = mapped_column(Text)
    edad_min_dias: Mapped[int] = mapped_column(Integer, default=0)
    edad_max_dias: Mapped[int | None] = mapped_column(Integer)
    orden: Mapped[int] = mapped_column(SmallInteger, default=0)
    color_hex: Mapped[str | None] = mapped_column(String(7))
    activo: Mapped[bool] = mapped_column(Boolean, default=True)


class VacunaCatalogo(Base):
    __tablename__ = "vacuna_catalogo"
    __table_args__ = {"schema": "sncev"}
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    clave_censia: Mapped[str] = mapped_column(String(20))
    nombre_generico: Mapped[str] = mapped_column(String(200))
    nombre_comercial: Mapped[str | None] = mapped_column(String(200))
    via_administracion: Mapped[str] = mapped_column(String(2))          # enum, solo lectura
    volumen_dosis_ml: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    tipo_vacuna: Mapped[str | None] = mapped_column(String(80))
    enfermedades: Mapped[list[str] | None] = mapped_column(ARRAY(Text))
    fhir_cvx_code: Mapped[str | None] = mapped_column(String(10))
    activo: Mapped[bool] = mapped_column(Boolean, default=True)


class EsquemaVacunacion(Base):
    __tablename__ = "esquema_vacunacion"
    __table_args__ = {"schema": "sncev"}
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tipo_cartilla_id: Mapped[int] = mapped_column(Integer)
    vacuna_id: Mapped[int] = mapped_column(Integer)
    numero_dosis: Mapped[int] = mapped_column(SmallInteger)
    serie: Mapped[str | None] = mapped_column(String(10))
    edad_min_dias: Mapped[int] = mapped_column(Integer, default=0)
    edad_max_dias: Mapped[int | None] = mapped_column(Integer)
    edad_optima_dias: Mapped[int | None] = mapped_column(Integer)
    intervalo_min_dias: Mapped[int | None] = mapped_column(Integer)
    es_refuerzo: Mapped[bool] = mapped_column(Boolean, default=False)
    activo: Mapped[bool] = mapped_column(Boolean, default=True)


# ─────────────────────────────── Clínico ─────────────────────────────────────

class Paciente(Base):
    __tablename__ = "paciente"
    __table_args__ = {"schema": "sncev"}

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID, primary_key=True, default=uuid.uuid4)
    tipo_cartilla_id: Mapped[int] = mapped_column(Integer, ForeignKey("sncev.tipo_cartilla.id"))
    nombre_enc: Mapped[str] = mapped_column(Text)
    ap_paterno_enc: Mapped[str] = mapped_column(Text)
    ap_materno_enc: Mapped[str | None] = mapped_column(Text)
    curp_enc: Mapped[str | None] = mapped_column(Text)
    curp_hash: Mapped[str | None] = mapped_column(String(64))
    fecha_nacimiento: Mapped[date] = mapped_column(Date)
    sexo: Mapped[str] = mapped_column(SexoEnum)
    municipio_nacimiento_id: Mapped[int | None] = mapped_column(Integer)
    estado_nacimiento: Mapped[str | None] = mapped_column(String(2))
    pais_nacimiento: Mapped[str] = mapped_column(String(3), default="MEX")
    grupo_etnico: Mapped[str | None] = mapped_column(String(100))
    lengua_indigena: Mapped[str | None] = mapped_column(String(100))
    habla_espanol: Mapped[bool | None] = mapped_column(Boolean)
    unidad_med_registro_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID)
    nss_imss_enc: Mapped[str | None] = mapped_column(Text)
    expediente_local: Mapped[str | None] = mapped_column(String(50))
    fhir_patient_id: Mapped[str | None] = mapped_column(String(100))
    activo: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(TS, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TS, server_default=func.now())
    created_by: Mapped[uuid.UUID | None] = mapped_column(PG_UUID)
    updated_by: Mapped[uuid.UUID | None] = mapped_column(PG_UUID)

    tipo_cartilla: Mapped[TipoCartilla] = relationship(lazy="joined")


class Responsable(Base):
    __tablename__ = "responsable"
    __table_args__ = {"schema": "sncev"}
    id: Mapped[uuid.UUID] = mapped_column(PG_UUID, primary_key=True, default=uuid.uuid4)
    paciente_id: Mapped[uuid.UUID] = mapped_column(PG_UUID, ForeignKey("sncev.paciente.id"))
    nombre_enc: Mapped[str] = mapped_column(Text)
    ap_paterno_enc: Mapped[str] = mapped_column(Text)
    ap_materno_enc: Mapped[str | None] = mapped_column(Text)
    curp_enc: Mapped[str | None] = mapped_column(Text)
    curp_hash: Mapped[str | None] = mapped_column(String(64))
    parentesco: Mapped[str] = mapped_column(String(50))
    telefono_enc: Mapped[str | None] = mapped_column(Text)
    telefono2_enc: Mapped[str | None] = mapped_column(Text)
    email_enc: Mapped[str | None] = mapped_column(Text)
    domicilio_calle_enc: Mapped[str | None] = mapped_column(Text)
    municipio_id: Mapped[int | None] = mapped_column(Integer)
    cp: Mapped[str | None] = mapped_column(String(5))
    es_principal: Mapped[bool] = mapped_column(Boolean, default=True)
    activo: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(TS, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TS, server_default=func.now())


class VacunaAplicada(Base):
    __tablename__ = "vacuna_aplicada"
    __table_args__ = {"schema": "sncev"}
    id: Mapped[uuid.UUID] = mapped_column(PG_UUID, primary_key=True, default=uuid.uuid4)
    paciente_id: Mapped[uuid.UUID] = mapped_column(PG_UUID, ForeignKey("sncev.paciente.id"))
    vacuna_id: Mapped[int] = mapped_column(Integer, ForeignKey("sncev.vacuna_catalogo.id"))
    esquema_id: Mapped[int | None] = mapped_column(Integer)
    numero_dosis: Mapped[int] = mapped_column(SmallInteger, default=1)
    serie: Mapped[str | None] = mapped_column(String(10))
    fecha_aplicacion: Mapped[date] = mapped_column(Date)
    lote: Mapped[str | None] = mapped_column(String(50))
    fecha_caducidad_lote: Mapped[date | None] = mapped_column(Date)
    laboratorio: Mapped[str | None] = mapped_column(String(100))
    temperatura_cadena: Mapped[Decimal | None] = mapped_column(Numeric(4, 1))
    unidad_medica_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID)
    municipio_aplicacion_id: Mapped[int | None] = mapped_column(Integer)
    aplicado_por: Mapped[uuid.UUID | None] = mapped_column(PG_UUID)
    nombre_aplicador: Mapped[str | None] = mapped_column(String(200))
    cedula_profesional: Mapped[str | None] = mapped_column(String(20))
    es_valida: Mapped[bool] = mapped_column(Boolean, default=True)
    motivo_invalidacion: Mapped[str | None] = mapped_column(Text)
    edad_dias_aplicacion: Mapped[int | None] = mapped_column(Integer, server_default=FetchedValue())
    fhir_immunization_id: Mapped[str | None] = mapped_column(String(100))
    observaciones: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(TS, server_default=func.now())
    created_by: Mapped[uuid.UUID | None] = mapped_column(PG_UUID)
    updated_at: Mapped[datetime] = mapped_column(TS, server_default=func.now())   # migración 06


class Somatometria(Base):
    __tablename__ = "somatometria"
    __table_args__ = {"schema": "sncev"}
    id: Mapped[uuid.UUID] = mapped_column(PG_UUID, primary_key=True, default=uuid.uuid4)
    paciente_id: Mapped[uuid.UUID] = mapped_column(PG_UUID, ForeignKey("sncev.paciente.id"))
    fecha_medicion: Mapped[date] = mapped_column(Date)
    edad_dias: Mapped[int | None] = mapped_column(Integer)
    peso_kg: Mapped[Decimal | None] = mapped_column(Numeric(6, 3))
    talla_cm: Mapped[Decimal | None] = mapped_column(Numeric(5, 1))
    pc_cm: Mapped[Decimal | None] = mapped_column(Numeric(5, 1))
    pt_cm: Mapped[Decimal | None] = mapped_column(Numeric(5, 1))
    imc: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), server_default=FetchedValue())
    percentil_peso: Mapped[str | None] = mapped_column(String(10))
    percentil_talla: Mapped[str | None] = mapped_column(String(10))
    percentil_imc: Mapped[str | None] = mapped_column(String(10))
    percentil_pc: Mapped[str | None] = mapped_column(String(10))
    clasificacion_nutricional: Mapped[str | None] = mapped_column(String(50))
    unidad_medica_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID)
    registrado_por: Mapped[uuid.UUID | None] = mapped_column(PG_UUID)
    observaciones: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(TS, server_default=func.now())


# ─────────────────────────────── Seguridad ───────────────────────────────────

class Rol(Base):
    __tablename__ = "rol"
    __table_args__ = {"schema": "sncev_admin"}
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre: Mapped[str] = mapped_column(String(60))
    descripcion: Mapped[str | None] = mapped_column(Text)
    nivel_acceso: Mapped[int] = mapped_column(SmallInteger, default=1)
    activo: Mapped[bool] = mapped_column(Boolean, default=True)


class Usuario(Base):
    __tablename__ = "usuario"
    __table_args__ = {"schema": "sncev_admin"}
    id: Mapped[uuid.UUID] = mapped_column(PG_UUID, primary_key=True, default=uuid.uuid4)
    username: Mapped[str] = mapped_column(String(60))
    email_enc: Mapped[str] = mapped_column(Text)
    email_hash: Mapped[str] = mapped_column(String(64))
    password_hash: Mapped[str] = mapped_column(Text)
    rol_id: Mapped[int] = mapped_column(Integer, ForeignKey("sncev_admin.rol.id"))
    unidad_medica_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID)
    jurisdiccion_id: Mapped[int | None] = mapped_column(Integer)
    estado_clave: Mapped[str | None] = mapped_column(String(2))
    nombre_enc: Mapped[str | None] = mapped_column(Text)
    cedula_profesional: Mapped[str | None] = mapped_column(String(20))
    especialidad: Mapped[str | None] = mapped_column(String(100))
    activo: Mapped[bool] = mapped_column(Boolean, default=True)
    mfa_habilitado: Mapped[bool] = mapped_column(Boolean, default=False)
    mfa_secret_enc: Mapped[str | None] = mapped_column(Text)
    email_verificado: Mapped[bool] = mapped_column(Boolean, default=False)
    email_token: Mapped[uuid.UUID | None] = mapped_column(PG_UUID)
    ultimo_acceso: Mapped[datetime | None] = mapped_column(TS)
    intentos_fallidos: Mapped[int] = mapped_column(SmallInteger, default=0)
    bloqueado_hasta: Mapped[datetime | None] = mapped_column(TS)
    password_cambiado_at: Mapped[datetime | None] = mapped_column(TS)
    requiere_cambio_pwd: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(TS, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TS, server_default=func.now())

    rol: Mapped[Rol] = relationship(lazy="joined")


class RefreshToken(Base):
    __tablename__ = "refresh_token"
    __table_args__ = {"schema": "sncev_admin"}
    id: Mapped[uuid.UUID] = mapped_column(PG_UUID, primary_key=True, default=uuid.uuid4)
    usuario_id: Mapped[uuid.UUID] = mapped_column(PG_UUID, ForeignKey("sncev_admin.usuario.id"))
    token_hash: Mapped[str] = mapped_column(String(64))
    familia: Mapped[uuid.UUID] = mapped_column(PG_UUID, default=uuid.uuid4)
    expira_at: Mapped[datetime] = mapped_column(TS)
    revocado: Mapped[bool] = mapped_column(Boolean, default=False)
    revocado_at: Mapped[datetime | None] = mapped_column(TS)
    ip_origen: Mapped[str | None] = mapped_column(INET)
    user_agent: Mapped[str | None] = mapped_column(Text)
    device_id: Mapped[str | None] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(TS, server_default=func.now())


class PasswordResetToken(Base):                                               # migración 06
    __tablename__ = "password_reset_token"
    __table_args__ = {"schema": "sncev_admin"}
    id: Mapped[uuid.UUID] = mapped_column(PG_UUID, primary_key=True, default=uuid.uuid4)
    usuario_id: Mapped[uuid.UUID] = mapped_column(PG_UUID, ForeignKey("sncev_admin.usuario.id"))
    token_hash: Mapped[str] = mapped_column(String(64))
    expira_at: Mapped[datetime] = mapped_column(TS)
    usado: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(TS, server_default=func.now())


class AuditLog(Base):
    __tablename__ = "audit_log"
    __table_args__ = {"schema": "sncev_audit"}
    id: Mapped[uuid.UUID] = mapped_column(PG_UUID, primary_key=True, default=uuid.uuid4)
    usuario_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID)
    username_snapshot: Mapped[str | None] = mapped_column(String(60))
    accion: Mapped[str] = mapped_column(AccionEnum)
    modulo: Mapped[str | None] = mapped_column(String(40))
    tabla_afectada: Mapped[str | None] = mapped_column(String(100))
    registro_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID)
    datos_anteriores: Mapped[dict | None] = mapped_column(JSONB)
    datos_nuevos: Mapped[dict | None] = mapped_column(JSONB)
    ip_origen: Mapped[str | None] = mapped_column(INET)
    user_agent: Mapped[str | None] = mapped_column(Text)
    request_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID)
    resultado: Mapped[str] = mapped_column(String(10), default="OK")
    detalle_error: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(TS, server_default=func.now())
