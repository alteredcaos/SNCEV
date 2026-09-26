import asyncio
from app.core import security as sec
from app.db.session import SessionLocal
from app.models.models import Usuario
from sqlalchemy import select

USERNAME = "admin"
EMAIL = "admin@sncev.local"
PASSWORD = "Provac_Cdmx*2026"   # cámbiala por una tuya antes de correr el script
ROL_ID = 1   # 1 = Administrador Nacional (nivel 6, todos los permisos)

async def main():
    async with SessionLocal() as db:
        existente = (await db.execute(select(Usuario).where(Usuario.username == USERNAME))).scalar_one_or_none()
        if existente:
            print(f"El usuario '{USERNAME}' ya existe (id: {existente.id})")
            return
        u = Usuario(
            username=USERNAME,
            email_enc=sec.cifrar(EMAIL),
            email_hash=sec.email_hash(EMAIL),
            password_hash=sec.hash_password(PASSWORD),
            rol_id=ROL_ID,
            requiere_cambio_pwd=False,
        )
        db.add(u)
        await db.commit()
        print(f"Usuario creado: {u.username} (id: {u.id})")
        print(f"Contraseña: {PASSWORD}")

asyncio.run(main())
