# SNCEV — Sistema Nacional de Cartilla Electrónica de Vacunación

Backend FastAPI + base de datos PostgreSQL para el proyecto SNCEV: registro de
pacientes, aplicación de vacunas, cartilla electrónica firmada digitalmente,
citas, reportes de cobertura, sincronización offline (app móvil) e
interoperabilidad FHIR R4 básica.

## Arranque rápido con Docker (recomendado)

Requiere Docker y Docker Compose instalados (`docker compose version`).

```bash
# 1. Configurar variables de entorno de la API
cp sncev_api/.env.example sncev_api/.env

# 2. Generar las claves de cifrado (AES) y pegarlas en sncev_api/.env
python3 -c "import secrets; print('AES_KEY_HEX=' + secrets.token_hex(32))"
python3 -c "import secrets; print('HASH_PEPPER_HEX=' + secrets.token_hex(32))"
#   -> Editar sncev_api/.env y pegar ambos valores

# 3. Levantar la base de datos primero (el DDL se carga solo, una vez, al crear el volumen)
docker compose up -d db
docker compose logs -f db     # esperar a "database system is ready to accept connections"

# 4. Generar el par de llaves RSA (JWT y firma de cartillas)
docker compose build api
docker compose run --rm api python scripts/generar_claves.py /app/certs

# 5. Levantar todo
docker compose up -d

# 6. Crear el primer usuario administrador
docker compose run --rm api python -m scripts.crear_usuario \
    --username admin --email admin@salud.gob.mx --rol "Administrador Nacional"
#   (pedirá la contraseña inicial por teclado; mínimo 12 caracteres, mayúscula, número y símbolo)

# 7. Probar
open http://localhost:3000        # Interfaz web React (Cartilla Electrónica)
open http://localhost:8000/docs   # Swagger UI de la API FastAPI
curl http://localhost:8000/health
```

El Frontend web queda en `http://localhost:3000`, la API en `http://localhost:8000`,
PostgreSQL expuesto en `localhost:5432` (usuario `postgres` / la contraseña de
`POSTGRES_SUPERUSER_PASSWORD` en el compose, por defecto `postgres_local_only` —
**cambiarla si el puerto queda accesible desde fuera de tu máquina**), y las métricas
del job nocturno en `http://localhost:9090/metrics`.

### Reiniciar desde cero

El DDL solo se carga la primera vez que se crea el volumen `sncev_db_data`. Para
reinstalar desde cero (se pierden los datos):

```bash
docker compose down -v
docker compose up -d db
```

## Arranque sin Docker (Ubuntu, para desarrollo)

```bash
# PostgreSQL 16 instalado y corriendo localmente
sudo -u postgres createdb sncev_db
sudo -u postgres psql -d sncev_db -f sql/00_instalar_todo.sql

cd sncev_api
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
python3 -c "import secrets; print('AES_KEY_HEX=' + secrets.token_hex(32))"
python3 -c "import secrets; print('HASH_PEPPER_HEX=' + secrets.token_hex(32))"
# pegar ambos en .env; ajustar DATABASE_URL a 127.0.0.1

python scripts/generar_claves.py certs
python -m scripts.crear_usuario --username admin --email admin@salud.gob.mx --rol "Administrador Nacional"

uvicorn app.main:app --reload --port 8000
```

WeasyPrint (generación de PDF de la cartilla) requiere librerías del sistema en
Ubuntu: `sudo apt install libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf2.0-0 libcairo2`.

## Estructura del repositorio

```
sql/            DDL de PostgreSQL (00 a 04 son el diseño original; 06 son los
                ajustes y correcciones que requirió el backend — ver CAMBIOS_DDL.md)
sncev_api/      Backend FastAPI (la API REST + FHIR)
sncev_jobs/     Job nocturno que recalcula sncev_report.cobertura_vacunacion
observabilidad/ Configuración de Prometheus
docker-compose.yml
```

