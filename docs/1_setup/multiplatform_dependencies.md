# 🔧 Gestión de Dependencias Multiplataforma con Poetry

Este documento explica cómo el proyecto maneja automáticamente diferentes versiones de dependencias según la plataforma y versión de Python utilizando **environment markers** de Poetry.

## 📋 Problema Resuelto

El proyecto necesita ejecutarse en diferentes entornos con distintas versiones de Python y dependencias:

- **Windows**: Python 3.11.9 con TensorFlow 2.14.0 + dependencias específicas de Intel
- **Linux**: Python 3.12.3 con TensorFlow 2.19.0

## ✅ Solución Implementada

### Environment Markers en `pyproject.toml`

```toml
[tool.poetry.dependencies]
python = ">=3.11,<3.13"

# TensorFlow con dependencias específicas por plataforma
tensorflow = [
    {version = "==2.14.0", markers = "platform_system == 'Windows' and python_version < '3.12'"},
    {version = "==2.19.0", markers = "platform_system == 'Linux' and python_version >= '3.12'"}
]

# Dependencias específicas de Windows con Python 3.11
tensorflow-estimator = {version = "==2.14.0", markers = "platform_system == 'Windows' and python_version < '3.12'"}
tensorflow-intel = {version = "==2.14.0", markers = "platform_system == 'Windows' and python_version < '3.12'"}
tensorflow-io-gcs-filesystem = {version = "==0.31.0", markers = "platform_system == 'Windows' and python_version < '3.12'"}
```

### Markers Utilizados

| Marker                         | Descripción     | Ejemplo                        |
| ------------------------------ | --------------- | ------------------------------ |
| `platform_system == 'Windows'` | Solo en Windows | Dependencias Intel-específicas |
| `platform_system == 'Linux'`   | Solo en Linux   | TensorFlow 2.19.0              |
| `python_version < '3.12'`      | Python 3.11.x   | Compatibilidad con tf-io-gcs   |
| `python_version >= '3.12'`     | Python 3.12+    | TensorFlow moderno             |

## 🚀 Funcionamiento Automático

### En Windows (Python 3.11.9)

```bash
poetry install  # Instala automáticamente:
# - tensorflow==2.14.0
# - tensorflow-estimator==2.14.0
# - tensorflow-intel==2.14.0
# - tensorflow-io-gcs-filesystem==0.31.0
```

### En Linux (Python 3.12.3)

```bash
poetry install  # Instala automáticamente:
# - tensorflow==2.19.0
# (sin dependencias específicas de Windows)
```

## 🔍 Verificación

### Script de Verificación

El proyecto incluye `test_verify_dependencies.py` que muestra:

- Información del sistema actual
- Versión de TensorFlow instalada
- Validación de que sea la versión correcta para la plataforma

```bash
poetry run python test_verify_dependencies.py
```

### Comandos de Verificación Manual

```bash
# Ver qué versión de TensorFlow está instalada
poetry show tensorflow

# Ver todas las dependencias instaladas
poetry show

# Verificar configuración de Poetry
poetry check

# Instalar dependencias (automáticamente selecciona las correctas)
poetry install
```

## 🛠️ Mantenimiento

### Agregar Nueva Plataforma

Para agregar soporte para macOS con Python 3.13:

```toml
tensorflow = [
    {version = "==2.14.0", markers = "platform_system == 'Windows' and python_version < '3.12'"},
    {version = "==2.19.0", markers = "platform_system == 'Linux' and python_version >= '3.12'"},
    {version = "==2.20.0", markers = "platform_system == 'Darwin' and python_version >= '3.13'"}
]
```

### Actualizar Versiones

1. Modificar las versiones en `pyproject.toml`
2. Regenerar el lock file: `poetry lock`
3. Verificar: `poetry run python test_verify_dependencies.py`

## 📚 Referencias

- [Poetry Dependency Specification](https://python-poetry.org/docs/dependency-specification/)
- [PEP 508 - Environment Markers](https://peps.python.org/pep-0508/)
- [Poetry Environment Markers](https://python-poetry.org/docs/dependency-specification/#using-environment-markers)

## ✨ Ventajas de esta Solución

1. **Sin Scripts**: Poetry maneja todo automáticamente
2. **Declarativo**: La configuración está en `pyproject.toml`
3. **Determinístico**: `poetry.lock` garantiza reproducibilidad
4. **Multiplataforma**: Funciona en CI/CD y desarrollo local
5. **Mantenible**: Fácil de actualizar y extender
6. **Estándar**: Usa PEP 508 y mejores prácticas de Poetry
