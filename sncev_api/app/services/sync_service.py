# =============================================================================
# SNCEV API — Sincronización offline (app móvil de campo)
#
# Idempotencia: cada registro entrante trae `local_id` (generado en el dispositivo).
# Antes de insertar se busca en sync_registro con local_key = "<tipo>:<local_id>";
# si ya existe, se devuelve el mismo servidor_id sin duplicar (reintentos de red).
# =============================================================================

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.security import cifrar, cifrar_nullable, hash_busqueda, normalizar_curp
from ..middleware.auth import UsuarioActual, registrar_audit
from ..models.models import Paciente, Somatometria, VacunaAplicada, VacunaCatalogo
from ..models.models_extra import CitaVacunacion, SyncRegistro
from ..schemas.schemas_extra import RegistroSync, SyncPullResponse, SyncPushError, SyncPushResponse

_TABLA_POR_TIPO = {
    "paciente": "paciente", "vacuna_aplicada": "vacuna_aplicada",
    "cita": "cita_vacunacion", "somatometria": "somatometria",
}


class SyncService:

    def __init__(self, db: AsyncSession, usuario: UsuarioActual):
        self.db = db
        self.u = usuario

    # ─────────────────────────────────────────────────────────────────────────
    # PUSH
    # ─────────────────────────────────────────────────────────────────────────

    async def push(self, device_id: str, registros: list[RegistroSync],
                   request: Request | None = None) -> SyncPushResponse:
        procesados = 0
        errores: list[SyncPushError] = []
        mapping: dict[str, str] = {}

        for r in registros:
            local_key = f"{r.tipo}:{r.local_id}"
            existente = (await self.db.execute(
                select(SyncRegistro.servidor_id).where(SyncRegistro.local_key == local_key)
            )).scalar_one_or_none()
            if existente is not None:
                mapping[r.local_id] = str(existente)   # ya procesado: reintento idempotente
                procesados += 1
                continue

            try:
                servidor_id = await self._procesar_uno(r, request)
            except Exception as exc:  # noqa: BLE001
                errores.append(SyncPushError(local_id=r.local_id, error=str(exc)[:300]))
                continue

            self.db.add(SyncRegistro(
                local_key=local_key, tabla=_TABLA_POR_TIPO[r.tipo], servidor_id=servidor_id,
                usuario_id=self.u.usuario_id, device_id=device_id,
            ))
            await self.db.flush()
            mapping[r.local_id] = str(servidor_id)
            procesados += 1

        await registrar_audit(self.db, self.u, "INSERT", "Sync", "sncev.sync_registro", request=request,
                              datos_nue={"device_id": device_id, "procesados": procesados,
                                         "errores": len(errores)})
        return SyncPushResponse(procesados=procesados, errores=errores, id_mapping=mapping)

    async def _procesar_uno(self, r: RegistroSync, request: Request | None) -> uuid.UUID:
        if r.tipo == "paciente":
            return await self._sync_paciente(r.datos)
        if r.tipo == "vacuna_aplicada":
            return await self._sync_vacuna(r.datos)
        if r.tipo == "somatometria":
            return await self._sync_somatometria(r.datos)
        if r.tipo == "cita":
            return await self._sync_cita(r.datos)
        raise ValueError(f"tipo de registro no soportado: {r.tipo}")

    async def _sync_paciente(self, d: dict) -> uuid.UUID:
        curp = d.get("curp")
        curp_hash = hash_busqueda(normalizar_curp(curp)) if curp else None
        if curp_hash:
            existente = (await self.db.execute(
                select(Paciente.id).where(Paciente.curp_hash == curp_hash))).scalar_one_or_none()
            if existente:
                return existente     # el paciente ya existía en el servidor (registrado por otro dispositivo)
        p = Paciente(
            tipo_cartilla_id=int(d["tipo_cartilla_id"]), nombre_enc=cifrar(d["nombre"]),
            ap_paterno_enc=cifrar(d["ap_paterno"]), ap_materno_enc=cifrar_nullable(d.get("ap_materno")),
            curp_enc=cifrar_nullable(curp), curp_hash=curp_hash,
            fecha_nacimiento=d["fecha_nacimiento"], sexo=d["sexo"],
            unidad_med_registro_id=d.get("unidad_med_registro_id") or self.u.unidad_id,
            created_by=self.u.usuario_id, updated_by=self.u.usuario_id,
        )
        self.db.add(p)
        await self.db.flush()
        return p.id

    async def _sync_vacuna(self, d: dict) -> uuid.UUID:
        paciente_id = uuid.UUID(str(d["paciente_id"]))
        if (await self.db.execute(select(Paciente.id).where(Paciente.id == paciente_id))).first() is None:
            raise ValueError("paciente_id no existe en el servidor")
        unidad_id = d.get("unidad_medica_id") or self.u.unidad_id
        if not unidad_id:
            raise ValueError("unidad_medica_id es obligatoria")
        v = VacunaAplicada(
            paciente_id=paciente_id, vacuna_id=int(d["vacuna_id"]), numero_dosis=int(d.get("numero_dosis", 1)),
            fecha_aplicacion=d["fecha_aplicacion"], lote=d.get("lote"), unidad_medica_id=unidad_id,
            aplicado_por=self.u.usuario_id, nombre_aplicador=d.get("nombre_aplicador"),
            observaciones=d.get("observaciones"), created_by=self.u.usuario_id,
        )
        self.db.add(v)
        await self.db.flush()
        return v.id

    async def _sync_somatometria(self, d: dict) -> uuid.UUID:
        paciente_id = uuid.UUID(str(d["paciente_id"]))
        s = Somatometria(
            paciente_id=paciente_id, fecha_medicion=d["fecha_medicion"], peso_kg=d.get("peso_kg"),
            talla_cm=d.get("talla_cm"), pc_cm=d.get("pc_cm"),
            unidad_medica_id=d.get("unidad_medica_id") or self.u.unidad_id, registrado_por=self.u.usuario_id,
        )
        self.db.add(s)
        await self.db.flush()
        return s.id

    async def _sync_cita(self, d: dict) -> uuid.UUID:
        c = CitaVacunacion(
            paciente_id=uuid.UUID(str(d["paciente_id"])),
            unidad_medica_id=d.get("unidad_medica_id") or self.u.unidad_id,
            vacuna_id=d.get("vacuna_id"), fecha_programada=d["fecha_programada"],
            notas=d.get("notas"), created_by=self.u.usuario_id,
        )
        self.db.add(c)
        await self.db.flush()
        return c.id

    # ─────────────────────────────────────────────────────────────────────────
    # PULL (delta sync)
    # ─────────────────────────────────────────────────────────────────────────

    async def pull(self, last_sync_at: datetime | None, unidad_medica_id: uuid.UUID | None) -> SyncPullResponse:
        hasta = datetime.now(timezone.utc)
        desde = last_sync_at or datetime.min.replace(tzinfo=timezone.utc)
        unidad_id = unidad_medica_id or self.u.unidad_id

        pac_q = select(Paciente).where(Paciente.updated_at > desde)
        if unidad_id:
            pac_q = pac_q.where(Paciente.unidad_med_registro_id == unidad_id)
        pacientes = (await self.db.execute(pac_q.limit(2000))).scalars().all()

        vac_q = select(VacunaAplicada).where(VacunaAplicada.updated_at > desde)
        if unidad_id:
            vac_q = vac_q.where(VacunaAplicada.unidad_medica_id == unidad_id)
        vacunas = (await self.db.execute(vac_q.limit(5000))).scalars().all()

        cita_q = select(CitaVacunacion).where(CitaVacunacion.updated_at > desde)
        if unidad_id:
            cita_q = cita_q.where(CitaVacunacion.unidad_medica_id == unidad_id)
        citas = (await self.db.execute(cita_q.limit(2000))).scalars().all()

        # Los catálogos casi no cambian: se envían completos solo en la primera sincronización
        # (sin checkpoint); en pulls posteriores el dispositivo ya los tiene.
        catalogos = {"vacunas": [], "esquemas": []}
        if last_sync_at is None:
            cats = (await self.db.execute(select(VacunaCatalogo).where(VacunaCatalogo.activo.is_(True)))).scalars().all()
            catalogos["vacunas"] = [
                {"id": v.id, "clave_censia": v.clave_censia, "nombre_generico": v.nombre_generico} for v in cats
            ]

        return SyncPullResponse(
            hasta=hasta,
            pacientes=[{"id": str(p.id), "tipo_cartilla_id": p.tipo_cartilla_id,
                       "fecha_nacimiento": p.fecha_nacimiento.isoformat(), "sexo": p.sexo,
                       "activo": p.activo} for p in pacientes],
            vacunas=[{"id": str(v.id), "paciente_id": str(v.paciente_id), "vacuna_id": v.vacuna_id,
                     "numero_dosis": v.numero_dosis, "fecha_aplicacion": v.fecha_aplicacion.isoformat(),
                     "es_valida": v.es_valida} for v in vacunas],
            citas=[{"id": str(c.id), "paciente_id": str(c.paciente_id),
                   "fecha_programada": c.fecha_programada.isoformat(), "estado": c.estado} for c in citas],
            catalogos=catalogos,
        )
