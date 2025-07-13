# 🚀 Guía de Inicio Rápido

Esta guía te ayudará a configurar y ejecutar el proyecto de semáforos inteligentes en tu entorno local.

## 📋 Prerrequisitos

- **Python 3.11+**
- **Git**
- **SUMO** (Simulación de tráfico)

## ⚡ Configuración Rápida

### 1. Clonar el Repositorio

```bash
git clone https://github.com/usuario/sistema-semaforos-inteligentes.git
cd sistema-semaforos-inteligentes
```

### 2. Instalar Poetry

**Windows (PowerShell):**

```powershell
(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | python -
```

**Linux/macOS:**

```bash
curl -sSL https://install.python-poetry.org | python3 -
```

### 3. Configurar el Proyecto

```bash
# Instalar todas las dependencias
poetry install

# Activar entorno virtual
poetry shell

# Instalar hooks de pre-commit para calidad de código
poetry run pre-commit install
```

### 4. Instalar SUMO

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

## 🎯 Ejecución del Sistema

### Simulación Básica

```bash
# Terminal 1: Iniciar simulación de tráfico
poetry run python run_simulation_provider.py

# Terminal 2: Iniciar agente de decisión DQN
poetry run python run_decision_agent.py

# Terminal 3: (Opcional) Iniciar detección de vehículos
poetry run python run_detection_provider.py
```

### Verificar Configuración

```bash
# Verificar entorno
poetry env info

# Verificar dependencias
poetry show

# Ejecutar herramientas de calidad
poetry run pre-commit run --all-files
```

## 📚 Documentación Completa

- **[Configuración de Dependencias](1_setup/dependencies.md)**: Gestión con Poetry
- **[Estructura del Proyecto](1_setup/project_structure.md)**: Arquitectura del código
- **[Herramientas de Desarrollo](2_guides/tooling.md)**: Pre-commit, Black, Ruff, etc.
- **[Guía de Contribución](2_guides/contributing.md)**: Estándares de desarrollo

## 🛠️ Comandos Útiles

```bash
# Desarrollo
poetry shell                    # Activar entorno
poetry add <paquete>            # Agregar dependencia
poetry run python <script.py>  # Ejecutar script

# Calidad de código
poetry run pre-commit run --all-files  # Verificar todo
poetry run black .                     # Formatear código
poetry run ruff check --fix .          # Linting
poetry run mypy .                      # Verificar tipos
```

## 🚨 Solución de Problemas

### Error: "poetry: command not found"

```bash
# Agregar Poetry al PATH
export PATH="$HOME/.local/bin:$PATH"
```

### Error: Pre-commit no funciona

```bash
# Reinstalar hooks
poetry run pre-commit clean
poetry run pre-commit install
```

### Error: Dependencias no se instalan

```bash
# Limpiar caché y reinstalar
poetry cache clear pypi --all
poetry install --no-cache
```

## ✅ Verificación de la Instalación

Si todo está configurado correctamente, deberías poder ejecutar:

```bash
poetry run python -c "import cv2, flask, numpy; print('✅ Dependencias básicas OK')"
poetry run pre-commit --version
poetry env info
```

¡Listo! Ya tienes el entorno configurado para desarrollar el sistema de semáforos inteligentes.
