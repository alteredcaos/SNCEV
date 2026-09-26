-- =============================================================================
-- SNCEV — DDL Módulo 02
-- Pacientes, Responsables, Vacunas aplicadas y datos clínicos de cartilla
-- =============================================================================

SET search_path TO sncev, sncev_geo, public;

-- ---------------------------------------------------------------------------
-- TABLA: Paciente
-- Las columnas _enc se cifran AES-256 en capa de aplicación (EF Core / ORM)
-- Se almacena como texto Base64(IV || CipherText)
-- ---------------------------------------------------------------------------
CREATE TABLE sncev.paciente (
    id                      UUID            PRIMARY KEY DEFAULT uuid_generate_v4(),
    tipo_cartilla_id        INT             NOT NULL REFERENCES sncev.tipo_cartilla(id),

    -- Datos de identidad (cifrados)
    nombre_enc              TEXT            NOT NULL,
    ap_paterno_enc          TEXT            NOT NULL,
    ap_materno_enc          TEXT,
    curp_enc                TEXT            UNIQUE,     -- UNIQUE sobre texto cifrado con hash determinístico
    curp_hash               CHAR(64),                  -- SHA-256 del CURP en claro para búsqueda exacta
    fecha_nacimiento        DATE            NOT NULL,
    sexo                    sncev.tipo_sexo NOT NULL,

    -- Lugar de nacimiento
    municipio_nacimiento_id INT             REFERENCES sncev_geo.municipio(id),
    estado_nacimiento       CHAR(2)         REFERENCES sncev_geo.estado(clave_inegi),
    pais_nacimiento         CHAR(3)         NOT NULL DEFAULT 'MEX', -- ISO 3166-1 Alpha-3

    -- Pertenencia cultural
    grupo_etnico            VARCHAR(100),
    lengua_indigena         VARCHAR(100),
    habla_espanol           BOOLEAN,

    -- Unidad médica de registro
    unidad_med_registro_id  UUID            REFERENCES sncev.unidad_medica(id),

    -- Identificadores externos
    nss_imss_enc            TEXT,           -- Número Seguridad Social (cifrado)
    expediente_local        VARCHAR(50),    -- Número de expediente en unidad médica local

    -- FHIR
    fhir_patient_id         VARCHAR(100),   -- ID del recurso Patient en servidor FHIR externo

    -- Metadata
    activo                  BOOLEAN         NOT NULL DEFAULT TRUE,
    created_at              TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    created_by              UUID,           -- FK a sncev_admin.usuario — circular, se agrega post-creación
    updated_by              UUID
);

-- Índices
CREATE INDEX idx_paciente_curp_hash         ON sncev.paciente(curp_hash);
CREATE INDEX idx_paciente_tipo_cartilla     ON sncev.paciente(tipo_cartilla_id);
CREATE INDEX idx_paciente_fecha_nac         ON sncev.paciente(fecha_nacimiento);
CREATE INDEX idx_paciente_municipio_nac     ON sncev.paciente(municipio_nacimiento_id);
CREATE INDEX idx_paciente_unidad_reg        ON sncev.paciente(unidad_med_registro_id);
CREATE INDEX idx_paciente_created_at        ON sncev.paciente(created_at);

COMMENT ON TABLE  sncev.paciente              IS 'Titular de la cartilla electrónica. Columnas _enc cifradas AES-256.';
COMMENT ON COLUMN sncev.paciente.curp_hash    IS 'SHA-256 del CURP en texto plano para búsquedas exactas sin descifrar';
COMMENT ON COLUMN sncev.paciente.nombre_enc   IS 'Nombre(s) cifrado AES-256. Descifrado solo en capa de aplicación.';

-- Trigger: actualizar updated_at automáticamente
CREATE OR REPLACE FUNCTION sncev.fn_set_updated_at()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    NEW.updated_at := NOW();
    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_paciente_updated_at
    BEFORE UPDATE ON sncev.paciente
    FOR EACH ROW EXECUTE FUNCTION sncev.fn_set_updated_at();

