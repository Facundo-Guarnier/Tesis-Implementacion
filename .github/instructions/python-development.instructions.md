---
description: "Instrucciones específicas para desarrollo en Python en el proyecto de semáforos inteligentes"
applyTo: "**/*.py"
---

# Instrucciones para Desarrollo en Python

## Estilo y Convenciones

- Usar **snake_case** para variables y funciones
- Usar **PascalCase** para clases
- Máximo 88 caracteres por línea (configuración de Black)
- Docstrings en español para métodos públicos
- Type hints obligatorios para parámetros y retornos

## Imports

- Orden: stdlib, third-party, local imports
- Usar imports absolutos desde `src/`
- Ejemplo correcto: `from src.traffic_system.core.config_loader import load_app_settings`

## Logging

- Usar el patrón estándar del proyecto:

```python
import logging
logger = logging.getLogger(__name__)
```

- Formato de logs: `"%(asctime)s - %(name)s - %(message)s"`
- Usar emojis para estados en logs: ✅ ❌ ⚠️ 🧪

## Configuración

- **NUNCA hardcodear configuraciones** - usar siempre `config.yaml`
- Para nuevas configuraciones, actualizar `config_models.py` primero
- Cargar configuración con: `settings = load_app_settings()`

## APIs REST

- Usar Flask para APIs
- Retornar tuplas: `return jsonify(data), status_code`
- Manejar errores con try/except y logs apropiados
- Usar timeouts en requests: `requests.get(url, timeout=5)`

## Patrones del Proyecto

- Apps principales en `src/traffic_system/{componente}/app.py`
- APIs en `src/traffic_system/api/`
- Clientes API en `src/traffic_system/api_client/`
- Modelos de datos con Pydantic en `config_models.py`
