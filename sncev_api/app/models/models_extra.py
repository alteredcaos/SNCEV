# =============================================================================
# SNCEV API — Modelos adicionales (citas, tamizajes, desarrollo, jurisdicción,
# cartilla firmada, sync, export_job, permisos)
# =============================================================================

from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, FetchedValue, ForeignKey, Integer, SmallInteger, String, Text, func
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID

from .models import Base

PG_UUID = UUID(as_uuid=True)
TS = DateTime(timezone=True)

from sqlalchemy.orm import Mapped, mapped_column


class Jurisdiccion(Base):
    __tablename__ = "jurisdiccion"
    __table_args__ = {"schema": "sncev_geo"}
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre: Mapped[str] = mapped_column(String(150))
    estado_clave: Mapped[str] = mapped_column(String(2))
    activo: Mapped[bool] = mapped_column(Boolean, default=True)


class Permiso(Base):
    __tablename__ = "permiso"
    __table_args__ = {"schema": "sncev_admin"}
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    codigo: Mapped[str] = mapped_column(String(60))
    descripcion: Mapped[str | None] = mapped_column(Text)
    activo: Mapped[bool] = mapped_column(Boolean, default=True)


class Tamizaje(Base):
    __tablename__ = "tamiz_neonatal"
    __table_args__ = {"schema": "sncev"}
    id: Mapped[uuid.UUID] = mapped_column(PG_UUID, primary_key=True, default=uuid.uuid4)
    paciente_id: Mapped[uuid.UUID] = mapped_column(PG_UUID, ForeignKey("sncev.paciente.id"))
    tipo_tamiz: Mapped[str] = mapped_column(String(80))
    fecha_toma: Mapped[date] = mapped_column(Date)
    numero_muestra: Mapped[int] = mapped_column(SmallInteger, default=1)
    resultado: Mapped[str] = mapped_column(String(20), default="Pendiente")
    detalle_resultado: Mapped[str | None] = mapped_column(Text)
    fecha_resultado: Mapped[date | None] = mapped_column(Date)
    requiere_seguimiento: Mapped[bool] = mapped_column(Boolean, default=False)
    observaciones: Mapped[str | None] = mapped_column(Text)
    unidad_medica_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID)
    realizado_por: Mapped[uuid.UUID | None] = mapped_column(PG_UUID)
    created_by: Mapped[uuid.UUID | None] = mapped_column(PG_UUID)
    created_at: Mapped[datetime] = mapped_column(TS, server_default=func.now())


class Desarrollo(Base):
    __tablename__ = "desarrollo_infantil"
    __table_args__ = {"schema": "sncev"}
    id: Mapped[uuid.UUID] = mapped_column(PG_UUID, primary_key=True, default=uuid.uuid4)
    paciente_id: Mapped[uuid.UUID] = mapped_column(PG_UUID, ForeignKey("sncev.paciente.id"))
    fecha_evaluacion: Mapped[date] = mapped_column(Date)
    area: Mapped[str] = mapped_column(String(30))
    resultado: Mapped[str] = mapped_column(String(20))
    habilidades_logradas: Mapped[list[str] | None] = mapped_column(ARRAY(Text))
    habilidades_pendientes: Mapped[list[str] | None] = mapped_column(ARRAY(Text))
    observaciones: Mapped[str | None] = mapped_column(Text)
    unidad_medica_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID)
    evaluado_por: Mapped[uuid.UUID | None] = mapped_column(PG_UUID)
    created_at: Mapped[datetime] = mapped_column(TS, server_default=func.now())


class CitaVacunacion(Base):
    __tablename__ = "cita_vacunacion"
    __table_args__ = {"schema": "sncev"}
    id: Mapped[uuid.UUID] = mapped_column(PG_UUID, primary_key=True, default=uuid.uuid4)
    paciente_id: Mapped[uuid.UUID] = mapped_column(PG_UUID, ForeignKey("sncev.paciente.id"))
    unidad_medica_id: Mapped[uuid.UUID] = mapped_column(PG_UUID)
    vacuna_id: Mapped[int | None] = mapped_column(Integer)
    esquema_id: Mapped[int | None] = mapped_column(Integer)
    fecha_programada: Mapped[datetime] = mapped_column(TS)
    fecha_real: Mapped[date | None] = mapped_column(Date)
    estado: Mapped[str] = mapped_column(String(20), default="Pendiente")
    motivo_cancelacion: Mapped[str | None] = mapped_column(Text)
    recordatorio_sms: Mapped[bool] = mapped_column(Boolean, default=False)
    recordatorio_push: Mapped[bool] = mapped_column(Boolean, default=False)
    fecha_recordatorio: Mapped[datetime | None] = mapped_column(TS)
    notas: Mapped[str | None] = mapped_column(Text)
    vacuna_aplicada_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID)
    created_by: Mapped[uuid.UUID | None] = mapped_column(PG_UUID)
    created_at: Mapped[datetime] = mapped_column(TS, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TS, server_default=func.now())      # migración 06


