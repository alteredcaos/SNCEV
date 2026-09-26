# =============================================================================
# SNCEV Jobs — Scheduler principal
#
# Jobs configurados:
#   01:00  Cálculo de coberturas (semana actual + anterior)
#   01:30  Refresco de vista materializada nacional
#   02:00  Limpieza de refresh tokens expirados
#   02:15  Limpieza de cola de salida confirmada (> 30 días)
#   03:00  Recálculo de rezago: actualiza sync_estado de vacunas tardías
#   Lunes 04:00  Recálculo completo del año en curso (corrección histórica)
#
# Zona horaria: America/Mexico_City (CST/CDT)
# =============================================================================

from __future__ import annotations

import logging
import os
import signal
import sys
from datetime import datetime, timezone

import sentry_sdk
import structlog
from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.schedulers.blocking import BlockingScheduler
from dotenv import load_dotenv
from prometheus_client import start_http_server

from common.db import inicializar_pool, cerrar_pool
from cobertura.worker import JobCobertura

# ---------------------------------------------------------------------------
# Configuración inicial
# ---------------------------------------------------------------------------

load_dotenv()

# Logging estructurado
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.add_log_level,
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.BoundLogger,
    logger_factory=structlog.PrintLoggerFactory(),
)
log = structlog.get_logger(__name__)

# Sentry para monitoreo de errores en producción
if dsn := os.environ.get("SENTRY_DSN"):
    sentry_sdk.init(
        dsn=dsn,
        traces_sample_rate=0.1,
        environment=os.environ.get("ENTORNO", "produccion"),
    )
    log.info("sentry_inicializado")

# ---------------------------------------------------------------------------
# Definición de los jobs
# ---------------------------------------------------------------------------

_job_cobertura = JobCobertura()


def job_cobertura_nocturno() -> None:
    """Job principal: calcula semana actual + semana anterior."""
    log.info("job_cobertura_nocturno_inicio")
    resultado = _job_cobertura.ejecutar()
    log.info(
        "job_cobertura_nocturno_fin",
        exitoso=resultado.exitoso,
        semanas=resultado.semanas_procesadas,
        filas=resultado.filas_calculadas,
        alertas=resultado.estados_en_alerta,
    )


def job_cobertura_semanal_completo() -> None:
    """
    Lunes 04:00 — Recalcula TODAS las semanas del año en curso.
    Captura cualquier registro offline que haya llegado tarde durante la semana.
    """
    log.info("job_cobertura_semanal_inicio")
    resultado = _job_cobertura.ejecutar(forzar_todo_anio=True)
    log.info(
        "job_cobertura_semanal_fin",
        exitoso=resultado.exitoso,
        semanas=resultado.semanas_procesadas,
        filas=resultado.filas_calculadas,
    )


def job_limpiar_refresh_tokens() -> None:
    """Elimina refresh tokens expirados de más de 7 días."""
    from common.db import conexion, cursor
    with conexion() as conn:
        with cursor(conn) as cur:
            cur.execute("""
                DELETE FROM sncev_admin.refresh_token
                WHERE expira_at < NOW() - INTERVAL '7 days'
                  AND revocado = TRUE
                RETURNING id
            """)
            eliminados = cur.rowcount
    log.info("tokens_limpios", eliminados=eliminados)


def job_limpiar_cola_salida() -> None:
    """
    Elimina registros confirmados de la cola de salida con más de 30 días.
    Los registros con error_permanente se mantienen para auditoría.
    """
    from common.db import conexion, cursor
    with conexion() as conn:
        with cursor(conn) as cur:
            cur.execute("""
                DELETE FROM sncev.cola_salida
                WHERE estado = 'confirmado'
                  AND ts_local < NOW() - INTERVAL '30 days'
                RETURNING id
            """)
            eliminados = cur.rowcount
    log.info("cola_limpia", eliminados=eliminados)


