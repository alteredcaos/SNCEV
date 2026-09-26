-- =============================================================================
-- SNCEV — Módulo 06: ajustes requeridos por el backend FastAPI
-- Se ejecuta después de 01–04. Es idempotente donde es posible.
-- =============================================================================

SET search_path TO sncev, sncev_admin, sncev_geo, sncev_audit, sncev_report, public;

-- ---------------------------------------------------------------------------
-- 1. CURP único por hash.
--    curp_enc se cifra con IV aleatorio, por lo que su UNIQUE nunca detecta
--    duplicados. La unicidad real debe recaer sobre curp_hash.
-- ---------------------------------------------------------------------------
CREATE UNIQUE INDEX IF NOT EXISTS uq_paciente_curp_hash
    ON sncev.paciente (curp_hash) WHERE curp_hash IS NOT NULL;

-- ---------------------------------------------------------------------------
-- 2. updated_at en vacuna_aplicada y cita_vacunacion.
--    Sin esta columna, /sync/pull no puede detectar correcciones de lote ni
--    invalidaciones de dosis, ni cambios de estado en citas.
-- ---------------------------------------------------------------------------
ALTER TABLE sncev.vacuna_aplicada
    ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW();
ALTER TABLE sncev.cita_vacunacion
    ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW();

DROP TRIGGER IF EXISTS trg_vacuna_aplicada_updated_at ON sncev.vacuna_aplicada;
CREATE TRIGGER trg_vacuna_aplicada_updated_at
    BEFORE UPDATE ON sncev.vacuna_aplicada
    FOR EACH ROW EXECUTE FUNCTION sncev.fn_set_updated_at();

DROP TRIGGER IF EXISTS trg_cita_updated_at ON sncev.cita_vacunacion;
CREATE TRIGGER trg_cita_updated_at
    BEFORE UPDATE ON sncev.cita_vacunacion
    FOR EACH ROW EXECUTE FUNCTION sncev.fn_set_updated_at();

CREATE INDEX IF NOT EXISTS idx_paciente_updated_at   ON sncev.paciente(updated_at);
CREATE INDEX IF NOT EXISTS idx_vac_aplic_updated_at  ON sncev.vacuna_aplicada(updated_at);
CREATE INDEX IF NOT EXISTS idx_cita_updated_at       ON sncev.cita_vacunacion(updated_at);

