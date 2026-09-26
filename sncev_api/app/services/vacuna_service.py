# =============================================================================
# SNCEV API — Servicio de vacunación
# La bitácora de vacuna_aplicada la escribe el trigger del DDL (fn_audit_vacuna_aplicada);
# aquí NO se audita para no duplicar registros.
# =============================================================================

from __future__ import annotations

import uuid
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import exists, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.config import settings
from ..core.errors import ApiError
from ..core.utils import hoy
from ..middleware.auth import UsuarioActual
from ..models.models import (
    EsquemaVacunacion, Paciente, UnidadMedica, VacunaAplicada, VacunaCatalogo,
)
from ..schemas.schemas import (
    EsquemaResumen, HistorialVacunacion, UnidadRef, VacunaAplicadaCreate, VacunaAplicadaResponse,
    VacunaEditar, VacunaPendiente, VacunaRef, VacunaRegistrada,
)

TEMP_CADENA_MIN = Decimal("2.0")
TEMP_CADENA_MAX = Decimal("8.0")


def _ref(v: VacunaCatalogo) -> VacunaRef:
    return VacunaRef(id=v.id, clave_censia=v.clave_censia, nombre_generico=v.nombre_generico)


class VacunaService:

    def __init__(self, db: AsyncSession, usuario: UsuarioActual):
        self.db = db
        self.u = usuario

    async def _paciente(self, paciente_id: uuid.UUID) -> Paciente:
        p = (await self.db.execute(select(Paciente).where(Paciente.id == paciente_id))).scalar_one_or_none()
        if p is None:
            raise ApiError(404, "Paciente no encontrado")
        return p

    # ─────────────────────────────────────────────────────────────────────────
    # APLICAR
    # ─────────────────────────────────────────────────────────────────────────

    async def aplicar(self, paciente_id: uuid.UUID, data: VacunaAplicadaCreate) -> VacunaRegistrada:
        pac = await self._paciente(paciente_id)
        if not pac.activo:
            raise ApiError(422, "El paciente está inactivo")

        vacuna = await self.db.get(VacunaCatalogo, data.vacuna_id)
        if vacuna is None or not vacuna.activo:
            raise ApiError(422, "vacuna_id no existe o está inactiva")

        # La dosis SIN unidad médica no entra a la cobertura (fn_calcular_cobertura hace INNER JOIN)
        # y RLS la ocultaría: la unidad es obligatoria y por defecto es la del usuario.
        unidad_id = data.unidad_medica_id or self.u.unidad_id
        if unidad_id is None:
            raise ApiError(422, "unidad_medica_id es obligatoria (su usuario no tiene unidad asignada)")
        unidad = await self.db.get(UnidadMedica, unidad_id)
        if unidad is None or not unidad.activo:
            raise ApiError(422, "unidad_medica_id no existe o está inactiva")

        esquema = await self._resolver_esquema(pac, data)

        hoy_ = hoy()
        if data.fecha_aplicacion > hoy_:
            raise ApiError(422, "La fecha de aplicación no puede ser futura")
        if data.fecha_aplicacion < pac.fecha_nacimiento:
            raise ApiError(422, "La fecha de aplicación es anterior al nacimiento del paciente")
        if data.fecha_caducidad_lote and data.fecha_caducidad_lote < data.fecha_aplicacion:
            raise ApiError(422, "El lote estaba caducado en la fecha de aplicación")

        duplicada = (await self.db.execute(
            select(VacunaAplicada.id).where(
                VacunaAplicada.paciente_id == paciente_id, VacunaAplicada.vacuna_id == data.vacuna_id,
                VacunaAplicada.numero_dosis == data.numero_dosis, VacunaAplicada.es_valida.is_(True))
        )).scalar_one_or_none()
        if duplicada:
            raise ApiError(409, "Esa dosis ya está registrada para el paciente", vacuna_aplicada_id=str(duplicada))

        advertencias = await self._advertencias(pac, data, esquema)

        temp = Decimal(str(round(data.temperatura_cadena, 1))) if data.temperatura_cadena is not None else None
        if temp is not None and not (TEMP_CADENA_MIN <= temp <= TEMP_CADENA_MAX):
            advertencias.append(f"Temperatura de cadena fría fuera de {TEMP_CADENA_MIN}–{TEMP_CADENA_MAX} °C")

        v = VacunaAplicada(
            paciente_id=paciente_id, vacuna_id=data.vacuna_id, esquema_id=esquema.id if esquema else None,
            numero_dosis=data.numero_dosis, serie=data.serie or (esquema.serie if esquema else None),
            fecha_aplicacion=data.fecha_aplicacion, lote=data.lote,
            fecha_caducidad_lote=data.fecha_caducidad_lote, laboratorio=data.laboratorio,
            temperatura_cadena=temp, unidad_medica_id=unidad_id,
            aplicado_por=self.u.usuario_id, nombre_aplicador=data.nombre_aplicador,
            cedula_profesional=data.cedula_profesional, observaciones=data.observaciones,
            created_by=self.u.usuario_id,
        )
        self.db.add(v)
        await self.db.flush()
        await self.db.refresh(v, ["edad_dias_aplicacion"])     # la calcula el trigger

        return VacunaRegistrada(
            id=v.id, paciente_id=paciente_id, vacuna=_ref(vacuna), fecha_aplicacion=v.fecha_aplicacion,
            edad_dias_aplicacion=v.edad_dias_aplicacion, advertencias=advertencias,
        )

    async def _resolver_esquema(self, pac: Paciente, data: VacunaAplicadaCreate) -> EsquemaVacunacion | None:
        if data.esquema_id is not None:
            e = await self.db.get(EsquemaVacunacion, data.esquema_id)
            if e is None or e.vacuna_id != data.vacuna_id or e.numero_dosis != data.numero_dosis:
                raise ApiError(422, "esquema_id no corresponde a la vacuna y número de dosis indicados")
            return e
        # Sin esquema explícito se busca el del tipo de cartilla del paciente: sin él la dosis
        # no contaría en la concordancia de la cobertura.
        return (await self.db.execute(
            select(EsquemaVacunacion).where(
                EsquemaVacunacion.tipo_cartilla_id == pac.tipo_cartilla_id,
                EsquemaVacunacion.vacuna_id == data.vacuna_id,
                EsquemaVacunacion.numero_dosis == data.numero_dosis, EsquemaVacunacion.activo.is_(True))
        )).scalars().first()

    async def _advertencias(self, pac: Paciente, data: VacunaAplicadaCreate,
                            esquema: EsquemaVacunacion | None) -> list[str]:
        avisos: list[str] = []
        edad = (data.fecha_aplicacion - pac.fecha_nacimiento).days
        if esquema is not None:
            if edad < esquema.edad_min_dias:
                avisos.append("Aplicada antes de la edad mínima del esquema")
            if esquema.edad_max_dias is not None and edad > esquema.edad_max_dias:
                avisos.append("Aplicada después de la edad máxima del esquema")
        if data.numero_dosis > 1:
            previa = (await self.db.execute(
                select(VacunaAplicada.fecha_aplicacion).where(
                    VacunaAplicada.paciente_id == pac.id, VacunaAplicada.vacuna_id == data.vacuna_id,
                    VacunaAplicada.numero_dosis == data.numero_dosis - 1, VacunaAplicada.es_valida.is_(True))
            )).scalar_one_or_none()
            if previa is None:
                avisos.append(f"No hay registro de la dosis {data.numero_dosis - 1} de esta vacuna")
            elif esquema is not None and esquema.intervalo_min_dias is not None \
                    and (data.fecha_aplicacion - previa).days < esquema.intervalo_min_dias:
                avisos.append(f"Intervalo menor al mínimo ({esquema.intervalo_min_dias} días) desde la dosis anterior")
        return avisos

    # ─────────────────────────────────────────────────────────────────────────
    # PENDIENTES / HISTORIAL
    # ─────────────────────────────────────────────────────────────────────────

    async def pendientes(self, paciente_id: uuid.UUID, pac: Paciente | None = None) -> list[VacunaPendiente]:
        """Dosis del esquema sin dosis válida. `vencida` = ya pasó su fecha límite (o su fecha
        óptima si el esquema no define límite). Se consulta directo a las tablas (no a
        v_vacunas_pendientes) porque esa vista descarta las dosis con límite vencido."""
        pac = pac or await self._paciente(paciente_id)
        aplicada = exists().where(
            VacunaAplicada.paciente_id == pac.id, VacunaAplicada.vacuna_id == EsquemaVacunacion.vacuna_id,
            VacunaAplicada.numero_dosis == EsquemaVacunacion.numero_dosis, VacunaAplicada.es_valida.is_(True))
        filas = (await self.db.execute(
            select(EsquemaVacunacion, VacunaCatalogo)
            .join(VacunaCatalogo, VacunaCatalogo.id == EsquemaVacunacion.vacuna_id)
            .where(EsquemaVacunacion.tipo_cartilla_id == pac.tipo_cartilla_id,
                   EsquemaVacunacion.activo.is_(True), ~aplicada)
        )).all()

        hoy_, nac = hoy(), pac.fecha_nacimiento
        salida: list[VacunaPendiente] = []
        for e, v in filas:
            optima = nac + timedelta(days=e.edad_optima_dias if e.edad_optima_dias is not None else e.edad_min_dias)
            limite = nac + timedelta(days=e.edad_max_dias) if e.edad_max_dias is not None else None
            referencia = limite or optima
            salida.append(VacunaPendiente(
                esquema_id=e.id, vacuna=_ref(v), numero_dosis=e.numero_dosis, serie=e.serie,
                fecha_optima=optima, fecha_limite=limite, dias_para_optima=(optima - hoy_).days,
                vencida=referencia < hoy_,
            ))
        salida.sort(key=lambda x: (x.fecha_optima or date.max, x.vacuna.clave_censia, x.numero_dosis))
        return salida

    def _respuesta(self, v: VacunaAplicada, cat: VacunaCatalogo, um: UnidadMedica | None) -> VacunaAplicadaResponse:
        return VacunaAplicadaResponse(
            id=v.id, paciente_id=v.paciente_id, vacuna=_ref(cat), numero_dosis=v.numero_dosis, serie=v.serie,
            fecha_aplicacion=v.fecha_aplicacion, edad_dias_aplicacion=v.edad_dias_aplicacion, lote=v.lote,
            fecha_caducidad_lote=v.fecha_caducidad_lote, laboratorio=v.laboratorio,
            temperatura_cadena=float(v.temperatura_cadena) if v.temperatura_cadena is not None else None,
            unidad=UnidadRef(id=um.id, clues=um.clues, nombre=um.nombre) if um else None,
            nombre_aplicador=v.nombre_aplicador, cedula_profesional=v.cedula_profesional,
            es_valida=v.es_valida, motivo_invalidacion=v.motivo_invalidacion,
            observaciones=v.observaciones, created_at=v.created_at,
        )

    async def historial(self, paciente_id: uuid.UUID) -> HistorialVacunacion:
        pac = await self._paciente(paciente_id)
        filas = (await self.db.execute(
            select(VacunaAplicada, VacunaCatalogo, UnidadMedica)
            .join(VacunaCatalogo, VacunaCatalogo.id == VacunaAplicada.vacuna_id)
            .outerjoin(UnidadMedica, UnidadMedica.id == VacunaAplicada.unidad_medica_id)
            .where(VacunaAplicada.paciente_id == paciente_id)
            .order_by(VacunaAplicada.fecha_aplicacion, VacunaCatalogo.clave_censia, VacunaAplicada.numero_dosis)
        )).all()
        pendientes = await self.pendientes(paciente_id, pac)

        total = len((await self.db.execute(
            select(EsquemaVacunacion.id).where(EsquemaVacunacion.tipo_cartilla_id == pac.tipo_cartilla_id,
                                               EsquemaVacunacion.activo.is_(True)))).all())
        completadas = max(0, total - len(pendientes))
        return HistorialVacunacion(
            aplicadas=[self._respuesta(v, c, u) for v, c, u in filas], pendientes=pendientes,
            esquema=EsquemaResumen(
                tipo_cartilla=pac.tipo_cartilla.nombre, dosis_esquema=total, dosis_completadas=completadas,
                dosis_pendientes=len(pendientes),
                porcentaje_completo=round(100 * completadas / total, 1) if total else 0.0),
        )

    # ─────────────────────────────────────────────────────────────────────────
    # OBTENER / EDITAR / INVALIDAR
    # ─────────────────────────────────────────────────────────────────────────

    async def obtener(self, vacuna_id: uuid.UUID) -> VacunaAplicadaResponse:
        fila = (await self.db.execute(
            select(VacunaAplicada, VacunaCatalogo, UnidadMedica)
            .join(VacunaCatalogo, VacunaCatalogo.id == VacunaAplicada.vacuna_id)
            .outerjoin(UnidadMedica, UnidadMedica.id == VacunaAplicada.unidad_medica_id)
            .where(VacunaAplicada.id == vacuna_id)
        )).first()
        if fila is None:                      # inexistente u oculta por RLS
            raise ApiError(404, "Dosis no encontrada")
        return self._respuesta(*fila)

    async def editar(self, vacuna_id: uuid.UUID, data: VacunaEditar) -> VacunaAplicadaResponse:
        campos = data.model_dump(exclude_unset=True)
        if not campos:
            raise ApiError(400, "No se enviaron campos para actualizar")
        res = await self.db.execute(
            update(VacunaAplicada).where(VacunaAplicada.id == vacuna_id).values(**campos)
            .returning(VacunaAplicada.id))
        if res.first() is None:
            raise ApiError(404, "Dosis no encontrada")
        return await self.obtener(vacuna_id)

    async def invalidar(self, vacuna_id: uuid.UUID, motivo: str) -> None:
        res = await self.db.execute(
            update(VacunaAplicada)
            .where(VacunaAplicada.id == vacuna_id, VacunaAplicada.es_valida.is_(True))
            .values(es_valida=False, motivo_invalidacion=motivo).returning(VacunaAplicada.id))
        if res.first() is None:
            existe = (await self.db.execute(
                select(VacunaAplicada.id).where(VacunaAplicada.id == vacuna_id))).first()
            raise ApiError(409, "La dosis ya estaba invalidada") if existe else ApiError(404, "Dosis no encontrada")
