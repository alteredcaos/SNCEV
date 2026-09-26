# =============================================================================
# SNCEV Jobs — Database helper
# Pool async de conexiones PostgreSQL con SQLAlchemy asyncio
# =============================================================================

import contextlib
from typing import AsyncIterator

import structlog
from sqlalchemy.ext.asyncio import (
    AsyncConnection,
    AsyncEngine,
    create_async_engine,
)
from sqlalchemy import text

from .config import get_settings

log = structlog.get_logger(__name__)
_engine: AsyncEngine | None = None


def get_engine() -> AsyncEngine:
    global _engine
    if _engine is None:
        cfg = get_settings()
        _engine = create_async_engine(
            cfg.db_url,
            pool_size=cfg.db_pool_min,
            max_overflow=cfg.db_pool_max - cfg.db_pool_min,
            pool_pre_ping=True,          # valida conexión antes de usar
            pool_recycle=3600,           # recicla conexiones cada 1h
            echo=cfg.environment == 'development',
        )
        log.info('Pool de BD creado', host=cfg.db_host, db=cfg.db_name)
    return _engine


@contextlib.asynccontextmanager
async def get_conn() -> AsyncIterator[AsyncConnection]:
    """Context manager que entrega una conexión del pool."""
    async with get_engine().connect() as conn:
        yield conn


@contextlib.asynccontextmanager
async def get_transaction() -> AsyncIterator[AsyncConnection]:
    """Context manager que entrega una conexión dentro de una transacción."""
    async with get_engine().begin() as conn:
        yield conn


async def ejecutar_funcion_pg(
    conn: AsyncConnection,
    nombre_funcion: str,
    *args,
) -> int:
    """Llama a una función PostgreSQL y retorna el valor entero resultante."""
    placeholders = ', '.join(f':p{i}' for i in range(len(args)))
    params = {f'p{i}': v for i, v in enumerate(args)}
    result = await conn.execute(
        text(f'SELECT {nombre_funcion}({placeholders})'),
        params,
    )
    row = result.fetchone()
    return row[0] if row else 0


async def dispose_engine() -> None:
    global _engine
    if _engine:
        await _engine.dispose()
        _engine = None
        log.info('Pool de BD cerrado')
