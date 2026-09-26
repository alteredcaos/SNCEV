# =============================================================================
# SNCEV API — Sesión de base de datos (SQLAlchemy async) y contexto RLS
#
# El DDL usa Row Level Security y triggers que leen current_setting('app.*').
# Cada TRANSACCIÓN de la sesión recibe esas variables (set_config con is_local=true)
# mediante el evento `after_begin`, de modo que también se reaplican si un servicio
# hace commit() a mitad de la petición. Se fijan SIEMPRE las siete variables: un
# `''::INT` o `''::UUID` (variable vacía en una conexión reutilizada del pool) lanzaría error.
# =============================================================================

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Annotated, AsyncIterator

from fastapi import Depends
from sqlalchemy import event, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Session

from ..core.config import settings

NIL_UUID = uuid.UUID(int=0)


@dataclass(frozen=True)
class ContextoRLS:
    usuario_id: uuid.UUID = NIL_UUID
    username: str = ""
    nivel: int = 0                       # 0 = anónimo: RLS no le muestra nada
    unidad_id: uuid.UUID | None = None
    jurisdiccion_id: int | None = None
    estado_clave: str | None = None

    @staticmethod
    def sistema() -> "ContextoRLS":
        """Contexto interno (nivel 6, sin usuario) para operaciones sin JWT que igual
        necesitan leer bajo RLS: verificación pública de cartilla por QR, login/refresh."""
        return ContextoRLS(NIL_UUID, "sistema", 6)

    @staticmethod
    def sistema() -> "ContextoRLS":
        """Sin usuario (login, refresh, logout). Nivel 6 solo para poder escribir en audit_log;
        esos flujos no tocan pacientes ni dosis."""
        return ContextoRLS(NIL_UUID, "sistema", 6)


_connect_args: dict = {
    "server_settings": {
        "application_name": "sncev_api",
        "timezone": settings.timezone,
        "search_path": "sncev,sncev_admin,sncev_geo,sncev_audit,sncev_report,public",
    }
}
if settings.db_ssl:
    _connect_args["ssl"] = settings.db_ssl

engine = create_async_engine(
    settings.database_url,
    pool_size=settings.db_pool_size,
    max_overflow=settings.db_max_overflow,
    pool_pre_ping=True,
    echo=settings.debug,
    connect_args=_connect_args,
)

AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, autoflush=False)

_SQL_CONTEXTO = text(
    """SELECT set_config('app.current_user_id',  :uid,    true),
              set_config('app.current_username', :uname,  true),
              set_config('app.rol_nivel',        :nivel,  true),
              set_config('app.unidad_medica_id', :unidad, true),
              set_config('app.jurisdiccion_id',  :jur,    true),
              set_config('app.estado_clave',     :estado, true),
              set_config('app.paciente_id',      '',      true)"""
)


def _params(ctx: ContextoRLS) -> dict[str, str]:
    return {
        "uid": str(ctx.usuario_id), "uname": ctx.username, "nivel": str(ctx.nivel),
        "unidad": str(ctx.unidad_id) if ctx.unidad_id else "",
        "jur": str(ctx.jurisdiccion_id) if ctx.jurisdiccion_id is not None else "",
        "estado": ctx.estado_clave or "",
    }


@event.listens_for(Session, "after_begin")
def _aplicar_contexto(session: Session, transaction, connection) -> None:
    ctx = session.info.get("rls") or ContextoRLS()
    connection.execute(_SQL_CONTEXTO, _params(ctx))


async def fijar_contexto(db: AsyncSession, ctx: ContextoRLS) -> None:
    """Asigna el contexto a la sesión; si ya hay transacción abierta, lo aplica de inmediato."""
    db.info["rls"] = ctx
    if db.in_transaction():
        await db.execute(_SQL_CONTEXTO, _params(ctx))


async def get_db() -> AsyncIterator[AsyncSession]:
    """Una sesión por petición: commit al terminar bien, rollback si hay excepción.
    Los servicios que necesiten persistir algo ANTES de lanzar un error (bloqueo por intentos,
    revocación de familia de tokens) deben llamar a `await db.commit()` explícitamente."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


# scope="function": el commit ocurre ANTES de enviar la respuesta (FastAPI >= 0.121).
DbDep = Annotated[AsyncSession, Depends(get_db, scope="function")]
