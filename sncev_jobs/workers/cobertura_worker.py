# =============================================================================
# SNCEV Jobs — Worker de cálculo de coberturas
#
# Responsabilidad:
#   1. Determinar qué semanas recalcular (semana actual + N semanas anteriores)
#   2. Llamar a sncev_report.fn_calcular_cobertura(año, semana) por semana
#   3. Registrar el resultado en sncev_report.job_log
#   4. Emitir métricas Prometheus
#   5. Disparar alertas si hay entidades por debajo del umbral
# =============================================================================

import asyncio
from datetime import datetime, date
from zoneinfo import ZoneInfo

import structlog
from prometheus_client import Counter, Histogram, Gauge
from sqlalchemy import text

from utils.config import get_settings
from utils.db import get_conn, get_transaction, ejecutar_funcion_pg

log = structlog.get_logger(__name__)
cfg = get_settings()
TZ  = ZoneInfo(cfg.timezone)

# ── Métricas Prometheus ──────────────────────────────────────────────────────

JOB_EJECUCIONES = Counter(
    'sncev_job_cobertura_total',
    'Total de ejecuciones del job de cobertura',
    ['resultado'],           # 'exito' | 'fallo'
)
JOB_DURACION = Histogram(
    'sncev_job_cobertura_duracion_segundos',
    'Duración del job de cobertura',
    buckets=[1, 5, 10, 30, 60, 120, 300, 600],
)
FILAS_CALCULADAS = Gauge(
    'sncev_cobertura_filas_calculadas',
    'Filas insertadas/actualizadas en el último run',
)
ENTIDADES_EN_ALERTA = Gauge(
    'sncev_entidades_bajo_umbral',
    'Entidades con cobertura por debajo del umbral',
    ['nivel'],               # 'estado' | 'municipio'
)


# ── Helpers de semana epidemiológica ─────────────────────────────────────────

def semana_epidemiologica(d: date) -> tuple[int, int]:
    """
    Retorna (año, semana) según el estándar epidemiológico mexicano.
    La semana 1 comienza el primer domingo del año (igual que CDC).
    Usamos isocalendar() como aproximación aceptable para reportes internos.
    """
    iso = d.isocalendar()
    return iso.year, iso.week


def semanas_a_calcular(n_semanas: int) -> list[tuple[int, int]]:
    """
    Genera la lista de (año, semana) para la semana actual
    y las N-1 semanas previas.
    """
    hoy = datetime.now(TZ).date()
    semanas: list[tuple[int, int]] = []
    for i in range(n_semanas):
        delta = hoy.toordinal() - i * 7
        d = date.fromordinal(delta)
        semanas.append(semana_epidemiologica(d))
    # Eliminar duplicados manteniendo orden
    vistos: set[tuple[int, int]] = set()
    resultado: list[tuple[int, int]] = []
    for s in semanas:
        if s not in vistos:
            vistos.add(s)
            resultado.append(s)
    return resultado


# ── Job principal ─────────────────────────────────────────────────────────────

async def calcular_coberturas() -> dict:
    """
    Job principal de cálculo de coberturas.
    Se invoca desde el scheduler y también puede lanzarse manualmente.

    Retorna un dict con el resumen de la ejecución.
    """
    inicio = datetime.now(TZ)
    log.info('Iniciando job de cobertura', timestamp=inicio.isoformat())

    total_filas    = 0
    semanas_ok: list[tuple[int, int]] = []
    semanas_err: list[tuple[int, int]] = []

    semanas = semanas_a_calcular(cfg.semanas_recalcular)
    log.info('Semanas a calcular', semanas=semanas)

    with JOB_DURACION.time():
        for anio, semana in semanas:
            try:
                filas = await _calcular_semana(anio, semana)
                total_filas += filas
                semanas_ok.append((anio, semana))
                log.info(
                    'Semana calculada',
                    anio=anio,
                    semana=semana,
                    filas=filas,
                )
            except Exception as exc:
                log.error(
                    'Error calculando semana',
                    anio=anio,
                    semana=semana,
                    error=str(exc),
                    exc_info=True,
                )
                semanas_err.append((anio, semana))

    FILAS_CALCULADAS.set(total_filas)

    duracion = (datetime.now(TZ) - inicio).total_seconds()
    exito    = len(semanas_err) == 0

    JOB_EJECUCIONES.labels(resultado='exito' if exito else 'fallo').inc()

    resumen = {
        'inicio':       inicio.isoformat(),
        'duracion_seg': round(duracion, 2),
        'semanas_ok':   semanas_ok,
        'semanas_err':  semanas_err,
        'total_filas':  total_filas,
        'exito':        exito,
    }

    await _registrar_en_log(resumen)

    log.info(
        'Job de cobertura finalizado',
        duracion_seg=resumen['duracion_seg'],
        total_filas=total_filas,
        exito=exito,
    )

    return resumen


