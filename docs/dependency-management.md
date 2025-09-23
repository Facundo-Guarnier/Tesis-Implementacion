# 📦 Gestión de Dependencias - Guía Completa

Esta guía cubre la gestión de dependencias para el proyecto de Sistema de Semáforos Inteligentes, tanto para desarrollo local con Poetry como para despliegue con Docker.

## 📑 Índice

- [Arquitectura de Dependencias](#arquitectura-de-dependencias)
- [Poetry (Desarrollo Local)](#poetry-desarrollo-local)
- [Docker (Servicios Específicos)](#docker-servicios-específicos)
- [Archivos de Requirements](#archivos-de-requirements)
- [Flujo de Trabajo](#flujo-de-trabajo)
- [Troubleshooting](#troubleshooting)

## 🏗️ Arquitectura de Dependencias

El proyecto utiliza una arquitectura modular de dependencias:

```
Sistema de Dependencias
├── pyproject.toml & poetry.lock    # Poetry - Desarrollo completo
├── requirements-docker.txt         # Docker - Servicios ML/CV completos (legacy)
├── requirements-decision.txt       # Docker - Decision Agent DQN optimizado
└── requirements-reporting.txt      # Docker - Reporting Service optimizado
```

### Servicios y Sus Dependencias

| Servicio | Archivo de Dependencias | Principales Librerías |
|----------|------------------------|-----------------------|
| **Decision Agent** | `requirements-decision.txt` | TensorFlow, NumPy, Requests |
| **Detection Provider** | `requirements-docker.txt` | YOLOv8, OpenCV, Supervision |
| **Simulation Provider** | Local (Poetry) | SUMO, Requests, Flask |
| **Reporting Service** | `requirements-reporting.txt` | Requests, Pydantic, PyYAML |
| **Frontend** | Local (Poetry) | Streamlit, Plotly, Pandas |

## 🎭 Poetry (Desarrollo Local)

### Comandos Básicos

```bash
# Instalar todas las dependencias del proyecto
poetry install

# Añadir nueva dependencia de producción
poetry add <package_name>

# Añadir dependencia con versión específica
poetry add "package_name>=1.2.0,<2.0.0"

# Añadir dependencia de desarrollo
poetry add --group dev <package_name>

# Actualizar dependencias
poetry update

# Actualizar dependencia específica
poetry update <package_name>

# Mostrar dependencias instaladas
poetry show

# Mostrar árbol de dependencias
poetry show --tree
```

### Gestión de Grupos

```bash
# Instalar solo dependencias de producción
poetry install --without dev

# Instalar dependencias específicas de un grupo
poetry install --with dev

# Añadir a grupo específico
poetry add --group ml tensorflow
```

### Manejo de Entornos Virtuales

```bash
# Activar entorno virtual
poetry shell

# Ejecutar comando en el entorno
poetry run python script.py

# Ver información del entorno
poetry env info

# Eliminar entorno virtual
poetry env remove <python_version>
```

## 🐳 Docker (Servicios Específicos)

### Archivos de Requirements

#### `requirements-docker.txt` (Completo)
Para servicios que requieren ML/CV (Decision Agent, Detection Provider):

```txt
requests>=2.31.0
pyyaml>=6.0
flask>=2.3.0
numpy>=1.24.0,<2.0
opencv-python>=4.8.0
pillow>=10.0.0
matplotlib>=3.7.0
pydantic>=2.11.7
tensorflow[and-cuda]==2.19.0
psutil>=7.0.0
pandas>=2.3.1
scipy>=1.16.0
supervision>=0.26.1
ultralytics>=8.3.177
streamlit>=1.28.0
streamlit-autorefresh>=1.0.1
plotly>=6.3.0
```

#### `requirements-decision.txt` (Optimizado para DQN)
Para el agente de decisión DQN (solo dependencias necesarias):

```txt
tensorflow[and-cuda]==2.19.0
numpy>=1.24.0,<2.0
requests>=2.31.0
pyyaml>=6.0
pydantic>=2.11.7
psutil>=7.0.0
```

#### `requirements-reporting.txt` (Optimizado)
Para el servicio de reportes (solo dependencias necesarias):

```txt
requests>=2.31.0
pyyaml>=6.0
pydantic>=2.11.7
psutil>=7.0.0
```

### Comandos Docker

```bash
# Construir imagen con requirements específicos
docker build -t traffic-reporting-service docker/reporting-service/

# Construir imagen del decision agent
docker build -t traffic-decision-agent docker/decision-agent/

# Ejecutar contenedor con volúmenes
docker run -v $(pwd)/config.yaml:/app/config.yaml traffic-reporting-service
```

## 📋 Archivos de Requirements

### Estructura de Archivos

```
Proyecto/
├── pyproject.toml                  # Poetry principal
├── poetry.lock                     # Lock file de Poetry
├── requirements-docker.txt         # Dependencias completas para Docker (legacy)
├── requirements-decision.txt       # Dependencias optimizadas para decision agent
├── requirements-reporting.txt      # Dependencias optimizadas para reporting
└── requirements.txt                # Dependencias básicas (legacy)
```

### Generación desde Poetry

```bash
# Exportar dependencias de Poetry a requirements.txt
poetry export -f requirements.txt --output requirements.txt

# Exportar solo dependencias de producción
poetry export -f requirements.txt --output requirements.txt --without dev

# Exportar con hashes para seguridad
poetry export -f requirements.txt --output requirements.txt --with-credentials
```

## 🔄 Flujo de Trabajo

### Agregar Nueva Dependencia

#### 1. Para Desarrollo Local

```bash
# 1. Añadir con Poetry
poetry add nueva_libreria

# 2. Verificar que funciona
poetry run python -c "import nueva_libreria; print('OK')"

# 3. Commit los cambios
git add pyproject.toml poetry.lock
git commit -m "feat: add nueva_libreria dependency"
```

#### 2. Para Servicio Docker (Decision Agent)

```bash
# 1. Editar requirements-decision.txt
echo "nueva_libreria>=1.0.0" >> requirements-decision.txt

# 2. Probar localmente si es posible
poetry add nueva_libreria

# 3. Reconstruir imagen Docker
docker build -t traffic-decision-agent docker/decision-agent/

# 4. Probar la imagen
docker run traffic-decision-agent python -c "import nueva_libreria; print('OK')"
```

#### 3. Para Servicio Docker (ML/CV Legacy)

```bash
# 1. Editar requirements-docker.txt
echo "nueva_libreria>=1.0.0" >> requirements-docker.txt

# 2. Probar localmente si es posible
poetry add nueva_libreria

# 3. Reconstruir imagen Docker
docker build -t service-name docker/service-directory/

# 4. Probar la imagen
docker run service-name python -c "import nueva_libreria; print('OK')"
```

#### 3. Para Reporting Service

```bash
# 1. Editar requirements-reporting.txt
echo "nueva_libreria>=1.0.0" >> requirements-reporting.txt

# 2. Verificar que es realmente necesaria
# (el reporting debe mantenerse mínimo)

# 3. Reconstruir imagen
docker build -t traffic-reporting-service docker/reporting-service/
```

#### 4. Para Decision Agent

```bash
# 1. Editar requirements-decision.txt
echo "nueva_libreria>=1.0.0" >> requirements-decision.txt

# 2. Verificar compatibilidad con TensorFlow

# 3. Reconstruir imagen
docker build -t traffic-decision-agent docker/decision-agent/
```

### Actualizar Dependencias

#### Poetry (Local)

```bash
# Actualizar todas
poetry update

# Actualizar una específica
poetry update tensorflow

# Ver qué se puede actualizar
poetry show --outdated
```

#### Docker

```bash
# 1. Actualizar versiones en requirements-*.txt
# 2. Reconstruir imágenes
docker build --no-cache -t service-name docker/service-directory/

# 3. Probar compatibilidad
docker run service-name python -c "import sys; print(sys.version)"
```

## 🔧 Troubleshooting

### Problemas Comunes

#### 1. Conflictos de Versiones

```bash
# Poetry - resolver conflictos
poetry lock --no-update
poetry install

# Ver qué está causando el conflicto
poetry show --tree | grep conflicting_package
```

#### 2. Dependencias Faltantes en Docker

```bash
# Verificar que el archivo se copia correctamente
docker run --rm service-name cat requirements-reporting.txt

# Instalar dependencias manualmente para debug
docker run -it service-name bash
pip install nueva_libreria
```

#### 3. Tamaño de Imagen Docker

```bash
# Ver capas de la imagen
docker history service-name

# Optimizar limpiando cache
RUN pip install --no-cache-dir -r requirements.txt
```

### Comandos de Diagnóstico

```bash
# Poetry
poetry check                    # Verificar pyproject.toml
poetry config --list           # Ver configuración
poetry env info                 # Info del entorno virtual

# Docker
docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}"
docker system df                # Uso de espacio
```

### Migración de Requirements

#### De Poetry a Docker

```bash
# Exportar dependencias específicas
poetry export --format requirements.txt \
    --only main \
    --without dev \
    --output requirements-new.txt

# Limpiar para Docker (remover hashes si es necesario)
sed 's/ --hash=sha256:[a-f0-9]*//g' requirements-new.txt > requirements-clean.txt
```

### Buenas Prácticas

1. **Versioning**: Usar rangos semánticos (`>=1.2.0,<2.0.0`)
2. **Lock Files**: Siempre commitear `poetry.lock`
3. **Testing**: Probar dependencias nuevas antes de commitear
4. **Documentation**: Documentar por qué se añade cada dependencia
5. **Security**: Revisar vulnerabilidades regularmente

```bash
# Auditoría de seguridad
poetry audit

# Actualizar solo parches de seguridad
poetry update --dry-run
```

## 📝 Ejemplos Prácticos

### Caso 1: Añadir Librería de Visualización

```bash
# 1. Para desarrollo local
poetry add plotly

# 2. Si se necesita en Docker para ML/CV
echo "plotly>=5.0.0" >> requirements-docker.txt

# 3. NO añadir a requirements-reporting.txt (no es necesario)
```

### Caso 2: Actualizar TensorFlow

```bash
# 1. Actualizar en Poetry
poetry add "tensorflow>=2.20.0"

# 2. Actualizar en Docker para Decision Agent
sed -i 's/tensorflow\[and-cuda\]==.*/tensorflow[and-cuda]==2.20.0/' requirements-decision.txt

# 3. Probar compatibilidad
poetry run python -c "import tensorflow as tf; print(tf.__version__)"
```

### Caso 3: Optimizar Imagen de Decision Agent

```bash
# Verificar dependencias realmente usadas para ML
poetry run python -c "
import tensorflow as tf
import numpy as np
print(f'TensorFlow: {tf.__version__}')
print(f'NumPy: {np.__version__}')
print('Dependencias ML cargadas correctamente')
"

# Solo mantener las esenciales en requirements-decision.txt
```

### Caso 4: Optimizar Imagen de Reporting

```bash
# Verificar dependencias realmente usadas
poetry run python -c "
import pkg_resources
import sys
sys.path.append('src')
from traffic_system.reporting.report_service import ReportService
print('Dependencias cargadas correctamente')
"

# Solo mantener las esenciales en requirements-reporting.txt
```

---

**💡 Tip**: Mantén las dependencias al mínimo en cada servicio para optimizar el rendimiento y reducir la superficie de ataque de seguridad.