-- ---------------------------------------------------------------------------
-- 3. Idempotencia de /sync/push.
--    La app móvil reintenta el lote si se pierde la respuesta; sin este
--    registro, un reintento duplicaría pacientes y dosis.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS sncev.sync_registro (
    local_key    TEXT         PRIMARY KEY,               -- 'paciente:local_<uuid>'
    tabla        VARCHAR(40)  NOT NULL,
    servidor_id  UUID         NOT NULL,
    usuario_id   UUID         NOT NULL REFERENCES sncev_admin.usuario(id),
    device_id    VARCHAR(100),
    created_at   TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_sync_registro_servidor ON sncev.sync_registro(servidor_id);

-- ---------------------------------------------------------------------------
-- 4. Restablecimiento de contraseña (POST /auth/forgot-password y /reset-password)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS sncev_admin.password_reset_token (
    id          UUID         PRIMARY KEY DEFAULT uuid_generate_v4(),
    usuario_id  UUID         NOT NULL REFERENCES sncev_admin.usuario(id) ON DELETE CASCADE,
    token_hash  CHAR(64)     NOT NULL UNIQUE,            -- SHA-256 del token; el plano solo viaja por correo
    expira_at   TIMESTAMPTZ  NOT NULL,
    usado       BOOLEAN      NOT NULL DEFAULT FALSE,
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_prt_usuario ON sncev_admin.password_reset_token(usuario_id);

-- ---------------------------------------------------------------------------
-- 5. Jobs de exportación asíncrona (POST /reportes/exportar)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS sncev_admin.export_job (
    id                UUID         PRIMARY KEY DEFAULT uuid_generate_v4(),
    usuario_id        UUID         NOT NULL REFERENCES sncev_admin.usuario(id),
    tipo              VARCHAR(30)  NOT NULL,
    formato           VARCHAR(10)  NOT NULL,
    filtros           JSONB        NOT NULL DEFAULT '{}'::JSONB,
    incluir_sensibles BOOLEAN      NOT NULL DEFAULT FALSE,
    estado            VARCHAR(12)  NOT NULL DEFAULT 'procesando'
                                   CHECK (estado IN ('procesando','listo','error')),
    archivo           TEXT,
    filas             INT,
    error             TEXT,
    created_at        TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    finished_at       TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS idx_export_job_usuario ON sncev_admin.export_job(usuario_id, created_at DESC);

-- ---------------------------------------------------------------------------
-- 6. RLS de vacuna_aplicada: ámbito ESTATAL.
--    La política original (04) solo contempla nivel 6, unidad y jurisdicción,
--    de modo que el rol «Administrador Estatal» (nivel 5, «acceso a datos de
--    su estado») no veía ninguna dosis. Se agrega app.estado_clave.
-- ---------------------------------------------------------------------------
DROP POLICY IF EXISTS rls_vacuna_por_ambito ON sncev.vacuna_aplicada;
CREATE POLICY rls_vacuna_por_ambito ON sncev.vacuna_aplicada
    USING (
        current_setting('app.rol_nivel', TRUE)::INT >= 6
        OR unidad_medica_id::TEXT = current_setting('app.unidad_medica_id', TRUE)
        OR unidad_medica_id IN (
            SELECT id FROM sncev.unidad_medica
            WHERE jurisdiccion_id::TEXT = current_setting('app.jurisdiccion_id', TRUE)
        )
        OR (
            current_setting('app.rol_nivel', TRUE)::INT >= 5
            AND unidad_medica_id IN (
                SELECT id FROM sncev.unidad_medica
                WHERE estado_clave = current_setting('app.estado_clave', TRUE)
            )
        )
    );

-- ---------------------------------------------------------------------------
-- 6b. cartilla_firmada: secciones incluidas y clave de almacenamiento del PDF.
--     El DDL original guarda url_pdf/url_qr ya resueltas; el backend genera URLs
--     temporales firmadas bajo demanda, así que persiste la CLAVE del objeto
--     (S3/almacén local) y las secciones que se incluyeron al generar.
-- ---------------------------------------------------------------------------
ALTER TABLE sncev.cartilla_firmada
    ADD COLUMN IF NOT EXISTS secciones_incluidas TEXT[],
    ADD COLUMN IF NOT EXISTS archivo_clave        TEXT;

-- ---------------------------------------------------------------------------
-- 6c. somatometria: updated_at para que /sync/pull detecte correcciones
--     (paciente y vacuna_aplicada ya lo tenían de la sección 2 de este archivo).
-- ---------------------------------------------------------------------------
ALTER TABLE sncev.somatometria
    ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW();
DROP TRIGGER IF EXISTS trg_somatometria_updated_at ON sncev.somatometria;
CREATE TRIGGER trg_somatometria_updated_at
    BEFORE UPDATE ON sncev.somatometria
    FOR EACH ROW EXECUTE FUNCTION sncev.fn_set_updated_at();
CREATE INDEX IF NOT EXISTS idx_somatometria_updated_at ON sncev.somatometria(updated_at);

-- ---------------------------------------------------------------------------
-- 8. fn_calcular_cobertura: dos defectos corregidos.
--    a) La UNIQUE de cobertura_vacunacion no incluía tipo_cartilla_id: dos tipos
--       de cartilla con la misma vacuna/dosis/AGEB/semana violaban la unicidad
--       y el job nocturno abortaba (reproducido con datos de prueba).
--    b) La función agrupaba por EXTRACT(WEEK) (semana ISO), pero sncev_jobs
--       calcula semana SINAVE (domingo a sábado, SE-1 contiene el primer jueves
--       del año — NOM-017-SSA2-2012). Para 2026-01-04 el ISO da semana 1 y
--       SINAVE da SE-2; quedaban desalineadas. Se replica el cálculo SINAVE en
--       SQL y se filtra por rango de fechas en vez de EXTRACT(WEEK).
-- ---------------------------------------------------------------------------
ALTER TABLE sncev_report.cobertura_vacunacion
    DROP CONSTRAINT IF EXISTS cobertura_vacunacion_vacuna_id_numero_dosis_ageb_clave_anio_key;
DO $$
DECLARE
    v_nombre_viejo TEXT;
BEGIN
    -- Localiza por columnas (no por nombre, que Postgres autogenera y puede truncar)
    -- la UNIQUE original de 5 columnas, sin tipo_cartilla_id, y la elimina si existe.
    SELECT con.conname INTO v_nombre_viejo
    FROM pg_constraint con
    JOIN pg_class rel ON rel.oid = con.conrelid
    WHERE rel.relname = 'cobertura_vacunacion' AND con.contype = 'u'
      AND con.conname <> 'uq_cobertura_vacunacion_dimension'
      AND (SELECT array_agg(attname::text ORDER BY attname)
           FROM unnest(con.conkey) WITH ORDINALITY AS k(attnum, ord)
           JOIN pg_attribute a ON a.attrelid = con.conrelid AND a.attnum = k.attnum)
          = (SELECT array_agg(c ORDER BY c)
             FROM unnest(ARRAY['vacuna_id','numero_dosis','ageb_clave','anio','semana_epidemiologica']) c)
    LIMIT 1;

    IF v_nombre_viejo IS NOT NULL THEN
        EXECUTE format('ALTER TABLE sncev_report.cobertura_vacunacion DROP CONSTRAINT %I', v_nombre_viejo);
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'uq_cobertura_vacunacion_dimension'
    ) THEN
        ALTER TABLE sncev_report.cobertura_vacunacion
            ADD CONSTRAINT uq_cobertura_vacunacion_dimension
            UNIQUE (vacuna_id, numero_dosis, tipo_cartilla_id, ageb_clave, anio, semana_epidemiologica);
    END IF;
