---
description: "Crear un nuevo script de test de integración"
mode: "edit"
---

# Crear Nuevo Test de Integración

Ayuda a crear tests que validen el funcionamiento completo del sistema.

## Contexto del Sistema

Los tests del proyecto son scripts ejecutables que:

- Validan APIs REST en http://127.0.0.1:5000
- Usan logging con emojis: 🧪 ✅ ❌ ⚠️
- Retornan True/False y exit codes apropiados
- Manejan timeouts y excepciones de red

## Template Base

```python
#!/usr/bin/env python3
"""
Script para probar [DESCRIPCIÓN_FUNCIONALIDAD].
"""

import logging
import time
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")
logger = logging.getLogger("Test[NOMBRE]")


def test_[funcionalidad](base_url: str = "http://127.0.0.1:5000"):
    """
    Prueba [DESCRIPCIÓN_DETALLADA].
    """
    logger.info("🧪 Iniciando prueba de [funcionalidad]...")

    try:
        # 1. Verificar precondiciones
        logger.info("1/N Verificando API disponible...")
        response = requests.get(f"{base_url}/simulacion", timeout=5)
        if response.status_code != 200:
            logger.error("❌ API no disponible")
            return False
        logger.info("✅ API disponible")

        # 2. Ejecutar operaciones de prueba
        logger.info("2/N [Descripción del paso]...")
        # ... código específico del test ...

        # 3. Verificar resultados
        if condicion_exitosa:
            logger.info("✅ [Funcionalidad] funciona correctamente")
            return True
        else:
            logger.error("❌ [Funcionalidad] falló")
            return False

    except requests.exceptions.ConnectionError:
        logger.error("❌ No se pudo conectar a la API")
        return False
    except requests.exceptions.Timeout:
        logger.error("❌ Timeout al conectar con la API")
        return False
    except Exception as e:
        logger.error(f"❌ Error inesperado: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("SCRIPT DE PRUEBA: [TITULO_MAYUSCULAS]")
    logger.info("=" * 60)
    logger.info("Nota: Asegúrate de que el servidor esté ejecutándose:")
    logger.info("      python run_simulation_provider.py")
    logger.info("=" * 60)

    exito = test_[funcionalidad]()

    if exito:
        logger.info("🎯 Todas las pruebas pasaron exitosamente")
        sys.exit(0)
    else:
        logger.error("💥 Las pruebas fallaron")
        sys.exit(1)
```

## APIs Disponibles para Testing

- `/simulacion` - Estado de la simulación
- `/reporte` - Métricas completas
- `/avanzar?steps=N` - Avanzar simulación
- `/semaforo` - Estados de semáforos
- `/espera` - Tiempos de espera
- `/sincronizacion` - Estado de sincronización
- `/simulacion/reiniciar` - Reinicio completo

## Ejemplos de Tests Existentes

Revisa estos archivos para patrones:

- `test_sync.py` - Sincronización
- `test_reinicio_api.py` - Reinicio
- `test_entrenamientodqn_completo.py` - Entrenamiento

¿Qué funcionalidad necesitas probar?
