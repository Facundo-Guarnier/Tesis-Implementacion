# 🧑‍💻 Guía de estilo de código en Python

Este documento define las **convenciones de codificación** utilizadas en el proyecto, basadas en la [PEP 8](https://peps.python.org/pep-0008/) (la guía oficial de estilo de Python), con algunas prácticas adicionales pensadas para mantener la coherencia y claridad entre los desarrolladores.

---

## 📌 Convenciones de nombres

| Elemento                     | Estilo              | Ejemplo                              |
| ---------------------------- | ------------------- | ------------------------------------ |
| **Variables**                | `snake_case`        | `velocidad_maxima`, `usuario_id`     |
| **Funciones / Métodos**      | `snake_case`        | `calcular_total()`, `enviar_email()` |
| **Clases**                   | `PascalCase`        | `ControlSemaforo`, `DetectorImagen`  |
| **Constantes**               | `MAYUS_CON_GUIONES` | `TIEMPO_LIMITE`, `MAX_REINTENTOS`    |
| **Módulos / Archivos .py**   | `snake_case.py`     | `procesador_video.py`                |
| **Paquetes (carpetas)**      | `snake_case/`       | `utilidades/`, `api_v1/`             |
| **Atributos protegidos**     | `_snake_case`       | `_contador_interno`                  |
| **Privados (name mangling)** | `__snake_case`      | `__generar_token()`                  |

> ✅ Usar nombres **descriptivos** y evitar abreviaciones innecesarias (`x`, `tmp`, `dato`, etc.).

---

## 🔠 Identación y formato

- Usar **4 espacios** por nivel de identación.
- Limitar las líneas a **88 caracteres** como recomienda [`Black`](https://black.readthedocs.io/).
- Usar comillas simples `'` o dobles `"`, pero ser **consistente** dentro de cada archivo.
- Incluir **comas finales** en estructuras multilínea (Black lo aplicará automáticamente).
- Dejar una línea en blanco **entre funciones**, y dos líneas entre **funciones o clases de nivel superior**.

---

## 🧼 Organización de imports

Los imports se organizan automáticamente con **Ruff** (que reemplaza a isort) usando configuración compatible con Black. El orden es:

```python
# 1. Librerías estándar
import datetime
import os
import sys

# 2. Paquetes de terceros
import cv2
import numpy as np
import requests

# 3. Módulos locales del proyecto
from src.traffic_system.decision.DQN.dqn_model import DQNModel
from src.traffic_system.detection.detector_service import DetectorService
from src.traffic_system.core.config_loader import load_app_settings
```

> 🔄 **Automático**: Ruff organiza imports automáticamente al guardar archivos en VSCode y en cada pre-commit.

---

## 📝 Logging vs Print Statements

### ❌ NO usar print() en código de producción

```python
# ❌ Evitar
print("Iniciando simulación...")
print(f"Error: {error}")
```

### ✅ Usar sistema de logging estándar

```python
# ✅ Correcto
import logging

logger = logging.getLogger(__name__)

logger.info("✅ Iniciando simulación...")
logger.error("❌ Error durante procesamiento: %s", error)
logger.warning("⚠️ Configuración no optimizada detectada")
logger.debug("🧪 Datos de debug: %s", debug_data)
```
