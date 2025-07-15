# API Reference Guide

Esta guía documenta los endpoints REST disponibles en el sistema de semáforos inteligentes.

**Nota**: Todos los endpoints utilizan DTOs (Data Transfer Objects) con Pydantic para garantizar tipado fuerte y validación automática. Los modelos están definidos en `src/traffic_system/api/api_models.py`.

## Simulation API (Puerto 5000)

### Estados de Simulación

- `GET /simulacion` - Verificar si la simulación está activa

  - **Response**: `SimulationStatusResponse`
  - **Estructura**: `{"activa": bool}`

- `GET /reporte` - Obtener reporte completo

  - **Response**: `ReportResponse`
  - **Estructura**: `{"step": int, "tiempos_espera": dict, "estados_semaforos": dict}`

- `POST /simulacion/reiniciar` - Reiniciar las simulaciones

  - **Response**: `ResetResponse` o `ErrorResponse`
  - **Estructura**: `{"message": str}` o `{"error": str}`

- `GET /sincronizacion` - Estado de sincronización entre S1 y S2
  - **Response**: `SynchronizationResponse`
  - **Estructura**: `{"sincronizada": bool, "diferencia_tiempo": float, "s1_time": float, "s2_time": float}`

### Control de Simulación

- `PUT /avanzar?steps=N` - Avanzar N pasos en la simulación

  - **Response**: `SimulationStepResponse`
  - **Estructura**: `{"step": int, "timestamp": str}`

- `GET /semaforo` - Obtener estados de todos los semáforos

  - **Response**: `TrafficLightStatesResponse`
  - **Estructura**: `{"estados": dict}`

- `PUT /semaforo/{id}?estado=ESTADO` - Cambiar estado de un semáforo

  - **Response**: `TrafficLightStateResponse`
  - **Estructura**: `{"id": str, "estado": str}`

- `PUT /semaforo` - Cambiar múltiples semáforos
  - **Request**: `TrafficLightUpdateRequest`
  - **Response**: `TrafficLightStatesResponse`

### Métricas de Tráfico

- `GET /espera` - Tiempos de espera de todas las zonas (S1)

  - **Response**: `WaitTimesResponse`
  - **Estructura**: `{"tiempos": dict}`

- `GET /espera2` - Tiempos de espera de la simulación de comparación (S2)
  - **Response**: `WaitTimesResponse`
  - **Estructura**: `{"tiempos": dict}`

## Detection API (Puerto 5000 - mismo servidor)

### Detección de Vehículos

- `GET /cantidad` - Cantidad de vehículos en todas las zonas

  - **Response**: `VehicleQuantitiesResponse`
  - **Estructura**: `{"cantidades": dict}`

- `GET /cantidad/{zona_name}` - Cantidad en una zona específica

  - **Response**: `VehicleQuantityResponse`
  - **Estructura**: `{"zona": str, "cantidad": int}`

- `GET /espera` - Tiempos de espera por zona (desde detección)
  - **Response**: `WaitTimesResponse`
  - **Estructura**: `{"tiempos": dict}`

## Estados de Semáforos

Los semáforos usan una cadena de caracteres donde:

- `G` = Verde (Green)
- `g` = Verde protegido
- `y` = Amarillo (Yellow)
- `r` = Rojo (Red)

Ejemplo: `"GGGGGGrrrrr"` - primeros 6 carriles en verde, últimos 5 en rojo.

## Clientes API con DTOs

El sistema incluye clientes Python preconfigurados que retornan objetos tipados:

- `DecisionAPI` en `src/traffic_system/api_client/data_source_client.py`
  - Todos los métodos retornan DTOs específicos (ej. `WaitTimesResponse`, `VehicleQuantitiesResponse`)
- `ReportAPI` en `src/traffic_system/api_client/reporting_client.py`
  - Métodos tipados: `get_report() -> ReportResponse | None`

### Ejemplo de uso con DTOs:

```python
from src.traffic_system.api_client.data_source_client import DecisionAPI

api = DecisionAPI("http://localhost:5000")
wait_times = api.get_wait_times()  # Retorna WaitTimesResponse
if wait_times:
    print(f"Tiempos: {wait_times.tiempos}")
```

## Modelos de Datos (DTOs)

Todos los modelos están definidos en `src/traffic_system/api/api_models.py`:

- `SimulationStepResponse`: Respuesta de avance de simulación
- `WaitTimesResponse`: Tiempos de espera por zona
- `VehicleQuantitiesResponse`: Cantidades de vehículos
- `TrafficLightStatesResponse`: Estados de semáforos
- `ReportResponse`: Reporte completo del sistema
- `ErrorResponse`: Respuesta estándar de error
- `SynchronizationResponse`: Estado de sincronización

## Respuestas de Error Comunes

Todos los errores siguen el formato estándar `ErrorResponse`:

- `400` - Parámetros faltantes o inválidos
  - **Response**: `{"error": "Descripción del error"}`
- `404` - Recurso no encontrado (ej. simulación de comparación no activa)
  - **Response**: `{"error": "Recurso no encontrado"}`
- `500` - Error interno del servidor o simulación no sincronizada
  - **Response**: `{"error": "Error interno del servidor"}`
