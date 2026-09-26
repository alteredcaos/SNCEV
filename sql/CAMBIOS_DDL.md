# Cambios al DDL original (verificados en PostgreSQL 16, instalación limpia sin errores)

| Archivo | Cambio | Motivo |
|---|---|---|
| 01_base_extensiones.sql | `estado.abreviatura` VARCHAR(4) → VARCHAR(6) | 'TAMPS' mide 5; el INSERT de los 32 estados abortaba completo |
| 02_pacientes_clinico.sql | `vacuna_aplicada.edad_dias_aplicacion`: columna GENERATED → INT + trigger `trg_vacuna_aplicada_edad_dias` | PostgreSQL no admite subconsultas en columnas generadas; la tabla no se creaba y fallaban ~20 objetos dependientes |
| 06_backend_ajustes.sql (nuevo) | Índice único en `curp_hash`; `updated_at` en vacuna_aplicada y cita; tabla `sync_registro` (idempotencia de /sync/push); `password_reset_token`; `export_job`; RLS de vacuna con ámbito estatal | Requerimientos del backend y huecos de las políticas originales |
| 00_instalar_todo.sql | Agrega `\i 06_backend_ajustes.sql` | — |

Uso: `psql -d sncev_db -f 00_instalar_todo.sql` (desde esta carpeta; `\i` es relativo al directorio actual).
