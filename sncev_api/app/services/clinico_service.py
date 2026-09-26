# =============================================================================
# SNCEV API — Servicio clínico: somatometría, tamizajes neonatales y desarrollo
# =============================================================================

from __future__ import annotations

import uuid
from decimal import Decimal

from fastapi import Request
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.errors import ApiError
from ..core.utils import hoy
from ..middleware.auth import UsuarioActual, registrar_audit
from ..models.models import Paciente, Somatometria
from ..models.models_extra import Desarrollo, Tamizaje
from ..schemas.schemas import SomatometriaCreate, SomatometriaResponse
from ..schemas.schemas_extra import (
    DesarrolloCreate, DesarrolloOut, TamizajeCreate, TamizajeOut, TamizajePatch,
)


def _dec(v: float | None, decimales: int) -> Decimal | None:
    return Decimal(str(round(v, decimales))) if v is not None else None


def _f(v: Decimal | None) -> float | None:
    return float(v) if v is not None else None


def _somato_out(s: Somatometria) -> SomatometriaResponse:
    return SomatometriaResponse(
        id=s.id, paciente_id=s.paciente_id, fecha_medicion=s.fecha_medicion, edad_dias=s.edad_dias,
        peso_kg=_f(s.peso_kg), talla_cm=_f(s.talla_cm), pc_cm=_f(s.pc_cm), pt_cm=_f(s.pt_cm), imc=_f(s.imc),
        percentil_peso=s.percentil_peso, percentil_talla=s.percentil_talla,
        percentil_imc=s.percentil_imc, percentil_pc=s.percentil_pc,
        clasificacion_nutricional=s.clasificacion_nutricional,
        observaciones=s.observaciones, created_at=s.created_at,
    )


def _tamiz_out(t: Tamizaje) -> TamizajeOut:
    return TamizajeOut(
        id=t.id, paciente_id=t.paciente_id, tipo_tamiz=t.tipo_tamiz, fecha_toma=t.fecha_toma,
        numero_muestra=t.numero_muestra, resultado=t.resultado, detalle_resultado=t.detalle_resultado,
        fecha_resultado=t.fecha_resultado, requiere_seguimiento=t.requiere_seguimiento,
        observaciones=t.observaciones, created_at=t.created_at,
    )


def _desarrollo_out(d: Desarrollo) -> DesarrolloOut:
    return DesarrolloOut(
        id=d.id, paciente_id=d.paciente_id, fecha_evaluacion=d.fecha_evaluacion, area=d.area,
        resultado=d.resultado, habilidades_logradas=d.habilidades_logradas,
        habilidades_pendientes=d.habilidades_pendientes, observaciones=d.observaciones,
        created_at=d.created_at,
    )


