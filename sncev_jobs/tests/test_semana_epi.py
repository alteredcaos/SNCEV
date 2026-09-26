# =============================================================================
# SNCEV Jobs — Tests de semana epidemiológica
# Ejecutar: python -m pytest tests/ -v
# =============================================================================

from datetime import date

import pytest

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from common.semana_epi import (
    semana_de_fecha,
    semanas_del_anio,
    semana_actual,
    rango_semanas,
)


class TestSemanaEpidemiologica:

    def test_recien_nacido_año(self):
        """1 de enero cae en SE-1 o SE-53 del año anterior."""
        se = semana_de_fecha(date(2026, 1, 1))
        assert se.anio in (2025, 2026)
        assert se.semana in (1, 52, 53)

    def test_inicio_siempre_domingo(self):
        """El inicio de cualquier semana epidemiológica es domingo (weekday=6)."""
        for d in [
            date(2026, 3, 15),
            date(2026, 7, 4),
            date(2025, 12, 25),
            date(2024, 2, 29),  # año bisiesto
        ]:
            se = semana_de_fecha(d)
            assert se.inicio.weekday() == 6, (
                f"{d} → {se}: inicio {se.inicio} no es domingo"
            )

    def test_fin_siempre_sabado(self):
        """El fin de cualquier semana epidemiológica es sábado (weekday=5)."""
        se = semana_de_fecha(date(2026, 6, 29))
        assert se.fin.weekday() == 5

    def test_duracion_siempre_7_dias(self):
        """Cada semana epidemiológica dura exactamente 7 días."""
        for anio in range(2020, 2027):
            for se in semanas_del_anio(anio):
                assert (se.fin - se.inicio).days == 6, (
                    f"{se}: duración incorrecta"
                )

    def test_año_con_53_semanas(self):
        """2020 tiene 53 semanas epidemiológicas."""
        semanas = semanas_del_anio(2020)
        assert len(semanas) == 53

    def test_año_con_52_semanas(self):
        """2021 tiene 52 semanas epidemiológicas."""
        semanas = semanas_del_anio(2021)
        assert len(semanas) == 52

    def test_cobertura_continua_sin_huecos(self):
        """Las semanas de un año se suceden sin huecos ni solapamientos."""
        semanas = semanas_del_anio(2026)
        for i in range(len(semanas) - 1):
            assert semanas[i + 1].inicio == semanas[i].fin + __import__("datetime").timedelta(days=1), (
                f"Hueco entre {semanas[i]} y {semanas[i+1]}"
            )

    def test_numeracion_consecutiva(self):
        """Las semanas se numeran del 1 al N consecutivamente."""
        semanas = semanas_del_anio(2026)
        numeros = [s.semana for s in semanas]
        assert numeros == list(range(1, len(semanas) + 1))

    def test_fecha_especifica_conocida(self):
        """
        El 29 de junio de 2026 (fecha actual de la conversación)
        cae en la SE-27 del 2026 (semana que inicia el domingo 28/06/2026).
        """
        se = semana_de_fecha(date(2026, 6, 29))
        assert se.anio   == 2026
        assert se.semana == 27
        assert se.inicio == date(2026, 6, 28)   # domingo
        assert se.fin    == date(2026, 7, 4)     # sábado

    def test_rango_semanas(self):
        """rango_semanas genera todas las semanas entre dos puntos inclusive."""
        semanas = semanas_del_anio(2026)
        se5  = semanas[4]   # SE-05
        se10 = semanas[9]   # SE-10
        rango = rango_semanas(se5, se10)
        assert len(rango) == 6
        assert rango[0].semana  == 5
        assert rango[-1].semana == 10

    def test_str_representacion(self):
        se = semana_de_fecha(date(2026, 6, 29))
        assert str(se)    == "2026-SE27"
        assert se.label   == "SE 27 / 2026"


if __name__ == "__main__":
    # Ejecutar sin pytest
    import sys
    casos = TestSemanaEpidemiologica()
    metodos = [m for m in dir(casos) if m.startswith("test_")]
    ok = err = 0
    for m in metodos:
        try:
            getattr(casos, m)()
            print(f"  ✓ {m}")
            ok += 1
        except AssertionError as e:
            print(f"  ✗ {m}: {e}")
            err += 1
        except Exception as e:
            print(f"  ✗ {m} (excepción): {e}")
            err += 1
    print(f"\n{ok} ok, {err} fallidos")
    sys.exit(0 if err == 0 else 1)
