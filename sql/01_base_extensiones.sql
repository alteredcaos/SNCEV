-- =============================================================================
-- SISTEMA NACIONAL DE CARTILLA ELECTRÓNICA DE VACUNACIÓN (SNCEV)
-- DDL Módulo 01 — Extensiones, esquemas y catálogos base
-- Motor: PostgreSQL 15+
-- Estándar: NOM-024-SSA3-2012 | HL7 FHIR R4
-- =============================================================================

-- ---------------------------------------------------------------------------
-- Extensiones requeridas
-- ---------------------------------------------------------------------------
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";      -- uuid_generate_v4()
CREATE EXTENSION IF NOT EXISTS "pgcrypto";       -- gen_random_bytes(), crypt()
CREATE EXTENSION IF NOT EXISTS "pg_trgm";        -- búsqueda difusa en nombres
CREATE EXTENSION IF NOT EXISTS "btree_gist";     -- índices compuestos con rangos

-- ---------------------------------------------------------------------------
-- Esquemas lógicos
-- ---------------------------------------------------------------------------
CREATE SCHEMA IF NOT EXISTS sncev;          -- datos clínicos
CREATE SCHEMA IF NOT EXISTS sncev_admin;    -- usuarios, roles, permisos
CREATE SCHEMA IF NOT EXISTS sncev_geo;     -- geografía: estados, municipios, AGEBs
CREATE SCHEMA IF NOT EXISTS sncev_audit;   -- bitácora inmutable
CREATE SCHEMA IF NOT EXISTS sncev_report;  -- coberturas y reportes analíticos

SET search_path TO sncev, sncev_admin, sncev_geo, sncev_audit, sncev_report, public;

-- ---------------------------------------------------------------------------
-- Tipos enumerados
-- ---------------------------------------------------------------------------

CREATE TYPE sncev.tipo_sexo         AS ENUM ('M', 'F', 'I');       -- Indeterminado
CREATE TYPE sncev.tipo_via_admin    AS ENUM ('IM', 'SC', 'ID', 'VO', 'IN', 'TD');
CREATE TYPE sncev.tipo_resultado    AS ENUM ('Normal', 'Anormal', 'Pendiente', 'NoRealizado');
CREATE TYPE sncev.tipo_cita_estado  AS ENUM ('Pendiente', 'Confirmada', 'Realizada', 'Cancelada', 'NoAsistio');
CREATE TYPE sncev.tipo_unidad       AS ENUM ('SSA', 'IMSS', 'ISSSTE', 'PEMEX', 'SEDENA', 'SEMAR', 'PRIVADO', 'OTRO');

CREATE TYPE sncev_admin.tipo_accion AS ENUM (
    'INSERT', 'UPDATE', 'DELETE',
    'LOGIN', 'LOGOUT', 'LOGIN_FALLIDO',
    'EXPORT', 'PRINT', 'VIEW_SENSITIVE'
);

-- ---------------------------------------------------------------------------
-- CATÁLOGO: Estados de la República Mexicana
-- ---------------------------------------------------------------------------
CREATE TABLE sncev_geo.estado (
    clave_inegi     CHAR(2)         PRIMARY KEY,
    nombre          VARCHAR(60)     NOT NULL,
    abreviatura     VARCHAR(6)      NOT NULL,   -- FIX-1: era VARCHAR(4); 'TAMPS' tiene 5 caracteres y abortaba el INSERT de los 32 estados
    activo          BOOLEAN         NOT NULL DEFAULT TRUE
);

COMMENT ON TABLE sncev_geo.estado IS 'Catálogo de entidades federativas INEGI';

INSERT INTO sncev_geo.estado (clave_inegi, nombre, abreviatura) VALUES
('01','Aguascalientes','AGS'),('02','Baja California','BC'),
('03','Baja California Sur','BCS'),('04','Campeche','CAM'),
('05','Coahuila','COAH'),('06','Colima','COL'),
('07','Chiapas','CHIS'),('08','Chihuahua','CHIH'),
('09','Ciudad de México','CDMX'),('10','Durango','DGO'),
('11','Guanajuato','GTO'),('12','Guerrero','GRO'),
('13','Hidalgo','HGO'),('14','Jalisco','JAL'),
('15','Estado de México','MEX'),('16','Michoacán','MICH'),
('17','Morelos','MOR'),('18','Nayarit','NAY'),
('19','Nuevo León','NL'),('20','Oaxaca','OAX'),
('21','Puebla','PUE'),('22','Querétaro','QRO'),
('23','Quintana Roo','QROO'),('24','San Luis Potosí','SLP'),
('25','Sinaloa','SIN'),('26','Sonora','SON'),
('27','Tabasco','TAB'),('28','Tamaulipas','TAMPS'),
('29','Tlaxcala','TLAX'),('30','Veracruz','VER'),
('31','Yucatán','YUC'),('32','Zacatecas','ZAC');

