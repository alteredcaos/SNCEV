# =============================================================================
# SNCEV API — Endpoints FHIR R4 (módulo 12 del OpenAPI)
#
# Cobertura pragmática (ver app/fhir/mappers.py): Patient y Immunization con
# read/search/create, ImmunizationRecommendation de solo lectura, Observation
# de solo creación (somatometría), y AuditEvent de solo lectura. No implementa
# el estándar FHIR completo (validación de perfiles, _include, etc.).
# =============================================================================

from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import APIRouter, Query, Request, Response, status
from sqlalchemy import select

from ....core.errors import ApiError
from ....db.session import DbDep
from ....fhir.mappers import (
    fhir_a_paciente_campos, fhir_a_vacuna_campos, fhir_observation_a_somatometria_campo,
    paciente_a_fhir, pendiente_a_recomendacion, somatometria_a_observaciones, vacuna_a_fhir,
)
from ....middleware.auth import UserDep
from ....models.models import Paciente, Somatometria, VacunaAplicada, VacunaCatalogo
from ....schemas.schemas import PacienteCreate, PaginacionParams, VacunaAplicadaCreate
from ....services.admin_service import AdminService
from ....services.clinico_service import ClinicoService
from ....services.paciente_service import PacienteService
from ....services.vacuna_service import VacunaService

router = APIRouter(prefix="/fhir", tags=["FHIR"])

_MEDIA_FHIR = "application/fhir+json"


def _bundle(recursos: list[dict], total: int | None = None) -> dict:
    return {"resourceType": "Bundle", "type": "searchset", "total": total if total is not None else len(recursos),
           "entry": [{"resource": r} for r in recursos]}


@router.get("/metadata")
async def capability_statement():
    return Response(content=__import__("json").dumps({
        "resourceType": "CapabilityStatement", "status": "active", "date": datetime.utcnow().isoformat(),
        "kind": "instance", "fhirVersion": "4.0.1", "format": ["json"],
        "rest": [{"mode": "server", "resource": [
            {"type": "Patient", "interaction": [{"code": c} for c in ("read", "search-type", "create")]},
            {"type": "Immunization", "interaction": [{"code": c} for c in ("read", "search-type", "create")]},
            {"type": "ImmunizationRecommendation", "interaction": [{"code": "search-type"}]},
            {"type": "Observation", "interaction": [{"code": "create"}]},
            {"type": "AuditEvent", "interaction": [{"code": "search-type"}]},
        ]}],
    }), media_type=_MEDIA_FHIR)


# ── Patient ──────────────────────────────────────────────────────────────────

@router.get("/Patient/{paciente_id}")
async def patient_read(paciente_id: uuid.UUID, request: Request, db: DbDep, usuario: UserDep):
    usuario.requiere_permiso("PACIENTE_VER")
    detalle_svc = PacienteService(db, usuario)
    p = (await db.execute(select(Paciente).where(Paciente.id == paciente_id))).scalar_one_or_none()
    if p is None:
        raise ApiError(404, "Paciente no encontrado")
    ve_sensibles = usuario.tiene_permiso("PACIENTE_DATOS_SENSIBLES")
    if ve_sensibles:
        from ....middleware.auth import registrar_audit
        await registrar_audit(db, usuario, "VIEW_SENSITIVE", "FHIR", "sncev.paciente", p.id, request=request)
    return Response(content=__import__("json").dumps(paciente_a_fhir(p, ve_sensibles)), media_type=_MEDIA_FHIR)


