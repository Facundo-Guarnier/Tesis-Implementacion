# docker build -f docker/decision-agent/Dockerfile -t traffic-decision-agent .
# docker run --rm --name traffic-decision-agent -v ${PWD}/config.yaml:/app/config.yaml -v ${PWD}/assets:/app/assets -v ${PWD}/logs:/app/logs -v ${PWD}/results:/app/results -p 8080:8080 traffic-decision-agent

# Dockerfile para Decision Agent (DQN)
FROM python:3.11-slim

# Metadatos del contenedor
LABEL maintainer="fj.guarnier@alumno.um.edu.ar"
LABEL description="Servicio DQN para toma de decisiones de semáforos inteligentes"
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
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Crear directorio de trabajo
WORKDIR /app

# Copiar archivos de dependencias
COPY requirements-decision.txt ./

# Instalar dependencias de Python
RUN pip install --no-cache-dir -r requirements-decision.txt

# Copiar código fuente
COPY src/ ./src/
COPY run_decision_agent.py ./
COPY config.yaml ./

# Crear directorio para modelos DQN
RUN mkdir -p assets/dqn_models

# Crear directorio para logs
RUN mkdir -p logs/services

# Configurar usuario no-root para seguridad
RUN groupadd -r dqnuser && useradd -r -g dqnuser dqnuser
RUN chown -R dqnuser:dqnuser /app
USER dqnuser

# Exponer puerto para health endpoint
EXPOSE 8080

# Comando por defecto
CMD ["python", "run_decision_agent.py"]
