---
description: "Añadir nueva configuración al sistema manteniendo consistencia"
mode: "edit"
---

# Añadir Nueva Configuración

Ayuda a añadir nuevos parámetros de configuración de forma segura.

## Proceso Requerido

El sistema usa configuración centralizada con validación Pydantic. **ORDEN IMPORTANTE**:

### 1. Actualizar `config_models.py` PRIMERO

Ubicación: `src/traffic_system/core/config_models.py`

```python
class ComponenteSettings(BaseModel):
    # ...campos existentes...
    nuevo_campo: tipo_dato  # bool, int, str, list[tipo], etc.
    campo_opcional: int = 42  # Con valor por defecto
```

### 2. Añadir al modelo principal si es necesario

```python
class AppSettings(BaseModel):
    # ...
    nuevo_componente: ComponenteSettings  # Si es sección nueva
```

### 3. Actualizar `config.yaml`

```yaml
componente:
  # ...configuración existente...
  nuevo_campo: valor #! Descripción del campo
  campo_opcional: 100 #* Campo opcional con valor por defecto
```

### 4. Usar en el código

```python
from src.traffic_system.core.config_loader import load_app_settings

settings = load_app_settings()
valor = settings.componente.nuevo_campo
```

## Convenciones

- Usar comentarios descriptivos en YAML: `#!` para obligatorios, `#*` para opcionales
- Nombres en snake_case
- Valores por defecto razonables
- Documentar propósito del campo
- Al editar o agregar un campo, asegurarse de hacerlo en Inglés y no en español.

¿Qué configuración necesitas añadir?
