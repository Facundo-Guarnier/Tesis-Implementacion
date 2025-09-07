# 🔧 Gestión de Dependencias Multiplataforma con Poetry

Este documento explica cómo el proyecto maneja automáticamente diferentes versiones de dependencias según la plataforma y versión de Python utilizando **environment markers** de Poetry.

## 📋 Problema Resuelto

El proyecto necesita ejecutarse en diferentes entornos con distintas versiones de Python y dependencias según la plataforma disponible.

## ✅ Solución Implementada

### Environment Markers en `pyproject.toml`

```toml
[tool.poetry.dependencies]
python = ">=3.11,<3.13"

# TensorFlow con dependencias específicas por plataforma
tensorflow = [
    {version = "==2.19.0", markers = "platform_system == 'Windows'"},
    {version = "==2.19.0", extras = ["and-cuda"], markers = "platform_system == 'Linux'"}
]
```

### Markers Utilizados

| Marker                         | Descripción     | Ejemplo                        |
| ------------------------------ | --------------- | ------------------------------ |
| `platform_system == 'Windows'` | Solo en Windows | TensorFlow estándar |
| `platform_system == 'Linux'`   | Solo en Linux   | TensorFlow con soporte CUDA              |
| `extras = ["and-cuda"]`      | Extensiones específicas | Soporte GPU en Linux             |

## 🚀 Funcionamiento Automático

### En Windows

```bash
poetry install  # Instala automáticamente:
# - tensorflow==2.19.0
# (versión estándar sin GPU)
```

### En Linux

```bash
poetry install  # Instala automáticamente:
# - tensorflow[and-cuda]==2.19.0
# (con soporte GPU NVIDIA automático)
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

Para agregar soporte para macOS:

```toml
tensorflow = [
    {version = "==2.19.0", markers = "platform_system == 'Windows'"},
    {version = "==2.19.0", extras = ["and-cuda"], markers = "platform_system == 'Linux'"},
    {version = "==2.19.0", markers = "platform_system == 'Darwin'"}
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
