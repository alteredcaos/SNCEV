#!/usr/bin/env python3
"""Genera las llaves del sistema.

    python scripts/generar_claves.py [directorio_certs]

· certs/private.pem y certs/public.pem  → firma de JWT (RS256, RSA-3072)
· imprime AES_KEY_HEX (32 bytes) y HASH_PEPPER_HEX para el .env

NO reemplace las claves AES/pepper de una base con datos: los datos cifrados y los hashes de
CURP/correo dejarían de poder leerse/buscarse. En producción guárdelas en un gestor de secretos.
"""
import secrets
import sys
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa


def main() -> None:
    destino = Path(sys.argv[1] if len(sys.argv) > 1 else "certs")
    destino.mkdir(parents=True, exist_ok=True)
    priv_path, pub_path = destino / "private.pem", destino / "public.pem"
    if priv_path.exists():
        sys.exit(f"{priv_path} ya existe; no se sobrescribe.")

    def _par(nombre_priv: str, nombre_pub: str, bits: int) -> None:
        llave = rsa.generate_private_key(public_exponent=65537, key_size=bits)
        (destino / nombre_priv).write_bytes(llave.private_bytes(
            serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()))
        (destino / nombre_priv).chmod(0o600)
        (destino / nombre_pub).write_bytes(llave.public_key().public_bytes(
            serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo))

    _par("private.pem", "public.pem", 3072)               # JWT (RS256)
    _par("firma_private.pem", "firma_public.pem", 2048)    # firma de cartillas

    print(f"Llaves escritas en {destino}/ (JWT: private/public.pem; firma: firma_private/public.pem)")
    print("\nAgregue al .env:")
    print(f"AES_KEY_HEX={secrets.token_hex(32)}")
    print(f"HASH_PEPPER_HEX={secrets.token_hex(32)}")


if __name__ == "__main__":
    main()