async def _calcular_semana(anio: int, semana: int) -> int:
    """
    Llama a sncev_report.fn_calcular_cobertura(año, semana) en PostgreSQL.
    Retorna el número de filas procesadas.
    """
    async with get_transaction() as conn:
        # La función está definida en 04_reportes_vistas_rls.sql
        filas = await ejecutar_funcion_pg(
            conn,
            'sncev_report.fn_calcular_cobertura',
            anio,
            semana,
        )
        return filas


# ── Job de refresco de vista materializada ───────────────────────────────────

async def refrescar_vista_materializada() -> dict:
    """
    Refresca CONCURRENTLY la vista materializada de cobertura nacional anual.
    CONCURRENTLY permite que la vista siga siendo consultable durante el refresh.
    """
    inicio = datetime.now(TZ)
    log.info('Iniciando refresh de vista materializada')

    try:
        async with get_transaction() as conn:
            await conn.execute(text(
                'REFRESH MATERIALIZED VIEW CONCURRENTLY '
                'sncev_report.mv_cobertura_nacional_anual'
            ))
        duracion = (datetime.now(TZ) - inicio).total_seconds()
        log.info('Vista materializada refrescada', duracion_seg=round(duracion, 2))
        return {'exito': True, 'duracion_seg': round(duracion, 2)}

    except Exception as exc:
        log.error('Error refrescando vista materializada', error=str(exc))
        return {'exito': False, 'error': str(exc)}


# ── Job de alertas ────────────────────────────────────────────────────────────

async def enviar_alertas_cobertura() -> dict:
    """
    Detecta entidades con cobertura por debajo del umbral y envía notificaciones.
    Consulta la vista sncev_report.v_cobertura_por_estado con los datos
    más recientes (última semana calculada).
    """
    log.info('Iniciando job de alertas de cobertura')

    anio, semana = semana_epidemiologica(datetime.now(TZ).date())

    async with get_conn() as conn:
        # Alertas a nivel estado
        result_estados = await conn.execute(text('''
            SELECT
                estado,
                estado_clave,
                vacuna,
                clave_censia,
                numero_dosis,
                cobertura_pct,
                total_dosis,
                total_poblacion
            FROM sncev_report.v_cobertura_por_estado
            WHERE anio = :anio
              AND semana_epidemiologica = :semana
              AND cobertura_pct < :umbral
              AND total_poblacion > 0
            ORDER BY cobertura_pct ASC
        '''), {
            'anio':   anio,
            'semana': semana,
            'umbral': cfg.umbral_alerta_pct,
        })
        alertas_estado = result_estados.mappings().all()

        # Alertas a nivel municipio (top 20 peores)
        result_mun = await conn.execute(text('''
            SELECT
                m.nombre                AS municipio,
                e.nombre                AS estado,
                cv.nombre_generico      AS vacuna,
                SUM(c.dosis_aplicadas)  AS dosis,
                SUM(c.poblacion_objetivo) AS poblacion,
                ROUND(
                    SUM(c.dosis_aplicadas) * 100.0
                    / NULLIF(SUM(c.poblacion_objetivo), 0)
                , 2)                    AS cobertura_pct
            FROM sncev_report.cobertura_vacunacion c
            JOIN sncev_geo.municipio      m  ON m.id         = c.municipio_id
            JOIN sncev_geo.estado         e  ON e.clave_inegi = c.estado_clave
            JOIN sncev.vacuna_catalogo    cv ON cv.id         = c.vacuna_id
            WHERE c.anio = :anio
              AND c.semana_epidemiologica = :semana
            GROUP BY m.nombre, e.nombre, cv.nombre_generico
            HAVING ROUND(
                SUM(c.dosis_aplicadas) * 100.0
                / NULLIF(SUM(c.poblacion_objetivo), 0)
            , 2) < :umbral
              AND SUM(c.poblacion_objetivo) > 100    -- excluir municipios muy pequeños
            ORDER BY cobertura_pct ASC
            LIMIT 20
        '''), {
            'anio':   anio,
            'semana': semana,
            'umbral': cfg.umbral_alerta_pct,
        })
        alertas_municipio = result_mun.mappings().all()

    ENTIDADES_EN_ALERTA.labels(nivel='estado').set(len(alertas_estado))
    ENTIDADES_EN_ALERTA.labels(nivel='municipio').set(len(alertas_municipio))

    resumen = {
        'semana':             f'{anio}-SE{semana:02d}',
        'alertas_estado':     len(alertas_estado),
        'alertas_municipio':  len(alertas_municipio),
        'detalle_estados':    [dict(r) for r in alertas_estado],
        'peores_municipios':  [dict(r) for r in alertas_municipio],
    }

    if alertas_estado or alertas_municipio:
        await _notificar(resumen)

    log.info(
        'Job de alertas finalizado',
        alertas_estado=len(alertas_estado),
        alertas_municipio=len(alertas_municipio),
    )

    return resumen


