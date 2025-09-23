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

# Terminal 5 (opcional): Frontend web de configuración
poetry run streamlit run run_frontend.py
```

#### Frontend de Configuración

El sistema incluye una **interfaz web moderna** basada en Streamlit para gestión completa del sistema:

```bash
# Iniciar frontend de configuración
poetry run streamlit run run_frontend.py
```

**🌐 Accede a la interfaz en:** http://localhost:8501

**🗂️ Pestañas del Frontend:**
- 🔧 **Servicios**: Control y monitoreo de microservicios en tiempo real
  - Iniciar/detener servicios individuales
  - Visualización de logs con auto-refresh configurable
  - Monitoreo de estado, PID y tiempo de ejecución
- ⚙️ **Configuración**: Editor visual avanzado de config.yaml
  - Validación en tiempo real con Pydantic
  - Widgets inteligentes específicos por tipo de dato
  - Tooltips explicativos y manejo robusto de errores
- 🧪 **API Testing**: Interface para probar endpoints REST
  - Testing de disponibilidad de microservicios
  - Historial de requests y respuestas formateadas
  - Configuración de URL base personalizable
- ⚠️ **Alertas**: Visualización de base de datos de congestión
  - Análisis de alertas SQLite con filtros avanzados
  - Gráficos temporales de tiempos de espera y vehículos
  - Exportación de datos para análisis externo
- 📊 **Métricas**: Comparaciones de rendimiento del sistema
  - Análisis comparativo DQN vs tiempo fijo
  - Métricas de entrenamiento y convergencia
  - Reportes estadísticos detallados

**✨ Características Avanzadas:**
- ✅ **Validación en tiempo real** con modelos Pydantic
- � **Monitoreo avanzado** de recursos y estado de servicios
- � **Auto-refresh** configurable para logs y métricas
- � **Exportación de datos** en formatos CSV y gráficos
- 🎛️ **Widgets inteligentes** que se adaptan al tipo de configuración
- � **Detección automática** de errores y problemas de servicios

Para más detalles, consulta la [documentación completa](docs/)

## 📦 Gestión de Dependencias

### Poetry (Desarrollo Local)

```bash
# Añadir nueva dependencia
poetry add <package_name>

# Añadir dependencia de desarrollo
poetry add --group dev <package_name>

# Actualizar todas las dependencias
poetry update

# Instalar dependencias exactas del proyecto
poetry install
```

### Docker (Servicios Específicos)

Para optimizar las imágenes Docker, cada servicio tiene su archivo de dependencias específico:

- **`requirements-docker.txt`**: Dependencias completas para servicios que requieren ML/CV (legacy)
- **`requirements-decision.txt`**: Dependencias específicas para el agente de decisión DQN
- **`requirements-reporting.txt`**: Dependencias mínimas para el servicio de reportes

**Agregar dependencia a un servicio Docker:**

1. **Editar el archivo de requirements correspondiente**:
   ```bash
   # Para decision service (DQN)
   echo "nueva_libreria>=1.0.0" >> requirements-decision.txt

   # Para reporting service
   echo "nueva_libreria>=1.0.0" >> requirements-reporting.txt

   # Para servicios con ML/CV completos (legacy)
   echo "nueva_libreria>=1.0.0" >> requirements-docker.txt
   ```

2. **Reconstruir la imagen Docker**:
   ```bash
   # Decision Agent
   docker build -t traffic-decision-agent docker/decision-agent/

   # Reporting Service
   docker build -t traffic-reporting-service docker/reporting-service/
   ```Para más detalles sobre gestión de dependencias, consulta [`docs/dependency-management.md`](docs/dependency-management.md)