def job_detectar_rezago() -> None:
    """
    Identifica pacientes con vacunas que cruzaron su fecha_limite
    desde la última ejecución y actualiza flags en la BD central.
    Esto alimenta el endpoint /reportes/rezago de la App 2.
    """
    from common.db import conexion, cursor
    with conexion() as conn:
        with cursor(conn) as cur:
            # Marcar pacientes nuevos en rezago (vista ya los calcula, esto es
            # para poblar una tabla de cache que acelera la paginación del API)
            cur.execute("""
                INSERT INTO sncev_report.cache_rezago
                    (paciente_id, vacuna_id, esquema_id, fecha_limite,
                     dias_rezago, calculado_at)
                SELECT
                    p.id,
                    ev.vacuna_id,
                    ev.id,
                    (p.fecha_nacimiento + ev.edad_max_dias * INTERVAL '1 day')::date,
                    (CURRENT_DATE -
                     (p.fecha_nacimiento + ev.edad_max_dias * INTERVAL '1 day')::date),
                    NOW()
                FROM sncev.paciente p
                JOIN sncev.esquema_vacunacion ev
                    ON ev.tipo_cartilla_id = p.tipo_cartilla_id
                WHERE p.activo
                  AND ev.activo
                  AND ev.edad_max_dias IS NOT NULL
                  AND (p.fecha_nacimiento + ev.edad_max_dias * INTERVAL '1 day')
                      < CURRENT_DATE
                  AND NOT EXISTS (
                      SELECT 1 FROM sncev.vacuna_aplicada va
                      WHERE va.paciente_id = p.id
                        AND va.vacuna_id    = ev.vacuna_id
                        AND va.numero_dosis = ev.numero_dosis
                        AND va.es_valida
                  )
                ON CONFLICT (paciente_id, vacuna_id, esquema_id)
                    DO UPDATE SET
                        dias_rezago   = EXCLUDED.dias_rezago,
                        calculado_at  = NOW()
            """)
            nuevos = cur.rowcount
    log.info("rezago_actualizado", registros=nuevos)


# ---------------------------------------------------------------------------
# Scheduler
# ---------------------------------------------------------------------------

def crear_scheduler() -> BlockingScheduler:
    executors = {
        "default": ThreadPoolExecutor(max_workers=4),
    }
    job_defaults = {
        "coalesce":      True,     # si el job se atrasó, ejecutar solo una vez
        "max_instances": 1,        # nunca dos instancias del mismo job en paralelo
        "misfire_grace_time": 600, # tolerar hasta 10 min de atraso antes de omitir
    }
    scheduler = BlockingScheduler(
        executors=job_defaults,
        job_defaults=job_defaults,
        timezone="America/Mexico_City",
    )

    # --- Job principal de cobertura (diario, 01:00) ---
    scheduler.add_job(
        job_cobertura_nocturno,
        trigger="cron",
        hour=1,
        minute=0,
        id="cobertura_nocturno",
        name="Cálculo nocturno de coberturas",
    )

    # --- Recálculo semanal completo (lunes, 04:00) ---
    scheduler.add_job(
        job_cobertura_semanal_completo,
        trigger="cron",
        day_of_week="mon",
        hour=4,
        minute=0,
        id="cobertura_semanal",
        name="Recálculo semanal completo de coberturas",
    )

    # --- Limpieza de refresh tokens (diario, 02:00) ---
    scheduler.add_job(
        job_limpiar_refresh_tokens,
        trigger="cron",
        hour=2,
        minute=0,
        id="limpiar_tokens",
        name="Limpieza de refresh tokens expirados",
    )

    # --- Limpieza de cola de salida (diario, 02:15) ---
    scheduler.add_job(
        job_limpiar_cola_salida,
        trigger="cron",
        hour=2,
        minute=15,
        id="limpiar_cola",
        name="Limpieza de cola de salida confirmada",
    )

    # --- Actualización de cache de rezago (diario, 03:00) ---
    scheduler.add_job(
        job_detectar_rezago,
        trigger="cron",
        hour=3,
        minute=0,
        id="detectar_rezago",
        name="Actualización de cache de rezago",
    )

    return scheduler


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    log.info(
        "scheduler_arrancando",
        entorno=os.environ.get("ENTORNO", "produccion"),
        hora=datetime.now(timezone.utc).isoformat(),
    )

    # Inicializar pool de conexiones
    inicializar_pool(minconn=2, maxconn=6)

    # Servidor de métricas Prometheus en puerto 9090
    puerto_metrics = int(os.environ.get("METRICS_PORT", "9090"))
    start_http_server(puerto_metrics)
    log.info("metrics_server_iniciado", puerto=puerto_metrics)

    scheduler = crear_scheduler()

    # Manejo limpio de señales de sistema (SIGTERM de Docker/systemd)
    def _shutdown(signum, frame):
        log.info("shutdown_signal", signal=signum)
        scheduler.shutdown(wait=False)
        cerrar_pool()
        sys.exit(0)

    signal.signal(signal.SIGTERM, _shutdown)
    signal.signal(signal.SIGINT,  _shutdown)

    # Listar jobs al arrancar
    log.info("jobs_registrados", jobs=[
        {"id": j.id, "nombre": j.name, "siguiente": str(j.next_run_time)}
        for j in scheduler.get_jobs()
    ])

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        log.info("scheduler_detenido")
    finally:
        cerrar_pool()


if __name__ == "__main__":
    main()
