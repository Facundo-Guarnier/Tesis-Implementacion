# Data Flow Diagram

Descripción del flujo de datos en el sistema de semáforos inteligentes.

## 🔄 Flujo Principal

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   SUMO S1       │    │  Decision Agent  │    │   SUMO S2       │
│  (Controlada)   │◄──►│      (DQN)       │    │  (Comparación)  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                        │                        │
         │                        │                        │
         ▼                        ▼                        ▼
┌─────────────────────────────────────────────────────────────────┐
│                      API REST (Flask)                          │
│  /avanzar  /semaforo  /espera  /sincronizacion  /reporte       │
└─────────────────────────────────────────────────────────────────┘
```

## 📊 Ciclo de Decisión

1. **Estado Actual**: El agente obtiene el estado de la simulación

   - Tiempos de espera por zona: `GET /espera`
   - Estados actuales de semáforos: `GET /semaforo`

2. **Procesamiento**: El modelo DQN procesa el estado

   - 12 zonas de entrada (tiempos de espera)
   - Red neuronal procesa el estado
   - Selecciona acción óptima

3. **Acción**: El agente ejecuta la decisión

   - Cambio de fases: `PUT /semaforo`
   - Avance de simulación: `PUT /avanzar?steps=N`

4. **Recompensa**: Evaluación del resultado
   - Reducción en tiempos de espera
   - Fluidez del tráfico
   - Actualización del modelo

## 🏗️ Componentes y Sus Datos

### Simulation Provider (`run_simulation_provider.py`)

**Entrada**:

- Comandos de control via API REST
- Configuración desde `config.yaml`

**Salida**:

- Estados de semáforos
- Tiempos de espera por zona
- Métricas de tráfico

**APIs Expuestas**:

```
GET  /simulacion     → {"simulacion": bool}
GET  /reporte        → {"steps": int, "tiempos_espera": [], "estados_semaforos": []}
PUT  /avanzar        → {"done": bool, "sync_status": str}
GET  /semaforo       → {"estados": []}
PUT  /semaforo       → {"estado": "OK"}
GET  /espera         → {"tiempo_espera_total": float, "tiempos_espera": []}
```

### Decision Agent (`run_decision_agent.py`)

**Entrada**:

- Estados de simulación (via `DecisionAPI`)
- Configuración de entrenamiento

**Salida**:

- Comandos de control a simulación
- Modelos entrenados (archivos .h5)

**Cliente API**:

```python
api = DecisionAPI("http://127.0.0.1:5000")
states = api.get_all_traffic_light_states()
wait_times = api.get_wait_times()
api.set_traffic_light_states(new_states)
api.advance_simulation(steps=10)
```

### Detection Provider (`run_detection_provider.py`)

**Entrada**:

- Videos o stream de cámara
- Configuración de zonas

**Salida**:

- Cantidad de vehículos por zona
- Tiempos de espera estimados

**APIs Expuestas**:

```
GET  /cantidad       → {zona_name: count}
GET  /cantidad/{zona} → {"zona": str, "cantidad_detecciones": int}
GET  /espera         → {"tiempo_espera_total": int, "tiempos_espera": []}
```

## 🔄 Flujos de Datos Específicos

### Entrenamiento DQN

```
1. Simulación inicial → Estado S₀
2. Modelo DQN → Acción A₀
3. Ejecutar A₀ → Nuevo estado S₁ + Recompensa R₀
4. Almacenar (S₀, A₀, R₀, S₁) en memoria
5. Entrenar red neuronal con batch de experiencias
6. Repetir hasta convergencia
```

### Inferencia (Uso del Modelo)

```
1. Obtener estado actual → GET /espera, GET /semaforo
2. Procesar con modelo DQN → Acción óptima
3. Ejecutar acción → PUT /semaforo
4. Avanzar simulación → PUT /avanzar?steps=10
5. Repetir ciclo
```

### Sincronización S1-S2

```
1. Acción en S1 → Cambio de semáforo (puede avanzar 3 steps)
2. Detectar steps avanzados → time_after - time_before
3. Sincronizar S2 → Avanzar misma cantidad de steps
4. Verificar sincronización → |time_s1 - time_s2| ≤ 1.0s
```

## 📈 Tipos de Datos

### Estado del Sistema

```python
{
    "tiempos_espera": [float] * 12,    # Por zona
    "estados_semaforos": [str] * 4,    # Por semáforo
    "steps": int,                      # Tiempo simulación
    "sync_status": str                 # "ok" | "desync"
}
```

### Acción DQN

```python
{
    "semaforo_1": str,  # ej. "GGGrrr"
    "semaforo_2": str,
    "semaforo_3": str,
    "semaforo_4": str
}
```

### Métricas de Comparación

```python
{
    "s1_tiempo_espera": float,
    "s2_tiempo_espera": float,
    "mejora_porcentual": float,
    "timestamp": str
}
```
