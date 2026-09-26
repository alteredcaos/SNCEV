-- =============================================================================
-- SNCEV — DDL Módulo 04
-- Reportes de cobertura, vistas analíticas, índices finales y RLS
-- =============================================================================

SET search_path TO sncev_report, sncev, sncev_admin, sncev_geo, sncev_audit, public;

-- ---------------------------------------------------------------------------
-- TABLA: Cobertura de vacunación por AGEB / semana epidemiológica
-- (tabla de hechos para App 2 — se recalcula via job nocturno)
-- ---------------------------------------------------------------------------
CREATE TABLE sncev_report.cobertura_vacunacion (
    id                      UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    vacuna_id               INT         NOT NULL REFERENCES sncev.vacuna_catalogo(id),
    numero_dosis            SMALLINT    NOT NULL DEFAULT 1,
    tipo_cartilla_id        INT         REFERENCES sncev.tipo_cartilla(id),
    ageb_clave              CHAR(13)    REFERENCES sncev_geo.ageb(clave),
    municipio_id            INT         REFERENCES sncev_geo.municipio(id),
    jurisdiccion_id         INT         REFERENCES sncev_geo.jurisdiccion(id),
    estado_clave            CHAR(2)     REFERENCES sncev_geo.estado(clave_inegi),
    anio                    SMALLINT    NOT NULL,
    semana_epidemiologica   SMALLINT    NOT NULL CHECK (semana_epidemiologica BETWEEN 1 AND 53),
    dosis_aplicadas         INT         NOT NULL DEFAULT 0,
    poblacion_objetivo      INT,        -- de tabla ageb según grupo de edad
    porcentaje_cobertura    NUMERIC(6,2) GENERATED ALWAYS AS (
        CASE WHEN poblacion_objetivo > 0
             THEN ROUND((dosis_aplicadas::NUMERIC / poblacion_objetivo) * 100, 2)
             ELSE NULL END
    ) STORED,
    concordancia_pct        NUMERIC(6,2),   -- % de dosis aplicadas en edad correcta
    dosis_invalidas         INT         NOT NULL DEFAULT 0,
    calculado_at            TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (vacuna_id, numero_dosis, ageb_clave, anio, semana_epidemiologica)
);

CREATE INDEX idx_cob_vacuna     ON sncev_report.cobertura_vacunacion(vacuna_id);
CREATE INDEX idx_cob_ageb       ON sncev_report.cobertura_vacunacion(ageb_clave);
CREATE INDEX idx_cob_municipio  ON sncev_report.cobertura_vacunacion(municipio_id);
CREATE INDEX idx_cob_estado     ON sncev_report.cobertura_vacunacion(estado_clave);
CREATE INDEX idx_cob_anio_sem   ON sncev_report.cobertura_vacunacion(anio, semana_epidemiologica);

COMMENT ON TABLE sncev_report.cobertura_vacunacion IS 'Tabla de hechos pre-calculada por job nocturno. Base de todos los dashboards de cobertura.';

-- ---------------------------------------------------------------------------
-- FUNCIÓN: Recalcular cobertura para una semana/año dados
-- (ejecutar desde job nocturno o manualmente)
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION sncev_report.fn_calcular_cobertura(
    p_anio  SMALLINT,
    p_semana SMALLINT
)
RETURNS INT LANGUAGE plpgsql AS $$
DECLARE
    v_rows INT;
