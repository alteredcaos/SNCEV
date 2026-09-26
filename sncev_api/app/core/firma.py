# =============================================================================
# SNCEV API — Firma RSA-2048/3072 de cartillas (SHA-256 + PKCS#1 v1.5)
#
# En producción, la propuesta técnica prevé KMS/HSM (la llave privada no sale del
# módulo criptográfico): basta con implementar la misma interfaz (thumbprint,
# firmar_digest, verificar_digest) sobre el proveedor elegido.
# =============================================================================

from __future__ import annotations

import base64
import hashlib
from functools import lru_cache

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, utils

from .config import settings


class FirmadorRSA:
    def __init__(self, ruta_privada, ruta_publica) -> None:
        try:
            self._priv = serialization.load_pem_private_key(ruta_privada.read_bytes(), password=None)
            self._pub = serialization.load_pem_public_key(ruta_publica.read_bytes())
        except FileNotFoundError as exc:
            raise RuntimeError(
                f"No se encontró la llave de firma: {exc.filename}. "
                "Ejecute: python scripts/generar_claves.py"
            ) from exc
        der = self._pub.public_bytes(serialization.Encoding.DER,
                                     serialization.PublicFormat.SubjectPublicKeyInfo)
        self.thumbprint = hashlib.sha256(der).hexdigest()   # 64 hex → cert_thumbprint VARCHAR(64)

    def firmar_digest(self, digest: bytes) -> str:
        firma = self._priv.sign(digest, padding.PKCS1v15(), utils.Prehashed(hashes.SHA256()))
        return base64.b64encode(firma).decode("ascii")

    def verificar_digest(self, digest: bytes, firma_b64: str, thumbprint: str | None) -> bool:
        if thumbprint and thumbprint != self.thumbprint:
            return False   # firmada con otra llave (rotación): requeriría el certificado histórico
        try:
            self._pub.verify(base64.b64decode(firma_b64), digest, padding.PKCS1v15(),
                             utils.Prehashed(hashes.SHA256()))
            return True
        except (InvalidSignature, ValueError):
            return False


@lru_cache
def get_firmador() -> FirmadorRSA:
    return FirmadorRSA(settings.firma_private_key_path, settings.firma_public_key_path)
