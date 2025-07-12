# API Reference Guide

Esta guía documenta los endpoints REST disponibles en el sistema de semáforos inteligentes.

## Simulation API (Puerto 5000)

### Estados de Simulación

- `GET /simulacion` - Verificar si la simulación está activa
- `GET /reporte` - Obtener reporte completo (steps, tiempos_espera, estados_semaforos)
- `POST /simulacion/reiniciar` - Reiniciar las simulaciones
- `GET /sincronizacion` - Estado de sincronización entre S1 y S2

### Control de Simulación

- `PUT /avanzar?steps=N` - Avanzar N pasos en la simulación
- `GET /semaforo` - Obtener estados de todos los semáforos
- `GET /semaforo/{id}` - Obtener estado de un semáforo específico
- `PUT /semaforo/{id}?estado=ESTADO` - Cambiar estado de un semáforo
- `PUT /semaforo` - Cambiar múltiples semáforos (JSON: {"data": [{"id": "1", "estado": "GGGrrr"}]})

### Métricas de Tráfico

- `GET /espera` - Tiempos de espera de todas las zonas (S1)
- `GET /espera2` - Tiempos de espera de la simulación de comparación (S2)
- `GET /espera/{zona_id}` - Tiempo de espera de una zona específica

## Detection API (Puerto 5000 - mismo servidor)

### Detección de Vehículos

- `GET /cantidad` - Cantidad de vehículos en todas las zonas
- `GET /cantidad/{zona_name}` - Cantidad en una zona específica
- `GET /espera` - Tiempos de espera por zona (desde detección)
- `POST /multas/{zona_name}` - Activar multas en una zona

## Estados de Semáforos

Los semáforos usan una cadena de caracteres donde:

- `G` = Verde (Green)
- `g` = Verde protegido
- `y` = Amarillo (Yellow)
- `r` = Rojo (Red)

Ejemplo: `"GGGGGGrrrrr"` - primeros 6 carriles en verde, últimos 5 en rojo.

## Clientes API

El sistema incluye clientes Python preconfigurados:

- `DecisionAPI` en `src/traffic_system/api_client/data_source_client.py`
- `ReportAPI` en `src/traffic_system/api_client/reporting_client.py`

## Respuestas de Error Comunes

- `400` - Parámetros faltantes o inválidos
- `404` - Recurso no encontrado (ej. simulación de comparación no activa)
- `500` - Error interno del servidor o simulación no sincronizada
