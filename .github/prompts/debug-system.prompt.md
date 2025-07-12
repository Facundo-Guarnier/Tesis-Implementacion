---
description: "Diagnosticar y resolver problemas comunes del sistema"
mode: "ask"
---

# Debug del Sistema de Semáforos

Ayuda a diagnosticar y resolver problemas comunes.

## Información de Debug

Proporciona la siguiente información para un diagnóstico efectivo:

### 1. Síntomas del Problema

- ¿Qué estabas intentando hacer?
- ¿Qué error específico ves?
- ¿En qué archivo/línea ocurre?

### 2. Estado del Sistema

Ejecuta estos comandos y comparte los resultados:

```powershell
# Verificar APIs
curl http://127.0.0.1:5000/simulacion
curl http://127.0.0.1:5000/sincronizacion

# Verificar configuración
python -c "from src.traffic_system.core.config_loader import load_app_settings; print('Config OK')"

# Verificar SUMO
sumo-gui --version

# Verificar GPU (si aplica)
python test_verificar_gpu.py
```

### 3. Logs Recientes

Copia los últimos logs del terminal donde ejecutas los servicios.

## Problemas Comunes

Según los síntomas, puedo ayudarte con:

- **Error de conexión**: API no disponible
- **Simulaciones desincronizadas**: Diferencias temporales > 1s
- **Modelo DQN no carga**: Archivos .h5 faltantes o corruptos
- **ConfigValidationError**: Errores en config.yaml
- **TraCIException**: Problemas con SUMO
- **Pre-commit falla**: Problemas de formato de código

## Recursos de Ayuda

- [Troubleshooting Guide](./../TROUBLESHOOTING.md)
- Scripts de prueba: `test_sync.py`, `test_reinicio_api.py`
- Configuración mínima de emergencia en `config.yaml`

¿Cuál es el problema específico que estás experimentando?
