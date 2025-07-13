# Testing Guide

Guía sobre las pruebas y validación en el proyecto.

## 🧪 Scripts de Prueba

### Pruebas de Integración

Estos scripts validan la integración entre componentes:

#### `test_sync.py`

- **Propósito**: Verificar sincronización entre simulaciones S1 y S2
- **Uso**: `python test_sync.py`
- **Verifica**:
  - Endpoints de la API están disponibles
  - Simulaciones avanzan sincronizadamente
  - Estados de semáforos son consistentes
  - Métricas de tiempo de espera

#### `test_reinicio_api.py`

- **Propósito**: Probar el reinicio de simulaciones vía API
- **Uso**: `python test_reinicio_api.py`
- **Flujo**:
  1. Verificar API disponible
  2. Avanzar simulación algunos pasos
  3. Reiniciar simulación
  4. Verificar que vuelve a tiempo 0
  5. Comprobar funcionamiento post-reinicio

#### `test_entrenamiento_dqn_completo.py`

- **Propósito**: Entrenamiento completo del modelo DQN
- **Uso**: `python test_entrenamiento_dqn_completo.py`
- **Incluye**: Configuración automatizada, entrenamiento y validación

### Pruebas de Componentes

#### `test_semaforo_sync.py`

- **Propósito**: Validar lógica específica de sincronización de semáforos
- **Enfoque**: Cambios de fase y consistencia temporal

#### `test_dispositivo_dqn.py`

- **Propósito**: Validar funcionamiento del modelo DQN
- **Verifica**: Carga de modelos, predicciones, estados válidos

#### `test_verificar_gpu.py`

- **Propósito**: Verificar disponibilidad y configuración de GPU
- **Uso**: Detectar si TensorFlow puede usar GPU para entrenamiento

## 🔄 Patrones de Prueba

### Estructura Típica de un Test

```python
import logging
import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TestName")

def test_functionality():
    logger.info("🧪 Iniciando prueba...")

    # 1. Verificar precondiciones
    response = requests.get("http://127.0.0.1:5000/simulacion")
    if response.status_code != 200:
        logger.error("❌ API no disponible")
        return False

    # 2. Ejecutar operación
    # ... código de prueba ...

    # 3. Verificar resultados
    if condition_met:
        logger.info("✅ Prueba exitosa")
        return True
    else:
        logger.error("❌ Prueba falló")
        return False

if __name__ == "__main__":
    success = test_functionality()
    exit(0 if success else 1)
```

### API Testing

Los tests utilizan la biblioteca `requests` para:

- Verificar disponibilidad de endpoints
- Probar flujos de datos completos
- Validar sincronización entre servicios
- Comprobar manejo de errores

## 📝 Convenciones de Testing

### Logging

- Usa emojis para estados: ✅ ❌ ⚠️ 🧪 🎯
- Niveles: INFO para progreso, ERROR para fallos
- Formato: `"%(asctime)s - %(name)s - %(message)s"`

### Timeouts

- Requests con timeout: `requests.get(url, timeout=5)`
- Esperas entre operaciones: `time.sleep(2)`

### Validación

- Verificar `status_code` de respuestas HTTP
- Validar estructura de datos JSON
- Comprobar rangos de valores (ej. tiempos de simulación)

## 🎯 Crear Nuevas Pruebas

Para añadir una nueva prueba de integración:

1. **Crear archivo**: `test_nueva_funcionalidad.py`
2. **Importar dependencias**:
   ```python
   import logging
   import requests
   import time
   ```
3. **Configurar logging** con el patrón estándar
4. **Implementar funciones de prueba** siguiendo el patrón típico
5. **Añadir al main** con manejo de excepciones
6. **Documentar** el propósito en este archivo

### Ejemplo de Nueva Prueba

```python
def test_new_feature():
    """Probar nueva funcionalidad del sistema."""
    logger.info("🧪 Probando nueva funcionalidad...")

    # Implementar lógica de prueba
    # ...

    return True  # o False si falla
```
