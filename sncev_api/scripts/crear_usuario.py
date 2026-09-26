#!/usr/bin/env python3
"""Crea un usuario (p. ej. el primer administrador).

    python -m scripts.crear_usuario --username admin --email admin@salud.gob.mx \\
        --rol "Administrador Nacional" [--unidad-id UUID] [--jurisdiccion-id N] [--estado 09] [--mfa]

La contraseña se pide por teclado (o variable SNCEV_PASSWORD). Queda con cambio obligatorio.
"""
import argparse
import asyncio
import getpass
import os
import sys
import uuid

from sqlalchemy import select

from app.core.security import (
    cifrar, cifrar_nullable, errores_politica_password, generar_secreto_totp, hash_busqueda,
    hash_password, normalizar_email, uri_totp,
)
from app.db.session import AsyncSessionLocal, engine
from app.models.models import Rol, Usuario


async def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--username", required=True)
    ap.add_argument("--email", required=True)
    ap.add_argument("--rol", required=True, help="Nombre exacto del rol (sncev_admin.rol.nombre)")
    ap.add_argument("--nombre")
    ap.add_argument("--unidad-id", type=uuid.UUID)
    ap.add_argument("--jurisdiccion-id", type=int)
    ap.add_argument("--estado")
    ap.add_argument("--mfa", action="store_true", help="Habilita TOTP y muestra el URI de enrolamiento")
    a = ap.parse_args()

    password = os.environ.get("SNCEV_PASSWORD") or getpass.getpass("Contraseña inicial: ")
    errs = errores_politica_password(password)
    if errs:
        sys.exit("Contraseña no válida: " + ", ".join(errs))

    async with AsyncSessionLocal() as db:
        rol = (await db.execute(select(Rol).where(Rol.nombre == a.rol))).scalar_one_or_none()
        if rol is None:
            nombres = [r for (r,) in (await db.execute(select(Rol.nombre))).all()]
            sys.exit(f"Rol no encontrado. Disponibles: {nombres}")
        secreto = generar_secreto_totp() if a.mfa else None
        db.add(Usuario(
            username=a.username, email_enc=cifrar(normalizar_email(a.email)),
            email_hash=hash_busqueda(normalizar_email(a.email)), password_hash=hash_password(password),
            rol_id=rol.id, nombre_enc=cifrar_nullable(a.nombre), unidad_medica_id=a.unidad_id,
            jurisdiccion_id=a.jurisdiccion_id, estado_clave=a.estado, mfa_habilitado=bool(secreto),
            mfa_secret_enc=cifrar(secreto) if secreto else None, requiere_cambio_pwd=True,
        ))
        await db.commit()
    print(f"Usuario '{a.username}' creado con rol '{a.rol}'.")
    if secreto:
        print("Enrole este URI en su app TOTP (se muestra una sola vez):\n", uri_totp(secreto, a.username))
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
