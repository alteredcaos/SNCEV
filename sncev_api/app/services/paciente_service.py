# =============================================================================
# SNCEV API — Servicio de pacientes y responsables
#
# Reglas de visibilidad:
#  · Listado (GET /pacientes): limitado al ámbito del usuario (unidad/jurisdicción/estado).
#  · Búsqueda por CURP exacta y consulta por id: nacional para cualquier profesional
#    (nivel >= 2), coherente con la política RLS del DDL y con una cartilla portable.
#    Cada lectura de datos sensibles queda en bitácora (VIEW_SENSITIVE, NOM-024).
#  · Los nombres están cifrados: no hay búsqueda parcial por nombre (ver README).
# =============================================================================

from __future__ import annotations

import uuid
from typing import Any

from fastapi import Request
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.ambito import filtro_unidad
from ..core.errors import ApiError
from ..core.security import (
    cifrar, cifrar_nullable, descifrar_nullable, hash_busqueda, normalizar_curp,
)
from ..middleware.auth import UsuarioActual, registrar_audit
from ..models.models import Estado, Municipio, Paciente, Responsable, TipoCartilla, UnidadMedica
from ..schemas.schemas import (
    CURP_RE, MunicipioRef, PacienteCreate, PacienteDetalle, PacientePaginado, PacientePatch,
    PacienteResumen, PaginacionParams, ResponsableInput, ResponsableOut, ResponsablePatch,
    TipoCartillaRef, UnidadRef, total_paginas,
)

_TABLA = "sncev.paciente"


