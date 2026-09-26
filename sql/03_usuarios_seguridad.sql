-- =============================================================================
-- SNCEV — DDL Módulo 03
-- Usuarios, Roles, Permisos, Seguridad y Auditoría
-- =============================================================================

SET search_path TO sncev_admin, sncev, sncev_geo, public;

-- ---------------------------------------------------------------------------
-- TABLA: Roles del sistema
-- ---------------------------------------------------------------------------
CREATE TABLE sncev_admin.rol (
    id              SERIAL      PRIMARY KEY,
    nombre          VARCHAR(60) NOT NULL UNIQUE,
    descripcion     TEXT,
    nivel_acceso    SMALLINT    NOT NULL DEFAULT 1 CHECK (nivel_acceso BETWEEN 1 AND 6),
    -- 1=Ciudadano, 2=Enfermera/Vacunador, 3=Médico, 4=Jurisdiccional, 5=Estatal, 6=Nacional
    activo          BOOLEAN     NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

INSERT INTO sncev_admin.rol (nombre, descripcion, nivel_acceso) VALUES
('Administrador Nacional',  'Acceso total al sistema nacional',                         6),
('Administrador Estatal',   'Acceso a datos de su estado',                              5),
('Coordinador Jurisdiccional', 'Acceso a datos de su jurisdicción sanitaria',           4),
('Médico',                  'Registro y consulta clínica, firma de cartillas',          3),
('Enfermera/Vacunador',     'Registro de vacunación en campo',                          2),
('Ciudadano',               'Consulta de su propia cartilla',                           1),
('Auditor',                 'Solo lectura de bitácoras y reportes de auditoría',        5),
('Analista Epidemiólogo',   'Acceso a reportes de cobertura y datos agregados',         4);

-- ---------------------------------------------------------------------------
-- TABLA: Permisos granulares
-- ---------------------------------------------------------------------------
CREATE TABLE sncev_admin.permiso (
    id          SERIAL      PRIMARY KEY,
    codigo      VARCHAR(80) NOT NULL UNIQUE,
    modulo      VARCHAR(40) NOT NULL,
    descripcion TEXT,
    activo      BOOLEAN     NOT NULL DEFAULT TRUE
);

INSERT INTO sncev_admin.permiso (codigo, modulo, descripcion) VALUES
-- Módulo PACIENTE
('PACIENTE_CREAR',          'Paciente',     'Registrar nuevo paciente'),
('PACIENTE_VER',            'Paciente',     'Consultar datos del paciente'),
('PACIENTE_EDITAR',         'Paciente',     'Modificar datos del paciente'),
('PACIENTE_DATOS_SENSIBLES','Paciente',     'Ver datos cifrados: CURP, nombre completo, teléfono'),
('PACIENTE_DESACTIVAR',     'Paciente',     'Desactivar (baja lógica) un paciente'),
-- Módulo VACUNACIÓN
('VACUNA_APLICAR',          'Vacunacion',   'Registrar una dosis aplicada'),
('VACUNA_EDITAR',           'Vacunacion',   'Corregir registro de dosis aplicada'),
('VACUNA_INVALIDAR',        'Vacunacion',   'Marcar una dosis como inválida'),
('VACUNA_VER',              'Vacunacion',   'Consultar historial de vacunación'),
-- Módulo CLÍNICO
('CLINICO_TAMIZ_CREAR',     'Clinico',      'Registrar tamiz neonatal'),
('CLINICO_SOMATO_CREAR',    'Clinico',      'Registrar somatometría'),
('CLINICO_DESARROLLO_CREAR','Clinico',      'Registrar evaluación de desarrollo'),
('CLINICO_VER',             'Clinico',      'Consultar datos clínicos'),
-- Módulo CARTILLA
('CARTILLA_GENERAR',        'Cartilla',     'Generar y firmar PDF de cartilla'),
('CARTILLA_VER_PUBLICA',    'Cartilla',     'Ver cartilla con datos básicos (ciudadano)'),
('CARTILLA_VER_COMPLETA',   'Cartilla',     'Ver cartilla completa con todos los datos clínicos'),
-- Módulo CITAS
('CITA_CREAR',              'Citas',        'Agendar cita de vacunación'),
('CITA_EDITAR',             'Citas',        'Modificar o cancelar cita'),
('CITA_VER',                'Citas',        'Ver agenda de citas'),
-- Módulo CATÁLOGOS
('CATALOGO_VER',            'Catalogo',     'Consultar catálogos (vacunas, esquemas)'),
('CATALOGO_EDITAR',         'Catalogo',     'Modificar catálogos nacionales'),
('UNIDAD_MEDICA_VER',       'Catalogo',     'Ver unidades médicas'),
('UNIDAD_MEDICA_EDITAR',    'Catalogo',     'Crear/modificar unidades médicas'),
-- Módulo REPORTES
('REPORTE_COBERTURA_VER',   'Reportes',     'Ver reportes de cobertura por AGEB/municipio'),
('REPORTE_EXPORTAR',        'Reportes',     'Exportar datos en CSV/XLSX'),
('REPORTE_NACIONAL_VER',    'Reportes',     'Ver reportes agregados a nivel nacional'),
-- Módulo USUARIOS
('USUARIO_CREAR',           'Usuarios',     'Crear nuevos usuarios del sistema'),
('USUARIO_EDITAR',          'Usuarios',     'Modificar usuarios'),
('USUARIO_ROLES_ASIGNAR',   'Usuarios',     'Asignar o quitar roles'),
('USUARIO_VER',             'Usuarios',     'Listar y consultar usuarios'),
-- Módulo AUDITORÍA
('AUDITORIA_VER',           'Auditoria',    'Consultar bitácora de auditoría'),
('AUDITORIA_EXPORTAR',      'Auditoria',    'Exportar bitácora de auditoría');

-- ---------------------------------------------------------------------------
-- TABLA PIVOTE: Rol ↔ Permiso
-- ---------------------------------------------------------------------------
CREATE TABLE sncev_admin.rol_permiso (
    rol_id          INT         NOT NULL REFERENCES sncev_admin.rol(id),
    permiso_id      INT         NOT NULL REFERENCES sncev_admin.permiso(id),
    asignado_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    asignado_por    UUID,       -- FK a usuario (auto-referencia, se agrega post-creación)
    PRIMARY KEY (rol_id, permiso_id)
);

-- Asignar permisos a roles (usando CTEs para legibilidad)
DO $$
DECLARE
    v_adm_nac   INT := (SELECT id FROM sncev_admin.rol WHERE nombre = 'Administrador Nacional');
    v_adm_est   INT := (SELECT id FROM sncev_admin.rol WHERE nombre = 'Administrador Estatal');
    v_coord     INT := (SELECT id FROM sncev_admin.rol WHERE nombre = 'Coordinador Jurisdiccional');
    v_medico    INT := (SELECT id FROM sncev_admin.rol WHERE nombre = 'Médico');
    v_enf       INT := (SELECT id FROM sncev_admin.rol WHERE nombre = 'Enfermera/Vacunador');
    v_ciudadano INT := (SELECT id FROM sncev_admin.rol WHERE nombre = 'Ciudadano');
    v_auditor   INT := (SELECT id FROM sncev_admin.rol WHERE nombre = 'Auditor');
    v_analist   INT := (SELECT id FROM sncev_admin.rol WHERE nombre = 'Analista Epidemiólogo');
BEGIN
    -- Administrador Nacional: todos los permisos
    INSERT INTO sncev_admin.rol_permiso (rol_id, permiso_id)
    SELECT v_adm_nac, id FROM sncev_admin.permiso;

    -- Administrador Estatal
    INSERT INTO sncev_admin.rol_permiso (rol_id, permiso_id)
    SELECT v_adm_est, id FROM sncev_admin.permiso
    WHERE codigo NOT IN ('CATALOGO_EDITAR','AUDITORIA_EXPORTAR','REPORTE_NACIONAL_VER','USUARIO_ROLES_ASIGNAR');

    -- Coordinador Jurisdiccional
    INSERT INTO sncev_admin.rol_permiso (rol_id, permiso_id)
    SELECT v_coord, id FROM sncev_admin.permiso
    WHERE codigo IN (
        'PACIENTE_VER','PACIENTE_DATOS_SENSIBLES',
        'VACUNA_VER','VACUNA_APLICAR','VACUNA_INVALIDAR',
        'CLINICO_VER','CLINICO_TAMIZ_CREAR','CLINICO_SOMATO_CREAR','CLINICO_DESARROLLO_CREAR',
        'CARTILLA_VER_COMPLETA','CARTILLA_GENERAR',
        'CITA_VER','CITA_CREAR','CITA_EDITAR',
        'CATALOGO_VER','UNIDAD_MEDICA_VER',
        'REPORTE_COBERTURA_VER','REPORTE_EXPORTAR',
        'USUARIO_VER'
    );

    -- Médico
    INSERT INTO sncev_admin.rol_permiso (rol_id, permiso_id)
    SELECT v_medico, id FROM sncev_admin.permiso
    WHERE codigo IN (
        'PACIENTE_CREAR','PACIENTE_VER','PACIENTE_EDITAR','PACIENTE_DATOS_SENSIBLES',
        'VACUNA_VER','VACUNA_APLICAR','VACUNA_EDITAR',
        'CLINICO_VER','CLINICO_TAMIZ_CREAR','CLINICO_SOMATO_CREAR','CLINICO_DESARROLLO_CREAR',
        'CARTILLA_VER_COMPLETA','CARTILLA_GENERAR',
        'CITA_VER','CITA_CREAR','CITA_EDITAR',
        'CATALOGO_VER','UNIDAD_MEDICA_VER'
    );

    -- Enfermera/Vacunador
    INSERT INTO sncev_admin.rol_permiso (rol_id, permiso_id)
    SELECT v_enf, id FROM sncev_admin.permiso
    WHERE codigo IN (
        'PACIENTE_CREAR','PACIENTE_VER','PACIENTE_DATOS_SENSIBLES',
        'VACUNA_VER','VACUNA_APLICAR',
        'CLINICO_SOMATO_CREAR','CLINICO_VER',
        'CARTILLA_VER_COMPLETA',
        'CITA_VER','CITA_CREAR',
        'CATALOGO_VER','UNIDAD_MEDICA_VER'
    );

    -- Ciudadano: solo su propia cartilla
    INSERT INTO sncev_admin.rol_permiso (rol_id, permiso_id)
    SELECT v_ciudadano, id FROM sncev_admin.permiso
    WHERE codigo IN ('CARTILLA_VER_PUBLICA','CITA_VER');

    -- Auditor
    INSERT INTO sncev_admin.rol_permiso (rol_id, permiso_id)
    SELECT v_auditor, id FROM sncev_admin.permiso
    WHERE codigo IN ('AUDITORIA_VER','AUDITORIA_EXPORTAR','USUARIO_VER','REPORTE_COBERTURA_VER');

    -- Analista Epidemiólogo
    INSERT INTO sncev_admin.rol_permiso (rol_id, permiso_id)
    SELECT v_analist, id FROM sncev_admin.permiso
    WHERE codigo IN (
        'REPORTE_COBERTURA_VER','REPORTE_EXPORTAR','REPORTE_NACIONAL_VER',
        'CATALOGO_VER','UNIDAD_MEDICA_VER','VACUNA_VER','PACIENTE_VER'
    );
END $$;

-- ---------------------------------------------------------------------------
-- TABLA: Usuarios del sistema
-- ---------------------------------------------------------------------------
CREATE TABLE sncev_admin.usuario (
    id                  UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    username            VARCHAR(60) NOT NULL UNIQUE,
    email_enc           TEXT        NOT NULL,               -- AES-256
    email_hash          CHAR(64)    NOT NULL UNIQUE,        -- SHA-256 para búsqueda
    password_hash       TEXT        NOT NULL,               -- bcrypt cost=12
    rol_id              INT         NOT NULL REFERENCES sncev_admin.rol(id),

    -- Ámbito geográfico / institucional
    unidad_medica_id    UUID        REFERENCES sncev.unidad_medica(id),
    jurisdiccion_id     INT         REFERENCES sncev_geo.jurisdiccion(id),
    estado_clave        CHAR(2)     REFERENCES sncev_geo.estado(clave_inegi),
    -- NULL en los tres = acceso nacional (solo rol Administrador Nacional)

    -- Datos del profesional
    nombre_enc          TEXT,                               -- nombre completo cifrado
    cedula_profesional  VARCHAR(20),
    especialidad        VARCHAR(100),

    -- Estado de cuenta
    activo              BOOLEAN     NOT NULL DEFAULT TRUE,
    mfa_habilitado      BOOLEAN     NOT NULL DEFAULT FALSE,
    mfa_secret_enc      TEXT,                               -- TOTP secret cifrado
    email_verificado    BOOLEAN     NOT NULL DEFAULT FALSE,
    email_token         UUID,                               -- token de verificación de email

    -- Control de acceso
    ultimo_acceso       TIMESTAMPTZ,
    intentos_fallidos   SMALLINT    NOT NULL DEFAULT 0,
    bloqueado_hasta     TIMESTAMPTZ,
    password_cambiado_at TIMESTAMPTZ,
    requiere_cambio_pwd BOOLEAN     NOT NULL DEFAULT FALSE,

    -- FHIR
    fhir_practitioner_id VARCHAR(100),

    -- Metadata
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by          UUID        REFERENCES sncev_admin.usuario(id)
);

CREATE INDEX idx_usuario_rol           ON sncev_admin.usuario(rol_id);
CREATE INDEX idx_usuario_unidad        ON sncev_admin.usuario(unidad_medica_id);
CREATE INDEX idx_usuario_jurisdiccion  ON sncev_admin.usuario(jurisdiccion_id);
CREATE INDEX idx_usuario_estado        ON sncev_admin.usuario(estado_clave);
CREATE INDEX idx_usuario_activo        ON sncev_admin.usuario(activo) WHERE activo = TRUE;

CREATE TRIGGER trg_usuario_updated_at
    BEFORE UPDATE ON sncev_admin.usuario
    FOR EACH ROW EXECUTE FUNCTION sncev.fn_set_updated_at();

COMMENT ON TABLE  sncev_admin.usuario                 IS 'Usuarios del sistema con RBAC granular. Datos sensibles cifrados.';
COMMENT ON COLUMN sncev_admin.usuario.password_hash   IS 'Bcrypt con cost=12. Nunca almacenar texto plano.';
COMMENT ON COLUMN sncev_admin.usuario.mfa_secret_enc  IS 'TOTP secret cifrado. Solo se usa en el servidor.';

-- Ahora sí agregamos las FK circulares (usuario → paciente y paciente → usuario)
ALTER TABLE sncev.paciente
    ADD CONSTRAINT fk_paciente_created_by FOREIGN KEY (created_by) REFERENCES sncev_admin.usuario(id),
    ADD CONSTRAINT fk_paciente_updated_by FOREIGN KEY (updated_by) REFERENCES sncev_admin.usuario(id);

ALTER TABLE sncev.vacuna_aplicada
    ADD CONSTRAINT fk_vacuna_aplic_aplicado_por FOREIGN KEY (aplicado_por) REFERENCES sncev_admin.usuario(id),
    ADD CONSTRAINT fk_vacuna_aplic_created_by   FOREIGN KEY (created_by)   REFERENCES sncev_admin.usuario(id);

ALTER TABLE sncev.tamiz_neonatal
    ADD CONSTRAINT fk_tamiz_realizado_por FOREIGN KEY (realizado_por) REFERENCES sncev_admin.usuario(id),
    ADD CONSTRAINT fk_tamiz_created_by    FOREIGN KEY (created_by)    REFERENCES sncev_admin.usuario(id);

ALTER TABLE sncev.somatometria
    ADD CONSTRAINT fk_somato_registrado_por FOREIGN KEY (registrado_por) REFERENCES sncev_admin.usuario(id);

ALTER TABLE sncev.desarrollo_infantil
    ADD CONSTRAINT fk_desarrollo_evaluado_por FOREIGN KEY (evaluado_por) REFERENCES sncev_admin.usuario(id);

ALTER TABLE sncev.cita_vacunacion
    ADD CONSTRAINT fk_cita_created_by FOREIGN KEY (created_by) REFERENCES sncev_admin.usuario(id);

ALTER TABLE sncev.cartilla_firmada
    ADD CONSTRAINT fk_cartilla_firmado_por FOREIGN KEY (firmado_por) REFERENCES sncev_admin.usuario(id);

-- ---------------------------------------------------------------------------
-- TABLA: Refresh Tokens (JWT rotation)
-- ---------------------------------------------------------------------------
CREATE TABLE sncev_admin.refresh_token (
    id              UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    usuario_id      UUID        NOT NULL REFERENCES sncev_admin.usuario(id) ON DELETE CASCADE,
    token_hash      CHAR(64)    NOT NULL UNIQUE,    -- SHA-256 del token real (nunca el token plano)
    familia         UUID        NOT NULL DEFAULT uuid_generate_v4(), -- para detección de reutilización
    expira_at       TIMESTAMPTZ NOT NULL,
    revocado        BOOLEAN     NOT NULL DEFAULT FALSE,
    revocado_at     TIMESTAMPTZ,
    ip_origen       INET,
    user_agent      TEXT,
    device_id       VARCHAR(100),                   -- para identificar dispositivo móvil
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_rt_usuario     ON sncev_admin.refresh_token(usuario_id);
CREATE INDEX idx_rt_familia     ON sncev_admin.refresh_token(familia);
CREATE INDEX idx_rt_expira      ON sncev_admin.refresh_token(expira_at);
-- Job de limpieza: DELETE FROM sncev_admin.refresh_token WHERE expira_at < NOW() - INTERVAL '7 days';

COMMENT ON COLUMN sncev_admin.refresh_token.familia         IS 'Todos los tokens de una sesión comparten familia. Reutilización de un revocado = revocar toda la familia (detección de robo).';
COMMENT ON COLUMN sncev_admin.refresh_token.token_hash      IS 'SHA-256 del refresh token. El token plano solo existe en el cliente.';

-- ---------------------------------------------------------------------------
-- TABLA: Bitácora de auditoría (INMUTABLE — solo INSERT)
-- ---------------------------------------------------------------------------
CREATE TABLE sncev_audit.audit_log (
    id                  UUID                    PRIMARY KEY DEFAULT uuid_generate_v4(),
    usuario_id          UUID                    REFERENCES sncev_admin.usuario(id),
    username_snapshot   VARCHAR(60),            -- copia del username al momento (el usuario puede cambiar)
    accion              sncev_admin.tipo_accion NOT NULL,
    modulo              VARCHAR(40),
    tabla_afectada      VARCHAR(100),
    registro_id         UUID,
    datos_anteriores    JSONB,                  -- snapshot BEFORE (UPDATE/DELETE)
    datos_nuevos        JSONB,                  -- snapshot AFTER  (INSERT/UPDATE)
    ip_origen           INET,
    user_agent          TEXT,
    request_id          UUID,                   -- correlación con logs del API Gateway
    resultado           VARCHAR(10) NOT NULL DEFAULT 'OK' CHECK (resultado IN ('OK','ERROR','DENEGADO')),
    detalle_error       TEXT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Solo índices de lectura — no FK salientes hacia tablas modificables para preservar integridad histórica
CREATE INDEX idx_audit_usuario     ON sncev_audit.audit_log(usuario_id);
CREATE INDEX idx_audit_accion      ON sncev_audit.audit_log(accion);
CREATE INDEX idx_audit_tabla       ON sncev_audit.audit_log(tabla_afectada);
CREATE INDEX idx_audit_registro    ON sncev_audit.audit_log(registro_id);
CREATE INDEX idx_audit_created_at  ON sncev_audit.audit_log(created_at);
CREATE INDEX idx_audit_ip          ON sncev_audit.audit_log USING GIST (ip_origen inet_ops);

-- Política de solo inserción: revocar UPDATE y DELETE a todos los roles de aplicación
-- (ejecutar con superusuario)
-- REVOKE UPDATE, DELETE ON sncev_audit.audit_log FROM sncev_app_role;

-- Row Level Security: un usuario con rol 'Ciudadano' solo puede ver sus propios registros
ALTER TABLE sncev_audit.audit_log ENABLE ROW LEVEL SECURITY;
CREATE POLICY audit_own_rows ON sncev_audit.audit_log
    USING (usuario_id = current_setting('app.current_user_id', TRUE)::UUID
           OR current_setting('app.rol_nivel', TRUE)::INT >= 5);

COMMENT ON TABLE sncev_audit.audit_log IS 'Bitácora inmutable. Solo INSERT. Cumple NOM-024 y trazabilidad FHIR AuditEvent.';

-- ---------------------------------------------------------------------------
-- Función trigger para auto-auditar cambios en vacuna_aplicada
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION sncev_audit.fn_audit_vacuna_aplicada()
RETURNS TRIGGER LANGUAGE plpgsql SECURITY DEFINER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        INSERT INTO sncev_audit.audit_log
            (usuario_id, username_snapshot, accion, modulo, tabla_afectada, registro_id, datos_nuevos)
        VALUES (
            current_setting('app.current_user_id', TRUE)::UUID,
            current_setting('app.current_username', TRUE),
            'INSERT', 'Vacunacion', 'sncev.vacuna_aplicada', NEW.id,
            to_jsonb(NEW) - 'id'
        );
    ELSIF TG_OP = 'UPDATE' THEN
        INSERT INTO sncev_audit.audit_log
            (usuario_id, username_snapshot, accion, modulo, tabla_afectada, registro_id, datos_anteriores, datos_nuevos)
        VALUES (
            current_setting('app.current_user_id', TRUE)::UUID,
            current_setting('app.current_username', TRUE),
            'UPDATE', 'Vacunacion', 'sncev.vacuna_aplicada', NEW.id,
            to_jsonb(OLD) - 'id', to_jsonb(NEW) - 'id'
        );
    END IF;
    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_audit_vacuna_aplicada
    AFTER INSERT OR UPDATE ON sncev.vacuna_aplicada
    FOR EACH ROW EXECUTE FUNCTION sncev_audit.fn_audit_vacuna_aplicada();