END $$;

-- Réplica exacta de sncev_jobs/common/semana_epi.py::_primer_domingo_epi
CREATE OR REPLACE FUNCTION sncev_report.fn_primer_domingo_epi(p_anio INT)
RETURNS DATE LANGUAGE plpgsql IMMUTABLE AS $$
DECLARE
    v_primer_jueves DATE := make_date(p_anio, 1, 1);
    v_dias_hasta_jueves INT;
BEGIN
    -- ISODOW: lunes=1 .. domingo=7 (equivalente a weekday()+1 de Python)
    v_dias_hasta_jueves := (3 - (EXTRACT(ISODOW FROM v_primer_jueves)::INT - 1) + 7) % 7;
    v_primer_jueves := v_primer_jueves + v_dias_hasta_jueves;
    RETURN v_primer_jueves - 4;
END;
$$;

-- Réplica exacta de sncev_jobs/common/semana_epi.py::semana_de_fecha (solo el rango)
CREATE OR REPLACE FUNCTION sncev_report.fn_rango_semana_epi(p_anio SMALLINT, p_semana SMALLINT)
RETURNS TABLE(inicio DATE, fin DATE) LANGUAGE sql IMMUTABLE AS $$
    SELECT d, d + 6
    FROM (SELECT sncev_report.fn_primer_domingo_epi(p_anio) + (p_semana - 1) * 7 AS d) t;
$$;

CREATE OR REPLACE FUNCTION sncev_report.fn_calcular_cobertura(
    p_anio  SMALLINT,
    p_semana SMALLINT
)
RETURNS INT LANGUAGE plpgsql AS $$
DECLARE
    v_rows INT;
    v_inicio DATE;
    v_fin DATE;
BEGIN
    SELECT inicio, fin INTO v_inicio, v_fin FROM sncev_report.fn_rango_semana_epi(p_anio, p_semana);

    DELETE FROM sncev_report.cobertura_vacunacion
    WHERE anio = p_anio AND semana_epidemiologica = p_semana;

    INSERT INTO sncev_report.cobertura_vacunacion
        (vacuna_id, numero_dosis, tipo_cartilla_id, ageb_clave, municipio_id,
         jurisdiccion_id, estado_clave, anio, semana_epidemiologica,
         dosis_aplicadas, poblacion_objetivo, concordancia_pct, dosis_invalidas)
    SELECT
        va.vacuna_id, va.numero_dosis, p.tipo_cartilla_id, ag.clave, um.municipio_id,
        um.jurisdiccion_id, um.estado_clave, p_anio, p_semana,
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
    WHERE va.fecha_aplicacion BETWEEN v_inicio AND v_fin
    GROUP BY va.vacuna_id, va.numero_dosis, p.tipo_cartilla_id,
             ag.clave, um.municipio_id, um.jurisdiccion_id, um.estado_clave;

    GET DIAGNOSTICS v_rows = ROW_COUNT;
    RETURN v_rows;
END;
$$;

-- ---------------------------------------------------------------------------
-- 9. Permisos del rol de aplicación sobre los objetos nuevos
-- ---------------------------------------------------------------------------
GRANT SELECT, INSERT, UPDATE ON sncev.sync_registro                TO sncev_app;
GRANT SELECT, INSERT, UPDATE ON sncev_admin.password_reset_token   TO sncev_app;
GRANT SELECT, INSERT, UPDATE ON sncev_admin.export_job             TO sncev_app;
GRANT SELECT, UPDATE ON sncev.cartilla_firmada, sncev.somatometria TO sncev_app;

-- ---------------------------------------------------------------------------
-- 8. OPCIONAL — requiere decisión de negocio (comentado a propósito).
--    Con la política actual, un vacunador solo ve las dosis aplicadas en SU
--    unidad/jurisdicción. Una cartilla nacional portable normalmente necesita
--    que el HISTORIAL sea visible para cualquier profesional (para no repetir
--    dosis), limitando solo la ESCRITURA al ámbito propio. Para habilitarlo:
--
--   DROP POLICY rls_vacuna_por_ambito ON sncev.vacuna_aplicada;
--   CREATE POLICY rls_vacuna_lectura ON sncev.vacuna_aplicada FOR SELECT
--       USING (current_setting('app.rol_nivel', TRUE)::INT >= 2);
--   CREATE POLICY rls_vacuna_escritura_ins ON sncev.vacuna_aplicada FOR INSERT
--       WITH CHECK ( <misma condición de ámbito de la sección 6> );
--   CREATE POLICY rls_vacuna_escritura_upd ON sncev.vacuna_aplicada FOR UPDATE
--       USING ( <misma condición de ámbito de la sección 6> );
-- ---------------------------------------------------------------------------
