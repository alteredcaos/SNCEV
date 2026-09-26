"""Ámbito geográfico/institucional del usuario (defensa en profundidad sobre RLS)."""
from __future__ import annotations

from sqlalchemy import false, select
from sqlalchemy.orm import InstrumentedAttribute

from ..models.models import UnidadMedica


def filtro_unidad(usuario, columna: InstrumentedAttribute):
    """Condición SQLAlchemy que limita `columna` (id de unidad médica) al ámbito del usuario.
    Nivel 6 = sin restricción; 5 = su estado; 4 = su jurisdicción; 2-3 = su unidad."""
    n = usuario.nivel
    if n >= 6:
        return None
    if n == 5 and usuario.estado_clave:
        return columna.in_(select(UnidadMedica.id).where(UnidadMedica.estado_clave == usuario.estado_clave))
    if n == 4 and usuario.jurisdiccion_id is not None:
        return columna.in_(select(UnidadMedica.id).where(UnidadMedica.jurisdiccion_id == usuario.jurisdiccion_id))
    if 2 <= n <= 3 and usuario.unidad_id:
        return columna == usuario.unidad_id
    return false()
