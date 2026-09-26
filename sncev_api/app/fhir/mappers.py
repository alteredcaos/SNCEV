# =============================================================================
# SNCEV API — Mapeo entre los modelos internos y recursos FHIR R4
#
# Cobertura deliberadamente pragmática: los campos que el contrato pide y que
# el modelo de datos ya tiene. No implementa el estándar FHIR completo (no hay
# validación de perfiles ni terminologías completas); es lo suficiente para
# interoperar con un sistema externo (IMSS/ISSSTE) que consuma estos recursos.
# =============================================================================

from __future__ import annotations

import uuid
from typing import Any

from ..core.security import descifrar_nullable
from ..models.models import Paciente, Somatometria, VacunaAplicada, VacunaCatalogo
from ..models.models_extra import Desarrollo, Tamizaje

_GENERO = {"M": "male", "F": "female", "I": "unknown"}
_GENERO_INV = {v: k for k, v in _GENERO.items()}

LOINC_OBSERVACION = {
    "29463-7": ("peso_kg", "kg"), "8302-2": ("talla_cm", "cm"), "9843-4": ("pc_cm", "cm"),
}


def paciente_a_fhir(p: Paciente, ver_sensibles: bool) -> dict[str, Any]:
    recurso: dict[str, Any] = {
        "resourceType": "Patient", "id": str(p.id),
        "meta": {"lastUpdated": p.updated_at.isoformat(),
                "profile": ["http://hl7.org/fhir/StructureDefinition/Patient"]},
        "gender": _GENERO.get(p.sexo, "unknown"), "birthDate": p.fecha_nacimiento.isoformat(),
        "active": p.activo,
    }
    if ver_sensibles:
        curp = descifrar_nullable(p.curp_enc)
        if curp:
            recurso["identifier"] = [{"system": "http://sncev.salud.gob.mx/curp", "value": curp}]
        nombre = descifrar_nullable(p.nombre_enc) or ""
        ap_pat = descifrar_nullable(p.ap_paterno_enc) or ""
        ap_mat = descifrar_nullable(p.ap_materno_enc) or ""
        recurso["name"] = [{"family": f"{ap_pat} {ap_mat}".strip(), "given": [nombre]}]
    if p.pais_nacimiento:
        recurso["address"] = [{"country": p.pais_nacimiento}]
    if p.lengua_indigena:
        recurso["communication"] = [{"language": {"text": p.lengua_indigena}, "preferred": True}]
    return recurso


def fhir_a_paciente_campos(recurso: dict[str, Any]) -> dict[str, Any]:
    """Extrae de un recurso Patient FHIR entrante los campos que PacienteCreate necesita."""
    if recurso.get("resourceType") != "Patient":
        raise ValueError("resourceType debe ser 'Patient'")
    nombres = recurso.get("name") or [{}]
    n0 = nombres[0]
    given = n0.get("given") or [""]
    familia = (n0.get("family") or "").split(" ", 1)
    curp = None
    for ident in recurso.get("identifier", []):
        if "curp" in (ident.get("system") or "").lower():
            curp = ident.get("value")
    genero = _GENERO_INV.get(recurso.get("gender"), "I")
    if not recurso.get("birthDate"):
        raise ValueError("birthDate es obligatorio")
    return {
        "nombre": given[0] or "N/D", "ap_paterno": familia[0] or "N/D",
        "ap_materno": familia[1] if len(familia) > 1 else None,
        "curp": curp, "fecha_nacimiento": recurso["birthDate"], "sexo": genero,
    }


def vacuna_a_fhir(v: VacunaAplicada, cat: VacunaCatalogo) -> dict[str, Any]:
    recurso: dict[str, Any] = {
        "resourceType": "Immunization", "id": str(v.id),
        "status": "completed" if v.es_valida else "not-done",
        "vaccineCode": {
            "coding": [{"system": "http://hl7.org/fhir/sid/cvx", "code": cat.fhir_cvx_code or "",
                       "display": cat.nombre_generico}],
            "text": cat.nombre_generico,
        },
        "patient": {"reference": f"Patient/{v.paciente_id}"},
        "occurrenceDateTime": v.fecha_aplicacion.isoformat(), "primarySource": True,
    }
    if v.lote:
        recurso["lotNumber"] = v.lote
    if v.fecha_caducidad_lote:
        recurso["expirationDate"] = v.fecha_caducidad_lote.isoformat()
    if v.unidad_medica_id:
        recurso["location"] = {"reference": f"Organization/{v.unidad_medica_id}"}
    if v.observaciones:
        recurso["note"] = [{"text": v.observaciones}]
    if not v.es_valida and v.motivo_invalidacion:
        recurso["statusReason"] = {"text": v.motivo_invalidacion}
    return recurso


