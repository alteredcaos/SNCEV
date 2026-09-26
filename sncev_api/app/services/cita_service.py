# =============================================================================
# SNCEV API — Citas de vacunación
# =============================================================================

from __future__ import annotations

import uuid

from fastapi import Request
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.ambito import filtro_unidad
from ..core.errors import ApiError
from ..middleware.auth import UsuarioActual, registrar_audit
from ..models.models import Paciente, UnidadMedica, VacunaAplicada, VacunaCatalogo
from ..models.models_extra import CitaVacunacion
from ..schemas.schemas import PaginacionParams, UnidadRef, VacunaRef, total_paginas
from ..schemas.schemas_extra import CitaCreate, CitaOut, CitaPaginada, CitaPatch

_TABLA = "sncev.cita_vacunacion"


def _out(c: CitaVacunacion, um: UnidadMedica | None, v: VacunaCatalogo | None) -> CitaOut:
    return CitaOut(
        id=c.id, paciente_id=c.paciente_id,
        unidad=UnidadRef(id=um.id, clues=um.clues, nombre=um.nombre) if um else None,
        vacuna=VacunaRef(id=v.id, clave_censia=v.clave_censia, nombre_generico=v.nombre_generico) if v else None,
        esquema_id=c.esquema_id, fecha_programada=c.fecha_programada, fecha_real=c.fecha_real,
        estado=c.estado, motivo_cancelacion=c.motivo_cancelacion, recordatorio_sms=c.recordatorio_sms,
        recordatorio_push=c.recordatorio_push, notas=c.notas, vacuna_aplicada_id=c.vacuna_aplicada_id,
        created_at=c.created_at,
    )


class CitaService:

    def __init__(self, db: AsyncSession, usuario: UsuarioActual):
        self.db = db
        self.u = usuario

    async def listar(self, pag: PaginacionParams, paciente_id: uuid.UUID | None,
                     unidad_medica_id: uuid.UUID | None, estado: str | None,
                     fecha_desde=None, fecha_hasta=None) -> CitaPaginada:
        conds = []
        ambito = filtro_unidad(self.u, CitaVacunacion.unidad_medica_id)
        if ambito is not None:
            conds.append(ambito)
        if paciente_id:
            conds.append(CitaVacunacion.paciente_id == paciente_id)
        if unidad_medica_id:
            conds.append(CitaVacunacion.unidad_medica_id == unidad_medica_id)
        if estado:
            conds.append(CitaVacunacion.estado == estado)
        if fecha_desde:
            conds.append(CitaVacunacion.fecha_programada >= fecha_desde)
        if fecha_hasta:
            conds.append(CitaVacunacion.fecha_programada <= fecha_hasta)

        total = (await self.db.execute(
            select(func.count()).select_from(CitaVacunacion).where(*conds))).scalar_one()
        filas = (await self.db.execute(
            select(CitaVacunacion, UnidadMedica, VacunaCatalogo)
            .outerjoin(UnidadMedica, UnidadMedica.id == CitaVacunacion.unidad_medica_id)
            .outerjoin(VacunaCatalogo, VacunaCatalogo.id == CitaVacunacion.vacuna_id)
            .where(*conds).order_by(CitaVacunacion.fecha_programada)
            .limit(pag.per_page).offset(pag.offset)
        )).all()
        return CitaPaginada(data=[_out(c, u, v) for c, u, v in filas], total=total,
                            page=pag.page, pages=total_paginas(total, pag.per_page))

    async def _cargar(self, cita_id: uuid.UUID) -> CitaOut:
        fila = (await self.db.execute(
            select(CitaVacunacion, UnidadMedica, VacunaCatalogo)
            .outerjoin(UnidadMedica, UnidadMedica.id == CitaVacunacion.unidad_medica_id)
            .outerjoin(VacunaCatalogo, VacunaCatalogo.id == CitaVacunacion.vacuna_id)
            .where(CitaVacunacion.id == cita_id)
        )).first()
        if fila is None:
            raise ApiError(404, "Cita no encontrada")
        return _out(*fila)

    async def obtener(self, cita_id: uuid.UUID) -> CitaOut:
        return await self._cargar(cita_id)

    async def crear(self, data: CitaCreate, request: Request | None = None) -> uuid.UUID:
        if (await self.db.execute(select(Paciente.id).where(Paciente.id == data.paciente_id))
           ).first() is None:
            raise ApiError(422, "paciente_id no existe")
        unidad = await self.db.get(UnidadMedica, data.unidad_medica_id)
        if unidad is None or not unidad.activo:
            raise ApiError(422, "unidad_medica_id no existe o está inactiva")
        if data.vacuna_id and await self.db.get(VacunaCatalogo, data.vacuna_id) is None:
            raise ApiError(422, "vacuna_id no existe")

        c = CitaVacunacion(
            paciente_id=data.paciente_id, unidad_medica_id=data.unidad_medica_id,
            vacuna_id=data.vacuna_id, esquema_id=data.esquema_id, fecha_programada=data.fecha_programada,
            recordatorio_sms=data.recordatorio_sms, recordatorio_push=data.recordatorio_push,
            notas=data.notas, created_by=self.u.usuario_id,
        )
        self.db.add(c)
        await self.db.flush()
        await registrar_audit(self.db, self.u, "INSERT", "Citas", _TABLA, c.id, request=request,
                              datos_nue={"paciente_id": str(data.paciente_id),
                                         "fecha_programada": data.fecha_programada.isoformat()})
        return c.id

    async def actualizar(self, cita_id: uuid.UUID, data: CitaPatch, request: Request | None = None) -> CitaOut:
        campos = data.model_dump(exclude_unset=True)
        if not campos:
            raise ApiError(400, "No se enviaron campos para actualizar")
        if "vacuna_aplicada_id" in campos and campos["vacuna_aplicada_id"] is not None:
            if (await self.db.execute(select(VacunaAplicada.id).where(
                    VacunaAplicada.id == campos["vacuna_aplicada_id"]))).first() is None:
                raise ApiError(422, "vacuna_aplicada_id no existe")
        res = await self.db.execute(
            update(CitaVacunacion).where(CitaVacunacion.id == cita_id).values(**campos)
            .returning(CitaVacunacion.id))
        if res.first() is None:
            raise ApiError(404, "Cita no encontrada")
        await registrar_audit(self.db, self.u, "UPDATE", "Citas", _TABLA, cita_id, request=request,
                              datos_nue={"campos_modificados": sorted(campos)})
        return await self._cargar(cita_id)

    async def cancelar(self, cita_id: uuid.UUID, motivo: str, request: Request | None = None) -> None:
        res = await self.db.execute(
            update(CitaVacunacion)
            .where(CitaVacunacion.id == cita_id, CitaVacunacion.estado.notin_(["Cancelada", "Atendida"]))
            .values(estado="Cancelada", motivo_cancelacion=motivo).returning(CitaVacunacion.id))
        if res.first() is None:
            existe = (await self.db.execute(
                select(CitaVacunacion.id).where(CitaVacunacion.id == cita_id))).first()
            raise ApiError(409, "La cita ya está cancelada o atendida") if existe else ApiError(404, "Cita no encontrada")
        await registrar_audit(self.db, self.u, "DELETE", "Citas", _TABLA, cita_id, request=request,
                              datos_nue={"estado": "Cancelada", "motivo": motivo})
