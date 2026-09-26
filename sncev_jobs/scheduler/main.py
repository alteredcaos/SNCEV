#!/usr/bin/env python3
# =============================================================================
# SNCEV Jobs — Scheduler principal
#
# Orquesta todos los jobs nocturnos con APScheduler (AsyncIOScheduler).
# Cada job tiene su propia expresión cron configurable desde .env.
#
# Diseño:
#   • Un job nunca bloquea a otro — todos son coroutines async
#   • Si un job falla, el siguiente se sigue ejecutando normalmente
#   • Cada ejecución queda registrada en sncev_report.job_log
#   • Métricas disponibles en :9090/metrics para Prometheus/Grafana
#
# Uso:
#   python scheduler/main.py                   # producción
#   python scheduler/main.py --run-now cobertura  # ejecución manual inmediata
# =============================================================================

import asyncio
import argparse
import logging
import signal
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

import structlog
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.events import EVENT_JOB_ERROR, EVENT_JOB_EXECUTED
from prometheus_client import start_http_server
from rich.console import Console
from rich.table import Table

from utils.config import get_settings
from utils.db import dispose_engine
from workers.cobertura_worker import (
    calcular_coberturas,
    refrescar_vista_materializada,
    enviar_alertas_cobertura,
    limpiar_datos_expirados,
)

# ── Logging estructurado ─────────────────────────────────────────────────────

structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt='iso'),
        structlog.dev.ConsoleRenderer()
        if '--dev' in sys.argv
        else structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
    logger_factory=structlog.PrintLoggerFactory(),
)

log     = structlog.get_logger(__name__)
cfg     = get_settings()
TZ      = ZoneInfo(cfg.timezone)
console = Console()


# ── Wrappers con manejo de errores ───────────────────────────────────────────

async def _run_job(nombre: str, coro) -> None:
    """Envuelve cualquier job para capturar excepciones sin detener el scheduler."""
    structlog.contextvars.bind_contextvars(job=nombre)
    try:
        log.info(f'Iniciando job: {nombre}')
        resultado = await coro()
        log.info(f'Job completado: {nombre}', resultado=resultado)
    except Exception as exc:
        log.error(f'Job falló: {nombre}', error=str(exc), exc_info=True)
    finally:
        structlog.contextvars.clear_contextvars()


async def job_calcular_coberturas():
    await _run_job('calcular_coberturas', calcular_coberturas)

async def job_refrescar_vistas():
    await _run_job('refrescar_vista_materializada', refrescar_vista_materializada)

async def job_enviar_alertas():
    await _run_job('enviar_alertas_cobertura', enviar_alertas_cobertura)

async def job_limpieza():
    await _run_job('limpiar_datos_expirados', limpiar_datos_expirados)


# ── Listener de eventos del scheduler ───────────────────────────────────────

def on_job_executed(event):
    log.info('APScheduler — job ejecutado', job_id=event.job_id,
             scheduled_run_time=str(event.scheduled_run_time))

def on_job_error(event):
    log.error('APScheduler — error en job', job_id=event.job_id,
              exception=str(event.exception))


# ── Configuración de jobs ─────────────────────────────────────────────────────

def _hora_a_cron(hora_str: str) -> tuple[int, int]:
    """Convierte 'HH:MM' a (hora, minuto) para CronTrigger."""
    h, m = hora_str.split(':')
    return int(h), int(m)


def crear_scheduler() -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone=TZ)

    scheduler.add_listener(on_job_executed, EVENT_JOB_EXECUTED)
    scheduler.add_listener(on_job_error, EVENT_JOB_ERROR)

    h_cob, m_cob = _hora_a_cron(cfg.hora_job_cobertura)
    h_mv,  m_mv  = _hora_a_cron(cfg.hora_job_mv_refresh)
    h_ale, m_ale = _hora_a_cron(cfg.hora_job_alertas)
    h_lim, m_lim = _hora_a_cron(cfg.hora_job_limpieza)

    # ── 1. Cálculo de coberturas ─── diario a las 02:00 ─────────────────────
    # El job más pesado: vacía y recalcula sncev_report.cobertura_vacunacion
    # para las últimas N semanas epidemiológicas.
    scheduler.add_job(
        job_calcular_coberturas,
        CronTrigger(hour=h_cob, minute=m_cob, timezone=TZ),
        id='calcular_coberturas',
        name='Cálculo de coberturas por AGEB/semana',
        replace_existing=True,
        misfire_grace_time=3600,   # si el servidor estuvo caído, ejecutar si el retraso < 1h
    )

    # ── 2. Refresh de vista materializada ─── diario a las 03:30 ────────────
    # Se ejecuta después del job de cálculo para que la vista
    # mv_cobertura_nacional_anual tenga los datos actualizados.
    scheduler.add_job(
        job_refrescar_vistas,
        CronTrigger(hour=h_mv, minute=m_mv, timezone=TZ),
        id='refrescar_vistas',
        name='Refresh de vistas materializadas',
        replace_existing=True,
        misfire_grace_time=1800,
    )

    # ── 3. Envío de alertas ─── diario a las 07:00 ──────────────────────────
    # Después de que el equipo haya llegado a trabajar, no en la madrugada.
    # Detecta estados/municipios con cobertura < umbral y envía al webhook.
    scheduler.add_job(
        job_enviar_alertas,
        CronTrigger(hour=h_ale, minute=m_ale, timezone=TZ),
        id='enviar_alertas',
        name='Alertas de cobertura por debajo del umbral',
        replace_existing=True,
        misfire_grace_time=3600,
    )

    # ── 4. Limpieza de datos expirados ─── diario a las 04:00 ───────────────
    scheduler.add_job(
        job_limpieza,
        CronTrigger(hour=h_lim, minute=m_lim, timezone=TZ),
        id='limpiar_datos',
        name='Limpieza de refresh tokens y logs expirados',
        replace_existing=True,
        misfire_grace_time=3600,
    )

    # ── 5. Refresh semanal completo ─── lunes a las 01:00 ───────────────────
    # Recalcula las últimas 52 semanas para corregir datos corregidos tardíamente.
    scheduler.add_job(
        _job_recalculo_historico,
        CronTrigger(day_of_week='mon', hour=1, minute=0, timezone=TZ),
        id='recalculo_historico',
        name='Recálculo histórico semanal (52 semanas)',
        replace_existing=True,
        misfire_grace_time=7200,
    )

    return scheduler