BEGIN
    -- Eliminar cálculo anterior para la semana
    DELETE FROM sncev_report.cobertura_vacunacion
    WHERE anio = p_anio AND semana_epidemiologica = p_semana;

    -- Insertar recálculo
    INSERT INTO sncev_report.cobertura_vacunacion
        (vacuna_id, numero_dosis, tipo_cartilla_id, ageb_clave, municipio_id,
         jurisdiccion_id, estado_clave, anio, semana_epidemiologica,
         dosis_aplicadas, poblacion_objetivo, concordancia_pct, dosis_invalidas)
    SELECT
        va.vacuna_id,
        va.numero_dosis,
        p.tipo_cartilla_id,
        ag.clave                            AS ageb_clave,
        um.municipio_id,
        um.jurisdiccion_id,
        um.estado_clave,
        p_anio,
        p_semana,
        COUNT(*) FILTER (WHERE va.es_valida)                 AS dosis_aplicadas,
        MAX(ag.poblacion_menor_5)                            AS poblacion_objetivo,   -- simplificado
        ROUND(
            COUNT(*) FILTER (WHERE va.es_valida AND va.edad_dias_aplicacion
                BETWEEN ev.edad_min_dias AND COALESCE(ev.edad_max_dias, 99999))
            * 100.0 / NULLIF(COUNT(*) FILTER (WHERE va.es_valida), 0)
        , 2)                                                 AS concordancia_pct,
        COUNT(*) FILTER (WHERE NOT va.es_valida)             AS dosis_invalidas
    FROM sncev.vacuna_aplicada va
    JOIN sncev.paciente           p  ON p.id  = va.paciente_id
    JOIN sncev.unidad_medica      um ON um.id = va.unidad_medica_id
    LEFT JOIN sncev_geo.ageb      ag ON ag.clave = um.ageb_clave
    LEFT JOIN sncev.esquema_vacunacion ev ON ev.id = va.esquema_id
    WHERE EXTRACT(YEAR  FROM va.fecha_aplicacion)::SMALLINT = p_anio
      AND EXTRACT(WEEK  FROM va.fecha_aplicacion)::SMALLINT = p_semana
    GROUP BY va.vacuna_id, va.numero_dosis, p.tipo_cartilla_id,
             ag.clave, um.municipio_id, um.jurisdiccion_id, um.estado_clave;

    GET DIAGNOSTICS v_rows = ROW_COUNT;
    RETURN v_rows;
END;
$$;

-- ---------------------------------------------------------------------------
-- VISTA: Paciente con esquema de vacunación pendiente
-- (usada por App 1 para mostrar "próximas vacunas")
-- ---------------------------------------------------------------------------
CREATE OR REPLACE VIEW sncev.v_vacunas_pendientes AS
SELECT
    p.id                        AS paciente_id,
    p.tipo_cartilla_id,
    tc.nombre                   AS tipo_cartilla,
    ev.id                       AS esquema_id,
    ev.numero_dosis,
    ev.serie,
    vc.clave_censia,
    vc.nombre_generico          AS vacuna,
    ev.edad_optima_dias,
    p.fecha_nacimiento + ev.edad_optima_dias * INTERVAL '1 day' AS fecha_optima,
    p.fecha_nacimiento + COALESCE(ev.edad_max_dias, 36500) * INTERVAL '1 day' AS fecha_limite,
    va.id                       AS aplicada_id           -- NULL si no se ha aplicado
FROM sncev.paciente p
JOIN sncev.tipo_cartilla  tc ON tc.id = p.tipo_cartilla_id
JOIN sncev.esquema_vacunacion ev ON ev.tipo_cartilla_id = p.tipo_cartilla_id AND ev.activo
JOIN sncev.vacuna_catalogo vc ON vc.id = ev.vacuna_id
LEFT JOIN sncev.vacuna_aplicada va
    ON  va.paciente_id   = p.id
    AND va.vacuna_id     = ev.vacuna_id
    AND va.numero_dosis  = ev.numero_dosis
    AND va.es_valida
WHERE p.activo
  AND va.id IS NULL   -- solo las no aplicadas
  AND (ev.edad_max_dias IS NULL
       OR p.fecha_nacimiento + ev.edad_max_dias * INTERVAL '1 day' > CURRENT_DATE);

COMMENT ON VIEW sncev.v_vacunas_pendientes IS 'Vacunas pendientes por paciente según esquema y edad. Usada en App 1.';

-- ---------------------------------------------------------------------------
-- VISTA: Dashboard de cobertura por estado (App 2)
-- ---------------------------------------------------------------------------
CREATE OR REPLACE VIEW sncev_report.v_cobertura_por_estado AS
SELECT
    e.nombre                    AS estado,
    cv.estado_clave,
    vc.nombre_generico          AS vacuna,
    vc.clave_censia,
    cv.numero_dosis,
    cv.anio,
    cv.semana_epidemiologica,
    SUM(cv.dosis_aplicadas)     AS total_dosis,
    SUM(cv.poblacion_objetivo)  AS total_poblacion,
    ROUND(SUM(cv.dosis_aplicadas) * 100.0 / NULLIF(SUM(cv.poblacion_objetivo), 0), 2)
                                AS cobertura_pct,
    AVG(cv.concordancia_pct)    AS concordancia_prom
