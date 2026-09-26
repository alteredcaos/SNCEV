# =============================================================================
# SNCEV API — Reportes y coberturas (módulo 8)
#
# /reportes/cobertura y /tendencia/mapa leen sncev_report.cobertura_vacunacion,
# una tabla PRE-CALCULADA por el job nocturno (sncev_jobs); este servicio no
# recalcula nada, solo agrega/filtra lo ya calculado. /rezago y /lotes sí
# consultan directo vacuna_aplicada porque necesitan el detalle por paciente/lote,
# que la tabla agregada no conserva.
# =============================================================================

from __future__ import annotations

import csv
import io
import uuid
from datetime import datetime, timezone

import openpyxl
from fastapi import Request
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.config import settings
from ..core.errors import ApiError
from ..core.params import get_float
from ..core.storage import get_almacen
from ..db.session import AsyncSessionLocal, ContextoRLS
from ..middleware.auth import UsuarioActual, registrar_audit
from ..models.models import UnidadMedica, VacunaAplicada, VacunaCatalogo
from ..models.models_extra import Ageb, CoberturaVacunacion, ExportJob
from ..schemas.schemas import VacunaRef
from ..schemas.schemas_extra import (
    CoberturaFila, CoberturaResponse, Dimension, ExportarRequest, LoteResponse, LoteUnidad,
    MapaFila, RezagoFila, RezagoResponse, TendenciaFila,
)

_DIM_COLUMNA = {
    "ageb": CoberturaVacunacion.ageb_clave, "municipio": CoberturaVacunacion.municipio_id,
    "jurisdiccion": CoberturaVacunacion.jurisdiccion_id, "estado": CoberturaVacunacion.estado_clave,
}