def fhir_a_vacuna_campos(recurso: dict[str, Any], vacuna_id_por_cvx: dict[str, int]) -> dict[str, Any]:
    if recurso.get("resourceType") != "Immunization":
        raise ValueError("resourceType debe ser 'Immunization'")
    cvx = None
    for c in (recurso.get("vaccineCode") or {}).get("coding", []):
        if "cvx" in (c.get("system") or "").lower():
            cvx = c.get("code")
    if cvx not in vacuna_id_por_cvx:
        raise ValueError(f"vaccineCode.coding con código CVX '{cvx}' no está en el catálogo")
    ref = (recurso.get("patient") or {}).get("reference", "")
    if not ref.startswith("Patient/"):
        raise ValueError("patient.reference debe tener la forma 'Patient/{id}'")
    fecha = recurso.get("occurrenceDateTime")
    if not fecha:
        raise ValueError("occurrenceDateTime es obligatorio")
    return {
        "paciente_id": uuid.UUID(ref.removeprefix("Patient/")), "vacuna_id": vacuna_id_por_cvx[cvx],
        "numero_dosis": 1, "fecha_aplicacion": fecha, "lote": recurso.get("lotNumber"),
        "fecha_caducidad_lote": recurso.get("expirationDate"),
        "observaciones": (recurso.get("note") or [{}])[0].get("text"),
    }


def pendiente_a_recomendacion(paciente_id: uuid.UUID, pendientes: list) -> dict[str, Any]:
    return {
        "resourceType": "ImmunizationRecommendation", "patient": {"reference": f"Patient/{paciente_id}"},
        "recommendation": [
            {
                "vaccineCode": [{"coding": [{"system": "http://hl7.org/fhir/sid/cvx",
                                            "code": p.vacuna.clave_censia}], "text": p.vacuna.nombre_generico}],
                "forecastStatus": {"coding": [{"code": "overdue" if p.vencida else "due",
                                              "display": "Vencida" if p.vencida else "Pendiente"}]},
                "dateCriterion": [
                    *([{"code": {"coding": [{"code": "30981-5"}]}, "value": p.fecha_optima.isoformat()}]
                     if p.fecha_optima else []),
                    *([{"code": {"coding": [{"code": "59778-1"}]}, "value": p.fecha_limite.isoformat()}]
                     if p.fecha_limite else []),
                ],
                "doseNumber": str(p.numero_dosis),
            }
            for p in pendientes
        ],
    }


_LOINC_POR_CAMPO = {v[0]: (codigo, v[1]) for codigo, v in LOINC_OBSERVACION.items()}


def somatometria_a_observaciones(s: Somatometria) -> list[dict[str, Any]]:
    salida = []
    for campo, (codigo, unidad) in _LOINC_POR_CAMPO.items():
        valor = getattr(s, campo, None)
        if valor is None:
            continue
        salida.append({
            "resourceType": "Observation", "status": "final",
            "category": [{"coding": [{"system": "http://terminology.hl7.org/CodeSystem/observation-category",
                                     "code": "vital-signs"}]}],
            "code": {"coding": [{"system": "http://loinc.org", "code": codigo}]},
            "subject": {"reference": f"Patient/{s.paciente_id}"},
            "effectiveDateTime": s.fecha_medicion.isoformat(),
            "valueQuantity": {"value": float(valor), "unit": unidad,
                             "system": "http://unitsofmeasure.org", "code": unidad},
        })
    return salida


def fhir_observation_a_somatometria_campo(recurso: dict[str, Any]) -> tuple[uuid.UUID, str, dict[str, Any]]:
    if recurso.get("resourceType") != "Observation":
        raise ValueError("resourceType debe ser 'Observation'")
    codigo = None
    for c in (recurso.get("code") or {}).get("coding", []):
        if "loinc" in (c.get("system") or "").lower():
            codigo = c.get("code")
    if codigo not in LOINC_OBSERVACION:
        raise ValueError(f"code.coding con código LOINC '{codigo}' no soportado")
    campo, _ = LOINC_OBSERVACION[codigo]
    ref = (recurso.get("subject") or {}).get("reference", "")
    if not ref.startswith("Patient/"):
        raise ValueError("subject.reference debe tener la forma 'Patient/{id}'")
    fecha = recurso.get("effectiveDateTime")
    if not fecha:
        raise ValueError("effectiveDateTime es obligatorio")
    valor = (recurso.get("valueQuantity") or {}).get("value")
    if valor is None:
        raise ValueError("valueQuantity.value es obligatorio")
    return uuid.UUID(ref.removeprefix("Patient/")), campo, {"fecha_medicion": fecha, campo: valor}
