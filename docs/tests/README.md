# 🧪 Documentación de Tests

Estructura de los principales scripts de prueba para el sistema de semáforos inteligentes.

## 📂 Estructura de Tests

```text
main_folder/
├── test_sumo_smoke.py              # Test de humo básico para SUMO
├── test_sincronizacion_completo.py # Test completo de sincronización
├── test_reinicio_api.py            # Test de reinicio vía API
├── test_entrenamiento_dqn_completo.py # Test de entrenamiento y configuración DQN
├── test_dispositivo_dqn.py         # Test de dispositivos DQN (patrón)
└── test_verificar_gpu.py           # Verificación de disponibilidad de GPU
```

> ℹ️ Ejecuta cada script con `poetry run python <nombre_script.py>` para validar la integración y funcionamiento de los componentes.
