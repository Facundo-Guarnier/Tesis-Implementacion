<p align="center">
    <img src="./docs/assets/um_emblem.png" alt="Universidad de Mendoza: Ingeniería" width="180"/>
</p>

# Trabajo Final Integrador de Grado

## INGENIERÍA EN INFORMÁTICA

## Facundo Guarnier

### Sistema de Semáforos Inteligentes

**2024 - Mendoza, Argentina**

**Asesor Especialista: Ignacio Bosch**

## Resumen

Este repositorio contiene el Trabajo Final de Grado "Sistema de semáforos inteligentes", que aborda la congestión vehicular en las intersecciones de la calle Rondeau/Arenales con el Acceso Este en Guaymallén, Mendoza. El proyecto propone un sistema de semáforos inteligentes para optimizar el flujo de tráfico, reducir tiempos de espera y mejorar la eficiencia vehicular.

El sistema se basa en una arquitectura que integra la detección de vehículos con YOLOv8, la simulación de tráfico con SUMO, y la toma de decisiones mediante una red neuronal Deep Q-Network (DQN) entrenada en un entorno de simulación. Los resultados demuestran que el sistema supera a los semáforos de tiempo fijo, logrando una mayor fluidez del tráfico y reducción de demoras, tanto en condiciones normales como de alto volumen vehicular.

## Tecnologías utilizadas

- **Python**: Lenguaje principal del proyecto.
- **Poetry**: Gestor moderno de dependencias y entornos virtuales.
- **YOLOv8**: Modelo de detección de objetos para identificar vehículos en video.
- **SUMO**: Simulador de tráfico para modelar y evaluar el sistema de semáforos.
- **TensorFlow**: Framework de aprendizaje profundo utilizado para entrenar la red neuronal DQN.
- **Deep Q-Network (DQN)**: Algoritmo de aprendizaje por refuerzo para la toma de decisiones en tiempo real.
- **OpenCV**: Biblioteca para procesamiento de imágenes y video.
- **Git**: Control de versiones para gestionar el código fuente.
- **Visual Studio Code**: Entorno de desarrollo integrado (IDE) utilizado para el desarrollo del proyecto.
- **Pre-commit**: Hooks automáticos para mantener la calidad del código con Black, Ruff y Mypy.

## 🚀 Inicio Rápido

### Configuración del Entorno

1. **Instalar Poetry**:

```bash
# Windows (PowerShell)
(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | python -

# Linux/macOS
curl -sSL https://install.python-poetry.org | python3 -
```

2. **Configurar el proyecto**:

```bash
# Instalar todas las dependencias
poetry install

# Ver el entorno virtual creado
poetry env list --full-path

# Activar entorno virtual
poetry shell
# o
poetry env activate <path_to_virtual_env>

# Instalar hooks de pre-commit
poetry run pre-commit install
```

### Ejecución del Sistema

#### Servicios Principales

```bash
# Terminal 1: Iniciar simulación
poetry run python run_simulation_provider.py

# Terminal 2: Iniciar agente de decisión
poetry run python run_decision_agent.py

# Terminal 3 (opcional): Iniciar detección
poetry run python run_detection_provider.py

# Terminal 4 (opcional): Iniciar reportes
poetry run python run_reporting_service.py
```

#### Frontend de Configuración

El sistema incluye una interfaz web moderna para gestionar la configuración y servicios:

```bash
# Iniciar frontend de configuración
poetry run streamlit run run_frontend.py
```

**Accede a la interfaz en:** http://localhost:8501

**Funcionalidades del Frontend:**
- 🏠 **Dashboard**: Métricas del sistema y estado general
- ⚙️ **Configuración**: Editor visual con validación en tiempo real
- 🔧 **Servicios**: Control y monitoreo de microservicios
- 📦 **Backups**: Gestión de copias de seguridad automáticas

**Características Avanzadas:**
- ✅ Validación en tiempo real con Pydantic
- 🔄 Sistema de backups automáticos antes de cambios
- 📊 Monitoreo de rendimiento y alertas
- 🚨 Detección de crashes de servicios
- 📋 Log de auditoría de cambios
- 🔒 Validación de seguridad en operaciones de archivos

Para más detalles, consulta la [documentación completa](docs/)
