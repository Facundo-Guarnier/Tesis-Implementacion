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
        return jsonify({"resultado": datos}), 200
    except Exception as e:
        self.logger.error(f"Error en endpoint: {e}")
        return jsonify({"error": str(e)}), 500
```

4. **Registra la ruta** en `__init__`:

```python
self.route("/nuevo-endpoint", methods=["GET"])(self.nuevo_endpoint)
```

5. **Añade cliente API** en `api_client/data_source_client.py`:

```python
def nuevo_endpoint_client(self) -> dict | None:
    response = requests.get(f"{self.base_url}/nuevo-endpoint")
    return response.json() if response.status_code == 200 else None
```

6. **Documenta en API_REFERENCE.md**

¿Qué endpoint necesitas crear?
