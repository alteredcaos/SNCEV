# =============================================================================
# SNCEV API — Parámetros de negocio configurables
#
# El DDL no define una tabla de parámetros en caliente; estos valores viven en
# `Settings` (variables de entorno) y se leen aquí para que los servicios no
# dependan de `settings` directamente y sea trivial mudarlos a una tabla de BD
# el día que se necesite administrarlos sin reiniciar el servicio.
# =============================================================================

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from .config import settings

_MAPA_FLOAT = {
    "META_COBERTURA_NACIONAL_PCT": "meta_cobertura_pct_default",
    "UMBRAL_ALERTA_COBERTURA_PCT": "umbral_alerta_pct",
}


async def get_float(db: AsyncSession, clave: str, default: float) -> float:
    """Firma async (recibe `db`) para permitir, sin cambiar los llamadores, que en el
    futuro esto consulte una tabla de configuración en lugar de `settings`."""
    atributo = _MAPA_FLOAT.get(clave)
    return getattr(settings, atributo, default) if atributo else default
