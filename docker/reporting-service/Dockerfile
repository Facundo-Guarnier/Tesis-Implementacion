# docker build --no-cache -f docker/reporting-service/Dockerfile -t traffic-reporting-service:v2 .
# docker run --name traffic-reporting-service -v ${PWD}/config.yaml:/app/config.yaml -v ${PWD}/results:/app/results -v ${PWD}/logs:/app/logs -p 8081:8081 traffic-reporting-service:v2
# Dockerfile para Reporting Service
FROM python:3.11-slim

# Metadatos del contenedor
LABEL maintainer="fj.guarnier@alumno.um.edu.ar"
LABEL description="Servicio de reportes y métricas para sistema de semáforos inteligentes"
LABEL version="1.0.0"

# Variables de entorno básicas
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV POETRY_NO_INTERACTION=1
ENV POETRY_VIRTUALENVS_CREATE=false
ENV POETRY_CACHE_DIR=/tmp/poetry_cache

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    curl \
    sqlite3 \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Crear directorio de trabajo
WORKDIR /app

# Copiar archivos de dependencias
COPY requirements-reporting.txt ./

# Instalar dependencias de Python
RUN pip install --no-cache-dir -r requirements-reporting.txt

# Copiar código fuente
COPY src/ ./src/
COPY run_reporting_service.py ./
COPY config.yaml ./

# Crear directorios necesarios
RUN mkdir -p results/reportes/db
RUN mkdir -p logs/services

# Configurar usuario no-root para seguridad
RUN groupadd -r reportuser && useradd -r -g reportuser reportuser
RUN chown -R reportuser:reportuser /app
USER reportuser

# Exponer puerto para health endpoint
EXPOSE 8081

# Comando por defecto
CMD ["python", "run_reporting_service.py"]
