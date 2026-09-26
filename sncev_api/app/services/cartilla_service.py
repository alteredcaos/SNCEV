# =============================================================================
# SNCEV API — Cartilla electrónica: generación de PDF, firma RSA y verificación
# pública por QR.
#
# El paciente puede tener varias cartillas firmadas históricas (correcciones,
# nuevas dosis); al generar una nueva se desactivan las anteriores (`activa`).
# La verificación pública (QR) NUNCA expone datos personales: solo validez.
# =============================================================================

from __future__ import annotations

import hashlib
import uuid
from datetime import date

from fastapi import Request
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ..cartilla.render import qr_data_uri, render_cartilla_pdf
from ..core.config import settings
from ..core.errors import ApiError
from ..core.firma import get_firmador
from ..core.security import descifrar_nullable
from ..core.storage import get_almacen
from ..middleware.auth import UsuarioActual, registrar_audit
from ..models.models import Paciente, Responsable
from ..models.models_extra import CartillaFirmada
from ..schemas.schemas_extra import CartillaGenerada, CartillaGenerarRequest, CartillaVerificacion
from .clinico_service import ClinicoService
from .vacuna_service import VacunaService

_SECCIONES_DEFAULT = ["vacunas", "tamizajes", "somatometria", "desarrollo"]


def _edad_texto(nacimiento: date, hoy_: date) -> str:
    dias = (hoy_ - nacimiento).days
    if dias < 60:
        return f"{dias} días"
    meses = dias // 30
    if meses < 24:
        return f"{meses} meses"
    return f"{meses // 12} años, {meses % 12} meses"


