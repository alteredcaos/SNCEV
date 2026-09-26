# Guía de Despliegue SNCEV: Local y Servidor de Producción (Host)

Este documento explica cómo correr el sistema **SNCEV (Sistema Nacional de Cartilla Electrónica de Vacunación)** tanto en tu máquina local como en un servidor en la nube / VPS (DigitalOcean, AWS, GCP, Linode, Hetzner, etc.).

---

## 1. Resumen de Cambios Realizados (Desvinculación de Base44)

El proyecto originalmente contenía dependencias del servicio de nube **Base44** que impedían su ejecución autónoma:
- ❌ Se eliminaron los paquetes `@base44/sdk` y `@base44/vite-plugin` de `package.json`.
- ❌ Se retiró el plugin de Vite que interceptaba peticiones y obligaba a autenticar con la nube de Base44.
- ❌ Se eliminaron llamadas a `base44.app.getPublicSettings()` y `base44.auth.me()` que causaban pantallas de carga infinitas y redirecciones forzadas a servicios externos.
- ❌ Se eliminó la carpeta propietaria `frontend/base44`.
- ✅ Se creó un cliente HTTP nativo en `frontend/src/api/apiClient.js` que se comunica con el backend de FastAPI (`/api/v1`) y maneja tokens JWT de forma local en `localStorage`.
- ✅ Se configuró `frontend/src/lib/AuthContext.jsx` con modo local resiliente para que la interfaz cargue de inmediato sin bloqueos ni dependencias de nube.
- ✅ Se configuró Vite con alias `@` apuntando a `src/` y proxy local inverso hacia `http://localhost:8000`.
- ✅ Se creó un `Dockerfile` multietapa (Node.js 20 build + Nginx Alpine) y `nginx.conf` con soporte para enrutamiento SPA y proxy de API.
- ✅ Se integró el servicio `frontend` en `docker-compose.yml` para levantar todo el ecosistema con un solo comando.

---

## 2. Ejecución en Local (En tu máquina)

Tienes dos alternativas para correr el sistema en local: con Docker (la más fácil y completa) o de forma manual nativa.

---

### Opción A: Todo con Docker Compose (Recomendada)

Requiere tener **Docker** y **Docker Compose** instalados.

#### Paso 1. Configurar variables de entorno del Backend
Abre una terminal en la raíz del proyecto `/home/mrrobot/proyectos/SNCEV`:

```bash
cp sncev_api/.env.example sncev_api/.env
```

Genera las claves de cifrado necesarias para AES y Pepper ejecutando:
```bash
python3 -c "import secrets; print('AES_KEY_HEX=' + secrets.token_hex(32))"
python3 -c "import secrets; print('HASH_PEPPER_HEX=' + secrets.token_hex(32))"
```
Abre `sncev_api/.env` con tu editor y pega los dos valores generados en sus líneas correspondientes.

#### Paso 2. Levantar la base de datos PostgreSQL
El esquema SQL se cargará automáticamente la primera vez que se cree el volumen:
```bash
docker compose up -d db
docker compose logs -f db
```
Espera unos segundos hasta ver el mensaje `"database system is ready to accept connections"`, y presiona `Ctrl + C` para salir del log.

#### Paso 3. Generar las llaves criptográficas RSA (JWT y firma de cartillas)
```bash
docker compose build api
docker compose run --rm api python scripts/generar_claves.py /app/certs
```

#### Paso 4. Levantar todos los servicios (BD + API + Jobs + Frontend)
```bash
docker compose up -d
```

#### Paso 5. Crear el usuario administrador
```bash
docker compose run --rm api python -m scripts.crear_usuario \
    --username admin --email admin@salud.gob.mx --rol "Administrador Nacional"
```
*(Ingresa una contraseña segura de al menos 12 caracteres que contenga mayúsculas, minúsculas, números y símbolos)*.

