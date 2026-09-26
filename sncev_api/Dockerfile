# =============================================================================
# SNCEV API — imagen de la aplicación FastAPI
# =============================================================================
FROM python:3.11-slim

# Dependencias de sistema requeridas por WeasyPrint (renderizado de la cartilla a PDF)
RUN apt-get update && apt-get install -y --no-install-recommends \
        libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf2.0-0 libffi-dev \
        libcairo2 libjpeg62-turbo shared-mime-info fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY scripts ./scripts

RUN mkdir -p /app/storage /app/certs && \
    useradd --create-home --uid 1000 sncev && \
    chown -R sncev:sncev /app
USER sncev

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request as u; u.urlopen('http://127.0.0.1:8000/health', timeout=3)" || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