@router.get("/Patient")
async def patient_search(db: DbDep, usuario: UserDep, _id: uuid.UUID | None = None,
                         identifier: str | None = None, birthdate: str | None = None,
                         gender: str | None = None, _count: int = Query(20, le=100), _offset: int = 0):
    usuario.requiere_permiso("PACIENTE_VER")
    conds = []
    if _id:
        conds.append(Paciente.id == _id)
    if identifier:
        from ....core.security import hash_busqueda, normalizar_curp
        curp = identifier.split("|")[-1]
        conds.append(Paciente.curp_hash == hash_busqueda(normalizar_curp(curp)))
    if gender:
        from ....fhir.mappers import _GENERO_INV
        conds.append(Paciente.sexo == _GENERO_INV.get(gender, gender))
    if birthdate:
        op, valor = (birthdate[:2], birthdate[2:]) if birthdate[:2] in ("ge", "le", "eq") else ("eq", birthdate)
        columna = Paciente.fecha_nacimiento
        conds.append({"ge": columna >= valor, "le": columna <= valor, "eq": columna == valor}[op])
    filas = (await db.execute(select(Paciente).where(*conds).limit(_count).offset(_offset))).scalars().all()
    ve_sensibles = usuario.tiene_permiso("PACIENTE_DATOS_SENSIBLES")
    import json
    return Response(content=json.dumps(_bundle([paciente_a_fhir(p, ve_sensibles) for p in filas])),
                    media_type=_MEDIA_FHIR)


@router.post("/Patient", status_code=status.HTTP_201_CREATED)
async def patient_create(recurso: dict, request: Request, db: DbDep, usuario: UserDep,
                         tipo_cartilla_id: int = Query(
                             ..., description="SNCEV no tiene equivalente FHIR estándar para este campo; "
                                              "se pasa como parámetro de consulta.")):
    usuario.requiere_permiso("PACIENTE_CREAR")
    try:
        campos = fhir_a_paciente_campos(recurso)
        data = PacienteCreate(tipo_cartilla_id=tipo_cartilla_id, **campos)
    except (ValueError, TypeError) as exc:
        raise ApiError(400, f"Recurso Patient inválido: {exc}") from exc
    paciente_id = await PacienteService(db, usuario).crear(data, request)
    return Response(content=__import__("json").dumps({"resourceType": "Patient", "id": str(paciente_id)}),
                    status_code=201, media_type=_MEDIA_FHIR)


# ── Immunization ─────────────────────────────────────────────────────────────

@router.get("/Immunization/{vacuna_aplicada_id}")
async def immunization_read(vacuna_aplicada_id: uuid.UUID, db: DbDep, usuario: UserDep):
    usuario.requiere_permiso("PACIENTE_VER")
    fila = (await db.execute(
        select(VacunaAplicada, VacunaCatalogo).join(VacunaCatalogo, VacunaCatalogo.id == VacunaAplicada.vacuna_id)
        .where(VacunaAplicada.id == vacuna_aplicada_id))).first()
    if fila is None:
        raise ApiError(404, "Dosis no encontrada")
    import json
    return Response(content=json.dumps(vacuna_a_fhir(*fila)), media_type=_MEDIA_FHIR)


@router.get("/Immunization")
async def immunization_search(db: DbDep, usuario: UserDep, patient: str | None = None,
                              vaccine_code: str | None = Query(None, alias="vaccine-code"),
                              status_: str | None = Query(None, alias="status"), _count: int = Query(20, le=100)):
    usuario.requiere_permiso("PACIENTE_VER")
    conds = []
    if patient:
        conds.append(VacunaAplicada.paciente_id == uuid.UUID(patient.removeprefix("Patient/")))
    if vaccine_code:
        conds.append(VacunaCatalogo.fhir_cvx_code == vaccine_code)
    if status_ == "completed":
        conds.append(VacunaAplicada.es_valida.is_(True))
    elif status_ == "not-done":
        conds.append(VacunaAplicada.es_valida.is_(False))
    filas = (await db.execute(
        select(VacunaAplicada, VacunaCatalogo).join(VacunaCatalogo, VacunaCatalogo.id == VacunaAplicada.vacuna_id)
        .where(*conds).limit(_count))).all()
    import json
    return Response(content=json.dumps(_bundle([vacuna_a_fhir(v, c) for v, c in filas])), media_type=_MEDIA_FHIR)


