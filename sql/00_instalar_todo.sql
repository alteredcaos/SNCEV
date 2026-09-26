-- =============================================================================
-- SNCEV — Script maestro de instalación
-- Ejecutar como superusuario en PostgreSQL 15+
-- Orden de ejecución obligatorio (dependencias entre módulos)
-- =============================================================================

-- Paso 0: Crear base de datos (ejecutar fuera de una transacción)
-- CREATE DATABASE sncev_db
--     WITH ENCODING='UTF8'
--     LC_COLLATE='es_MX.UTF-8'
--     LC_CTYPE='es_MX.UTF-8'
--     TEMPLATE=template0;
-- \c sncev_db

-- Paso 1: Catálogos base, extensiones y geografía
\ir 01_base_extensiones.sql

-- Paso 2: Entidades clínicas (pacientes, vacunas, datos de cartilla)
\ir 02_pacientes_clinico.sql

-- Paso 3: Usuarios, seguridad, auditoría
\ir 03_usuarios_seguridad.sql

-- Paso 4: Reportes, vistas, RLS y permisos de BD
\ir 04_reportes_vistas_rls.sql

-- Paso 5: Ajustes requeridos por el backend FastAPI
\ir 06_backend_ajustes.sql

-- Verificación post-instalación
DO $$
DECLARE
    v_tablas INT;
    v_vistas INT;
    v_vacunas INT;
    v_esquemas INT;
    v_roles INT;
BEGIN
    SELECT COUNT(*) INTO v_tablas
    FROM information_schema.tables
    WHERE table_schema IN ('sncev','sncev_admin','sncev_geo','sncev_audit','sncev_report')
      AND table_type = 'BASE TABLE';

    SELECT COUNT(*) INTO v_vistas
    FROM information_schema.views
    WHERE table_schema IN ('sncev','sncev_report');

    SELECT COUNT(*) INTO v_vacunas  FROM sncev.vacuna_catalogo;
    SELECT COUNT(*) INTO v_esquemas FROM sncev.esquema_vacunacion;
    SELECT COUNT(*) INTO v_roles    FROM sncev_admin.rol;

    RAISE NOTICE '============================================';
    RAISE NOTICE 'SNCEV — Instalación completada';
    RAISE NOTICE '  Tablas creadas:    %', v_tablas;
    RAISE NOTICE '  Vistas creadas:    %', v_vistas;
    RAISE NOTICE '  Vacunas catálogo:  %', v_vacunas;
    RAISE NOTICE '  Esquemas vacu.:    %', v_esquemas;
    RAISE NOTICE '  Roles del sistema: %', v_roles;
    RAISE NOTICE '============================================';
    RAISE NOTICE 'IMPORTANTE: Cambiar contraseña del rol sncev_app en producción.';
    RAISE NOTICE 'IMPORTANTE: Configurar clave AES-256 en Azure Key Vault.';
    RAISE NOTICE 'IMPORTANTE: Cargar catálogo de municipios (2456 registros).';
    RAISE NOTICE 'IMPORTANTE: Cargar catálogo de AGEBs INEGI.';
END $$;
