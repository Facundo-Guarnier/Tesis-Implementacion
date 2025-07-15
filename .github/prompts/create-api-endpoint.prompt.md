---
description: "Crear un nuevo endpoint REST para la API del sistema"
mode: "edit"
---

# Crear Nuevo Endpoint API

Ayuda a crear un nuevo endpoint REST siguiendo los patrones del proyecto.

## Contexto del Proyecto

Este sistema usa Flask para APIs REST con el patrón:

- APIs definidas en `src/traffic_system/api/`
- Clientes en `src/traffic_system/api_client/`
- Simulación API en puerto 5000
- Retorno con tuplas: `return jsonify(data), status_code`

## Instrucciones

1. **Identifica el componente**: ¿Es para simulación, detección o reportes?

2. **Añade al archivo API correspondiente**:

   - `simulation_server.py` para simulación
   - `detection_server.py` para detección
   - Crear nuevo archivo si es necesario

3. **Sigue el patrón existente**:

```python
def nuevo_endpoint(self) -> tuple[Response, int]:
    """Descripción del endpoint."""
    try:
        # Lógica del endpoint
        response = MiResponse(resultado=datos)
        return jsonify(response.model_dump()), 200
    except Exception as e:
        self.logger.error(f"❌ Error en endpoint: {e}")
        error_response = ErrorResponse(error=str(e))
        return jsonify(error_response.model_dump()), 500
```

4. **Registra la ruta** en `__init__`:

```python
self.route("/nuevo-endpoint", methods=["GET"])(self.nuevo_endpoint)
```

5. **Añade cliente API** en `api_client/data_source_client.py`:

```python
def nuevo_endpoint_client(self) -> MiResponse | None:
    """Cliente que consume el endpoint usando DTOs."""
    try:
        response = requests.get(f"{self.base_url}/nuevo-endpoint")
        if response.status_code == 200:
            return MiResponse.model_validate(response.json())
        else:
            error = ErrorResponse.model_validate(response.json())
            self.logger.error(f"❌ Error API: {error.error}")
            return None
    except Exception as e:
        self.logger.error(f"❌ Error cliente: {e}")
        return None
```

6. **Documenta en API_REFERENCE.md**

¿Qué endpoint necesitas crear?
