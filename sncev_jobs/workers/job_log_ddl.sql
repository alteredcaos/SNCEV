-- =============================================================================
-- SNCEV — Tabla job_log para registro de ejecuciones de jobs nocturnos
-- Agregar al final del Módulo 04 (04_reportes_vistas_rls.sql)
-- =============================================================================

CREATE TABLE IF NOT EXISTS sncev_report.job_log (
    id              BIGSERIAL       PRIMARY KEY,
    nombre_job      VARCHAR(80)     NOT NULL,
    inicio          TIMESTAMPTZ     NOT NULL,
    fin             TIMESTAMPTZ     DEFAULT NOW(),
    duracion_seg    NUMERIC(10,2),
    filas_procesadas INT            DEFAULT 0,
    exito           BOOLEAN         NOT NULL DEFAULT TRUE,
    detalle_json    JSONB,
    created_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_job_log_nombre ON sncev_report.job_log(nombre_job, inicio DESC);
CREATE INDEX idx_job_log_fecha  ON sncev_report.job_log(inicio DESC);

COMMENT ON TABLE sncev_report.job_log IS
    'Bitácora de ejecuciones de jobs nocturnos. Solo INSERT desde el scheduler.';

-- Vista útil para monitoreo desde App 2 o Grafana
CREATE OR REPLACE VIEW sncev_report.v_job_log_reciente AS
SELECT
    nombre_job,
    inicio,
    duracion_seg,
    filas_procesadas,
    exito,
    CASE WHEN exito THEN '✓' ELSE '✗' END AS estado
FROM sncev_report.job_log
ORDER BY inicio DESC
LIMIT 100;