FROM sncev_report.cobertura_vacunacion cv
JOIN sncev_geo.estado         e  ON e.clave_inegi   = cv.estado_clave
JOIN sncev.vacuna_catalogo    vc ON vc.id           = cv.vacuna_id
GROUP BY e.nombre, cv.estado_clave, vc.nombre_generico, vc.clave_censia,
         cv.numero_dosis, cv.anio, cv.semana_epidemiologica;

-- ---------------------------------------------------------------------------
-- VISTA MATERIALIZADA: Resumen anual de cobertura nacional (se refresca diario)
-- ---------------------------------------------------------------------------
CREATE MATERIALIZED VIEW sncev_report.mv_cobertura_nacional_anual AS
SELECT
    vc.clave_censia,
    vc.nombre_generico          AS vacuna,
    cv.numero_dosis,
    cv.tipo_cartilla_id,
    tc.nombre                   AS tipo_cartilla,
    cv.anio,
    SUM(cv.dosis_aplicadas)     AS total_dosis_nac,
    SUM(cv.poblacion_objetivo)  AS total_pob_nac,
    ROUND(SUM(cv.dosis_aplicadas) * 100.0 / NULLIF(SUM(cv.poblacion_objetivo), 0), 2)
                                AS cobertura_nac_pct
FROM sncev_report.cobertura_vacunacion cv
JOIN sncev.vacuna_catalogo    vc ON vc.id = cv.vacuna_id
JOIN sncev.tipo_cartilla      tc ON tc.id = cv.tipo_cartilla_id
GROUP BY vc.clave_censia, vc.nombre_generico, cv.numero_dosis,
         cv.tipo_cartilla_id, tc.nombre, cv.anio
WITH DATA;

CREATE UNIQUE INDEX ON sncev_report.mv_cobertura_nacional_anual
    (clave_censia, numero_dosis, tipo_cartilla_id, anio);

-- Refrescar con: REFRESH MATERIALIZED VIEW CONCURRENTLY sncev_report.mv_cobertura_nacional_anual;

-- ---------------------------------------------------------------------------
-- ROW LEVEL SECURITY — restricción de filas por ámbito geográfico del usuario
-- ---------------------------------------------------------------------------

-- Habilitar RLS en tablas principales
ALTER TABLE sncev.vacuna_aplicada   ENABLE ROW LEVEL SECURITY;
ALTER TABLE sncev.paciente          ENABLE ROW LEVEL SECURITY;

-- Política para vacunas: un usuario solo ve registros de su unidad/jurisdicción/estado
-- (los administradores nacionales ven todo — nivel 6)
CREATE POLICY rls_vacuna_por_ambito ON sncev.vacuna_aplicada
    USING (
        current_setting('app.rol_nivel', TRUE)::INT >= 6
        OR unidad_medica_id::TEXT = current_setting('app.unidad_medica_id', TRUE)
        OR unidad_medica_id IN (
            SELECT id FROM sncev.unidad_medica
            WHERE jurisdiccion_id::TEXT = current_setting('app.jurisdiccion_id', TRUE)
        )
    );

-- Política para pacientes: ciudadanos solo ven su propio registro
CREATE POLICY rls_paciente_ciudadano ON sncev.paciente
    USING (
        current_setting('app.rol_nivel', TRUE)::INT >= 2
        OR id::TEXT = current_setting('app.paciente_id', TRUE)
    );

-- ---------------------------------------------------------------------------
-- ROL DE BASE DE DATOS para la aplicación (principio de mínimo privilegio)
-- ---------------------------------------------------------------------------
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'sncev_app') THEN
        CREATE ROLE sncev_app LOGIN PASSWORD 'Provac_Cdmx*2026';
    END IF;
END $$;

GRANT USAGE  ON SCHEMA sncev, sncev_admin, sncev_geo, sncev_audit, sncev_report TO sncev_app;
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA sncev       TO sncev_app;
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA sncev_admin TO sncev_app;
GRANT SELECT                 ON ALL TABLES IN SCHEMA sncev_geo   TO sncev_app;
GRANT INSERT                 ON sncev_audit.audit_log             TO sncev_app;  -- solo INSERT
GRANT SELECT                 ON sncev_audit.audit_log             TO sncev_app;
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA sncev_report TO sncev_app;
GRANT USAGE  ON ALL SEQUENCES IN SCHEMA sncev        TO sncev_app;
GRANT USAGE  ON ALL SEQUENCES IN SCHEMA sncev_admin  TO sncev_app;