class CartillaFirmada(Base):
    __tablename__ = "cartilla_firmada"
    __table_args__ = {"schema": "sncev"}
    id: Mapped[uuid.UUID] = mapped_column(PG_UUID, primary_key=True, default=uuid.uuid4)
    paciente_id: Mapped[uuid.UUID] = mapped_column(PG_UUID, ForeignKey("sncev.paciente.id"))
    version_cartilla: Mapped[str] = mapped_column(String(20), default="2023")
    hash_sha256: Mapped[str] = mapped_column(Text)
    firma_rsa: Mapped[str] = mapped_column(Text)
    cert_thumbprint: Mapped[str | None] = mapped_column(String(64))
    firmado_por: Mapped[uuid.UUID] = mapped_column(PG_UUID)
    url_pdf: Mapped[str | None] = mapped_column(Text)
    url_qr: Mapped[str | None] = mapped_column(Text)
    qr_token: Mapped[uuid.UUID] = mapped_column(PG_UUID, default=uuid.uuid4)
    fecha_firma: Mapped[datetime] = mapped_column(TS, server_default=func.now())
    activa: Mapped[bool] = mapped_column(Boolean, default=True)


class SyncRegistro(Base):                                                     # migración 06
    __tablename__ = "sync_registro"
    __table_args__ = {"schema": "sncev"}
    local_key: Mapped[str] = mapped_column(Text, primary_key=True)
    tabla: Mapped[str] = mapped_column(String(40))
    servidor_id: Mapped[uuid.UUID] = mapped_column(PG_UUID)
    usuario_id: Mapped[uuid.UUID] = mapped_column(PG_UUID)
    device_id: Mapped[str | None] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(TS, server_default=func.now())


class ExportJob(Base):                                                        # migración 06
    __tablename__ = "export_job"
    __table_args__ = {"schema": "sncev_admin"}
    id: Mapped[uuid.UUID] = mapped_column(PG_UUID, primary_key=True, default=uuid.uuid4)
    usuario_id: Mapped[uuid.UUID] = mapped_column(PG_UUID)
    tipo: Mapped[str] = mapped_column(String(30))
    formato: Mapped[str] = mapped_column(String(10))
    filtros: Mapped[dict] = mapped_column(JSONB, default=dict)
    incluir_sensibles: Mapped[bool] = mapped_column(Boolean, default=False)
    estado: Mapped[str] = mapped_column(String(12), default="procesando")
    archivo: Mapped[str | None] = mapped_column(Text)
    filas: Mapped[int | None] = mapped_column(Integer)
    error: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(TS, server_default=func.now())
    finished_at: Mapped[datetime | None] = mapped_column(TS)


# ─────────────────────────────── Reportes ────────────────────────────────────

from sqlalchemy import Numeric, CHAR


class Ageb(Base):
    __tablename__ = "ageb"
    __table_args__ = {"schema": "sncev_geo"}
    clave: Mapped[str] = mapped_column(CHAR(13), primary_key=True)
    nombre: Mapped[str | None] = mapped_column(String(200))
    tipo: Mapped[str] = mapped_column(CHAR(1), default="U")
    municipio_id: Mapped[int] = mapped_column(Integer)
    estado_clave: Mapped[str] = mapped_column(String(2))
    poblacion_total: Mapped[int | None] = mapped_column(Integer)
    poblacion_menor_5: Mapped[int | None] = mapped_column(Integer)
    poblacion_5_14: Mapped[int | None] = mapped_column(Integer)
    poblacion_15_49_f: Mapped[int | None] = mapped_column(Integer)
    poblacion_60_mas: Mapped[int | None] = mapped_column(Integer)
    geom_wkt: Mapped[str | None] = mapped_column(Text)
    activo: Mapped[bool] = mapped_column(Boolean, default=True)


class CoberturaVacunacion(Base):
    __tablename__ = "cobertura_vacunacion"
    __table_args__ = {"schema": "sncev_report"}
    id: Mapped[uuid.UUID] = mapped_column(PG_UUID, primary_key=True, default=uuid.uuid4)
    vacuna_id: Mapped[int] = mapped_column(Integer)
    numero_dosis: Mapped[int] = mapped_column(SmallInteger, default=1)
    tipo_cartilla_id: Mapped[int | None] = mapped_column(Integer)
    ageb_clave: Mapped[str | None] = mapped_column(CHAR(13))
    municipio_id: Mapped[int | None] = mapped_column(Integer)
    jurisdiccion_id: Mapped[int | None] = mapped_column(Integer)
    estado_clave: Mapped[str | None] = mapped_column(String(2))
    anio: Mapped[int] = mapped_column(SmallInteger)
    semana_epidemiologica: Mapped[int] = mapped_column(SmallInteger)
    dosis_aplicadas: Mapped[int] = mapped_column(Integer, default=0)
    poblacion_objetivo: Mapped[int | None] = mapped_column(Integer)
    porcentaje_cobertura: Mapped[float | None] = mapped_column(Numeric(6, 2), server_default=FetchedValue())
    concordancia_pct: Mapped[float | None] = mapped_column(Numeric(6, 2))
    dosis_invalidas: Mapped[int] = mapped_column(Integer, default=0)
    calculado_at: Mapped[datetime] = mapped_column(TS, server_default=func.now())
