# =============================================================================
# SNCEV Jobs — Semana epidemiológica mexicana
# Conforme a NOM-017-SSA2-2012 y criterio CDC (EpiWeek):
#   - La semana epidemiológica inicia el domingo.
#   - La semana 1 es la que contiene el primer jueves del año.
#   - El año epidemiológico puede tener 52 o 53 semanas.
# =============================================================================

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta


@dataclass(frozen=True)
class SemanaEpidemiologica:
    anio: int
    semana: int        # 1-53
    inicio: date       # domingo de la semana
    fin: date          # sábado de la semana

    def __str__(self) -> str:
        return f"{self.anio}-SE{self.semana:02d}"

    @property
    def label(self) -> str:
        return f"SE {self.semana:02d} / {self.anio}"


def _primer_domingo_epi(anio: int) -> date:
    """
    Domingo de inicio de la semana epidemiológica 1 del año dado.
    Regla: la SE-1 contiene el primer jueves del año.
    Retrocedemos al domingo de esa semana.
    """
    primer_jueves = date(anio, 1, 1)
    # Avanzar hasta el primer jueves (weekday: lunes=0, jueves=3)
    dias_hasta_jueves = (3 - primer_jueves.weekday()) % 7
    primer_jueves += timedelta(days=dias_hasta_jueves)
    # El domingo de esa semana está 4 días antes
    return primer_jueves - timedelta(days=4)


def semana_de_fecha(fecha: date) -> SemanaEpidemiologica:
    """
    Calcula la semana epidemiológica a la que pertenece una fecha.
    Prueba año actual, año anterior y año siguiente (para fechas de
    fin de diciembre que pueden caer en SE-1 del año siguiente).
    """
    for anio in (fecha.year, fecha.year - 1, fecha.year + 1):
        inicio_se1        = _primer_domingo_epi(anio)
        inicio_se1_sig    = _primer_domingo_epi(anio + 1)
        # La fecha debe estar dentro del rango del año epidemiológico
        if not (inicio_se1 <= fecha < inicio_se1_sig):
            continue
        delta  = (fecha - inicio_se1).days
        semana = delta // 7 + 1
        inicio = inicio_se1 + timedelta(weeks=semana - 1)
        fin    = inicio + timedelta(days=6)
        return SemanaEpidemiologica(
            anio=anio, semana=semana, inicio=inicio, fin=fin
        )

    raise ValueError(f"No se pudo calcular semana epidemiológica para {fecha}")


def semana_actual() -> SemanaEpidemiologica:
    return semana_de_fecha(date.today())


def semanas_del_anio(anio: int) -> list[SemanaEpidemiologica]:
    """Todas las semanas epidemiológicas de un año dado."""
    inicio_se1 = _primer_domingo_epi(anio)
    inicio_se1_sig = _primer_domingo_epi(anio + 1)
    total = (inicio_se1_sig - inicio_se1).days // 7
    semanas = []
    for s in range(1, total + 1):
        inicio = inicio_se1 + timedelta(weeks=s - 1)
        fin    = inicio + timedelta(days=6)
        semanas.append(SemanaEpidemiologica(
            anio=anio, semana=s, inicio=inicio, fin=fin
        ))
    return semanas


def rango_semanas(
    desde: SemanaEpidemiologica,
    hasta: SemanaEpidemiologica,
) -> list[SemanaEpidemiologica]:
    """Genera todas las semanas epidemiológicas en un rango inclusivo."""
    resultado: list[SemanaEpidemiologica] = []
    actual = desde
    while actual.inicio <= hasta.inicio:
        resultado.append(actual)
        siguiente_domingo = actual.inicio + timedelta(weeks=1)
        actual = semana_de_fecha(siguiente_domingo)
    return resultado


# ---------------------------------------------------------------------------
# Tests rápidos (ejecutar como script)
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    casos = [
        date(2026, 1, 1),
        date(2026, 6, 29),   # fecha de hoy aproximada
        date(2026, 12, 31),
        date(2025, 1, 5),    # primer domingo de 2025
        date(2024, 12, 29),  # puede ser SE-1 del 2025
    ]
    for d in casos:
        se = semana_de_fecha(d)
        print(f"  {d} → {se}  [{se.inicio} – {se.fin}]")

    print("\nSemanas 2026:")
    semanas_2026 = semanas_del_anio(2026)
    print(f"  Total semanas: {len(semanas_2026)}")
    print(f"  SE-01: {semanas_2026[0].inicio} – {semanas_2026[0].fin}")
    print(f"  SE-52: {semanas_2026[-1].inicio} – {semanas_2026[-1].fin}")