class ClinicoService:

    def __init__(self, db: AsyncSession, usuario: UsuarioActual):
        self.db = db
        self.u = usuario

    async def _paciente(self, paciente_id: uuid.UUID) -> Paciente:
        p = (await self.db.execute(select(Paciente).where(Paciente.id == paciente_id))).scalar_one_or_none()
        if p is None:
            raise ApiError(404, "Paciente no encontrado")
        return p

    # ─────────────────────────────────────────────────────────────────────────
    # Somatometría
    # ─────────────────────────────────────────────────────────────────────────

    async def listar_somatometria(self, paciente_id: uuid.UUID) -> list[SomatometriaResponse]:
        await self._paciente(paciente_id)
        filas = (await self.db.execute(
            select(Somatometria).where(Somatometria.paciente_id == paciente_id)
            .order_by(Somatometria.fecha_medicion.desc()))).scalars().all()
        return [_somato_out(s) for s in filas]

    async def registrar_somatometria(self, paciente_id: uuid.UUID, data: SomatometriaCreate,
                                     request: Request | None = None) -> SomatometriaResponse:
        pac = await self._paciente(paciente_id)
        if data.fecha_medicion > hoy():
            raise ApiError(422, "La fecha de medición no puede ser futura")
        if data.fecha_medicion < pac.fecha_nacimiento:
            raise ApiError(422, "La fecha de medición es anterior al nacimiento del paciente")

        existente = (await self.db.execute(
            select(Somatometria.id).where(Somatometria.paciente_id == paciente_id,
                                          Somatometria.fecha_medicion == data.fecha_medicion)
        )).scalar_one_or_none()
        if existente:
            raise ApiError(409, "Ya existe una medición de ese paciente para esa fecha",
                           somatometria_id=str(existente))

        s = Somatometria(
            paciente_id=paciente_id, fecha_medicion=data.fecha_medicion,
            edad_dias=data.edad_dias if data.edad_dias is not None
            else (data.fecha_medicion - pac.fecha_nacimiento).days,
            peso_kg=_dec(data.peso_kg, 3), talla_cm=_dec(data.talla_cm, 1), pc_cm=_dec(data.pc_cm, 1),
            pt_cm=_dec(data.pt_cm, 1), percentil_peso=data.percentil_peso, percentil_talla=data.percentil_talla,
            percentil_imc=data.percentil_imc, percentil_pc=data.percentil_pc,
            clasificacion_nutricional=data.clasificacion_nutricional,
            unidad_medica_id=data.unidad_medica_id or self.u.unidad_id,
            registrado_por=self.u.usuario_id, observaciones=data.observaciones,
        )
        self.db.add(s)
        await self.db.flush()
        await self.db.refresh(s, ["imc"])                 # calculado por la BD
        await registrar_audit(self.db, self.u, "INSERT", "Clinico", "sncev.somatometria", s.id,
                              request=request, datos_nue={"paciente_id": str(paciente_id),
                                                          "fecha_medicion": data.fecha_medicion.isoformat()})
        return _somato_out(s)

    # ─────────────────────────────────────────────────────────────────────────
    # Tamizajes neonatales
    # ─────────────────────────────────────────────────────────────────────────

    async def listar_tamizajes(self, paciente_id: uuid.UUID) -> list[TamizajeOut]:
        await self._paciente(paciente_id)
        filas = (await self.db.execute(
            select(Tamizaje).where(Tamizaje.paciente_id == paciente_id)
            .order_by(Tamizaje.fecha_toma.desc()))).scalars().all()
        return [_tamiz_out(t) for t in filas]

    async def registrar_tamizaje(self, paciente_id: uuid.UUID, data: TamizajeCreate,
                                 request: Request | None = None) -> TamizajeOut:
        pac = await self._paciente(paciente_id)
        if data.fecha_toma > hoy():
            raise ApiError(422, "La fecha de toma no puede ser futura")
        if data.fecha_toma < pac.fecha_nacimiento:
            raise ApiError(422, "La fecha de toma es anterior al nacimiento del paciente")
        t = Tamizaje(
            paciente_id=paciente_id, tipo_tamiz=data.tipo_tamiz, fecha_toma=data.fecha_toma,
            numero_muestra=data.numero_muestra, resultado=data.resultado,
            detalle_resultado=data.detalle_resultado, fecha_resultado=data.fecha_resultado,
            requiere_seguimiento=data.requiere_seguimiento, observaciones=data.observaciones,
            unidad_medica_id=data.unidad_medica_id or self.u.unidad_id,
            realizado_por=self.u.usuario_id, created_by=self.u.usuario_id,
        )
        self.db.add(t)
        await self.db.flush()
        await registrar_audit(self.db, self.u, "INSERT", "Clinico", "sncev.tamiz_neonatal", t.id,
                              request=request,
                              datos_nue={"paciente_id": str(paciente_id), "tipo_tamiz": data.tipo_tamiz})
        return _tamiz_out(t)

    async def editar_tamizaje(self, tamizaje_id: uuid.UUID, data: TamizajePatch,
                              request: Request | None = None) -> TamizajeOut:
        campos = data.model_dump(exclude_unset=True)
        if not campos:
            raise ApiError(400, "No se enviaron campos para actualizar")
        res = await self.db.execute(
            update(Tamizaje).where(Tamizaje.id == tamizaje_id).values(**campos).returning(Tamizaje.id))
        if res.first() is None:
            raise ApiError(404, "Tamizaje no encontrado")
        await registrar_audit(self.db, self.u, "UPDATE", "Clinico", "sncev.tamiz_neonatal", tamizaje_id,
                              request=request, datos_nue={"campos_modificados": sorted(campos)})
        t = (await self.db.execute(select(Tamizaje).where(Tamizaje.id == tamizaje_id))).scalar_one()
        return _tamiz_out(t)

    # ─────────────────────────────────────────────────────────────────────────
    # Desarrollo infantil
    # ─────────────────────────────────────────────────────────────────────────

    async def listar_desarrollo(self, paciente_id: uuid.UUID) -> list[DesarrolloOut]:
        await self._paciente(paciente_id)
        filas = (await self.db.execute(
            select(Desarrollo).where(Desarrollo.paciente_id == paciente_id)
            .order_by(Desarrollo.fecha_evaluacion.desc()))).scalars().all()
        return [_desarrollo_out(d) for d in filas]

    async def registrar_desarrollo(self, paciente_id: uuid.UUID, data: DesarrolloCreate,
                                   request: Request | None = None) -> DesarrolloOut:
        pac = await self._paciente(paciente_id)
        if data.fecha_evaluacion > hoy():
            raise ApiError(422, "La fecha de evaluación no puede ser futura")
        if data.fecha_evaluacion < pac.fecha_nacimiento:
            raise ApiError(422, "La fecha de evaluación es anterior al nacimiento del paciente")
        d = Desarrollo(
            paciente_id=paciente_id, fecha_evaluacion=data.fecha_evaluacion, area=data.area,
            resultado=data.resultado, habilidades_logradas=data.habilidades_logradas,
            habilidades_pendientes=data.habilidades_pendientes, observaciones=data.observaciones,
            unidad_medica_id=data.unidad_medica_id or self.u.unidad_id, evaluado_por=self.u.usuario_id,
        )
        self.db.add(d)
        await self.db.flush()
        await registrar_audit(self.db, self.u, "INSERT", "Clinico", "sncev.desarrollo_infantil", d.id,
                              request=request, datos_nue={"paciente_id": str(paciente_id), "area": data.area})
        return _desarrollo_out(d)