class CartillaService:

    def __init__(self, db: AsyncSession, usuario: UsuarioActual):
        self.db = db
        self.u = usuario
        self.almacen = get_almacen()

    async def _paciente(self, paciente_id: uuid.UUID) -> Paciente:
        p = (await self.db.execute(select(Paciente).where(Paciente.id == paciente_id))).scalar_one_or_none()
        if p is None:
            raise ApiError(404, "Paciente no encontrado")
        return p

    # ─────────────────────────────────────────────────────────────────────────
    # GET /pacientes/{id}/cartilla — todos los módulos en un solo response
    # ─────────────────────────────────────────────────────────────────────────

    async def obtener_completa(self, paciente_id: uuid.UUID) -> dict:
        from .paciente_service import PacienteService     # import diferido: evita ciclo de módulos

        pac_svc = PacienteService(self.db, self.u)
        clin_svc = ClinicoService(self.db, self.u)
        vac_svc = VacunaService(self.db, self.u)

        detalle = await pac_svc.obtener(paciente_id)
        responsables = await pac_svc.listar_responsables(paciente_id)
        historial = await vac_svc.historial(paciente_id)
        tamizajes = await clin_svc.listar_tamizajes(paciente_id)
        somatometria = await clin_svc.listar_somatometria(paciente_id)
        desarrollo = await clin_svc.listar_desarrollo(paciente_id)

        firma = (await self.db.execute(
            select(CartillaFirmada).where(CartillaFirmada.paciente_id == paciente_id,
                                          CartillaFirmada.activa.is_(True))
            .order_by(CartillaFirmada.fecha_firma.desc())
        )).scalars().first()

        return {
            "paciente": detalle,
            "responsable": next((r for r in responsables if r.es_principal), responsables[0] if responsables else None),
            "vacunas": {"aplicadas": historial.aplicadas, "pendientes": historial.pendientes},
            "tamizajes": tamizajes,
            "somatometria": somatometria,
            "desarrollo": desarrollo,
            "firma": self._firma_out(firma) if firma else None,
        }

    def _firma_out(self, f: CartillaFirmada) -> CartillaGenerada:
        return CartillaGenerada(
            id=f.id, hash_sha256=f.hash_sha256,
            url_pdf=self.almacen.url_temporal(f.archivo_clave, f"cartilla_{f.paciente_id}.pdf", "application/pdf"),
            url_qr=f"{settings.public_base_url.rstrip('/')}/v1/cartilla/verificar/{f.qr_token}",
            qr_token=f.qr_token, fecha_firma=f.fecha_firma,
        )

    # ─────────────────────────────────────────────────────────────────────────
    # POST /pacientes/{id}/cartilla/generar
    # ─────────────────────────────────────────────────────────────────────────

    async def generar(self, paciente_id: uuid.UUID, data: CartillaGenerarRequest,
                      request: Request | None = None) -> CartillaGenerada:
        from .paciente_service import PacienteService

        pac = await self._paciente(paciente_id)
        secciones = data.incluir_secciones or _SECCIONES_DEFAULT

        pac_svc = PacienteService(self.db, self.u)
        clin_svc = ClinicoService(self.db, self.u)
        vac_svc = VacunaService(self.db, self.u)

        nombre = descifrar_nullable(pac.nombre_enc) or ""
        ap_paterno = descifrar_nullable(pac.ap_paterno_enc) or ""
        ap_materno = descifrar_nullable(pac.ap_materno_enc) or ""
        curp = descifrar_nullable(pac.curp_enc) or ""
        hoy_ = date.today()

        historial = await vac_svc.historial(paciente_id) if "vacunas" in secciones else None
        tamizajes = await clin_svc.listar_tamizajes(paciente_id) if "tamizajes" in secciones else []
        somatometria = await clin_svc.listar_somatometria(paciente_id) if "somatometria" in secciones else []

        qr_token = uuid.uuid4()
        url_verificacion = f"{settings.public_base_url.rstrip('/')}/v1/cartilla/verificar/{qr_token}"

        contexto = {
            "paciente": {
                "nombre_completo": f"{nombre} {ap_paterno} {ap_materno}".strip(),
                "curp": curp, "fecha_nacimiento": pac.fecha_nacimiento.isoformat(),
                "sexo": pac.sexo, "edad_texto": _edad_texto(pac.fecha_nacimiento, hoy_),
                "tipo_cartilla": pac.tipo_cartilla.nombre,
            },
            "vacunas": {
                "aplicadas": [
                    {"vacuna": v.vacuna.nombre_generico, "dosis": v.numero_dosis,
                     "fecha": v.fecha_aplicacion.isoformat(), "lote": v.lote or "",
                     "unidad": v.unidad.nombre if v.unidad else ""}
                    for v in (historial.aplicadas if historial else [])
                ],
                "pendientes": [
                    {"vacuna": v.vacuna.nombre_generico, "dosis": v.numero_dosis,
                     "fecha_optima": v.fecha_optima.isoformat() if v.fecha_optima else None,
                     "clase_css": "badge-vencida" if v.vencida else "badge-pendiente"}
                    for v in (historial.pendientes if historial else [])
                ],
            } if historial else None,
            "tamizajes": [
                {"tipo": t.tipo_tamiz, "fecha": t.fecha_toma.isoformat(), "resultado": t.resultado,
                 "clase_css": {"Normal": "badge-aplicada", "Anormal": "badge-vencida"}.get(t.resultado, "badge-pendiente")}
                for t in tamizajes
            ],
            "somatometria": [
                {"fecha": s.fecha_medicion.isoformat(), "edad": s.edad_dias, "peso": s.peso_kg,
                 "talla": s.talla_cm, "pc": s.pc_cm, "imc": s.imc,
                 "percentil_clase": f"percentil-{ {'N':'normal','R':'riesgo','A':'alerta'}.get((s.percentil_peso or 'N')[:1], 'normal') }",
                 "percentil_texto": s.percentil_peso or ""}
                for s in somatometria
            ],
            "qr_header_data_uri": qr_data_uri(url_verificacion),
            "firma": {"fecha_firma": None, "firmado_por": None, "cedula": None,
                     "hash_sha256": None, "qr_data_uri": qr_data_uri(url_verificacion)},
        }

        pdf_bytes = render_cartilla_pdf(contexto)
        hash_sha256 = hashlib.sha256(pdf_bytes).hexdigest()

        firmador = get_firmador()
        firma_b64 = firmador.firmar_digest(bytes.fromhex(hash_sha256))

        clave_archivo = f"cartillas/{paciente_id}/{uuid.uuid4()}.pdf"
        await self.almacen.guardar(clave_archivo, pdf_bytes)

        await self.db.execute(
            update(CartillaFirmada).where(CartillaFirmada.paciente_id == paciente_id,
                                          CartillaFirmada.activa.is_(True)).values(activa=False)
        )
        f = CartillaFirmada(
            paciente_id=paciente_id, hash_sha256=hash_sha256, firma_rsa=firma_b64,
            cert_thumbprint=firmador.thumbprint, firmado_por=self.u.usuario_id, qr_token=qr_token,
            secciones_incluidas=secciones, archivo_clave=clave_archivo,
        )
        self.db.add(f)
        await self.db.flush()

        await registrar_audit(self.db, self.u, "PRINT", "Cartilla", "sncev.cartilla_firmada", f.id,
                              request=request, datos_nue={"paciente_id": str(paciente_id),
                                                          "secciones": secciones, "hash_sha256": hash_sha256})
        return self._firma_out(f)

    # ─────────────────────────────────────────────────────────────────────────
    # GET /cartilla/verificar/{qr_token} — PÚBLICO, sin datos personales
    # ─────────────────────────────────────────────────────────────────────────

    async def verificar_qr(self, qr_token: uuid.UUID) -> CartillaVerificacion:
        fila = (await self.db.execute(
            select(CartillaFirmada, Paciente)
            .join(Paciente, Paciente.id == CartillaFirmada.paciente_id)
            .where(CartillaFirmada.qr_token == qr_token)
        )).first()
        if fila is None:
            raise ApiError(404, "QR no encontrado")
        f, pac = fila
        firmador = get_firmador()
        valida = f.activa and firmador.verificar_digest(
            bytes.fromhex(f.hash_sha256), f.firma_rsa, f.cert_thumbprint)
        return CartillaVerificacion(
            valida=valida, fecha_firma=f.fecha_firma, tipo_cartilla=pac.tipo_cartilla.nombre,
            estado_emision=pac.estado_nacimiento or "", qr_version="1.0",
        )
