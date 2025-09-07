# 📂 Estructura del Proyecto

A continuación, se presenta la estructura de directorios del proyecto de semáforos inteligentes.

## 🚀 Scripts de Inicio

```
run_simulation_provider.py     # Simulación SUMO + API REST (puerto 5000)
run_decision_agent.py          # Agente DQN de decisión
run_detection_provider.py      # Detección YOLOv8 (puerto 5000) 
run_reporting_service.py       # Servicios de reportes (puerto 5001)
run_frontend.py                # Frontend web Streamlit (puerto 8501)
```

## 📁 Arquitectura Principal

```
src/traffic_system/
├── api/                       # APIs Flask
│   ├── simulation_api.py
│   ├── decision_api.py
│   └── detection_api.py
├── api_client/                # Clientes para consumir APIs
│   ├── simulation_client.py
│   └── decision_client.py
├── core/                      # Configuración y modelos centrales
│   ├── config_models.py      # FUENTE DE VERDAD - Modelos Pydantic
│   └── config_loader.py      # Cargador de configuración
├── simulation/                # Lógica de simulación SUMO
│   └── app.py
├── decision/                  # Algoritmos DQN y toma de decisiones
│   └── app.py
├── detection/                 # Detección de vehículos YOLOv8
│   └── app.py
├── reporting/                 # Servicios de métricas y reportes
│   └── app.py
└── frontend/                  # 🌟 Frontend web Streamlit
    ├── app.py                 # Aplicación principal con 5 pestañas
    ├── config_manager.py      # Gestión de config.yaml
    ├── service_controller.py  # Control de microservicios
    ├── config/
    │   └── tooltips.py       # Tooltips para campos
    └── utils/
        └── utils.py          # Utilidades comunes
```

## 🗂️ Activos y Recursos

```
assets/
├── dqn_models/               # Modelos DQN entrenados (.h5, .keras)
├── sumo_maps/                # Mapas y configuraciones SUMO
│   ├── Mapa/
│   ├── MapaDe0/
│   └── MapaDe0_semaforos_de_30s/
├── yolo_models/              # Modelos YOLOv8 (.pt)
├── dataset-1080x1920-30fps/ # Dataset de video de alta resolución
├── dataset-576x1024-5fps/   # Dataset de video optimizado
└── detection_zones/         # Configuración de zonas de detección
    └── zones.yaml
```

## 📊 Resultados y Logs

```
results/
├── comparisons/              # Comparaciones de algoritmos
├── detection_results/        # Resultados de detección
├── reportes/                # Reportes de métricas por sesión
│   └── report_YYYY-MM-DD_HH-MM-SS/
│       └── reporte.db       # Base de datos SQLite de alertas
└── training/                # Resultados de entrenamiento DQN

logs/
└── services/                # Logs de microservicios
```

## ⚙️ Configuración

```
config.yaml                  # Configuración principal (validada por Pydantic)
config copy.yaml             # Copia de respaldo
config.yaml.backup           # Backup automático
pyproject.toml              # Dependencias Poetry y configuración herramientas
poetry.lock                 # Lock file de dependencias
```

## 🧪 Testing y Scripts

```
test_sincronizacion_completo.py    # Test de integración completo
test_entrenamiento_dqn_completo.py # Test de entrenamiento DQN
test_reinicio_api.py               # Test de reinicio de APIs
test_sumo_smoke.py                 # Test básico de SUMO
test_verificar_gpu.py              # Verificación de GPU para TensorFlow
test_verify_dependencies.py       # Verificación de dependencias
```

## 📚 Documentación

```
docs/
├── quickstart.md            # Guía de inicio rápido
├── frontend_usage.md        # 🌟 Documentación completa del frontend
├── 1_setup/                # Configuración inicial
│   ├── dependencies.md
│   └── project_structure.md
├── 2_guides/               # Guías de desarrollo
│   ├── tooling.md
│   └── contributing.md
└── 3_reference/           # Referencias técnicas
```

## 🎯 Flujo de Datos

```
Frontend Web (puerto 8501)
    ↓ (configuración)
config.yaml
    ↓ (validación)
Pydantic Models (config_models.py)
    ↓ (carga)
Microservicios:
├── Simulación (puerto 5000) ←→ Decisión
├── Detección (puerto 5000)
└── Reportes (puerto 5001)
    ↓ (métricas)
Base de Datos SQLite
    ↓ (visualización)
Frontend Web (pestaña Alertas)
```

## 🔧 Scripts de Utilidad

```
scripts/
├── Coordenadas_en_un_video.py  # Extracción de coordenadas
├── Print-Tree.ps1              # Visualización de estructura
├── Productor-Consumidor.py     # Patrones de concurrencia
└── Reescalar_resolucion.py     # Procesamiento de video
```
