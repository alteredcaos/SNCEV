-- =============================================================================
-- SNCEV — DDL Módulo 07
-- Permisos del módulo de inventario de lotes (06_inventario_lotes.sql).
-- Archivo separado porque el catálogo de permisos vive en 03_usuarios_seguridad.sql,
-- ya ejecutado en instalaciones existentes — este módulo solo agrega, no reemplaza.
--
-- Se ejecuta DESPUÉS de 06 (00_instalar_todo.sql lo incluye como Paso 7).
-- Idempotente: seguro de re-ejecutar.
-- =============================================================================

SET search_path TO sncev_admin, sncev, public;

INSERT INTO sncev_admin.permiso (codigo, modulo, descripcion) VALUES
    ('INVENTARIO_VER',            'Inventario', 'Consultar existencias y trazabilidad de lotes'),
    ('INVENTARIO_ENTRADA',        'Inventario', 'Registrar la entrada de un lote nuevo al almacén de la unidad'),
    ('INVENTARIO_CERRAR_FRASCO',  'Inventario', 'Cerrar un frasco multidosis abierto y registrar su merma'),
    ('INVENTARIO_BAJA',           'Inventario', 'Dar de baja un lote completo por incidencia (rotura, cadena de frío, caducidad)')
ON CONFLICT (codigo) DO NOTHING;

DO $$
DECLARE
    v_coord  INT := (SELECT id FROM sncev_admin.rol WHERE nombre = 'Coordinador Jurisdiccional');
    v_medico INT := (SELECT id FROM sncev_admin.rol WHERE nombre = 'Médico');
    v_enf    INT := (SELECT id FROM sncev_admin.rol WHERE nombre = 'Enfermera/Vacunador');
    v_analist INT := (SELECT id FROM sncev_admin.rol WHERE nombre = 'Analista Epidemiólogo');
BEGIN
    -- Coordinador Jurisdiccional y Médico: operan el almacén completo de su unidad/jurisdicción
    INSERT INTO sncev_admin.rol_permiso (rol_id, permiso_id)
    SELECT r, p.id
      FROM unnest(ARRAY[v_coord, v_medico]) AS r
      CROSS JOIN sncev_admin.permiso p
     WHERE p.codigo IN ('INVENTARIO_VER', 'INVENTARIO_ENTRADA', 'INVENTARIO_CERRAR_FRASCO', 'INVENTARIO_BAJA')
    ON CONFLICT (rol_id, permiso_id) DO NOTHING;

    -- Enfermera/Vacunador: aplica dosis y cierra su propio frasco al final de jornada,
    -- pero no da de alta lotes nuevos ni los da de baja (reservado a nivel 3+)
    INSERT INTO sncev_admin.rol_permiso (rol_id, permiso_id)
    SELECT v_enf, p.id FROM sncev_admin.permiso p
     WHERE p.codigo IN ('INVENTARIO_VER', 'INVENTARIO_CERRAR_FRASCO')
    ON CONFLICT (rol_id, permiso_id) DO NOTHING;

    -- Analista Epidemiólogo: solo lectura, para cruzar mermas con cobertura
    INSERT INTO sncev_admin.rol_permiso (rol_id, permiso_id)
    SELECT v_analist, p.id FROM sncev_admin.permiso p
     WHERE p.codigo = 'INVENTARIO_VER'
    ON CONFLICT (rol_id, permiso_id) DO NOTHING;
END $$;

-- Administrador Nacional y Administrador Estatal: en 03_usuarios_seguridad.sql su asignación
-- fue un SELECT de una sola vez al momento de la instalación original ("todos los permisos que
-- existían entonces"), no una regla que se aplique sola a los permisos creados después. Por eso
-- hay que dárselos aquí explícitamente, igual que a los demás roles:
INSERT INTO sncev_admin.rol_permiso (rol_id, permiso_id)
SELECT (SELECT id FROM sncev_admin.rol WHERE nombre = 'Administrador Estatal'), p.id
  FROM sncev_admin.permiso p
 WHERE p.codigo IN ('INVENTARIO_VER', 'INVENTARIO_ENTRADA', 'INVENTARIO_CERRAR_FRASCO', 'INVENTARIO_BAJA')
ON CONFLICT (rol_id, permiso_id) DO NOTHING;

INSERT INTO sncev_admin.rol_permiso (rol_id, permiso_id)
SELECT (SELECT id FROM sncev_admin.rol WHERE nombre = 'Administrador Nacional'), p.id
  FROM sncev_admin.permiso p
 WHERE p.codigo IN ('INVENTARIO_VER', 'INVENTARIO_ENTRADA', 'INVENTARIO_CERRAR_FRASCO', 'INVENTARIO_BAJA')
ON CONFLICT (rol_id, permiso_id) DO NOTHING;

DO $$
BEGIN
    RAISE NOTICE '============================================';
    RAISE NOTICE 'SNCEV — Módulo 07 (permisos de inventario) instalado';
    RAISE NOTICE '  Permisos INVENTARIO_*: %', (SELECT COUNT(*) FROM sncev_admin.permiso WHERE modulo = 'Inventario');
    RAISE NOTICE '============================================';
END $$;
