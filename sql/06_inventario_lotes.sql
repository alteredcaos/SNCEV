-- =============================================================================
-- SNCEV — DDL Módulo 06
-- Inventario real de lotes (RedPax local): entradas, descuento automático por
-- dosis aplicada, cierre de frasco multidosis con merma automática y bajas
-- por incidencia. Resuelve el punto ciego que el propio AAMATES tiene hoy
-- (ver AAMATES_vs_Provac_vs_Propuesta_de_Mejora.pdf, sección "Reto de los
-- frascos multidosis"): hasta hoy `vacuna_aplicada.lote` era texto libre sin
-- inventario real detrás.
--
-- Se ejecuta DESPUÉS de 01-05 (00_instalar_todo.sql lo incluye como Paso 6).
-- Idempotente: seguro de re-ejecutar sobre una instalación existente.
-- =============================================================================

SET search_path TO sncev, sncev_admin, sncev_geo, sncev_audit, sncev_report, public;

-- ---------------------------------------------------------------------------
-- ENUMS
-- ---------------------------------------------------------------------------
DO $$ BEGIN
    CREATE TYPE sncev.estado_lote AS ENUM ('cerrado', 'en_uso', 'agotado', 'de_baja');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
    CREATE TYPE sncev.tipo_movimiento_inventario AS ENUM
        ('entrada', 'aplicacion', 'merma_frasco', 'baja_incidencia');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

-- ---------------------------------------------------------------------------
-- Cuántas dosis trae cada presentación (necesario para calcular mermas)
-- Nota: valores de referencia — ajustar según presentación real del proveedor.
-- ---------------------------------------------------------------------------
ALTER TABLE sncev.vacuna_catalogo
    ADD COLUMN IF NOT EXISTS dosis_por_frasco SMALLINT NOT NULL DEFAULT 1
        CHECK (dosis_por_frasco >= 1);

UPDATE sncev.vacuna_catalogo SET dosis_por_frasco = 20 WHERE clave_censia = 'BCG';
UPDATE sncev.vacuna_catalogo SET dosis_por_frasco = 10 WHERE clave_censia IN ('SRP', 'SR', 'Inf', 'Inf_Ped');

COMMENT ON COLUMN sncev.vacuna_catalogo.dosis_por_frasco IS
    'Dosis por frasco/vial de la presentación multidosis. 1 = monodosis/prellenada.';

-- ---------------------------------------------------------------------------
-- CATÁLOGO: Motivos de merma / baja
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS sncev.motivo_merma (
    id              SERIAL          PRIMARY KEY,
    nombre          VARCHAR(100)    NOT NULL UNIQUE,
    aplica_a        VARCHAR(20)     NOT NULL CHECK (aplica_a IN ('frasco', 'baja', 'ambos')),
    activo          BOOLEAN         NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);

INSERT INTO sncev.motivo_merma (nombre, aplica_a) VALUES
    ('Frasco multidosis remanente al cierre de jornada', 'frasco'),
    ('Rotura de frasco', 'ambos'),
    ('Cadena de frío rota', 'ambos'),
    ('Lote caducado', 'baja'),
    ('Extravío', 'baja'),
    ('Otro', 'ambos')
ON CONFLICT (nombre) DO NOTHING;

COMMENT ON TABLE sncev.motivo_merma IS 'Catálogo cerrado de motivos para merma de frasco abierto o baja de lote completo.';

-- ---------------------------------------------------------------------------
-- TABLA: Lotes de vacuna (inventario real por unidad médica)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS sncev.lote_vacuna (
    id                          UUID            PRIMARY KEY DEFAULT uuid_generate_v4(),
    vacuna_id                   INT             NOT NULL REFERENCES sncev.vacuna_catalogo(id),
    unidad_medica_id            UUID            NOT NULL REFERENCES sncev.unidad_medica(id),

    numero_lote                 VARCHAR(50)     NOT NULL,
    laboratorio                 VARCHAR(100),
    fecha_caducidad             DATE            NOT NULL,

    frascos_recibidos           INT             NOT NULL CHECK (frascos_recibidos > 0),
    -- copiado del catálogo al momento de la entrada: si el catálogo cambia después,
    -- este lote ya recibido conserva la presentación con la que en verdad llegó.
    dosis_por_frasco_snapshot   SMALLINT        NOT NULL CHECK (dosis_por_frasco_snapshot >= 1),
    dosis_totales               INT GENERATED ALWAYS AS
                                     (frascos_recibidos * dosis_por_frasco_snapshot) STORED,

    -- Contadores mantenidos por los triggers/funciones de este módulo — no escribir a mano.
    dosis_aplicadas_total       INT             NOT NULL DEFAULT 0,
    dosis_merma_total           INT             NOT NULL DEFAULT 0,
    dosis_baja_total            INT             NOT NULL DEFAULT 0,
    dosis_aplicadas_frasco_actual SMALLINT      NOT NULL DEFAULT 0,

    estado                      sncev.estado_lote NOT NULL DEFAULT 'cerrado',

    created_by                  UUID,
    created_at                  TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    updated_at                  TIMESTAMPTZ     NOT NULL DEFAULT NOW(),

    UNIQUE (numero_lote, vacuna_id, unidad_medica_id),
    CHECK (dosis_aplicadas_frasco_actual <= dosis_por_frasco_snapshot),
    CHECK (dosis_aplicadas_total + dosis_merma_total + dosis_baja_total <= dosis_totales)
);

CREATE INDEX IF NOT EXISTS idx_lote_vacuna_vacuna     ON sncev.lote_vacuna(vacuna_id);
CREATE INDEX IF NOT EXISTS idx_lote_vacuna_unidad     ON sncev.lote_vacuna(unidad_medica_id);
CREATE INDEX IF NOT EXISTS idx_lote_vacuna_estado     ON sncev.lote_vacuna(estado)
    WHERE estado IN ('cerrado', 'en_uso');
CREATE INDEX IF NOT EXISTS idx_lote_vacuna_caducidad  ON sncev.lote_vacuna(fecha_caducidad);

COMMENT ON TABLE sncev.lote_vacuna IS
    'Inventario real por lote físico y unidad médica. Reemplaza el texto libre que antes vivía en vacuna_aplicada.lote.';
COMMENT ON COLUMN sncev.lote_vacuna.estado IS
    'cerrado=sin frasco abierto todavía | en_uso=hay un frasco abierto con dosis parciales | agotado=todo el stock se consumió/mermó legítimamente | de_baja=se escribió de baja por incidencia.';

DROP TRIGGER IF EXISTS trg_lote_vacuna_updated_at ON sncev.lote_vacuna;
CREATE TRIGGER trg_lote_vacuna_updated_at
    BEFORE UPDATE ON sncev.lote_vacuna
    FOR EACH ROW EXECUTE FUNCTION sncev.fn_set_updated_at();

-- ---------------------------------------------------------------------------
-- TABLA: Movimientos de inventario (bitácora auditable, nunca se edita ni borra)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS sncev.movimiento_inventario (
    id                  UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    lote_vacuna_id      UUID        NOT NULL REFERENCES sncev.lote_vacuna(id),
    tipo                sncev.tipo_movimiento_inventario NOT NULL,
    cantidad_dosis      INT         NOT NULL CHECK (cantidad_dosis > 0),

    vacuna_aplicada_id  UUID        REFERENCES sncev.vacuna_aplicada(id),
    motivo_merma_id     INT         REFERENCES sncev.motivo_merma(id),

    observaciones       TEXT,
    usuario_id          UUID        REFERENCES sncev_admin.usuario(id),
    dispositivo_id      UUID,       -- device_id de App 1 cuando el movimiento vino de una sync offline

    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CHECK (tipo <> 'aplicacion' OR vacuna_aplicada_id IS NOT NULL),
    CHECK (tipo NOT IN ('merma_frasco', 'baja_incidencia') OR motivo_merma_id IS NOT NULL)
);

CREATE INDEX IF NOT EXISTS idx_mov_inv_lote      ON sncev.movimiento_inventario(lote_vacuna_id);
CREATE INDEX IF NOT EXISTS idx_mov_inv_tipo      ON sncev.movimiento_inventario(tipo);
CREATE INDEX IF NOT EXISTS idx_mov_inv_fecha     ON sncev.movimiento_inventario(created_at);
CREATE INDEX IF NOT EXISTS idx_mov_inv_vac_aplic ON sncev.movimiento_inventario(vacuna_aplicada_id)
    WHERE vacuna_aplicada_id IS NOT NULL;

COMMENT ON TABLE sncev.movimiento_inventario IS
    'Bitácora inmutable de cada cambio de stock: entrada, aplicación, merma de frasco o baja por incidencia.';

-- ---------------------------------------------------------------------------
-- Enlazar vacuna_aplicada con el lote real (columna nueva, nullable para no
-- romper registros históricos que solo tenían el texto libre `lote`)
-- ---------------------------------------------------------------------------
ALTER TABLE sncev.vacuna_aplicada
    ADD COLUMN IF NOT EXISTS lote_vacuna_id UUID REFERENCES sncev.lote_vacuna(id);

CREATE INDEX IF NOT EXISTS idx_vac_aplic_lote_vacuna ON sncev.vacuna_aplicada(lote_vacuna_id)
    WHERE lote_vacuna_id IS NOT NULL;

COMMENT ON COLUMN sncev.vacuna_aplicada.lote_vacuna_id IS
    'Lote real del inventario (sncev.lote_vacuna). El campo lote (texto libre) se conserva para compatibilidad histórica.';

-- ---------------------------------------------------------------------------
-- FUNCIÓN: Registrar entrada de un lote nuevo al inventario de una unidad
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION sncev.fn_inventario_entrada(
    p_vacuna_id         INT,
    p_unidad_medica_id  UUID,
    p_numero_lote       VARCHAR,
    p_laboratorio       VARCHAR,
    p_fecha_caducidad   DATE,
    p_frascos_recibidos INT,
    p_usuario_id        UUID
) RETURNS UUID LANGUAGE plpgsql AS $$
DECLARE
    v_dosis_por_frasco SMALLINT;
    v_lote_id          UUID;
BEGIN
    SELECT dosis_por_frasco INTO v_dosis_por_frasco
      FROM sncev.vacuna_catalogo WHERE id = p_vacuna_id;

    IF v_dosis_por_frasco IS NULL THEN
        RAISE EXCEPTION 'vacuna_id % no existe en el catálogo', p_vacuna_id;
    END IF;

    INSERT INTO sncev.lote_vacuna
        (vacuna_id, unidad_medica_id, numero_lote, laboratorio, fecha_caducidad,
         frascos_recibidos, dosis_por_frasco_snapshot, created_by)
    VALUES
        (p_vacuna_id, p_unidad_medica_id, p_numero_lote, p_laboratorio, p_fecha_caducidad,
         p_frascos_recibidos, v_dosis_por_frasco, p_usuario_id)
    ON CONFLICT (numero_lote, vacuna_id, unidad_medica_id) DO UPDATE
        SET frascos_recibidos = sncev.lote_vacuna.frascos_recibidos + EXCLUDED.frascos_recibidos
    RETURNING id INTO v_lote_id;

    INSERT INTO sncev.movimiento_inventario (lote_vacuna_id, tipo, cantidad_dosis, usuario_id, observaciones)
    VALUES (v_lote_id, 'entrada', p_frascos_recibidos * v_dosis_por_frasco, p_usuario_id,
            format('Entrada de %s frasco(s)', p_frascos_recibidos));

    RETURN v_lote_id;
END $$;

COMMENT ON FUNCTION sncev.fn_inventario_entrada IS
    'Alta de un lote nuevo (o refuerzo de uno existente con el mismo número+vacuna+unidad). Llamar desde POST /v1/inventario/lotes.';

-- ---------------------------------------------------------------------------
-- TRIGGER: Al aplicar una dosis con lote_vacuna_id, descuenta inventario solo
-- (esto es el "descuento en espejo" que el documento describe para RedPax,
-- pero calculado real por frasco, no solo por dosis total del lote)
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION sncev.fn_vacuna_aplicada_descontar_inventario()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
DECLARE
    v_lote sncev.lote_vacuna%ROWTYPE;
BEGIN
    IF NEW.lote_vacuna_id IS NULL THEN
        RETURN NEW;
    END IF;

    SELECT * INTO v_lote FROM sncev.lote_vacuna WHERE id = NEW.lote_vacuna_id FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'lote_vacuna_id % no existe', NEW.lote_vacuna_id;
    END IF;

    IF v_lote.estado IN ('agotado', 'de_baja') THEN
        RAISE EXCEPTION 'El lote % ya está % y no admite más aplicaciones', v_lote.numero_lote, v_lote.estado;
    END IF;

    UPDATE sncev.lote_vacuna SET
        estado = 'en_uso',
        dosis_aplicadas_total = dosis_aplicadas_total + 1,
        dosis_aplicadas_frasco_actual =
            CASE WHEN dosis_aplicadas_frasco_actual + 1 >= dosis_por_frasco_snapshot
                 THEN 0                                   -- frasco se agotó por uso completo, sin merma
                 ELSE dosis_aplicadas_frasco_actual + 1
            END
    WHERE id = NEW.lote_vacuna_id;

    -- Si con esta dosis ya no queda nada disponible en todo el lote, se marca agotado
    UPDATE sncev.lote_vacuna SET estado = 'agotado'
     WHERE id = NEW.lote_vacuna_id
       AND dosis_aplicadas_total + dosis_merma_total + dosis_baja_total >= dosis_totales;

    INSERT INTO sncev.movimiento_inventario
        (lote_vacuna_id, tipo, cantidad_dosis, vacuna_aplicada_id, usuario_id)
    VALUES (NEW.lote_vacuna_id, 'aplicacion', 1, NEW.id, NEW.aplicado_por);

    RETURN NEW;
END $$;

DROP TRIGGER IF EXISTS trg_vacuna_aplicada_inventario ON sncev.vacuna_aplicada;
CREATE TRIGGER trg_vacuna_aplicada_inventario
    AFTER INSERT ON sncev.vacuna_aplicada
    FOR EACH ROW EXECUTE FUNCTION sncev.fn_vacuna_aplicada_descontar_inventario();

-- ---------------------------------------------------------------------------
-- FUNCIÓN: Cerrar frasco abierto al final de la jornada → merma automática
-- de lo que quedó sin usar. Esto es justo el paso que, según el documento,
-- el personal "olvida hacer" en AAMATES.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION sncev.fn_inventario_cerrar_frasco(
    p_lote_id       UUID,
    p_usuario_id    UUID,
    p_motivo_id     INT DEFAULT NULL
) RETURNS INT LANGUAGE plpgsql AS $$
DECLARE
    v_lote      sncev.lote_vacuna%ROWTYPE;
    v_restantes INT;
    v_motivo_id INT;
BEGIN
    SELECT * INTO v_lote FROM sncev.lote_vacuna WHERE id = p_lote_id FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'lote_vacuna_id % no existe', p_lote_id;
    END IF;

    IF v_lote.estado <> 'en_uso' OR v_lote.dosis_aplicadas_frasco_actual = 0 THEN
        RAISE EXCEPTION 'El lote % no tiene un frasco abierto con dosis pendientes por cerrar', v_lote.numero_lote;
    END IF;

    v_restantes := v_lote.dosis_por_frasco_snapshot - v_lote.dosis_aplicadas_frasco_actual;

    v_motivo_id := COALESCE(
        p_motivo_id,
        (SELECT id FROM sncev.motivo_merma WHERE nombre = 'Frasco multidosis remanente al cierre de jornada')
    );

    INSERT INTO sncev.movimiento_inventario
        (lote_vacuna_id, tipo, cantidad_dosis, motivo_merma_id, usuario_id, observaciones)
    VALUES (p_lote_id, 'merma_frasco', v_restantes, v_motivo_id, p_usuario_id,
            'Cierre de frasco al final de jornada');

    UPDATE sncev.lote_vacuna SET
        dosis_merma_total = dosis_merma_total + v_restantes,
        dosis_aplicadas_frasco_actual = 0,
        estado = CASE WHEN dosis_aplicadas_total + dosis_merma_total + v_restantes + dosis_baja_total >= dosis_totales
                      THEN 'agotado' ELSE 'cerrado' END
    WHERE id = p_lote_id;

    RETURN v_restantes;
END $$;

COMMENT ON FUNCTION sncev.fn_inventario_cerrar_frasco IS
    'Cierra el frasco actualmente abierto de un lote y registra como merma automática las dosis no usadas. Llamar desde App 1 al cerrar sesión con frascos abiertos, o manualmente desde App 2.';

-- ---------------------------------------------------------------------------
-- FUNCIÓN: Baja de un lote completo por incidencia (rotura, cadena de frío,
-- caducidad, extravío) — da de baja TODO lo que quedaba disponible.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION sncev.fn_inventario_dar_baja(
    p_lote_id       UUID,
    p_usuario_id    UUID,
    p_motivo_id     INT,
    p_observaciones TEXT DEFAULT NULL
) RETURNS INT LANGUAGE plpgsql AS $$
DECLARE
    v_lote        sncev.lote_vacuna%ROWTYPE;
    v_disponible  INT;
BEGIN
    SELECT * INTO v_lote FROM sncev.lote_vacuna WHERE id = p_lote_id FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'lote_vacuna_id % no existe', p_lote_id;
    END IF;

    IF v_lote.estado = 'de_baja' THEN
        RAISE EXCEPTION 'El lote % ya estaba dado de baja', v_lote.numero_lote;
    END IF;

    v_disponible := v_lote.dosis_totales - v_lote.dosis_aplicadas_total
                    - v_lote.dosis_merma_total - v_lote.dosis_baja_total;

    IF v_disponible <= 0 THEN
        RAISE EXCEPTION 'El lote % ya no tiene dosis disponibles para dar de baja', v_lote.numero_lote;
    END IF;

    INSERT INTO sncev.movimiento_inventario
        (lote_vacuna_id, tipo, cantidad_dosis, motivo_merma_id, usuario_id, observaciones)
    VALUES (p_lote_id, 'baja_incidencia', v_disponible, p_motivo_id, p_usuario_id, p_observaciones);

    UPDATE sncev.lote_vacuna SET
        dosis_baja_total = dosis_baja_total + v_disponible,
        dosis_aplicadas_frasco_actual = 0,
        estado = 'de_baja'
    WHERE id = p_lote_id;

    RETURN v_disponible;
END $$;

COMMENT ON FUNCTION sncev.fn_inventario_dar_baja IS
    'Da de baja TODO el stock restante de un lote por una incidencia (rotura, cadena de frío, caducidad, extravío).';

-- ---------------------------------------------------------------------------
-- VISTA: Inventario disponible, para App 2 / dropdown de App 1
-- ---------------------------------------------------------------------------
CREATE OR REPLACE VIEW sncev.v_lote_disponible AS
SELECT
    l.id,
    l.vacuna_id,
    v.nombre_generico                                  AS vacuna_nombre,
    l.unidad_medica_id,
    u.clues,
    u.nombre                                           AS unidad_nombre,
    l.numero_lote,
    l.laboratorio,
    l.fecha_caducidad,
    l.frascos_recibidos,
    l.dosis_por_frasco_snapshot,
    l.dosis_totales,
    l.dosis_aplicadas_total,
    l.dosis_merma_total,
    l.dosis_baja_total,
    (l.dosis_totales - l.dosis_aplicadas_total - l.dosis_merma_total - l.dosis_baja_total) AS dosis_disponibles,
    l.dosis_aplicadas_frasco_actual,
    l.estado,
    (l.estado = 'en_uso' AND l.dosis_aplicadas_frasco_actual > 0)                          AS tiene_frasco_abierto,
    (l.fecha_caducidad < CURRENT_DATE)                                                     AS caducado,
    (l.fecha_caducidad BETWEEN CURRENT_DATE AND CURRENT_DATE + INTERVAL '30 days')         AS por_caducar
FROM sncev.lote_vacuna l
JOIN sncev.vacuna_catalogo v ON v.id = l.vacuna_id
JOIN sncev.unidad_medica u   ON u.id = l.unidad_medica_id;

COMMENT ON VIEW sncev.v_lote_disponible IS
    'Inventario por lote con dosis disponibles ya calculadas y alertas de caducidad. Base del dropdown de lote en App 1 y de la pantalla de inventario en App 2.';

-- ---------------------------------------------------------------------------
-- RLS: mismo criterio de ámbito que ya usa vacuna_aplicada (unidad/jurisdicción/nacional)
-- ---------------------------------------------------------------------------
ALTER TABLE sncev.lote_vacuna          ENABLE ROW LEVEL SECURITY;
ALTER TABLE sncev.movimiento_inventario ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS rls_lote_por_ambito ON sncev.lote_vacuna;
CREATE POLICY rls_lote_por_ambito ON sncev.lote_vacuna
    USING (
        current_setting('app.rol_nivel', TRUE)::INT >= 6
        OR unidad_medica_id::TEXT = current_setting('app.unidad_medica_id', TRUE)
        OR unidad_medica_id IN (
            SELECT id FROM sncev.unidad_medica
            WHERE jurisdiccion_id::TEXT = current_setting('app.jurisdiccion_id', TRUE)
        )
    );

DROP POLICY IF EXISTS rls_movimiento_por_ambito ON sncev.movimiento_inventario;
CREATE POLICY rls_movimiento_por_ambito ON sncev.movimiento_inventario
    USING (
        current_setting('app.rol_nivel', TRUE)::INT >= 6
        OR lote_vacuna_id IN (SELECT id FROM sncev.lote_vacuna)  -- ya filtrado por la policy anterior
    );

-- ---------------------------------------------------------------------------
-- PERMISOS — las tablas/función/vista nuevas no heredan los GRANT ON ALL TABLES
-- que ya se ejecutaron en 05_backend_soporte.sql, hay que otorgarlos aquí.
-- ---------------------------------------------------------------------------
GRANT SELECT, INSERT, UPDATE ON sncev.lote_vacuna, sncev.movimiento_inventario, sncev.motivo_merma
    TO sncev_app;
GRANT USAGE, SELECT ON SEQUENCE sncev.motivo_merma_id_seq TO sncev_app;
GRANT SELECT ON sncev.v_lote_disponible TO sncev_app;
GRANT EXECUTE ON FUNCTION
    sncev.fn_inventario_entrada(INT, UUID, VARCHAR, VARCHAR, DATE, INT, UUID),
    sncev.fn_inventario_cerrar_frasco(UUID, UUID, INT),
    sncev.fn_inventario_dar_baja(UUID, UUID, INT, TEXT)
    TO sncev_app;

GRANT SELECT ON sncev.lote_vacuna, sncev.movimiento_inventario, sncev.motivo_merma, sncev.v_lote_disponible
    TO sncev_jobs;

DO $$
BEGIN
    RAISE NOTICE '============================================';
    RAISE NOTICE 'SNCEV — Módulo 06 (inventario de lotes) instalado';
    RAISE NOTICE '  Lotes registrados:      %', (SELECT COUNT(*) FROM sncev.lote_vacuna);
    RAISE NOTICE '  Motivos de merma/baja:  %', (SELECT COUNT(*) FROM sncev.motivo_merma);
    RAISE NOTICE '============================================';
END $$;
