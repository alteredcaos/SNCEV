# =============================================================================
# SNCEV Jobs — Dockerfile
# =============================================================================
FROM python:3.11-slim

# Dependencias del sistema para psycopg2
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Usuario sin privilegios
RUN useradd -r -s /bin/false sncev
USER sncev

EXPOSE 9090

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:9090/metrics', timeout=5)"

CMD ["python", "scheduler.py"]