Dentro de `sncev_api/app/`:

```
core/        configuración, seguridad (JWT/bcrypt/TOTP/AES), errores, storage, firma
db/          sesión SQLAlchemy async + contexto de Row-Level Security
models/      modelos SQLAlchemy (espejo exacto del DDL, verificado columna por columna)
schemas/     esquemas Pydantic (contrato de la API)
middleware/  autenticación JWT, permisos (RBAC), bitácora de auditoría
services/    toda la lógica de negocio, por módulo
api/v1/endpoints/  los endpoints HTTP (delgados: validan permisos y llaman al servicio)
fhir/        mapeo a recursos FHIR R4
cartilla/    plantilla Jinja2 + render a PDF con WeasyPrint
```

## Qué cubre esta entrega

Todos los módulos del contrato (`sql/05_api_rest_fhir.yaml`): autenticación
(login, MFA/TOTP, refresh con rotación y detección de reutilización, cambio y
restablecimiento de contraseña), pacientes y responsables, vacunación
(aplicar/editar/invalidar/pendientes), clínico (somatometría, tamizajes,
desarrollo), citas, catálogos, cartilla electrónica (PDF firmado con RSA +
verificación pública por QR), reportes de cobertura (por AGEB/municipio/
jurisdicción/estado, tendencia, mapa, trazabilidad de lote, rezago,
exportación asíncrona a CSV/XLSX), administración de usuarios/roles/permisos,
consulta de auditoría, sincronización offline con idempotencia, y FHIR R4
(Patient, Immunization, ImmunizationRecommendation, Observation, AuditEvent,
CapabilityStatement).

## Limitaciones conocidas / siguientes pasos

- **FHIR** tiene alcance pragmático, no 100% conformante al estándar (sin
  `_include`, sin validación de perfiles, terminologías parciales). Ver el
  encabezado de `app/fhir/mappers.py`.
- **`sncev_jobs`** se incluye tal como venía en el proyecto original; no fue
  auditado línea por línea en esta entrega (solo se corrigió el bug de la
  función SQL `fn_calcular_cobertura` que él invoca — ver `sql/CAMBIOS_DDL.md`).
  Antes de operarlo en producción, revisar `sncev_jobs/scheduler.py` y los
  workers de la misma forma en que se auditó `sncev_api`.
- **Notificaciones por correo** (`app/core/notificaciones.py`) solo registran
  en el log; falta conectar un proveedor SMTP real para que
  `/auth/forgot-password` envíe correos de verdad.
- **Almacenamiento de archivos** (`app/core/storage.py`) es local en disco con
  URLs firmadas; para producción con más de una instancia de la API, sustituir
  por S3 (la interfaz ya está pensada para eso).
- El **rate limiting** de `app/middleware/request_id.py` es en memoria (por
  proceso); con más de un contenedor de la API replicado, cada uno lleva su
  propio conteo. Para producción con réplicas, mover a Redis o al gateway.
- Falta correr un smoke-test end-to-end automatizado (login → paciente →
  vacuna → cartilla → verificación QR → sync). El flujo se probó por partes
  contra PostgreSQL real durante el desarrollo, pero no de punta a punta con
  el servidor HTTP levantado.

## Seguridad — antes de producción

- Cambiar la contraseña del rol `sncev_app` (hoy `CAMBIAR_EN_PRODUCCION` tanto
  en `sql/04_reportes_vistas_rls.sql` como en el `.env`/compose) y la del
  superusuario de PostgreSQL.
- `AES_KEY_HEX` y `HASH_PEPPER_HEX` no deben regenerarse una vez que haya datos
  cifrados/hasheados con ellas (los datos existentes quedarían ilegibles).
  Guardarlas en un gestor de secretos, no en el `.env` del repositorio.
- Las llaves en `certs/` (JWT y firma de cartillas) tampoco deben regenerarse
  con datos en producción sin un plan de rotación.
