# 📦 Gestión de Dependencias con Poetry

Este documento explica cómo gestionar las dependencias del proyecto usando Poetry.

## 🚀 Configuración Inicial

### 1. Instalar Poetry

**Windows (PowerShell):**

```powershell
(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | python -
```

**Linux/macOS:**

```bash
curl -sSL https://install.python-poetry.org | python3 -
```

### 2. Instalar Dependencias del Proyecto

```bash
# Instalar todas las dependencias (desarrollo + producción)
poetry install

# Solo dependencias de producción
poetry install --no-dev
```

## 🛠️ Uso Diario

### Activar Entorno Virtual

```bash
# Opción 1: Entrar al shell de Poetry
poetry shell

# Opción 2: Ejecutar comandos específicos
poetry run python run_simulation_provider.py
poetry run pre-commit run --all-files
```

### Gestión de Dependencias

```bash
# Agregar nueva dependencia de producción
poetry add requests

# Agregar dependencia de desarrollo
poetry add --group dev pytest

# Actualizar todas las dependencias
poetry update

# Ver dependencias instaladas
poetry show
```

## 📦 Dependencias del Proyecto

### Producción

- **Flask**: Servidor web para APIs REST
- **requests**: Cliente HTTP para consumir APIs
- **numpy**: Computación científica y arrays
- **opencv-python**: Procesamiento de imágenes y video
- **pydantic**: Validación de configuración y modelos de datos

### Desarrollo

- **pre-commit**: Hooks automáticos de calidad de código
- **black**: Formateo automático de código
- **ruff**: Linter rápido con correcciones automáticas
- **mypy**: Verificación de tipos estáticos
- **types-\*\*\***: Stubs de tipos para librerías externas

## 🐧 Dependencias del Sistema

### SUMO (Simulación de Tráfico)

**Ubuntu/Debian:**

```bash
sudo add-apt-repository ppa:sumo/stable -y
sudo apt-get update
sudo apt-get install sumo sumo-tools sumo-doc
```

**Windows:**
Descargar desde: https://eclipse.dev/sumo/

**macOS:**

```bash
brew install sumo
```

## 🔧 Pre-commit Hooks

Los hooks de calidad de código se ejecutan automáticamente en cada commit:

```bash
# Instalar hooks (solo primera vez)
poetry run pre-commit install

# Ejecutar manualmente en todos los archivos
poetry run pre-commit run --all-files
```