-- Denegar explícitamente operaciones destructivas en auditoría
REVOKE UPDATE, DELETE, TRUNCATE ON sncev_audit.audit_log FROM sncev_app;

-- ---------------------------------------------------------------------------
-- ÍNDICES adicionales de rendimiento para consultas frecuentes
-- ---------------------------------------------------------------------------

-- Búsqueda de paciente por rango de edad (para cartillas de campaña)
CREATE INDEX idx_paciente_fecha_nac_sexo
    ON sncev.paciente(fecha_nacimiento, sexo, tipo_cartilla_id)
    WHERE activo = TRUE;

-- Vacunas aplicadas por unidad, fecha y vacuna (reporte semanal)
CREATE INDEX idx_vac_aplic_unidad_fecha_vacuna
    ON sncev.vacuna_aplicada(unidad_medica_id, fecha_aplicacion, vacuna_id)
    WHERE es_valida = TRUE;

-- Búsqueda de lotes (trazabilidad de cadena de frío)
CREATE INDEX idx_vac_aplic_lote_vacuna
    ON sncev.vacuna_aplicada(lote, vacuna_id, fecha_aplicacion)
    WHERE lote IS NOT NULL;

-- Citas próximas (para recordatorios)
CREATE INDEX idx_cita_prox_pendientes
    ON sncev.cita_vacunacion(fecha_programada, estado, unidad_medica_id)
    WHERE estado = 'Pendiente';

-- Búsqueda GiST en audit_log por IP (bloqueo por IP en intentos de acceso fallidos)
-- ya creado arriba con inet_ops

-- ---------------------------------------------------------------------------
-- TABLA: Parámetros del sistema (configuración global)
-- ---------------------------------------------------------------------------
CREATE TABLE sncev_admin.parametro_sistema (
    clave           VARCHAR(80)     PRIMARY KEY,
    valor           TEXT            NOT NULL,
    descripcion     TEXT,
    tipo            VARCHAR(20)     NOT NULL DEFAULT 'string'
                                    CHECK (tipo IN ('string','int','bool','json','date')),
    es_secreto      BOOLEAN         NOT NULL DEFAULT FALSE, -- si TRUE, no mostrar en UI
    updated_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    updated_by      UUID            REFERENCES sncev_admin.usuario(id)
);

INSERT INTO sncev_admin.parametro_sistema (clave, valor, descripcion, tipo) VALUES
('jwt_expiracion_minutos',      '15',       'Tiempo de vida del JWT de acceso en minutos',      'int'),
('rt_expiracion_dias',          '8',        'Tiempo de vida del refresh token en días',          'int'),
('max_intentos_login',          '5',        'Intentos de login fallidos antes de bloquear',      'int'),
('bloqueo_minutos',             '30',       'Minutos de bloqueo tras intentos fallidos',         'int'),
('version_esquema_vacunacion',  '2023',     'Versión del esquema de vacunación vigente',         'string'),
('url_fhir_server',             '',         'URL del servidor FHIR externo para interop.',       'string'),
('recordatorio_anticipacion_h', '24',       'Horas de anticipación para enviar recordatorio',    'int'),
('cobertura_meta_pct',          '95',       'Porcentaje meta de cobertura nacional',             'int'),
('semanas_alerta_cobertura',    '4',        'Semanas sin vacunación para emitir alerta',         'int');

-- ---------------------------------------------------------------------------
-- Comentario final de integridad del modelo
-- ---------------------------------------------------------------------------
COMMENT ON SCHEMA sncev         IS 'Datos clínicos del paciente: vacunas, tamizajes, somatometría, citas.';
COMMENT ON SCHEMA sncev_admin   IS 'Gestión de usuarios, roles, permisos y tokens de sesión.';
COMMENT ON SCHEMA sncev_geo     IS 'Catálogos geográficos: estados, municipios, AGEBs, jurisdicciones.';
COMMENT ON SCHEMA sncev_audit   IS 'Bitácora inmutable de auditoría. Cumple NOM-024-SSA3-2012.';
COMMENT ON SCHEMA sncev_report  IS 'Datos precalculados para App 2: coberturas, reportes, dashboards.';
