import asyncio
from app.core import security as sec
from app.db.session import AsyncSessionLocal, ContextoRLS, fijar_contexto
from app.models.models import Usuario
from sqlalchemy import select

USERNAME = "admin"
NUEVA_PASSWORD = "Provac_Cdmx*2026"

async def main():
    async with AsyncSessionLocal() as db:
        # Fijar el contexto RLS con permisos de sistema (Nivel 6) 
        # para saltar las restricciones de Row Level Security
        await fijar_contexto(db, ContextoRLS.sistema())
        
        # 1. Buscar al usuario admin
        existente = (await db.execute(select(Usuario).where(Usuario.username == USERNAME))).scalar_one_or_none()
        
        if not existente:
            print(f"Error: El usuario '{USERNAME}' no existe en la base de datos.")
            return
        
        # 2. Actualizar los campos
        existente.password_hash = sec.hash_password(NUEVA_PASSWORD)
        existente.requiere_cambio_pwd = False  
        
        # 3. Confirmar la transacción
        await db.commit()
        print(f"¡Contraseña actualizada con éxito para el usuario: '{USERNAME}'!")
        print(f"Nueva contraseña establecida: {NUEVA_PASSWORD}")

asyncio.run(main())
