---
description: "Instrucciones para crear y ejecutar tests de integración"
applyTo: "**/test_*.py"
---

# Instrucciones para Testing

## Estructura de Tests

Los tests son scripts de integración ejecutables que validan el sistema completo:

```python
import logging
import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(message)s")
logger = logging.getLogger("TestName")

def test_functionality():
    logger.info("🧪 Iniciando prueba...")

    # 1. Verificar precondiciones
    response = requests.get("http://127.0.0.1:5000/simulacion", timeout=5)
    if response.status_code != 200:
        logger.error("❌ API no disponible")
        return False

    # 2. Ejecutar operación
    # ... código de prueba ...

    # 3. Verificar resultados
    if success:
        logger.info("✅ Prueba exitosa")
        return True
    else:
        logger.error("❌ Prueba falló")
        return False

if __name__ == "__main__":
    success = test_functionality()
    exit(0 if success else 1)
```

## Convenciones

- Usar emojis en logs: 🧪 ✅ ❌ ⚠️
- Timeouts en requests: `timeout=5`
- Manejo de excepciones específicas: `ConnectionError`, `Timeout`
- Retornar True/False para éxito/fallo
- Exit codes: 0 para éxito, 1 para fallo

## Tipos de Tests Existentes

- `test_sync.py`: Verificar sincronización entre simulaciones
- `test_reinicio_api.py`: Probar reinicio de simulaciones
- `test_entrenamientodqn_completo.py`: Entrenamiento completo
- `test_verificar_gpu.py`: Verificar configuración GPU

## APIs de Testing

- Base URL: `http://127.0.0.1:5000`
- Endpoints clave: `/simulacion`, `/reporte`, `/avanzar`, `/sincronizacion`
- Verificar respuestas JSON con `response.json()`