-- ---------------------------------------------------------------------------
-- TABLA: Responsable / Tutor del paciente
-- ---------------------------------------------------------------------------
CREATE TABLE sncev.responsable (
    id                  UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    paciente_id         UUID        NOT NULL REFERENCES sncev.paciente(id) ON DELETE CASCADE,
    nombre_enc          TEXT        NOT NULL,
    ap_paterno_enc      TEXT        NOT NULL,
    ap_materno_enc      TEXT,
    curp_enc            TEXT,
    curp_hash           CHAR(64),
    parentesco          VARCHAR(50) NOT NULL,   -- Madre, Padre, Tutor, Abuelo/a, etc.
    telefono_enc        TEXT,
    telefono2_enc       TEXT,
    email_enc           TEXT,
    domicilio_calle_enc TEXT,
    domicilio_num_ext   VARCHAR(20),
    domicilio_num_int   VARCHAR(20),
    domicilio_colonia   VARCHAR(100),
    cp                  CHAR(5),
    municipio_id        INT         REFERENCES sncev_geo.municipio(id),
    es_principal        BOOLEAN     NOT NULL DEFAULT TRUE,
    activo              BOOLEAN     NOT NULL DEFAULT TRUE,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_responsable_paciente ON sncev.responsable(paciente_id);
CREATE INDEX idx_responsable_curp_hash ON sncev.responsable(curp_hash);

CREATE TRIGGER trg_responsable_updated_at
    BEFORE UPDATE ON sncev.responsable
    FOR EACH ROW EXECUTE FUNCTION sncev.fn_set_updated_at();

-- ---------------------------------------------------------------------------
-- TABLA: Vacunas aplicadas
-- ---------------------------------------------------------------------------
CREATE TABLE sncev.vacuna_aplicada (
    id                  UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    paciente_id         UUID        NOT NULL REFERENCES sncev.paciente(id),
    vacuna_id           INT         NOT NULL REFERENCES sncev.vacuna_catalogo(id),
    esquema_id          INT         REFERENCES sncev.esquema_vacunacion(id),
    numero_dosis        SMALLINT    NOT NULL DEFAULT 1,
    serie               VARCHAR(10),

    -- Datos del evento de vacunación
    fecha_aplicacion    DATE        NOT NULL,
    lote                VARCHAR(50),
    fecha_caducidad_lote DATE,
    laboratorio         VARCHAR(100),
    temperatura_cadena  NUMERIC(4,1),          -- temperatura de cadena de frío registrada

    -- Lugar y profesional
    unidad_medica_id    UUID        REFERENCES sncev.unidad_medica(id),
    municipio_aplicacion_id INT     REFERENCES sncev_geo.municipio(id),
    aplicado_por        UUID,                  -- FK a sncev_admin.usuario
    nombre_aplicador    VARCHAR(200),          -- cédula/nombre cuando no es usuario del sistema
    cedula_profesional  VARCHAR(20),

    -- Validación
    es_valida           BOOLEAN     NOT NULL DEFAULT TRUE,
    motivo_invalidacion TEXT,
    edad_dias_aplicacion INT,                  -- FIX-2: una columna GENERATED con subconsulta no es válida en PostgreSQL; la calcula el trigger trg_vacuna_aplicada_edad_dias

    -- FHIR
    fhir_immunization_id VARCHAR(100),

    -- Metadata
    observaciones       TEXT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by          UUID
);

CREATE INDEX idx_vac_aplic_paciente    ON sncev.vacuna_aplicada(paciente_id);
CREATE INDEX idx_vac_aplic_vacuna      ON sncev.vacuna_aplicada(vacuna_id);
CREATE INDEX idx_vac_aplic_fecha       ON sncev.vacuna_aplicada(fecha_aplicacion);
CREATE INDEX idx_vac_aplic_unidad      ON sncev.vacuna_aplicada(unidad_medica_id);
CREATE INDEX idx_vac_aplic_municipio   ON sncev.vacuna_aplicada(municipio_aplicacion_id);
CREATE INDEX idx_vac_aplic_lote        ON sncev.vacuna_aplicada(lote) WHERE lote IS NOT NULL;

-- FIX-2: cálculo de la edad en días al aplicar (fecha - fecha = entero de días)
CREATE OR REPLACE FUNCTION sncev.fn_calc_edad_dias_aplicacion()
RETURNS TRIGGER LANGUAGE plpgsql SECURITY DEFINER SET search_path = sncev, pg_temp AS $$
BEGIN
    SELECT (NEW.fecha_aplicacion - p.fecha_nacimiento)
      INTO NEW.edad_dias_aplicacion
      FROM sncev.paciente p WHERE p.id = NEW.paciente_id;
    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_vacuna_aplicada_edad_dias
    BEFORE INSERT OR UPDATE OF fecha_aplicacion, paciente_id ON sncev.vacuna_aplicada
    FOR EACH ROW EXECUTE FUNCTION sncev.fn_calc_edad_dias_aplicacion();

COMMENT ON TABLE  sncev.vacuna_aplicada                     IS 'Registro individual de cada dosis aplicada. Un registro por dosis.';
COMMENT ON COLUMN sncev.vacuna_aplicada.edad_dias_aplicacion IS 'Edad en días al momento de la aplicación (columna generada).';

-- ---------------------------------------------------------------------------
-- TABLA: Tamizajes neonatales (sección de la cartilla Niña/Niño)
-- ---------------------------------------------------------------------------
CREATE TABLE sncev.tamiz_neonatal (
    id                  UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    paciente_id         UUID        NOT NULL REFERENCES sncev.paciente(id),

    -- Datos del tamiz
    tipo_tamiz          VARCHAR(80) NOT NULL,   -- Metabólico, Auditivo, Cardiaco, Oftalmológico, Caderas
    fecha_toma          DATE        NOT NULL,
    numero_muestra      SMALLINT    NOT NULL DEFAULT 1 CHECK (numero_muestra BETWEEN 1 AND 3),
    resultado           sncev.tipo_resultado NOT NULL DEFAULT 'Pendiente',
    detalle_resultado   TEXT,
    fecha_resultado     DATE,
    requiere_seguimiento BOOLEAN    NOT NULL DEFAULT FALSE,
    observaciones       TEXT,

    -- Lugar y profesional
    unidad_medica_id    UUID        REFERENCES sncev.unidad_medica(id),
    realizado_por       UUID,                   -- FK a sncev_admin.usuario

    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by          UUID
);

CREATE INDEX idx_tamiz_paciente ON sncev.tamiz_neonatal(paciente_id);
CREATE INDEX idx_tamiz_tipo     ON sncev.tamiz_neonatal(tipo_tamiz);

-- ---------------------------------------------------------------------------
-- TABLA: Somatometría / Medidas antropométricas
-- ---------------------------------------------------------------------------
CREATE TABLE sncev.somatometria (
    id                  UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    paciente_id         UUID        NOT NULL REFERENCES sncev.paciente(id),
    fecha_medicion      DATE        NOT NULL,
    edad_dias           INT,
    peso_kg             NUMERIC(6,3),
    talla_cm            NUMERIC(5,1),
    pc_cm               NUMERIC(5,1),       -- Perímetro cefálico
    pt_cm               NUMERIC(5,1),       -- Perímetro torácico
    imc                 NUMERIC(5,2)        GENERATED ALWAYS AS (
                            CASE WHEN talla_cm > 0 THEN
                                ROUND((peso_kg / ((talla_cm/100)^2))::NUMERIC, 2)
                            ELSE NULL END
                        ) STORED,

    -- Percentiles (calculados por la aplicación según tablas OMS)
    percentil_peso      VARCHAR(10),
    percentil_talla     VARCHAR(10),
    percentil_imc       VARCHAR(10),
    percentil_pc        VARCHAR(10),
    clasificacion_nutricional VARCHAR(50),  -- Normal, Desnutrición leve/moderada/severa, Sobrepeso, Obesidad

    -- Contexto
    unidad_medica_id    UUID        REFERENCES sncev.unidad_medica(id),
    registrado_por      UUID,               -- FK a sncev_admin.usuario
    observaciones       TEXT,

    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (paciente_id, fecha_medicion)    -- Una medición por día por paciente
);

CREATE INDEX idx_somato_paciente ON sncev.somatometria(paciente_id);
CREATE INDEX idx_somato_fecha    ON sncev.somatometria(fecha_medicion);

-- ---------------------------------------------------------------------------
-- TABLA: Evaluación del desarrollo psicomotor (cartilla Niña/Niño)
-- ---------------------------------------------------------------------------
CREATE TABLE sncev.desarrollo_infantil (
    id                  UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    paciente_id         UUID        NOT NULL REFERENCES sncev.paciente(id),
    fecha_evaluacion    DATE        NOT NULL,
    edad_dias           INT,
    area                VARCHAR(50) NOT NULL CHECK (area IN ('Motor grueso','Motor fino','Lenguaje','Social','Cognitivo')),
    resultado           VARCHAR(20) NOT NULL CHECK (resultado IN ('Adecuado','Riesgo','Retraso','No evaluado')),
    habilidades_logradas TEXT[],    -- arreglo de hitos superados
    habilidades_pendientes TEXT[],
    observaciones       TEXT,
    unidad_medica_id    UUID        REFERENCES sncev.unidad_medica(id),
    evaluado_por        UUID,       -- FK a sncev_admin.usuario
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_desarrollo_paciente ON sncev.desarrollo_infantil(paciente_id);

-- ---------------------------------------------------------------------------
-- TABLA: Citas de vacunación
-- ---------------------------------------------------------------------------
CREATE TABLE sncev.cita_vacunacion (
    id                  UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    paciente_id         UUID        NOT NULL REFERENCES sncev.paciente(id),
    unidad_medica_id    UUID        NOT NULL REFERENCES sncev.unidad_medica(id),
    vacuna_id           INT         REFERENCES sncev.vacuna_catalogo(id),
    esquema_id          INT         REFERENCES sncev.esquema_vacunacion(id),
    fecha_programada    TIMESTAMPTZ NOT NULL,
    fecha_real          DATE,
    estado              sncev.tipo_cita_estado NOT NULL DEFAULT 'Pendiente',
    motivo_cancelacion  TEXT,
    recordatorio_sms    BOOLEAN     NOT NULL DEFAULT FALSE,
    recordatorio_push   BOOLEAN     NOT NULL DEFAULT FALSE,
    fecha_recordatorio  TIMESTAMPTZ,
    notas               TEXT,
    vacuna_aplicada_id  UUID        REFERENCES sncev.vacuna_aplicada(id),   -- vinculada al registro real
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by          UUID
);

CREATE INDEX idx_cita_paciente   ON sncev.cita_vacunacion(paciente_id);
CREATE INDEX idx_cita_unidad     ON sncev.cita_vacunacion(unidad_medica_id);
CREATE INDEX idx_cita_fecha      ON sncev.cita_vacunacion(fecha_programada);
CREATE INDEX idx_cita_estado     ON sncev.cita_vacunacion(estado);

-- ---------------------------------------------------------------------------
-- TABLA: Cartilla firmada digitalmente
-- ---------------------------------------------------------------------------
CREATE TABLE sncev.cartilla_firmada (
    id                  UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    paciente_id         UUID        NOT NULL REFERENCES sncev.paciente(id),
    version_cartilla    VARCHAR(20) NOT NULL DEFAULT '2023',
    hash_sha256         TEXT        NOT NULL,   -- SHA-256 del PDF generado
    firma_rsa           TEXT        NOT NULL,   -- firma RSA-2048 del certificado del profesional
    cert_thumbprint     VARCHAR(64),            -- huella del certificado usado para firmar
    firmado_por         UUID        NOT NULL,   -- FK a sncev_admin.usuario
    url_pdf             TEXT,                   -- URL del PDF en almacenamiento seguro
    url_qr              TEXT,                   -- URL del QR público de verificación
    qr_token            UUID        NOT NULL DEFAULT uuid_generate_v4(), -- token en QR
    fecha_firma         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    activa              BOOLEAN     NOT NULL DEFAULT TRUE
);

CREATE UNIQUE INDEX idx_cartilla_qr_token  ON sncev.cartilla_firmada(qr_token);
CREATE INDEX        idx_cartilla_paciente  ON sncev.cartilla_firmada(paciente_id);

COMMENT ON TABLE sncev.cartilla_firmada IS 'Registro de cartillas emitidas con firma digital RSA. Inmutable.';
COMMENT ON COLUMN sncev.cartilla_firmada.qr_token IS 'UUID único embebido en QR para verificación pública sin exponer id interno.';
