# =============================================================================
# SNCEV API — Catálogos (lectura). Sin escritura: los catálogos se administran
# por migración/carga masiva, no por la API (ver sncev_jobs).
# =============================================================================

from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.errors import ApiError
from ..models.models import Estado, Municipio, TipoCartilla, UnidadMedica, VacunaCatalogo
from ..models.models_extra import Jurisdiccion
from ..models.models import EsquemaVacunacion
from ..schemas.schemas import VacunaRef
from ..schemas.schemas_extra import (
    EsquemaOut, EstadoOut, JurisdiccionOut, MunicipioOut, TipoCartillaOut, UnidadMedicaOut,
    VacunaCatalogoOut,
)

RADIO_KM_DEFAULT = 20
# La distancia se calcula en Python (Haversine) sobre el resultado ya filtrado: el DDL
# no habilita PostGIS y el volumen de unidades médicas por consulta es bajo (<500).


class CatalogoService:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def vacunas(self, tipo_cartilla_id: int | None, activo: bool | None) -> list[VacunaCatalogoOut]:
        q = select(VacunaCatalogo)
        if activo is not None:
            q = q.where(VacunaCatalogo.activo.is_(activo))
        if tipo_cartilla_id is not None:
            q = q.where(VacunaCatalogo.id.in_(
                select(EsquemaVacunacion.vacuna_id).where(EsquemaVacunacion.tipo_cartilla_id == tipo_cartilla_id)))
        filas = (await self.db.execute(q.order_by(VacunaCatalogo.clave_censia))).scalars().all()
        return [VacunaCatalogoOut.model_validate(v, from_attributes=True) for v in filas]

    async def vacuna(self, vacuna_id: int) -> VacunaCatalogoOut:
        v = await self.db.get(VacunaCatalogo, vacuna_id)
        if v is None:
            raise ApiError(404, "Vacuna no encontrada en el catálogo")
        return VacunaCatalogoOut.model_validate(v, from_attributes=True)

    async def esquemas_de_vacuna(self, vacuna_id: int) -> list[EsquemaOut]:
        await self.vacuna(vacuna_id)
        return await self.esquemas(vacuna_id=vacuna_id, tipo_cartilla_id=None)

    async def esquemas(self, tipo_cartilla_id: int | None, vacuna_id: int | None) -> list[EsquemaOut]:
        q = select(EsquemaVacunacion, VacunaCatalogo).join(
            VacunaCatalogo, VacunaCatalogo.id == EsquemaVacunacion.vacuna_id
        ).where(EsquemaVacunacion.activo.is_(True))
        if tipo_cartilla_id is not None:
            q = q.where(EsquemaVacunacion.tipo_cartilla_id == tipo_cartilla_id)
        if vacuna_id is not None:
            q = q.where(EsquemaVacunacion.vacuna_id == vacuna_id)
        filas = (await self.db.execute(q.order_by(EsquemaVacunacion.edad_min_dias))).all()
        return [EsquemaOut(
            id=e.id, tipo_cartilla_id=e.tipo_cartilla_id,
            vacuna=VacunaRef(id=v.id, clave_censia=v.clave_censia, nombre_generico=v.nombre_generico),
            numero_dosis=e.numero_dosis, serie=e.serie, edad_min_dias=e.edad_min_dias,
            edad_max_dias=e.edad_max_dias, edad_optima_dias=e.edad_optima_dias,
            intervalo_min_dias=e.intervalo_min_dias, es_refuerzo=e.es_refuerzo,
        ) for e, v in filas]

    async def tipos_cartilla(self) -> list[TipoCartillaOut]:
        filas = (await self.db.execute(
            select(TipoCartilla).where(TipoCartilla.activo.is_(True)).order_by(TipoCartilla.orden)
        )).scalars().all()
        return [TipoCartillaOut.model_validate(t, from_attributes=True) for t in filas]

    async def unidades_medicas(self, estado: str | None, municipio_id: int | None,
                               jurisdiccion_id: int | None, tipo: str | None, q: str | None,
                               lat: float | None, lng: float | None, radio_km: int | None) -> list[UnidadMedicaOut]:
        base = select(UnidadMedica).where(UnidadMedica.activo.is_(True))
        if estado:
            base = base.where(UnidadMedica.estado_clave == estado)
        if municipio_id:
            base = base.where(UnidadMedica.municipio_id == municipio_id)
        if jurisdiccion_id:
            base = base.where(UnidadMedica.jurisdiccion_id == jurisdiccion_id)
        if tipo:
            base = base.where(UnidadMedica.tipo == tipo)
        if q:
            like = f"%{q.strip()}%"
            base = base.where((UnidadMedica.nombre.ilike(like)) | (UnidadMedica.clues.ilike(like)))

        filas = (await self.db.execute(base.order_by(UnidadMedica.nombre).limit(500))).scalars().all()

        salida = [UnidadMedicaOut.model_validate(u, from_attributes=True) for u in filas]
        if lat is not None and lng is not None:
            from math import asin, cos, radians, sin, sqrt

            def _hav(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
                dlat, dlon = radians(lat2 - lat1), radians(lon2 - lon1)
                a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
                return 6371 * 2 * asin(sqrt(a))

            radio = radio_km or RADIO_KM_DEFAULT
            con_distancia = []
            for u in salida:
                if u.latitud is None or u.longitud is None:
                    continue
                d = _hav(lat, lng, u.latitud, u.longitud)
                if d <= radio:
                    u.distancia_km = round(d, 2)
                    con_distancia.append(u)
            salida = sorted(con_distancia, key=lambda x: x.distancia_km or 0)
        return salida

    async def unidad_medica(self, unidad_id: uuid.UUID) -> UnidadMedicaOut:
        u = await self.db.get(UnidadMedica, unidad_id)
        if u is None:
            raise ApiError(404, "Unidad médica no encontrada")
        return UnidadMedicaOut.model_validate(u, from_attributes=True)

    async def jurisdicciones(self, estado: str | None) -> list[JurisdiccionOut]:
        q = select(Jurisdiccion).where(Jurisdiccion.activo.is_(True))
        if estado:
            q = q.where(Jurisdiccion.estado_clave == estado)
        filas = (await self.db.execute(q.order_by(Jurisdiccion.nombre))).scalars().all()
        return [JurisdiccionOut.model_validate(j, from_attributes=True) for j in filas]

    async def estados(self) -> list[EstadoOut]:
        filas = (await self.db.execute(
            select(Estado).where(Estado.activo.is_(True)).order_by(Estado.nombre))).scalars().all()
        return [EstadoOut.model_validate(e, from_attributes=True) for e in filas]

    async def municipios(self, estado: str | None) -> list[MunicipioOut]:
        q = select(Municipio).where(Municipio.activo.is_(True))
        if estado:
            q = q.where(Municipio.estado_clave == estado)
        filas = (await self.db.execute(q.order_by(Municipio.nombre))).scalars().all()
        return [MunicipioOut.model_validate(m, from_attributes=True) for m in filas]