-- ---------------------------------------------------------------------------
-- CATÁLOGO: Municipios
-- ---------------------------------------------------------------------------
CREATE TABLE sncev_geo.municipio (
    id              SERIAL          PRIMARY KEY,
    clave_inegi     CHAR(5)         NOT NULL UNIQUE,   -- ej: "09001"
    nombre          VARCHAR(100)    NOT NULL,
    estado_clave    CHAR(2)         NOT NULL REFERENCES sncev_geo.estado(clave_inegi),
    activo          BOOLEAN         NOT NULL DEFAULT TRUE
);

CREATE INDEX idx_municipio_estado ON sncev_geo.municipio(estado_clave);
COMMENT ON TABLE sncev_geo.municipio IS 'Catálogo de municipios INEGI (2 456 registros)';

-- ---------------------------------------------------------------------------
-- CATÁLOGO: AGEBs (Área Geoestadística Básica)
-- ---------------------------------------------------------------------------
CREATE TABLE sncev_geo.ageb (
    clave           CHAR(13)        PRIMARY KEY,       -- ej: "0901400010030"
    nombre          VARCHAR(200),
    tipo            CHAR(1)         NOT NULL DEFAULT 'U' CHECK (tipo IN ('U','R')), -- Urbana/Rural
    municipio_id    INT             NOT NULL REFERENCES sncev_geo.municipio(id),
    estado_clave    CHAR(2)         NOT NULL REFERENCES sncev_geo.estado(clave_inegi),
    poblacion_total INT,
    poblacion_menor_5   INT,
    poblacion_5_14      INT,
    poblacion_15_49_f   INT,        -- mujeres en edad fértil
    poblacion_60_mas    INT,
    geom_wkt        TEXT,           -- geometría WKT para mapas (opcional)
    activo          BOOLEAN         NOT NULL DEFAULT TRUE
);

CREATE INDEX idx_ageb_municipio ON sncev_geo.ageb(municipio_id);
CREATE INDEX idx_ageb_estado    ON sncev_geo.ageb(estado_clave);
COMMENT ON TABLE sncev_geo.ageb IS 'AGEBs INEGI — unidad mínima para coberturas';

-- ---------------------------------------------------------------------------
-- CATÁLOGO: Jurisdicciones sanitarias
-- ---------------------------------------------------------------------------
CREATE TABLE sncev_geo.jurisdiccion (
    id                  SERIAL      PRIMARY KEY,
    numero              SMALLINT    NOT NULL,
    nombre              VARCHAR(100) NOT NULL,
    estado_clave        CHAR(2)     NOT NULL REFERENCES sncev_geo.estado(clave_inegi),
    sede_municipio_id   INT         REFERENCES sncev_geo.municipio(id),
    telefono            VARCHAR(20),
    activo              BOOLEAN     NOT NULL DEFAULT TRUE,
    UNIQUE (numero, estado_clave)
);

COMMENT ON TABLE sncev_geo.jurisdiccion IS 'Jurisdicciones sanitarias por estado';

