# Funcionalidad de Reinicio de Simulación

Este documento explica la nueva funcionalidad de reinicio implementada para las simulaciones SUMO.

## 🔄 ¿Qué se implementó?

Se añadió la capacidad de reiniciar las simulaciones SUMO tanto programáticamente como a través de la API REST, solucionando el problema donde el método `reiniciar()` no funcionaba después de mover la lógica de inicialización fuera de la clase `AppSUMO`.

## 📝 Cambios realizados

### 1. Modificaciones en `AppSUMO.py`

- **Constructor actualizado**: Ahora acepta parámetros adicionales para poder recrear la conexión:

  - `config_file`: Ruta al archivo de configuración SUMO
  - `use_gui`: Si usar interfaz gráfica
  - `restart_callback`: Función que puede recrear la conexión Traci

- **Método `reiniciar()` mejorado**:
  - Cierra la conexión actual de forma segura
  - Usa el callback para recrear una nueva conexión
  - Maneja errores apropiadamente
  - Proporciona logging detallado

### 2. Modificaciones en `run_simulation_provider.py`

- Actualizado para pasar los nuevos parámetros al constructor de `AppSUMO`
- Tanto `app_s1` como `app_s2` ahora pueden reiniciarse correctamente

### 3. Nueva API REST endpoint

- **POST `/simulacion/reiniciar`**: Reinicia las simulaciones S1 y S2 (si existe)
- Retorna estado de éxito/error en formato JSON
- Maneja errores de forma apropiada

## 🚀 Cómo usar

### Reinicio programático

```python
# La simulación ahora puede reiniciarse directamente
app_sumo.reiniciar()
```

### Reinicio por API REST

```bash
# Usando curl
curl -X POST http://127.0.0.1:5000/simulacion/reiniciar

# Usando requests en Python con DTOs
import requests
from src.traffic_system.api.api_models import ResetResponse, ErrorResponse

response = requests.post("http://127.0.0.1:5000/simulacion/reiniciar")
if response.status_code == 200:
    reset_response = ResetResponse.model_validate(response.json())
    print(f"✅ {reset_response.message}")
else:
    error_response = ErrorResponse.model_validate(response.json())
    print(f"❌ {error_response.error}")
```

## 🧪 Scripts de prueba

Se incluyen dos scripts de prueba:

### 1. `test_reinicio_simulation.py`

Prueba el reinicio programático directamente:

```bash
poetry run python test_reinicio_simulation.py
```

### 2. `test_reinicio_api.py`

Prueba el reinicio a través de la API REST:

```bash
# Primero inicia el servidor
poetry run python run_simulation_provider.py

# En otra terminal, ejecuta la prueba
poetry run python test_reinicio_api.py
```

## ⚙️ Configuración

No se requiere configuración adicional. El reinicio usa la misma configuración SUMO que se cargó inicialmente.

## 🔍 Validación

El reinicio se considera exitoso cuando:

1. ✅ La conexión anterior se cierra sin errores
2. ✅ Se crea una nueva conexión SUMO exitosamente
3. ✅ El tiempo de simulación se resetea a 0
4. ✅ La simulación puede avanzar normalmente después del reinicio

## ⚠️ Consideraciones

- El reinicio cierra completamente la simulación y la vuelve a abrir desde el estado inicial
- Todos los vehículos y estados se pierden (comportamiento esperado)
- El reinicio puede tomar unos segundos en completarse
- Si hay errores en el reinicio, se lanzan excepciones apropiadas

## 🐛 Troubleshooting

### Error: "No se puede reiniciar: callback no disponible"

- **Causa**: La instancia de `AppSUMO` fue creada sin el parámetro `restart_callback`
- **Solución**: Asegúrate de pasar la función `start_traci_connection` al constructor

### Error: "Error al reiniciar la simulación"

- **Causa**: Problema con SUMO o archivos de configuración
- **Solución**: Verifica que SUMO esté instalado y los archivos de configuración sean válidos

### API devuelve error 500

- **Causa**: Error en el proceso de reinicio del servidor
- **Solución**: Revisa los logs del servidor para detalles específicos

## 📋 Ejemplo completo

```python
import traci
from src.traffic_system.simulation.AppSUMO import AppSUMO
from src.traffic_system.simulation.zonas.ZonaList import ZonaList

def start_traci_connection(label, config_file, use_gui):
    sumo_binary = "sumo-gui" if use_gui else "sumo"
    command = [sumo_binary, "-c", config_file, "--no-warnings"]
    traci.start(cmd=command, label=label)
    return traci.getConnection(label)

# Crear simulación con capacidad de reinicio
zonas = ZonaList()
traci_conn = start_traci_connection("test", "assets/sumo_maps/MapaDe0/mapa.sumocfg", False)
app = AppSUMO(traci_conn, zonas, "test", "assets/sumo_maps/MapaDe0/mapa.sumocfg", False, start_traci_connection)

# Usar la simulación
app.avanzar(10)
print(f"Tiempo antes del reinicio: {app.traci.simulation.getTime()}")

# Reiniciar
app.reiniciar()
print(f"Tiempo después del reinicio: {app.traci.simulation.getTime()}")  # Debería ser 0

# Continuar usando
app.avanzar(5)
print(f"Tiempo final: {app.traci.simulation.getTime()}")
```

---

_Esta funcionalidad fue implementada para resolver el problema de reinicio en las simulaciones SUMO._