async def _job_recalculo_historico():
    """Versión del job de cobertura que recalcula las últimas 52 semanas."""
    import os
    os.environ['SNCEV_SEMANAS_RECALCULAR'] = '52'
    await _run_job('recalculo_historico', calcular_coberturas)
    os.environ.pop('SNCEV_SEMANAS_RECALCULAR', None)


# ── Ejecución manual inmediata ───────────────────────────────────────────────

JOBS_DISPONIBLES = {
    'cobertura':  job_calcular_coberturas,
    'vistas':     job_refrescar_vistas,
    'alertas':    job_enviar_alertas,
    'limpieza':   job_limpieza,
}

async def ejecutar_ahora(nombre: str) -> None:
    """Ejecuta un job manualmente sin pasar por el scheduler."""
    if nombre not in JOBS_DISPONIBLES:
        console.print(
            f'[red]Job desconocido: {nombre}[/red]\n'
            f'Disponibles: {", ".join(JOBS_DISPONIBLES)}'
        )
        sys.exit(1)
    console.print(f'[yellow]Ejecutando job manualmente: {nombre}[/yellow]')
    await JOBS_DISPONIBLES[nombre]()


# ── Señales del sistema operativo ───────────────────────────────────────────

def registrar_senales(scheduler: AsyncIOScheduler, loop: asyncio.AbstractEventLoop):
    def _shutdown(signum, frame):
        log.info('Señal de apagado recibida', signal=signum)
        scheduler.shutdown(wait=False)
        loop.call_soon_threadsafe(loop.stop)

    signal.signal(signal.SIGTERM, _shutdown)
    signal.signal(signal.SIGINT,  _shutdown)


# ── Tabla de próximas ejecuciones (para diagnóstico al arrancar) ─────────────

def mostrar_proximas_ejecuciones(scheduler: AsyncIOScheduler) -> None:
    jobs = scheduler.get_jobs()
    tabla = Table(title='Próximas ejecuciones de jobs SNCEV')
    tabla.add_column('Job',          style='cyan')
    tabla.add_column('Próxima vez',  style='green')
    tabla.add_column('Misfire grace')
    for job in jobs:
        prox = job.next_run_time
        tabla.add_row(
            job.name,
            prox.strftime('%Y-%m-%d %H:%M %Z') if prox else 'N/D',
            f'{job.misfire_grace_time}s',
        )
    console.print(tabla)


# ── Entry point ───────────────────────────────────────────────────────────────

async def main() -> None:
    parser = argparse.ArgumentParser(description='SNCEV Job Scheduler')
    parser.add_argument(
        '--run-now',
        metavar='JOB',
        help=f'Ejecutar un job manualmente. Opciones: {", ".join(JOBS_DISPONIBLES)}',
    )
    parser.add_argument('--dev', action='store_true',
                        help='Modo desarrollo: logs legibles en consola')
    args = parser.parse_args()

    # Iniciar servidor de métricas Prometheus
    start_http_server(cfg.prometheus_port)
    log.info('Servidor de métricas iniciado', port=cfg.prometheus_port)

    # Ejecución manual
    if args.run_now:
        await ejecutar_ahora(args.run_now)
        await dispose_engine()
        return

    # Modo scheduler normal
    scheduler = crear_scheduler()
    scheduler.start()
    mostrar_proximas_ejecuciones(scheduler)

    log.info(
        'Scheduler iniciado',
        timezone=cfg.timezone,
        environment=cfg.environment,
        jobs=len(scheduler.get_jobs()),
    )

    loop = asyncio.get_running_loop()
    registrar_senales(scheduler, loop)

    try:
        # Mantener el proceso vivo
        while True:
            await asyncio.sleep(60)
    except (KeyboardInterrupt, SystemExit):
        pass
    finally:
        scheduler.shutdown(wait=True)
        await dispose_engine()
        log.info('Scheduler apagado correctamente')


if __name__ == '__main__':
    asyncio.run(main())
