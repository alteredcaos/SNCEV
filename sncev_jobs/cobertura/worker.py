# =============================================================================
# SNCEV Jobs — Worker de cálculo de coberturas
#
# Responsabilidades:
#   1. Determinar qué semanas necesitan (re)calcularse
#   2. Llamar fn_calcular_cobertura() en PostgreSQL por cada semana
#   3. Refrescar la vista materializada mv_cobertura_nacional_anual
#   4. Registrar resultados en job_log
#   5. Emitir métricas Prometheus y alertas si hay estados por debajo del umbral
# =============================================================================

from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

import httpx
import structlog
from prometheus_client import Counter, Gauge, Histogram
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    before_sleep_log,
    retry_if_exception_type,
)
import psycopg2

from common.db import conexion, cursor
from common.semana_epi import (
    SemanaEpidemiologica,
    semana_actual,
    semanas_del_anio,
    rango_semanas,
)

log = structlog.get_logger(__name__)

# ---------------------------------------------------------------------------
# Métricas Prometheus
# ---------------------------------------------------------------------------

JOB_DURACION = Histogram(
    "sncev_job_cobertura_duracion_segundos",
    "Duración del job de cálculo de coberturas",
    buckets=[5, 15, 30, 60, 120, 300, 600],
)
JOB_SEMANAS_PROCESADAS = Counter(
    "sncev_job_cobertura_semanas_total",
    "Semanas epidemiológicas procesadas",
    ["resultado"],  # 'ok' | 'error'
)
JOB_FILAS_CALCULADAS = Counter(
    "sncev_job_cobertura_filas_total",
    "Filas insertadas en cobertura_vacunacion",
)
COBERTURA_NACIONAL = Gauge(
    "sncev_cobertura_nacional_pct",
    "Cobertura nacional más reciente por vacuna",
    ["clave_censia", "numero_dosis"],
)
ESTADOS_EN_ALERTA = Gauge(
    "sncev_estados_en_alerta_total",
    "Número de estados con cobertura < umbral",
    ["umbral"],
)

# ---------------------------------------------------------------------------
# Resultado del job
# ---------------------------------------------------------------------------

@dataclass
class ResultadoJob:
    semanas_procesadas: int = 0
    semanas_error: int = 0
    filas_calculadas: int = 0
    estados_en_alerta: int = 0
    duracion_seg: float = 0.0
    errores: list[str] = field(default_factory=list)
    alertas: list[dict[str, Any]] = field(default_factory=list)

    @property
    def exitoso(self) -> bool:
        return self.semanas_error == 0


# ---------------------------------------------------------------------------
# Worker principal
# ---------------------------------------------------------------------------