-- ---------------------------------------------------------------------------
-- CATÁLOGO: Unidades médicas (CLUES)
-- ---------------------------------------------------------------------------
CREATE TABLE sncev.unidad_medica (
    id              UUID            PRIMARY KEY DEFAULT uuid_generate_v4(),
    clues           VARCHAR(11)     NOT NULL UNIQUE,    -- Clave CLUES oficial
    nombre          VARCHAR(200)    NOT NULL,
    tipo            sncev.tipo_unidad NOT NULL DEFAULT 'SSA',
    nivel_atencion  SMALLINT        CHECK (nivel_atencion BETWEEN 1 AND 3),
    municipio_id    INT             NOT NULL REFERENCES sncev_geo.municipio(id),
    estado_clave    CHAR(2)         NOT NULL REFERENCES sncev_geo.estado(clave_inegi),
    jurisdiccion_id INT             REFERENCES sncev_geo.jurisdiccion(id),
    ageb_clave      CHAR(13)        REFERENCES sncev_geo.ageb(clave),
    domicilio       TEXT,
    cp              CHAR(5),
    telefono        VARCHAR(20),
    latitud         NUMERIC(10,7),
    longitud        NUMERIC(10,7),
    activo          BOOLEAN         NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_unidad_jurisdiccion ON sncev.unidad_medica(jurisdiccion_id);
CREATE INDEX idx_unidad_municipio    ON sncev.unidad_medica(municipio_id);
COMMENT ON TABLE sncev.unidad_medica IS 'Unidades médicas con clave CLUES oficial';

-- ---------------------------------------------------------------------------
-- CATÁLOGO: Tipos de cartilla
-- ---------------------------------------------------------------------------
CREATE TABLE sncev.tipo_cartilla (
    id              SERIAL          PRIMARY KEY,
    nombre          VARCHAR(80)     NOT NULL,
    descripcion     TEXT,
    edad_min_dias   INT             NOT NULL DEFAULT 0,
    edad_max_dias   INT,            -- NULL = sin límite superior
    orden           SMALLINT        NOT NULL DEFAULT 0,
    color_hex       CHAR(7)         DEFAULT '#1D9E75',  -- para UI
    activo          BOOLEAN         NOT NULL DEFAULT TRUE
);

INSERT INTO sncev.tipo_cartilla (nombre, edad_min_dias, edad_max_dias, orden, color_hex) VALUES
('Niña y Niño',         0,      4015,   1, '#1D9E75'),   -- 0 a 11 años
('Adolescente',         4016,   6209,   2, '#185FA5'),   -- 11 a 17 años
('Mujer',               4016,   NULL,   3, '#D4537E'),   -- mujer ≥11 años
('Adulto',              6210,   21899,  4, '#BA7517'),   -- 18 a 59 años
('Adulto Mayor',        21900,  NULL,   5, '#534AB7');   -- ≥60 años

-- ---------------------------------------------------------------------------
-- CATÁLOGO: Vacunas (catálogo nacional CENSIA 2023)
-- ---------------------------------------------------------------------------
CREATE TABLE sncev.vacuna_catalogo (
    id                  SERIAL          PRIMARY KEY,
    clave_censia        VARCHAR(20)     NOT NULL UNIQUE,
    nombre_generico     VARCHAR(200)    NOT NULL,
    nombre_comercial    VARCHAR(200),
    via_administracion  sncev.tipo_via_admin NOT NULL,
    volumen_dosis_ml    NUMERIC(5,2),
    sitio_aplicacion    VARCHAR(100),   -- ej: "Músculo vasto externo del muslo"
    tipo_vacuna         VARCHAR(80),    -- ej: "Atenuada", "Inactivada", "Toxoide", "Recombinante"
    enfermedades        TEXT[],         -- arreglo de enfermedades que previene
    cadena_frio         VARCHAR(20)     DEFAULT '2-8°C',
    fabricante_ref      VARCHAR(100),   -- fabricante de referencia
    fhir_cvx_code       VARCHAR(10),    -- código CVX estándar CDC/HL7
    fhir_system         VARCHAR(200)    DEFAULT 'http://hl7.org/fhir/sid/cvx',
    observaciones       TEXT,
    activo              BOOLEAN         NOT NULL DEFAULT TRUE,
    created_at          TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);

-- Esquema Nacional de Vacunación 2023 (principales biológicos)
INSERT INTO sncev.vacuna_catalogo
    (clave_censia, nombre_generico, via_administracion, volumen_dosis_ml, tipo_vacuna, enfermedades, fhir_cvx_code) VALUES
('BCG',     'BCG (Bacilo de Calmette-Guérin)',                  'ID', 0.1,  'Atenuada',     ARRAY['Tuberculosis meníngea','Tuberculosis miliar'], '19'),
('HB',      'Hepatitis B pediátrica',                           'IM', 0.5,  'Recombinante', ARRAY['Hepatitis B'], '45'),
('Penta',   'Pentavalente acelular',                            'IM', 0.5,  'Combinada',    ARRAY['Difteria','Tos ferina','Tétanos','Haemophilus influenzae b','Hepatitis B'], '120'),
('Rota',    'Rotavirus',                                        'VO', 1.5,  'Atenuada',     ARRAY['Gastroenteritis por Rotavirus'], '116'),
('Neumo',   'Neumocócica conjugada 13-valente',                 'IM', 0.5,  'Conjugada',    ARRAY['Neumonía','Meningitis neumocócica'], '133'),
('SRP',     'Triple viral SRP',                                 'SC', 0.5,  'Atenuada',     ARRAY['Sarampión','Rubéola','Parotiditis'], '03'),
('SR',      'Doble viral SR',                                   'SC', 0.5,  'Atenuada',     ARRAY['Sarampión','Rubéola'], '04'),
('VPH',     'Virus del Papiloma Humano',                        'IM', 0.5,  'Recombinante', ARRAY['VPH','Cáncer cervicouterino'], '62'),
('dTpa',    'Toxoide tetánico-diftérico con pertussis acelular','IM', 0.5,  'Toxoide',      ARRAY['Tétanos','Difteria','Tos ferina'], '115'),
('VHB_A',   'Hepatitis B para adultos',                         'IM', 1.0,  'Recombinante', ARRAY['Hepatitis B'], '45'),
('Inf',     'Influenza estacional (adultos)',                   'IM', 0.5,  'Inactivada',   ARRAY['Influenza'], '141'),
('Inf_Ped', 'Influenza estacional (pediátrica)',                'IM', 0.25, 'Inactivada',   ARRAY['Influenza'], '141'),
('dT',      'Toxoide tetánico-diftérico para adultos',          'IM', 0.5,  'Toxoide',      ARRAY['Tétanos','Difteria'], '09'),
('SA14',    'Fiebre amarilla',                                  'SC', 0.5,  'Atenuada',     ARRAY['Fiebre amarilla'], '37'),
('TiO',     'Tifoidea oral',                                    'VO', NULL, 'Atenuada',     ARRAY['Fiebre tifoidea'], '25'),
('Varic',   'Varicela',                                         'SC', 0.5,  'Atenuada',     ARRAY['Varicela'], '21'),
('HepA',    'Hepatitis A',                                      'IM', 0.5,  'Inactivada',   ARRAY['Hepatitis A'], '52'),
('Neumo23', 'Neumocócica polisacárida 23-valente',              'IM', 0.5,  'Polisacárida', ARRAY['Neumonía neumocócica'], '33'),
('Covid',   'COVID-19',                                         'IM', 0.5,  'ARNm/Vector',  ARRAY['COVID-19'], '213'),
('HerZ',    'Herpes zóster',                                    'IM', 0.5,  'Recombinante', ARRAY['Herpes zóster'], '187');

-- ---------------------------------------------------------------------------
-- CATÁLOGO: Esquema nacional de vacunación por tipo de cartilla
-- ---------------------------------------------------------------------------
CREATE TABLE sncev.esquema_vacunacion (
    id              SERIAL          PRIMARY KEY,
    tipo_cartilla_id INT            NOT NULL REFERENCES sncev.tipo_cartilla(id),
    vacuna_id       INT             NOT NULL REFERENCES sncev.vacuna_catalogo(id),
    numero_dosis    SMALLINT        NOT NULL DEFAULT 1,
    serie           VARCHAR(10),    -- ej: 'D1','D2','R1','R2'
    edad_min_dias   INT             NOT NULL DEFAULT 0,
    edad_max_dias   INT,
    edad_optima_dias INT,           -- edad ideal de aplicación
    intervalo_min_dias INT,         -- intervalo mínimo desde dosis anterior
    es_refuerzo     BOOLEAN         NOT NULL DEFAULT FALSE,
    es_campaña      BOOLEAN         NOT NULL DEFAULT FALSE,
    obligatoria     BOOLEAN         NOT NULL DEFAULT TRUE,
    observaciones   TEXT,
    activo          BOOLEAN         NOT NULL DEFAULT TRUE,
    UNIQUE (tipo_cartilla_id, vacuna_id, numero_dosis)
);

-- Esquema cartilla Niña/Niño (tipo_cartilla_id = 1)
INSERT INTO sncev.esquema_vacunacion
    (tipo_cartilla_id, vacuna_id, numero_dosis, serie, edad_min_dias, edad_max_dias, edad_optima_dias, intervalo_min_dias) 
SELECT 1, id, 1, 'D1', 0, 7, 0, NULL FROM sncev.vacuna_catalogo WHERE clave_censia = 'BCG';
INSERT INTO sncev.esquema_vacunacion
    (tipo_cartilla_id, vacuna_id, numero_dosis, serie, edad_min_dias, edad_max_dias, edad_optima_dias, intervalo_min_dias) 
SELECT 1, id, 1, 'D1', 0, 3, 0, NULL FROM sncev.vacuna_catalogo WHERE clave_censia = 'HB';
INSERT INTO sncev.esquema_vacunacion
    (tipo_cartilla_id, vacuna_id, numero_dosis, serie, edad_min_dias, edad_optima_dias, intervalo_min_dias) 
SELECT 1, id, 1, 'D1', 56,  60, NULL FROM sncev.vacuna_catalogo WHERE clave_censia = 'Penta';
INSERT INTO sncev.esquema_vacunacion
    (tipo_cartilla_id, vacuna_id, numero_dosis, serie, edad_min_dias, edad_optima_dias, intervalo_min_dias) 
SELECT 1, id, 2, 'D2', 112, 120, 56 FROM sncev.vacuna_catalogo WHERE clave_censia = 'Penta';
INSERT INTO sncev.esquema_vacunacion
    (tipo_cartilla_id, vacuna_id, numero_dosis, serie, edad_min_dias, edad_optima_dias, intervalo_min_dias) 
SELECT 1, id, 3, 'D3', 168, 180, 56 FROM sncev.vacuna_catalogo WHERE clave_censia = 'Penta';
INSERT INTO sncev.esquema_vacunacion
    (tipo_cartilla_id, vacuna_id, numero_dosis, serie, edad_min_dias, edad_max_dias, edad_optima_dias, intervalo_min_dias) 
SELECT 1, id, 1, 'D1', 56, 90, 60, NULL FROM sncev.vacuna_catalogo WHERE clave_censia = 'Rota';
INSERT INTO sncev.esquema_vacunacion
    (tipo_cartilla_id, vacuna_id, numero_dosis, serie, edad_min_dias, edad_max_dias, edad_optima_dias, intervalo_min_dias) 
SELECT 1, id, 2, 'D2', 112, 150, 120, 28 FROM sncev.vacuna_catalogo WHERE clave_censia = 'Rota';
INSERT INTO sncev.esquema_vacunacion
    (tipo_cartilla_id, vacuna_id, numero_dosis, serie, edad_min_dias, edad_optima_dias, intervalo_min_dias) 
SELECT 1, id, 1, 'D1', 56,  60, NULL FROM sncev.vacuna_catalogo WHERE clave_censia = 'Neumo';
INSERT INTO sncev.esquema_vacunacion
    (tipo_cartilla_id, vacuna_id, numero_dosis, serie, edad_min_dias, edad_optima_dias, intervalo_min_dias) 
SELECT 1, id, 2, 'D2', 112, 120, 56 FROM sncev.vacuna_catalogo WHERE clave_censia = 'Neumo';
INSERT INTO sncev.esquema_vacunacion
    (tipo_cartilla_id, vacuna_id, numero_dosis, serie, edad_min_dias, edad_optima_dias, intervalo_min_dias, es_refuerzo) 
SELECT 1, id, 3, 'R1', 335, 365, NULL, TRUE FROM sncev.vacuna_catalogo WHERE clave_censia = 'Neumo';
INSERT INTO sncev.esquema_vacunacion
    (tipo_cartilla_id, vacuna_id, numero_dosis, serie, edad_min_dias, edad_optima_dias) 
SELECT 1, id, 1, 'D1', 335, 365 FROM sncev.vacuna_catalogo WHERE clave_censia = 'SRP';
INSERT INTO sncev.esquema_vacunacion
    (tipo_cartilla_id, vacuna_id, numero_dosis, serie, edad_min_dias, edad_optima_dias, es_refuerzo) 
SELECT 1, id, 2, 'R1', 548, 548, TRUE FROM sncev.vacuna_catalogo WHERE clave_censia = 'SRP';
INSERT INTO sncev.esquema_vacunacion
    (tipo_cartilla_id, vacuna_id, numero_dosis, serie, edad_min_dias, edad_optima_dias) 
SELECT 1, id, 1, 'D1', 0, 180 FROM sncev.vacuna_catalogo WHERE clave_censia = 'Inf_Ped';

-- Esquema cartilla Adolescente (tipo_cartilla_id = 2)
INSERT INTO sncev.esquema_vacunacion
    (tipo_cartilla_id, vacuna_id, numero_dosis, serie, edad_min_dias, edad_max_dias) 
SELECT 2, id, 1, 'D1', 3650, 4745 FROM sncev.vacuna_catalogo WHERE clave_censia = 'VPH';
INSERT INTO sncev.esquema_vacunacion
    (tipo_cartilla_id, vacuna_id, numero_dosis, serie, edad_min_dias, edad_max_dias, intervalo_min_dias) 
SELECT 2, id, 2, 'D2', 3650, 4745, 182 FROM sncev.vacuna_catalogo WHERE clave_censia = 'VPH';
INSERT INTO sncev.esquema_vacunacion
    (tipo_cartilla_id, vacuna_id, numero_dosis, serie, edad_min_dias, edad_max_dias) 
SELECT 2, id, 1, 'SR', 4016, 6209 FROM sncev.vacuna_catalogo WHERE clave_censia = 'SR';
INSERT INTO sncev.esquema_vacunacion
    (tipo_cartilla_id, vacuna_id, numero_dosis, serie, edad_min_dias, edad_max_dias) 
SELECT 2, id, 1, 'D1', 4016, 6209 FROM sncev.vacuna_catalogo WHERE clave_censia = 'Inf';

-- Esquema cartilla Mujer (tipo_cartilla_id = 3)
INSERT INTO sncev.esquema_vacunacion
    (tipo_cartilla_id, vacuna_id, numero_dosis, serie, edad_min_dias, observaciones) 
SELECT 3, id, 1, 'D1', 4016, 'Primera dosis o sin esquema previo' FROM sncev.vacuna_catalogo WHERE clave_censia = 'dTpa';
INSERT INTO sncev.esquema_vacunacion
    (tipo_cartilla_id, vacuna_id, numero_dosis, serie, edad_min_dias, intervalo_min_dias, observaciones) 
SELECT 3, id, 2, 'D2', 4016, 28, 'Al menos 4 semanas después de D1' FROM sncev.vacuna_catalogo WHERE clave_censia = 'dTpa';
INSERT INTO sncev.esquema_vacunacion
    (tipo_cartilla_id, vacuna_id, numero_dosis, serie, edad_min_dias, intervalo_min_dias, es_refuerzo, observaciones) 
SELECT 3, id, 3, 'R1', 4016, 182, TRUE, 'Refuerzo 6 meses después de D2' FROM sncev.vacuna_catalogo WHERE clave_censia = 'dTpa';
INSERT INTO sncev.esquema_vacunacion
    (tipo_cartilla_id, vacuna_id, numero_dosis, serie, edad_min_dias, es_refuerzo, observaciones) 
SELECT 3, id, 4, 'R2', 4016, TRUE, 'Cada 10 años' FROM sncev.vacuna_catalogo WHERE clave_censia = 'dTpa';

-- Esquema Adulto Mayor (tipo_cartilla_id = 5)
INSERT INTO sncev.esquema_vacunacion
    (tipo_cartilla_id, vacuna_id, numero_dosis, serie, edad_min_dias, observaciones) 
SELECT 5, id, 1, 'D1', 21900, 'Dosis única o anual según biológico' FROM sncev.vacuna_catalogo WHERE clave_censia = 'Inf';
INSERT INTO sncev.esquema_vacunacion
    (tipo_cartilla_id, vacuna_id, numero_dosis, serie, edad_min_dias, observaciones) 
SELECT 5, id, 1, 'D1', 21900, 'Dosis única' FROM sncev.vacuna_catalogo WHERE clave_censia = 'Neumo23';
INSERT INTO sncev.esquema_vacunacion
    (tipo_cartilla_id, vacuna_id, numero_dosis, serie, edad_min_dias, observaciones) 
SELECT 5, id, 1, 'D1', 21900, 'Dosis única recomendada ≥60 años' FROM sncev.vacuna_catalogo WHERE clave_censia = 'HerZ';
