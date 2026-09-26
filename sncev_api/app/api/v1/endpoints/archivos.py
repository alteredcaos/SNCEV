# =============================================================================
# SNCEV API — Descarga de archivos vía URL temporal firmada (cartillas, exports)
# =============================================================================

from __future__ import annotations

from fastapi import APIRouter, Response

from ....core.errors import ApiError
from ....core.storage import get_almacen

router = APIRouter(prefix="/archivos", tags=["Archivos"])


@router.get("/{token}")
async def descargar(token: str):
    datos = get_almacen().resolver_token(token)
    if datos is None:
        raise ApiError(404, "Enlace inválido o expirado")
    contenido = await get_almacen().leer(datos["k"])
    return Response(content=contenido, media_type=datos["t"],
                    headers={"Content-Disposition": f'attachment; filename="{datos["n"]}"'})