# ── Job de limpieza ──────────────────────────────────────────────────────────

async def limpiar_datos_expirados() -> dict:
    """
    Limpieza periódica de datos transientes:
    - Refresh tokens vencidos desde hace más de 7 días
    - Cola de salida confirmada desde hace más de 30 días (sync service)
    - Items de sync log con más de 90 días
    """
    log.info('Iniciando job de limpieza')
    resultados: dict[str, int] = {}

    async with get_transaction() as conn:
        # Refresh tokens expirados
        r1 = await conn.execute(text('''
            DELETE FROM sncev_admin.refresh_token
            WHERE expira_at < NOW() - INTERVAL '7 days'
        '''))
        resultados['refresh_tokens_eliminados'] = r1.rowcount

        # sync_log antiguos
        r2 = await conn.execute(text('''
            DELETE FROM sncev.sync_log
            WHERE iniciado_at < NOW() - INTERVAL '90 days'
        '''))
        resultados['sync_logs_eliminados'] = r2.rowcount

        # cola_salida confirmada antigua
        r3 = await conn.execute(text('''
            DELETE FROM sncev.cola_salida
            WHERE estado = 'confirmado'
              AND ts_local < NOW() - INTERVAL '30 days'
        '''))
        resultados['cola_salida_limpiada'] = r3.rowcount

    log.info('Limpieza completada', **resultados)
    return resultados


# ── Registro en log de jobs ──────────────────────────────────────────────────

async def _registrar_en_log(resumen: dict) -> None:
    """Registra el resultado del job en la tabla job_log de PostgreSQL."""
    try:
        async with get_transaction() as conn:
            await conn.execute(text('''
                INSERT INTO sncev_report.job_log
                    (nombre_job, inicio, duracion_seg,
                     filas_procesadas, exito, detalle_json)
                VALUES
                    ('calcular_coberturas', :inicio, :duracion,
                     :filas, :exito, CAST(:detalle AS jsonb))
            '''), {
                'inicio':   resumen['inicio'],
                'duracion': resumen['duracion_seg'],
                'filas':    resumen['total_filas'],
                'exito':    resumen['exito'],
                'detalle':  str(resumen),
            })
    except Exception as exc:
        log.warning('No se pudo registrar en job_log', error=str(exc))


# ── Notificaciones ────────────────────────────────────────────────────────────

async def _notificar(resumen: dict) -> None:
    """Envía resumen de alertas al webhook configurado (Slack / Teams / etc.)."""
    if not cfg.webhook_alertas_url:
        return

    import httpx

    estados_texto = '\n'.join(
        f"  • {r['estado']} — {r['vacuna']} D{r['numero_dosis']}: "
        f"{r['cobertura_pct']:.1f}%"
        for r in resumen['detalle_estados'][:10]
    )

    mensaje = {
        'text': (
            f"🔴 *Alerta SNCEV — {resumen['semana']}*\n"
            f"*{resumen['alertas_estado']} estado(s)* por debajo del "
            f"{cfg.umbral_alerta_pct:.0f}% de cobertura:\n"
            f"{estados_texto}\n"
            f"{'...' if resumen['alertas_estado'] > 10 else ''}\n"
            f"_{resumen['alertas_municipio']} municipios también en alerta._"
        )
    }

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.post(cfg.webhook_alertas_url, json=mensaje)
            r.raise_for_status()
            log.info('Alerta enviada al webhook')
    except Exception as exc:
        log.warning('Error enviando alerta al webhook', error=str(exc))