class ReporteService:

    def __init__(self, db: AsyncSession, usuario: UsuarioActual):
        self.db = db
        self.u = usuario

    # ─────────────────────────────────────────────────────────────────────────
    # GET /reportes/cobertura
    # ─────────────────────────────────────────────────────────────────────────

    async def cobertura(self, anio: int, semana_desde: int, semana_hasta: int, dimension: Dimension,
                        vacuna_id: int | None, numero_dosis: int | None, tipo_cartilla_id: int | None,
                        ageb_clave: str | None, municipio_id: int | None, jurisdiccion_id: int | None,
                        estado_clave: str | None) -> CoberturaResponse:
        c = CoberturaVacunacion
        conds = [c.anio == anio, c.semana_epidemiologica.between(semana_desde, semana_hasta)]
        if vacuna_id:
            conds.append(c.vacuna_id == vacuna_id)
        if numero_dosis:
            conds.append(c.numero_dosis == numero_dosis)
        if tipo_cartilla_id:
            conds.append(c.tipo_cartilla_id == tipo_cartilla_id)
        if ageb_clave:
            conds.append(c.ageb_clave == ageb_clave)
        if municipio_id:
            conds.append(c.municipio_id == municipio_id)
        if jurisdiccion_id:
            conds.append(c.jurisdiccion_id == jurisdiccion_id)
        if estado_clave:
            conds.append(c.estado_clave == estado_clave)

        if dimension == "nacional":
            filas = await self._agregar(conds, c.vacuna_id, c.numero_dosis)
            nombres_v = await self._nombres_vacuna([f.vacuna_id for f in filas])
            salida = [self._fila(f, "NAL", "Nacional", nombres_v) for f in filas]
        else:
            columna = _DIM_COLUMNA[dimension]
            filas = await self._agregar(conds, c.vacuna_id, c.numero_dosis, columna)
            nombres = await self._nombres_dimension(dimension, [f.dim for f in filas])
            nombres_v = await self._nombres_vacuna([f.vacuna_id for f in filas])
            salida = [self._fila(f, str(f.dim), nombres.get(str(f.dim), str(f.dim)), nombres_v) for f in filas]

        meta = await get_float(self.db, "META_COBERTURA_NACIONAL_PCT", settings.meta_cobertura_pct_default)
        return CoberturaResponse(
            periodo={"anio": anio, "semana_desde": semana_desde, "semana_hasta": semana_hasta},
            dimension=dimension, datos=salida, meta_nacional_pct=meta,
        )

    async def _agregar(self, conds, col_vacuna, col_dosis, columna_dim=None):
        c = CoberturaVacunacion
        campos = [
            columna_dim.label("dim") if columna_dim is not None else func.cast(None, c.estado_clave.type).label("dim"),
            col_vacuna.label("vacuna_id"), col_dosis.label("numero_dosis"),
            func.sum(c.dosis_aplicadas).label("dosis_aplicadas"),
            func.sum(func.coalesce(c.poblacion_objetivo, 0)).label("poblacion_objetivo"),
            func.avg(c.concordancia_pct).label("concordancia_pct"),
            func.sum(c.dosis_invalidas).label("dosis_invalidas"),
        ]
        agrupar = [col_vacuna, col_dosis] + ([columna_dim] if columna_dim is not None else [])
        q = select(*campos).where(*conds).group_by(*agrupar)
        return (await self.db.execute(q)).all()

    def _fila(self, f, dim_id: str, dim_nombre: str, nombres_v: dict[int, tuple[str, str]]) -> CoberturaFila:
        pobj = f.poblacion_objetivo or 0
        pct = round(100 * f.dosis_aplicadas / pobj, 2) if pobj else 0.0
        cvx, nom = nombres_v.get(f.vacuna_id, ("", ""))
        return CoberturaFila(
            dimension_id=dim_id, dimension_nombre=dim_nombre,
            vacuna=VacunaRef(id=f.vacuna_id, clave_censia=cvx, nombre_generico=nom),
            numero_dosis=f.numero_dosis, dosis_aplicadas=f.dosis_aplicadas, poblacion_objetivo=pobj,
            cobertura_pct=pct, concordancia_pct=round(float(f.concordancia_pct or 0), 2),
            dosis_invalidas=f.dosis_invalidas,
        )

    async def _nombres_vacuna(self, ids: list[int]) -> dict[int, tuple[str, str]]:
        ids = sorted({i for i in ids if i is not None})
        if not ids:
            return {}
        filas = (await self.db.execute(
            select(VacunaCatalogo.id, VacunaCatalogo.clave_censia, VacunaCatalogo.nombre_generico)
            .where(VacunaCatalogo.id.in_(ids)))).all()
        return {i: (cvx, nom) for i, cvx, nom in filas}

    async def _nombres_dimension(self, dimension: Dimension, ids: list[str]) -> dict[str, str]:
        ids = [i for i in ids if i not in (None, "None")]
        if not ids:
            return {}
        if dimension == "municipio":
            from ..models.models import Municipio
            filas = (await self.db.execute(select(Municipio.id, Municipio.nombre)
                                           .where(Municipio.id.in_([int(i) for i in ids])))).all()
            return {str(i): n for i, n in filas}
        if dimension == "estado":
            from ..models.models import Estado
            filas = (await self.db.execute(select(Estado.clave_inegi, Estado.nombre)
                                           .where(Estado.clave_inegi.in_(ids)))).all()
            return {i: n for i, n in filas}
        if dimension == "jurisdiccion":
            from ..models.models_extra import Jurisdiccion
            filas = (await self.db.execute(select(Jurisdiccion.id, Jurisdiccion.nombre)
                                           .where(Jurisdiccion.id.in_([int(i) for i in ids])))).all()
            return {str(i): n for i, n in filas}
        if dimension == "ageb":
            filas = (await self.db.execute(select(Ageb.clave, Ageb.nombre).where(Ageb.clave.in_(ids)))).all()
            return {i: (n or i) for i, n in filas}
        return {}

    # ─────────────────────────────────────────────────────────────────────────
    # GET /reportes/cobertura/tendencia
    # ─────────────────────────────────────────────────────────────────────────

    async def tendencia(self, vacuna_id: int, numero_dosis: int | None, estado_clave: str | None,
                        municipio_id: int | None, anio_desde: int, anio_hasta: int) -> list[TendenciaFila]:
        c = CoberturaVacunacion
        conds = [c.vacuna_id == vacuna_id, c.anio.between(anio_desde, anio_hasta)]
        if numero_dosis:
            conds.append(c.numero_dosis == numero_dosis)
        if estado_clave:
            conds.append(c.estado_clave == estado_clave)
        if municipio_id:
            conds.append(c.municipio_id == municipio_id)
        filas = (await self.db.execute(
            select(c.anio, c.semana_epidemiologica, func.sum(c.dosis_aplicadas),
                  func.sum(func.coalesce(c.poblacion_objetivo, 0)))
            .where(*conds).group_by(c.anio, c.semana_epidemiologica)
            .order_by(c.anio, c.semana_epidemiologica)
        )).all()
        return [TendenciaFila(anio=a, semana=s, dosis_aplicadas=d, poblacion_objetivo=p,
                              cobertura_pct=round(100 * d / p, 2) if p else 0.0) for a, s, d, p in filas]

    # ─────────────────────────────────────────────────────────────────────────
    # GET /reportes/cobertura/mapa
    # ─────────────────────────────────────────────────────────────────────────

    async def mapa(self, vacuna_id: int, numero_dosis: int | None, anio: int, semana: int | None,
                   estado_clave: str | None, nivel: str) -> list[MapaFila]:
        c = CoberturaVacunacion
        conds = [c.vacuna_id == vacuna_id, c.anio == anio]
        if numero_dosis:
            conds.append(c.numero_dosis == numero_dosis)
        if semana:
            conds.append(c.semana_epidemiologica == semana)
        if estado_clave:
            conds.append(c.estado_clave == estado_clave)
        elif nivel in ("municipio", "ageb"):
            raise ApiError(422, "estado_clave es requerido para nivel municipio o ageb")

        if nivel == "estado":
            filas = (await self.db.execute(
                select(c.estado_clave, func.sum(c.dosis_aplicadas), func.sum(func.coalesce(c.poblacion_objetivo, 0)))
                .where(*conds).group_by(c.estado_clave))).all()
            geoms: dict[str, str | None] = {}
        elif nivel == "municipio":
            filas = (await self.db.execute(
                select(c.municipio_id, func.sum(c.dosis_aplicadas), func.sum(func.coalesce(c.poblacion_objetivo, 0)))
                .where(*conds).group_by(c.municipio_id))).all()
            from ..models.models import Municipio
            ids = [f[0] for f in filas if f[0] is not None]
            nombres = dict((await self.db.execute(
                select(Municipio.id, Municipio.nombre).where(Municipio.id.in_(ids)))).all())
            geoms = {}
        else:  # ageb
            filas = (await self.db.execute(
                select(c.ageb_clave, func.sum(c.dosis_aplicadas), func.sum(func.coalesce(c.poblacion_objetivo, 0)))
                .where(*conds).group_by(c.ageb_clave))).all()
            claves = [f[0] for f in filas if f[0] is not None]
            geoms_rows = (await self.db.execute(
                select(Ageb.clave, Ageb.nombre, Ageb.geom_wkt).where(Ageb.clave.in_(claves)))).all()
            nombres = {k: (n or k) for k, n, _ in geoms_rows}
            geoms = {k: g for k, _, g in geoms_rows}

        umbral = await get_float(self.db, "UMBRAL_ALERTA_COBERTURA_PCT", settings.umbral_alerta_pct)
        salida = []
        for clave, dosis, pobj in filas:
            if clave is None:
                continue
            pct = round(100 * dosis / pobj, 2) if pobj else 0.0
            nombre = clave if nivel == "estado" else nombres.get(clave, clave)
            salida.append(MapaFila(clave=str(clave), nombre=nombre, cobertura_pct=pct,
                                   geom_wkt=geoms.get(clave) if nivel == "ageb" else None,
                                   alerta=pct < umbral))
        return salida

    # ─────────────────────────────────────────────────────────────────────────
    # GET /reportes/lotes — trazabilidad (consulta directa, no la tabla agregada)
    # ─────────────────────────────────────────────────────────────────────────

    async def lotes(self, lote: str, vacuna_id: int | None) -> LoteResponse:
        conds = [VacunaAplicada.lote == lote]
        if vacuna_id:
            conds.append(VacunaAplicada.vacuna_id == vacuna_id)
        filas = (await self.db.execute(
            select(VacunaAplicada, VacunaCatalogo, UnidadMedica)
            .join(VacunaCatalogo, VacunaCatalogo.id == VacunaAplicada.vacuna_id)
            .outerjoin(UnidadMedica, UnidadMedica.id == VacunaAplicada.unidad_medica_id)
            .where(*conds)
        )).all()
        if not filas:
            raise ApiError(404, "No se encontraron dosis con ese lote")

        v_cat = filas[0][1]
        fechas = [f[0].fecha_aplicacion for f in filas]
        alertas = sum(1 for f in filas if f[0].temperatura_cadena is not None
                     and not (settings.temp_cadena_min <= float(f[0].temperatura_cadena) <= settings.temp_cadena_max))

        por_unidad: dict[str, LoteUnidad] = {}
        for va, _, um in filas:
            if um is None:
                continue
            key = um.clues
            if key not in por_unidad:
                por_unidad[key] = LoteUnidad(clues=um.clues, nombre=um.nombre, dosis_aplicadas=0)
            por_unidad[key].dosis_aplicadas += 1

        return LoteResponse(
            lote=lote, vacuna=VacunaRef(id=v_cat.id, clave_censia=v_cat.clave_censia,
                                        nombre_generico=v_cat.nombre_generico),
            total_dosis=len(filas), unidades=list(por_unidad.values()),
            fecha_primera=min(fechas), fecha_ultima=max(fechas), alertas=alertas,
        )

    # ─────────────────────────────────────────────────────────────────────────
    # GET /reportes/rezago
    # ─────────────────────────────────────────────────────────────────────────

    async def rezago(self, page: int, per_page: int, tipo_cartilla_id: int | None, vacuna_id: int | None,
                     municipio_id: int | None, dias_rezago: int) -> RezagoResponse:
        # v_vacunas_pendientes (DDL 04) ya filtra correctamente lo vencido según fecha_limite;
        # no expone vacuna_id, solo clave_censia/nombre, así que el filtro por vacuna_id se hace
        # uniendo vacuna_catalogo por clave_censia.
        from sqlalchemy import text
        conds_sql = ["1=1"]
        params: dict = {"limit": per_page, "offset": (page - 1) * per_page, "dias": dias_rezago}
        if tipo_cartilla_id:
            conds_sql.append("vp.tipo_cartilla_id = :tipo_cartilla_id")
            params["tipo_cartilla_id"] = tipo_cartilla_id
        if vacuna_id:
            conds_sql.append("vc.id = :vacuna_id")
            params["vacuna_id"] = vacuna_id
        if municipio_id:
            conds_sql.append("p.municipio_nacimiento_id = :municipio_id")
            params["municipio_id"] = municipio_id

        ambito_sql, ambito_params = self._ambito_sql()
        params.update(ambito_params)
        where = " AND ".join(conds_sql + [ambito_sql])

        sql = text(f"""
            SELECT vp.paciente_id, p.fecha_nacimiento, vc.id, vc.clave_censia, vc.nombre_generico,
                   vp.serie, vp.fecha_limite, (CURRENT_DATE - vp.fecha_limite) AS dias_rezago,
                   um.nombre, mu.nombre
            FROM sncev.v_vacunas_pendientes vp
            JOIN sncev.paciente p ON p.id = vp.paciente_id
            JOIN sncev.vacuna_catalogo vc ON vc.clave_censia = vp.clave_censia
            LEFT JOIN sncev.unidad_medica um ON um.id = p.unidad_med_registro_id
            LEFT JOIN sncev_geo.municipio mu ON mu.id = p.municipio_nacimiento_id
            WHERE {where} AND (CURRENT_DATE - vp.fecha_limite) >= :dias
            ORDER BY dias_rezago DESC
            LIMIT :limit OFFSET :offset
        """)
        filas = (await self.db.execute(sql, params)).all()
        total_sql = text(f"""
            SELECT count(*) FROM sncev.v_vacunas_pendientes vp
            JOIN sncev.paciente p ON p.id = vp.paciente_id
            JOIN sncev.vacuna_catalogo vc ON vc.clave_censia = vp.clave_censia
            LEFT JOIN sncev.unidad_medica um ON um.id = p.unidad_med_registro_id
            WHERE {where} AND (CURRENT_DATE - vp.fecha_limite) >= :dias
        """)
        total = (await self.db.execute(
            total_sql, {k: v for k, v in params.items() if k not in ("limit", "offset")})).scalar_one()

        data = [RezagoFila(
            paciente_id=pid, fecha_nacimiento=fnac,
            vacuna=VacunaRef(id=vid, clave_censia=cvx, nombre_generico=nom), serie=serie,
            fecha_limite=flim, dias_rezago=int(drez), unidad_registro=um_nom, municipio=mun_nom,
        ) for pid, fnac, vid, cvx, nom, serie, flim, drez, um_nom, mun_nom in filas]
        return RezagoResponse(data=data, total=total)

    def _ambito_sql(self) -> tuple[str, dict]:
        n = self.u.nivel
        if n >= 6:
            return "TRUE", {}
        if n == 5 and self.u.estado_clave:
            return ("um.id IN (SELECT id FROM sncev.unidad_medica WHERE estado_clave = :amb_estado)",
                   {"amb_estado": self.u.estado_clave})
        if n == 4 and self.u.jurisdiccion_id is not None:
            return ("um.id IN (SELECT id FROM sncev.unidad_medica WHERE jurisdiccion_id = :amb_jur)",
                   {"amb_jur": self.u.jurisdiccion_id})
        if 2 <= n <= 3 and self.u.unidad_id:
            return "um.id = :amb_unidad", {"amb_unidad": str(self.u.unidad_id)}
        return "FALSE", {}

    # ─────────────────────────────────────────────────────────────────────────
    # POST /reportes/exportar (job asíncrono) + GET /reportes/exportar/{job_id}
    # ─────────────────────────────────────────────────────────────────────────

    async def solicitar_exportacion(self, data: ExportarRequest, request: Request | None = None) -> uuid.UUID:
        if data.incluir_datos_sensibles:
            self.u.requiere_permiso("PACIENTE_DATOS_SENSIBLES")
        job = ExportJob(usuario_id=self.u.usuario_id, tipo=data.tipo, formato=data.formato,
                        filtros=data.filtros, incluir_sensibles=data.incluir_datos_sensibles)
        self.db.add(job)
        await self.db.flush()
        await registrar_audit(self.db, self.u, "EXPORT", "Reportes", "sncev_admin.export_job", job.id,
                              request=request, datos_nue={"tipo": data.tipo, "formato": data.formato})
        job_id = job.id
        # El job corre tras el commit de la petición (necesita ver la fila insertada).
        import asyncio
        asyncio.create_task(self._ejecutar_exportacion(job_id))
        return job_id

    async def estado_exportacion(self, job_id: uuid.UUID) -> ExportJob:
        job = (await self.db.execute(select(ExportJob).where(
            ExportJob.id == job_id, ExportJob.usuario_id == self.u.usuario_id))).scalar_one_or_none()
        if job is None:
            raise ApiError(404, "Job de exportación no encontrado")
        return job

    async def _ejecutar_exportacion(self, job_id: uuid.UUID) -> None:
        """Corre en background, en su PROPIA sesión (la de la petición ya cerró)."""
        async with AsyncSessionLocal() as db:
            job = await db.get(ExportJob, job_id)
            if job is None:
                return
            db.info["rls"] = ContextoRLS(job.usuario_id, "export", 6)
            try:
                if job.tipo == "vacunas_aplicadas":
                    filas = (await db.execute(select(
                        VacunaAplicada.id, VacunaAplicada.fecha_aplicacion, VacunaAplicada.numero_dosis,
                        VacunaAplicada.lote,
                    ).limit(settings.export_max_filas))).all()
                    encabezados = ["id", "fecha_aplicacion", "numero_dosis", "lote"]
                else:
                    filas, encabezados = [], ["sin_datos"]

                contenido = self._serializar(encabezados, filas, job.formato)
                clave = f"exportaciones/{job.usuario_id}/{job.id}.{job.formato}"
                await get_almacen().guardar(clave, contenido)
                job.archivo = clave
                job.filas = len(filas)
                job.estado = "listo"
                job.finished_at = datetime.now(timezone.utc)
            except Exception as exc:  # noqa: BLE001
                job.estado = "error"
                job.error = str(exc)[:500]
                job.finished_at = datetime.now(timezone.utc)
            await db.commit()

    @staticmethod
    def _serializar(encabezados: list[str], filas: list, formato: str) -> bytes:
        if formato == "csv":
            buf = io.StringIO()
            w = csv.writer(buf)
            w.writerow(encabezados)
            for f in filas:
                w.writerow([str(v) for v in f])
            return buf.getvalue().encode("utf-8-sig")
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.append(encabezados)
        for f in filas:
            ws.append([str(v) for v in f])
        buf = io.BytesIO()
        wb.save(buf)
        return buf.getvalue()
