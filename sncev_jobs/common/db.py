# =============================================================================
# SNCEV Jobs — Pool de conexiones PostgreSQL
# =============================================================================

from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Generator

import psycopg2
import psycopg2.extras
import psycopg2.pool
import structlog

log = structlog.get_logger(__name__)

_pool: psycopg2.pool.ThreadedConnectionPool | None = None


def inicializar_pool(
    minconn: int = 2,
    maxconn: int = 8,
) -> None:
    """Inicializar el pool al arrancar el scheduler. Llamar una sola vez."""
    global _pool
    _pool = psycopg2.pool.ThreadedConnectionPool(
        minconn=minconn,
        maxconn=maxconn,
        dsn=_dsn(),
        cursor_factory=psycopg2.extras.RealDictCursor,
    )
    log.info("pool_inicializado", minconn=minconn, maxconn=maxconn)


def cerrar_pool() -> None:
    global _pool
    if _pool:
        _pool.closeall()
        _pool = None
        log.info("pool_cerrado")


def _dsn() -> str:
    return (
        f"host={os.environ['DB_HOST']} "
        f"port={os.environ.get('DB_PORT', '5432')} "
        f"dbname={os.environ['DB_NAME']} "
        f"user={os.environ['DB_USER']} "
        f"password={os.environ['DB_PASSWORD']} "
        f"sslmode={os.environ.get('DB_SSLMODE', 'require')} "
        f"options=-csearch_path=sncev,sncev_admin,sncev_geo,"
        f"sncev_audit,sncev_report,public"
    )


@contextmanager
def conexion() -> Generator[psycopg2.extensions.connection, None, None]:
    """
    Context manager que obtiene/devuelve una conexión del pool.
    Hace commit automático al salir sin error, rollback si hay excepción.
    """
    if _pool is None:
        raise RuntimeError("Pool no inicializado — llamar inicializar_pool() primero")

    conn = _pool.getconn()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        _pool.putconn(conn)


@contextmanager
def cursor(conn: psycopg2.extensions.connection):
    """Context manager de cursor con RealDictCursor."""
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    try:
        yield cur
    finally:
        cur.close()