#### Paso 6. Acceder al sistema
- **Frontend (Cartilla y Panel):** [http://localhost:3000](http://localhost:3000)
- **API Swagger / OpenAPI:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **Salud de la API:** [http://localhost:8000/health](http://localhost:8000/health)
- **Métricas Prometheus:** [http://localhost:9090/metrics](http://localhost:9090/metrics)

---

### Opción B: Ejecución Manual en Local (Sin Docker)

Si prefieres correr el frontend o el backend directamente en tu entorno de desarrollo:

#### 1. Base de Datos (PostgreSQL 16)
```bash
sudo -u postgres createdb sncev_db
sudo -u postgres psql -d sncev_db -f sql/00_instalar_todo.sql
```

#### 2. Backend FastAPI
```bash
cd /home/mrrobot/proyectos/SNCEV/sncev_api

# Crear entorno virtual e instalar dependencias
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configurar .env y claves
cp .env.example .env
# Generar claves AES y PEPPER y pegarlas en .env
python scripts/generar_claves.py certs
python -m scripts.crear_usuario --username admin --email admin@salud.gob.mx --rol "Administrador Nacional"

# Iniciar servidor FastAPI
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### 3. Frontend React (Vite)
Abre otra terminal:
```bash
cd /home/mrrobot/proyectos/SNCEV/frontend

# Instalar dependencias
npm install --legacy-peer-deps

# Iniciar servidor de desarrollo
npm run dev
```
La aplicación abrirá en [http://localhost:5173](http://localhost:5173). Vite reenviará automáticamente todas las llamadas `/api/*` hacia `http://localhost:8000`.

---

## 3. Despliegue en un Host / Servidor en la Nube (Producción / VPS)

Para montar el proyecto en un servidor remoto (Ubuntu 22.04 o 24.04 LTS en DigitalOcean, AWS EC2, Hetzner, etc.):

### Paso 1. Preparar el servidor
En tu servidor remoto, actualiza los paquetes e instala Docker:
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y curl git ufw

# Instalar Docker oficial
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
newgrp docker
```

### Paso 2. Clonar el repositorio en el servidor
```bash
git clone <URL_DE_TU_REPOSITORIO> /opt/sncev
cd /opt/sncev
```

### Paso 3. Asegurar variables de entorno para Producción
En un servidor expuesto a internet, **NUNCA** uses contraseñas por defecto:

1. Edita `sncev_api/.env`:
   - `ENVIRONMENT=produccion`
   - `OPENAPI_URL=` (deja vacío para deshabilitar `/docs` públicos en producción si se requiere).
   - `ALLOWED_HOSTS=["tu-dominio.gob.mx", "localhost"]`
   - `CORS_ORIGINS=["https://tu-dominio.gob.mx"]`
   - `TRUST_FORWARDED_FOR=true`
   - `POSTGRES_PASSWORD`: contraseña segura para el superusuario.
   - `SNCEV_APP_DB_PASSWORD`: contraseña segura para el rol `sncev_app`.
   - `AES_KEY_HEX` y `HASH_PEPPER_HEX`: generadas con `python3 -c "import secrets; print(secrets.token_hex(32))"`.

2. En `docker-compose.yml`, para mayor seguridad en producción, **no expongas el puerto 5432 ni el 8000 al público**; déjalos solo accesibles en la red interna de Docker, exponiendo únicamente el Frontend (puerto 80 y 443 a través de Nginx o un proxy inverso).

### Paso 4. Desplegar los contenedores
```bash
# 1. Base de datos
docker compose up -d db

# 2. Generar claves criptográficas RSA dentro del volumen de producción
docker compose build api
docker compose run --rm api python scripts/generar_claves.py /app/certs

# 3. Levantar todo el stack
docker compose up -d --build

# 4. Crear el usuario Administrador Nacional
docker compose run --rm api python -m scripts.crear_usuario \
    --username admin --email admin@tu-dominio.gob.mx --rol "Administrador Nacional"
```

---

### Paso 5. Configurar Dominio y Certificados SSL (HTTPS) con Nginx y Let's Encrypt

Para que el sistema funcione bajo HTTPS (`https://tu-dominio.gob.mx`):

1. **Instalar Nginx y Certbot en el host:**
   ```bash
   sudo apt install -y nginx certbot python3-certbot-nginx
   ```

2. **Crear archivo de configuración en `/etc/nginx/sites-available/sncev`:**
   ```nginx
   server {
       server_name tu-dominio.gob.mx;

       # Frontend (React servido en el puerto 3000 por Docker)
       location / {
           proxy_pass http://127.0.0.1:3000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }

       # Backend API (puerto 8000 de FastAPI)
       location /api/ {
           proxy_pass http://127.0.0.1:8000/api/;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
           proxy_read_timeout 90;
       }

       # Endpoint de verificación pública de cartillas QR
       location /cartilla/verificar/ {
           proxy_pass http://127.0.0.1:8000/cartilla/verificar/;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
   }
   ```

3. **Habilitar el sitio y generar el certificado SSL gratuito:**
   ```bash
   sudo ln -s /etc/nginx/sites-available/sncev /etc/nginx/sites-enabled/
   sudo nginx -t
   sudo systemctl reload nginx

   # Obtener certificado SSL gratuito de Let's Encrypt
   sudo certbot --nginx -d tu-dominio.gob.mx
   ```
   Certbot configurará automáticamente la renovación periódica y el cifrado HTTPS (puerto 443).

4. **Configurar el Firewall (UFW):**
   ```bash
   sudo ufw allow OpenSSH
   sudo ufw allow 'Nginx Full'
   sudo ufw enable
   ```

---

## 4. Mantenimiento y Respaldos

- **Ver el estado de los contenedores:**
  ```bash
  docker compose ps
  ```

- **Ver logs en tiempo real:**
  ```bash
  docker compose logs -f frontend
  docker compose logs -f api
  docker compose logs -f db
  ```

- **Hacer un respaldo de la Base de Datos:**
  ```bash
  docker compose exec -t db pg_dump -U postgres sncev_db > backup_sncev_$(date +%Y%m%d_%H%M%S).sql
  ```

- **Restaurar un respaldo:**
  ```bash
  docker compose exec -T db psql -U postgres sncev_db < backup_sncev_XXXXXX.sql
  ```

- **Actualizar a una nueva versión:**
  ```bash
  git pull
  docker compose up -d --build
  ```