@router.post("/Immunization", status_code=status.HTTP_201_CREATED)
async def immunization_create(recurso: dict, request: Request, db: DbDep, usuario: UserDep):
    usuario.requiere_permiso("VACUNA_APLICAR")
    cvx_map = dict((await db.execute(
        select(VacunaCatalogo.fhir_cvx_code, VacunaCatalogo.id)
        .where(VacunaCatalogo.fhir_cvx_code.is_not(None)))).all())
    try:
        campos = fhir_a_vacuna_campos(recurso, cvx_map)
        data = VacunaAplicadaCreate(**{k: v for k, v in campos.items() if k != "paciente_id"})
    except (ValueError, TypeError) as exc:
        raise ApiError(400, f"Recurso Immunization inválido: {exc}") from exc
    resultado = await VacunaService(db, usuario).aplicar(campos["paciente_id"], data)
    import json
    return Response(content=json.dumps({"resourceType": "Immunization", "id": str(resultado.id)}),
                    status_code=201, media_type=_MEDIA_FHIR)


# ── ImmunizationRecommendation ───────────────────────────────────────────────

@router.get("/ImmunizationRecommendation")
async def immunization_recommendation_search(db: DbDep, usuario: UserDep, patient: str = Query(...)):
    usuario.requiere_permiso("PACIENTE_VER")
    paciente_id = uuid.UUID(patient.removeprefix("Patient/"))
    pendientes = await VacunaService(db, usuario).pendientes(paciente_id)
    import json
    return Response(content=json.dumps(_bundle([pendiente_a_recomendacion(paciente_id, pendientes)], total=1)),
                    media_type=_MEDIA_FHIR)


# ── Observation ──────────────────────────────────────────────────────────────

@router.post("/Observation", status_code=status.HTTP_201_CREATED)
async def observation_create(recurso: dict, request: Request, db: DbDep, usuario: UserDep):
    usuario.requiere_permiso("CLINICO_REGISTRAR")
    try:
        paciente_id, _campo, datos = fhir_observation_a_somatometria_campo(recurso)
    except (ValueError, TypeError) as exc:
        raise ApiError(400, f"Recurso Observation inválido: {exc}") from exc
    from ....schemas.schemas import SomatometriaCreate
    resultado = await ClinicoService(db, usuario).registrar_somatometria(
        paciente_id, SomatometriaCreate(**datos), request)
    import json
    return Response(content=json.dumps({"resourceType": "Observation", "id": str(resultado.id)}),
                    status_code=201, media_type=_MEDIA_FHIR)


# ── AuditEvent ───────────────────────────────────────────────────────────────

@router.get("/AuditEvent")
async def audit_event_search(db: DbDep, usuario: UserDep, entity: uuid.UUID | None = None,
                             agent: uuid.UUID | None = None, action: str | None = None,
                             outcome: str | None = None, _count: int = Query(20, le=100)):
    usuario.requiere_permiso("AUDITORIA_VER")
    accion_map = {"C": "INSERT", "R": "VIEW_SENSITIVE", "U": "UPDATE", "D": "DELETE", "E": "LOGIN"}
    resultado_map = {"0": "OK", "8": "ERROR"}
    pag = await AdminService(db, usuario).auditoria(
        PaginacionParams(page=1, per_page=_count), agent, accion_map.get(action, action), None,
        resultado_map.get(outcome, outcome), None, None)
    recursos = [{
        "resourceType": "AuditEvent", "action": next((k for k, v in accion_map.items() if v == a.accion), "E"),
        "recorded": a.created_at.isoformat(), "outcome": "0" if a.resultado == "OK" else "8",
        "agent": [{"who": {"reference": f"Practitioner/{a.usuario_id}"}, "requestor": True}] if a.usuario_id else [],
        "source": {"site": "SNCEV-API"},
        "entity": [{"what": {"reference": f"{a.tabla_afectada}/{a.registro_id}"}}] if a.registro_id else [],
    } for a in pag.data if entity is None or a.registro_id == entity]
    import json
    return Response(content=json.dumps(_bundle(recursos, total=pag.total)), media_type=_MEDIA_FHIR)