class PacienteService:

    def __init__(self, db: AsyncSession, usuario: UsuarioActual):
        self.db = db
        self.u = usuario

    @property
    def _ve_sensibles(self) -> bool:
        return self.u.tiene_permiso("PACIENTE_DATOS_SENSIBLES")

    # ─────────────────────────────────────────────────────────────────────────
    # CREAR
    # ─────────────────────────────────────────────────────────────────────────

    async def crear(self, data: PacienteCreate, request: Request | None = None) -> uuid.UUID:
        tc = await self.db.get(TipoCartilla, data.tipo_cartilla_id)
        if tc is None or not tc.activo:
            raise ApiError(422, "tipo_cartilla_id no existe o está inactivo")

        curp_hash = None
        if data.curp:
            curp_hash = hash_busqueda(normalizar_curp(data.curp))
            existente = (await self.db.execute(
                select(Paciente.id).where(Paciente.curp_hash == curp_hash))).scalar_one_or_none()
            if existente:
                raise ApiError(409, "Ya existe un paciente con esa CURP", paciente_id=str(existente))

        paciente = Paciente(
            tipo_cartilla_id=data.tipo_cartilla_id,
            nombre_enc=cifrar(data.nombre), ap_paterno_enc=cifrar(data.ap_paterno),
            ap_materno_enc=cifrar_nullable(data.ap_materno),
            curp_enc=cifrar_nullable(data.curp), curp_hash=curp_hash,
            fecha_nacimiento=data.fecha_nacimiento, sexo=data.sexo,
            municipio_nacimiento_id=data.municipio_nacimiento_id,
            estado_nacimiento=data.estado_nacimiento, pais_nacimiento=data.pais_nacimiento,
            grupo_etnico=data.grupo_etnico, lengua_indigena=data.lengua_indigena,
            habla_espanol=data.habla_espanol,
            unidad_med_registro_id=data.unidad_med_registro_id or self.u.unidad_id,
            nss_imss_enc=cifrar_nullable(data.nss_imss),
            created_by=self.u.usuario_id, updated_by=self.u.usuario_id,
        )
        self.db.add(paciente)
        await self.db.flush()

        if data.responsable:
            self.db.add(self._nuevo_responsable(paciente.id, data.responsable))
            await self.db.flush()

        await registrar_audit(
            self.db, self.u, "INSERT", "Paciente", _TABLA, paciente.id, request=request,
            datos_nue={"tipo_cartilla_id": data.tipo_cartilla_id,
                       "fecha_nacimiento": data.fecha_nacimiento.isoformat(), "sexo": data.sexo,
                       "con_curp": bool(data.curp), "con_responsable": data.responsable is not None},
        )
        return paciente.id

    # ─────────────────────────────────────────────────────────────────────────
    # BUSCAR
    # ─────────────────────────────────────────────────────────────────────────

    async def buscar(self, pag: PaginacionParams, q: str | None = None, curp: str | None = None,
                     sexo: str | None = None, tipo_cartilla_id: int | None = None,
                     municipio_id: int | None = None, unidad_med_registro_id: uuid.UUID | None = None,
                     activo: bool = True) -> PacientePaginado:
        conds: list[Any] = [Paciente.activo.is_(activo)]

        curp_buscada = curp or (q if q and CURP_RE.match(q.strip().upper()) else None)
        if curp_buscada:
            # Búsqueda exacta de CURP: alcance nacional (portabilidad de la cartilla).
            conds.append(Paciente.curp_hash == hash_busqueda(normalizar_curp(curp_buscada)))
        else:
            ambito = filtro_unidad(self.u, Paciente.unidad_med_registro_id)
            if ambito is not None:
                conds.append(ambito)
            if q:
                conds.append(Paciente.expediente_local.istartswith(q.strip(), autoescape=True))

        if sexo:
            conds.append(Paciente.sexo == sexo)
        if tipo_cartilla_id:
            conds.append(Paciente.tipo_cartilla_id == tipo_cartilla_id)
        if municipio_id:
            conds.append(Paciente.municipio_nacimiento_id == municipio_id)
        if unidad_med_registro_id:
            conds.append(Paciente.unidad_med_registro_id == unidad_med_registro_id)

        total = (await self.db.execute(select(func.count()).select_from(Paciente).where(*conds))).scalar_one()
        filas = (await self.db.execute(
            select(Paciente).where(*conds)
            .order_by(Paciente.created_at.desc(), Paciente.id)
            .limit(pag.per_page).offset(pag.offset)
        )).scalars().all()

        return PacientePaginado(
            data=[PacienteResumen(
                id=p.id, tipo_cartilla_id=p.tipo_cartilla_id, tipo_cartilla=p.tipo_cartilla.nombre,
                fecha_nacimiento=p.fecha_nacimiento, sexo=p.sexo,
                municipio_nacimiento_id=p.municipio_nacimiento_id,
                unidad_med_registro_id=p.unidad_med_registro_id, activo=p.activo, created_at=p.created_at,
            ) for p in filas],
            total=total, page=pag.page, pages=total_paginas(total, pag.per_page),
        )

    # ─────────────────────────────────────────────────────────────────────────
    # OBTENER
    # ─────────────────────────────────────────────────────────────────────────

    async def obtener(self, paciente_id: uuid.UUID, request: Request | None = None) -> PacienteDetalle:
        fila = (await self.db.execute(
            select(Paciente, Municipio.id, Municipio.nombre, Estado.nombre,
                   UnidadMedica.id, UnidadMedica.clues, UnidadMedica.nombre)
            .outerjoin(Municipio, Municipio.id == Paciente.municipio_nacimiento_id)
            .outerjoin(Estado, Estado.clave_inegi == Municipio.estado_clave)
            .outerjoin(UnidadMedica, UnidadMedica.id == Paciente.unidad_med_registro_id)
            .where(Paciente.id == paciente_id)
        )).first()
        if fila is None:
            raise ApiError(404, "Paciente no encontrado")
        p, mun_id, mun_nom, est_nom, uni_id, uni_clues, uni_nom = fila

        detalle = PacienteDetalle(
            id=p.id, tipo_cartilla=TipoCartillaRef(id=p.tipo_cartilla.id, nombre=p.tipo_cartilla.nombre),
            fecha_nacimiento=p.fecha_nacimiento, sexo=p.sexo, pais_nacimiento=p.pais_nacimiento,
            estado_nacimiento=p.estado_nacimiento,
            municipio_nacimiento=MunicipioRef(id=mun_id, nombre=mun_nom, estado=est_nom) if mun_id else None,
            grupo_etnico=p.grupo_etnico, lengua_indigena=p.lengua_indigena, habla_espanol=p.habla_espanol,
            unidad_med_registro=UnidadRef(id=uni_id, clues=uni_clues, nombre=uni_nom) if uni_id else None,
            fhir_patient_id=p.fhir_patient_id, activo=p.activo,
            created_at=p.created_at, updated_at=p.updated_at,
        )
        if self._ve_sensibles:
            detalle.nombre = descifrar_nullable(p.nombre_enc)
            detalle.ap_paterno = descifrar_nullable(p.ap_paterno_enc)
            detalle.ap_materno = descifrar_nullable(p.ap_materno_enc)
            detalle.curp = descifrar_nullable(p.curp_enc)
            await registrar_audit(self.db, self.u, "VIEW_SENSITIVE", "Paciente", _TABLA, p.id, request=request)
        return detalle

    # ─────────────────────────────────────────────────────────────────────────
    # ACTUALIZAR / DESACTIVAR
    # ─────────────────────────────────────────────────────────────────────────

    async def actualizar(self, paciente_id: uuid.UUID, data: PacientePatch,
                         request: Request | None = None) -> None:
        campos = data.model_dump(exclude_unset=True)
        if not campos:
            raise ApiError(400, "No se enviaron campos para actualizar")

        sensibles = {"nombre", "ap_paterno", "ap_materno", "curp", "nss_imss"} & campos.keys()
        if sensibles:
            self.u.requiere_permiso("PACIENTE_DATOS_SENSIBLES")
        for obligatorio in ("nombre", "ap_paterno", "tipo_cartilla_id"):
            if obligatorio in campos and campos[obligatorio] is None:
                raise ApiError(422, f"'{obligatorio}' no puede quedar vacío")

        p = (await self.db.execute(select(Paciente).where(Paciente.id == paciente_id))).scalar_one_or_none()
        if p is None:
            raise ApiError(404, "Paciente no encontrado")

        if "tipo_cartilla_id" in campos:
            tc = await self.db.get(TipoCartilla, campos["tipo_cartilla_id"])
            if tc is None or not tc.activo:
                raise ApiError(422, "tipo_cartilla_id no existe o está inactivo")

        if "curp" in campos:
            nuevo_hash = hash_busqueda(normalizar_curp(campos["curp"])) if campos["curp"] else None
            if nuevo_hash:
                otro = (await self.db.execute(
                    select(Paciente.id).where(Paciente.curp_hash == nuevo_hash, Paciente.id != paciente_id)
                )).scalar_one_or_none()
                if otro:
                    raise ApiError(409, "Ya existe otro paciente con esa CURP", paciente_id=str(otro))
            p.curp_hash = nuevo_hash
            p.curp_enc = cifrar_nullable(campos["curp"])

        cifrados = {"nombre": "nombre_enc", "ap_paterno": "ap_paterno_enc",
                    "ap_materno": "ap_materno_enc", "nss_imss": "nss_imss_enc"}
        antes: dict[str, Any] = {}
        despues: dict[str, Any] = {}
        for campo, valor in campos.items():
            if campo == "curp":
                continue
            if campo in cifrados:
                setattr(p, cifrados[campo], cifrar_nullable(valor))
            else:
                antes[campo] = getattr(p, campo)
                despues[campo] = valor
                setattr(p, campo, valor)
        p.updated_by = self.u.usuario_id
        await self.db.flush()

        if sensibles:
            despues["campos_sensibles_modificados"] = sorted(sensibles)   # solo nombres, nunca valores
        await registrar_audit(self.db, self.u, "UPDATE", "Paciente", _TABLA, paciente_id,
                              datos_ant=antes or None, datos_nue=despues, request=request)

    async def desactivar(self, paciente_id: uuid.UUID, request: Request | None = None) -> None:
        res = await self.db.execute(
            update(Paciente).where(Paciente.id == paciente_id, Paciente.activo.is_(True))
            .values(activo=False, updated_by=self.u.usuario_id).returning(Paciente.id)
        )
        if res.first() is None:
            raise ApiError(404, "Paciente no encontrado o ya inactivo")
        await registrar_audit(self.db, self.u, "DELETE", "Paciente", _TABLA, paciente_id, request=request,
                              datos_nue={"activo": False, "baja_logica": True})

    # ─────────────────────────────────────────────────────────────────────────
    # RESPONSABLES
    # ─────────────────────────────────────────────────────────────────────────

    @staticmethod
    def _nuevo_responsable(paciente_id: uuid.UUID, r: ResponsableInput) -> Responsable:
        return Responsable(
            paciente_id=paciente_id, nombre_enc=cifrar(r.nombre), ap_paterno_enc=cifrar(r.ap_paterno),
            ap_materno_enc=cifrar_nullable(r.ap_materno), curp_enc=cifrar_nullable(r.curp),
            curp_hash=hash_busqueda(normalizar_curp(r.curp)) if r.curp else None,
            parentesco=r.parentesco, telefono_enc=cifrar_nullable(r.telefono),
            telefono2_enc=cifrar_nullable(r.telefono2), email_enc=cifrar_nullable(r.email),
            domicilio_calle_enc=cifrar_nullable(r.domicilio_calle),
            municipio_id=r.municipio_id, cp=r.cp, es_principal=r.es_principal,
        )

    async def _existe_paciente(self, paciente_id: uuid.UUID) -> None:
        if (await self.db.execute(select(Paciente.id).where(Paciente.id == paciente_id))).first() is None:
            raise ApiError(404, "Paciente no encontrado")

    def _responsable_out(self, r: Responsable) -> ResponsableOut:
        out = ResponsableOut(id=r.id, parentesco=r.parentesco, es_principal=r.es_principal,
                             activo=r.activo, municipio_id=r.municipio_id, cp=r.cp)
        if self._ve_sensibles:
            out.nombre = descifrar_nullable(r.nombre_enc)
            out.ap_paterno = descifrar_nullable(r.ap_paterno_enc)
            out.ap_materno = descifrar_nullable(r.ap_materno_enc)
            out.curp = descifrar_nullable(r.curp_enc)
            out.telefono = descifrar_nullable(r.telefono_enc)
            out.telefono2 = descifrar_nullable(r.telefono2_enc)
            out.email = descifrar_nullable(r.email_enc)
            out.domicilio_calle = descifrar_nullable(r.domicilio_calle_enc)
        return out

    async def listar_responsables(self, paciente_id: uuid.UUID,
                                  request: Request | None = None) -> list[ResponsableOut]:
        await self._existe_paciente(paciente_id)
        filas = (await self.db.execute(
            select(Responsable).where(Responsable.paciente_id == paciente_id, Responsable.activo.is_(True))
            .order_by(Responsable.es_principal.desc(), Responsable.created_at)
        )).scalars().all()
        if filas and self._ve_sensibles:
            await registrar_audit(self.db, self.u, "VIEW_SENSITIVE", "Paciente", "sncev.responsable",
                                  paciente_id, request=request)
        return [self._responsable_out(r) for r in filas]

    async def _despromover_principales(self, paciente_id: uuid.UUID, excepto: uuid.UUID | None = None) -> None:
        cond = [Responsable.paciente_id == paciente_id, Responsable.es_principal.is_(True)]
        if excepto:
            cond.append(Responsable.id != excepto)
        await self.db.execute(update(Responsable).where(*cond).values(es_principal=False))

    async def crear_responsable(self, paciente_id: uuid.UUID, data: ResponsableInput,
                                request: Request | None = None) -> uuid.UUID:
        await self._existe_paciente(paciente_id)
        if data.es_principal:
            await self._despromover_principales(paciente_id)
        r = self._nuevo_responsable(paciente_id, data)
        self.db.add(r)
        await self.db.flush()
        await registrar_audit(self.db, self.u, "INSERT", "Paciente", "sncev.responsable", r.id,
                              request=request, datos_nue={"paciente_id": str(paciente_id),
                                                          "parentesco": data.parentesco})
        return r.id

    async def _cargar_responsable(self, paciente_id: uuid.UUID, responsable_id: uuid.UUID) -> Responsable:
        r = (await self.db.execute(select(Responsable).where(
            Responsable.id == responsable_id, Responsable.paciente_id == paciente_id,
            Responsable.activo.is_(True)))).scalar_one_or_none()
        if r is None:
            raise ApiError(404, "Responsable no encontrado")
        return r

    async def actualizar_responsable(self, paciente_id: uuid.UUID, responsable_id: uuid.UUID,
                                     data: ResponsablePatch, request: Request | None = None) -> None:
        campos = data.model_dump(exclude_unset=True)
        if not campos:
            raise ApiError(400, "No se enviaron campos para actualizar")
        for obligatorio in ("nombre", "ap_paterno", "parentesco"):
            if obligatorio in campos and campos[obligatorio] is None:
                raise ApiError(422, f"'{obligatorio}' no puede quedar vacío")
        r = await self._cargar_responsable(paciente_id, responsable_id)

        cifrados = {"nombre": "nombre_enc", "ap_paterno": "ap_paterno_enc", "ap_materno": "ap_materno_enc",
                    "telefono": "telefono_enc", "telefono2": "telefono2_enc", "email": "email_enc",
                    "domicilio_calle": "domicilio_calle_enc"}
        for campo, valor in campos.items():
            if campo == "curp":
                r.curp_enc = cifrar_nullable(valor)
                r.curp_hash = hash_busqueda(normalizar_curp(valor)) if valor else None
            elif campo in cifrados:
                setattr(r, cifrados[campo], cifrar_nullable(valor))
            elif campo == "es_principal":
                if valor:
                    await self._despromover_principales(paciente_id, excepto=r.id)
                r.es_principal = bool(valor)
            else:
                setattr(r, campo, valor)
        await self.db.flush()
        await registrar_audit(self.db, self.u, "UPDATE", "Paciente", "sncev.responsable", r.id, request=request,
                              datos_nue={"campos_modificados": sorted(campos)})

    async def eliminar_responsable(self, paciente_id: uuid.UUID, responsable_id: uuid.UUID,
                                   request: Request | None = None) -> None:
        r = await self._cargar_responsable(paciente_id, responsable_id)
        r.activo = False
        r.es_principal = False
        await self.db.flush()
        await registrar_audit(self.db, self.u, "DELETE", "Paciente", "sncev.responsable", r.id,
                              request=request, datos_nue={"baja_logica": True})