class JobCobertura:
    """
    Job que se ejecuta cada noche (01:00 hora de México) y recalcula
    las coberturas de vacunación de las semanas pendientes del año en curso.

    También puede ejecutarse manualmente para recalcular semanas históricas.
    """

    META_COBERTURA_PCT: float = float(os.environ.get("META_COBERTURA_PCT", "95"))
    UMBRAL_ALERTA_PCT:  float = float(os.environ.get("UMBRAL_ALERTA_PCT",  "80"))
    WEBHOOK_URL: str | None   = os.environ.get("SLACK_WEBHOOK_URL")

    def ejecutar(
        self,
        *,
        anio: int | None = None,
        semana_desde: int | None = None,
        semana_hasta: int | None = None,
        forzar_todo_anio: bool = False,
    ) -> ResultadoJob:
        """
        Punto de entrada principal del job.

        Por defecto calcula solo la semana epidemiológica actual y la anterior
        (para corregir registros que llegaron con retraso offline).
        Con forzar_todo_anio=True recalcula todas las semanas del año.
        """
        inicio = datetime.now(timezone.utc)
        resultado = ResultadoJob()
        log_id = self._iniciar_log()

        log.info("job_cobertura_inicio",
                 anio=anio, semana_desde=semana_desde,
                 semana_hasta=semana_hasta, forzar=forzar_todo_anio)

        try:
            semanas = self._determinar_semanas(
                anio=anio,
                semana_desde=semana_desde,
                semana_hasta=semana_hasta,
                forzar_todo_anio=forzar_todo_anio,
            )

            log.info("semanas_a_procesar", cantidad=len(semanas),
                     primera=str(semanas[0]), ultima=str(semanas[-1]))

            for se in semanas:
                try:
                    filas = self._calcular_semana(se)
                    resultado.semanas_procesadas += 1
                    resultado.filas_calculadas   += filas
                    JOB_SEMANAS_PROCESADAS.labels(resultado="ok").inc()
                    JOB_FILAS_CALCULADAS.inc(filas)
                    log.info("semana_calculada", semana=str(se), filas=filas)

                except Exception as exc:
                    resultado.semanas_error += 1
                    resultado.errores.append(f"{se}: {exc}")
                    JOB_SEMANAS_PROCESADAS.labels(resultado="error").inc()
                    log.error("semana_error", semana=str(se), error=str(exc))

            # Refrescar vista materializada una sola vez al final
            self._refrescar_vista_materializada()

            # Leer métricas de cobertura y emitir alertas
            resultado.alertas       = self._detectar_alertas()
            resultado.estados_en_alerta = len(resultado.alertas)
            self._emitir_metricas_prometheus()

            if resultado.alertas:
                self._notificar_alertas(resultado.alertas)

        except Exception as exc:
            resultado.errores.append(f"Error crítico: {exc}")
            log.exception("job_cobertura_error_critico", error=str(exc))
            raise

        finally:
            resultado.duracion_seg = (
                datetime.now(timezone.utc) - inicio
            ).total_seconds()
            JOB_DURACION.observe(resultado.duracion_seg)
            self._finalizar_log(log_id, resultado)

            log.info(
                "job_cobertura_fin",
                exitoso=resultado.exitoso,
                semanas_ok=resultado.semanas_procesadas,
                semanas_error=resultado.semanas_error,
                filas=resultado.filas_calculadas,
                alertas=resultado.estados_en_alerta,
                duracion_seg=round(resultado.duracion_seg, 2),
            )

        return resultado

    # ---------------------------------------------------------------------------
    # Determinar semanas a procesar
    # ---------------------------------------------------------------------------

    def _determinar_semanas(
        self,
        *,
        anio: int | None,
        semana_desde: int | None,
        semana_hasta: int | None,
        forzar_todo_anio: bool,
    ) -> list[SemanaEpidemiologica]:
        se_actual = semana_actual()
        anio_calc = anio or se_actual.anio

        if forzar_todo_anio:
            # Todas las semanas del año hasta la actual
            todas = semanas_del_anio(anio_calc)
            return [s for s in todas if s.inicio <= se_actual.inicio]

        if semana_desde is not None:
            # Rango explícito
            todas = semanas_del_anio(anio_calc)
            sd = next(s for s in todas if s.semana == semana_desde)
            sh = next(s for s in todas
                      if s.semana == (semana_hasta or semana_desde))
            return rango_semanas(sd, sh)

        # Comportamiento nocturno por defecto:
        # Semana actual + semana anterior (para capturar registros offline tardíos)
        semanas_objetivo = [se_actual]
        if se_actual.semana > 1:
            todas = semanas_del_anio(se_actual.anio)
            semanas_objetivo.insert(0, todas[se_actual.semana - 2])
        return semanas_objetivo

    # ---------------------------------------------------------------------------
    # Cálculo de una semana (llama a la función PostgreSQL)
    # ---------------------------------------------------------------------------

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, min=4, max=30),
        retry=retry_if_exception_type(psycopg2.OperationalError),
        before_sleep=before_sleep_log(log, "warning"),
    )
    def _calcular_semana(self, se: SemanaEpidemiologica) -> int:
        """
        Llama a sncev_report.fn_calcular_cobertura(anio, semana) en PostgreSQL.
        Retorna el número de filas insertadas/actualizadas.
        La función ya implementa el DELETE + INSERT dentro de una transacción.
        """
        with conexion() as conn:
            with cursor(conn) as cur:
                cur.execute(
                    "SELECT sncev_report.fn_calcular_cobertura(%s, %s) AS filas",
                    (se.anio, se.semana),
                )
                row = cur.fetchone()
                return int(row["filas"]) if row else 0

    # ---------------------------------------------------------------------------
    # Refrescar vista materializada
    # ---------------------------------------------------------------------------

    def _refrescar_vista_materializada(self) -> None:
        log.info("refrescando_vista_materializada")
        with conexion() as conn:
            with cursor(conn) as cur:
                # CONCURRENTLY evita bloquear lecturas mientras se refresca
                cur.execute(
                    "REFRESH MATERIALIZED VIEW CONCURRENTLY "
                    "sncev_report.mv_cobertura_nacional_anual"
                )
        log.info("vista_materializada_refrescada")

    # ---------------------------------------------------------------------------
    # Detectar estados por debajo del umbral de alerta
    # ---------------------------------------------------------------------------

    def _detectar_alertas(self) -> list[dict[str, Any]]:
        se = semana_actual()
        with conexion() as conn:
            with cursor(conn) as cur:
                cur.execute("""
                    SELECT
                        e.nombre                AS estado,
                        cv.clave_censia,
                        cv.nombre_generico      AS vacuna,
                        cv.numero_dosis,
                        cv.cobertura_nac_pct    AS cobertura_pct
                    FROM sncev_report.mv_cobertura_nacional_anual cv
                    CROSS JOIN sncev_geo.estado e
                    -- join simulado; en producción usar la vista por estado
                    WHERE cv.anio = %s
                      AND cv.cobertura_nac_pct < %s
                    ORDER BY cv.cobertura_nac_pct ASC
                    LIMIT 20
                """, (se.anio, self.UMBRAL_ALERTA_PCT))
                return [dict(r) for r in cur.fetchall()]

    # ---------------------------------------------------------------------------
    # Emitir métricas Prometheus desde la vista materializada
    # ---------------------------------------------------------------------------

    def _emitir_metricas_prometheus(self) -> None:
        se = semana_actual()
        with conexion() as conn:
            with cursor(conn) as cur:
                cur.execute("""
                    SELECT clave_censia, numero_dosis, cobertura_nac_pct
                    FROM sncev_report.mv_cobertura_nacional_anual
                    WHERE anio = %s
                """, (se.anio,))
                for row in cur.fetchall():
                    COBERTURA_NACIONAL.labels(
                        clave_censia=row["clave_censia"],
                        numero_dosis=str(row["numero_dosis"]),
                    ).set(float(row["cobertura_nac_pct"] or 0))

                # Contar estados en alerta (requiere vista por estado)
                cur.execute("""
                    SELECT COUNT(*) AS total
                    FROM sncev_report.v_cobertura_por_estado
                    WHERE anio = %s
                      AND semana_epidemiologica = %s
                      AND cobertura_pct < %s
                """, (se.anio, se.semana, self.UMBRAL_ALERTA_PCT))
                row = cur.fetchone()
                total_alerta = int(row["total"]) if row else 0
                ESTADOS_EN_ALERTA.labels(
                    umbral=str(int(self.UMBRAL_ALERTA_PCT))
                ).set(total_alerta)

    # ---------------------------------------------------------------------------
    # Notificaciones por webhook (Slack / Teams)
    # ---------------------------------------------------------------------------

    def _notificar_alertas(self, alertas: list[dict[str, Any]]) -> None:
        if not self.WEBHOOK_URL:
            log.info("webhook_no_configurado",
                     msg="Omitiendo notificación de alertas")
            return

        se = semana_actual()
        lineas = "\n".join(
            f"• {a['vacuna']} D{a['numero_dosis']} — "
            f"{a['cobertura_pct']:.1f}% cobertura nacional"
            for a in alertas[:10]
        )
        payload = {
            "text": (
                f":warning: *SNCEV — Alerta de cobertura {se.label}*\n"
                f"Los siguientes biológicos están por debajo "
                f"del {self.UMBRAL_ALERTA_PCT:.0f}%:\n"
                f"{lineas}\n"
                f"_Revisa el dashboard: https://app2.sncev.salud.gob.mx_"
            )
        }
        try:
            r = httpx.post(self.WEBHOOK_URL, json=payload, timeout=10)
            r.raise_for_status()
            log.info("notificacion_enviada", alertas=len(alertas))
        except Exception as exc:
            log.warning("notificacion_error", error=str(exc))

    # ---------------------------------------------------------------------------
    # Registro del job en base de datos (tabla job_log)
    # ---------------------------------------------------------------------------

    def _iniciar_log(self) -> int | None:
        try:
            with conexion() as conn:
                with cursor(conn) as cur:
                    cur.execute("""
                        INSERT INTO sncev_admin.parametro_sistema
                            (clave, valor, descripcion, tipo)
                        VALUES
                            ('job_cobertura_ultimo_inicio',
                             NOW()::TEXT, 'Último inicio del job de cobertura', 'string')
                        ON CONFLICT (clave) DO UPDATE
                            SET valor = NOW()::TEXT, updated_at = NOW()
                        RETURNING clave
                    """)
                    return 1  # placeholder — en producción usar tabla job_log
        except Exception as exc:
            log.warning("log_inicio_error", error=str(exc))
            return None

    def _finalizar_log(
        self, log_id: int | None, resultado: ResultadoJob
    ) -> None:
        try:
            with conexion() as conn:
                with cursor(conn) as cur:
                    cur.execute("""
                        INSERT INTO sncev_admin.parametro_sistema
                            (clave, valor, descripcion, tipo)
                        VALUES
                            ('job_cobertura_ultimo_resultado',
                             %s, 'Resultado del último job de cobertura', 'json')
                        ON CONFLICT (clave) DO UPDATE
                            SET valor = %s, updated_at = NOW()
                    """, (
                        _resultado_json(resultado),
                        _resultado_json(resultado),
                    ))
        except Exception as exc:
            log.warning("log_fin_error", error=str(exc))


def _resultado_json(r: ResultadoJob) -> str:
    import json
    return json.dumps({
        "semanas_procesadas": r.semanas_procesadas,
        "semanas_error":      r.semanas_error,
        "filas_calculadas":   r.filas_calculadas,
        "estados_en_alerta":  r.estados_en_alerta,
        "duracion_seg":       round(r.duracion_seg, 2),
        "exitoso":            r.exitoso,
        "errores":            r.errores[:10],
    })
