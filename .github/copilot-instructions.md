# GitHub Copilot Instructions

## 🎯 Proyecto
Sistema semáforos inteligentes: YOLOv8 + DQN + SUMO + Streamlit

## 🏗️ Arquitectura
```
Frontend (8501) ↔ APIs ↔ Services
├─ Servicios      ├─ Decision Agent
├─ Configuración  ├─ Detection
├─ API            ├─ Simulation
├─ Alertas        └─ Reporting
└─ Métricas
```

## 📋 Reglas Críticas

### Dependencias
- **OBLIGATORIO**: Poetry (NUNCA pip install)
- Comando: `poetry add <package>` | `poetry install`

### Config
- `config.yaml` validado por `src/traffic_system/core/config_models.py`

### Estructura
```
src/traffic_system/
├─ api/               # APIs REST centralizadas
├─ api_client/        # Clientes para APIs
├─ core/              # Código base común
├─ decision/          # Agente de decisión DQN
├─ detection/         # Detección YOLOv8
├─ frontend/          # Streamlit 5 pestañas
├─ reporting/         # Reportes y métricas
└─ simulation/        # Simulación SUMO
```

## 🚀 Comandos
```bash
poetry install && poetry shell
poetry run python run_simulation_provider.py    # Simulation
poetry run python run_detection_provider.py     # Detection
poetry run python run_decision_agent.py         # Agente DQN
poetry run python run_reporting_service.py      # Reporting
poetry run python run_frontend.py              # 8501
```

## 🔧 Frontend (Streamlit)
- **Servicios**: Monitor servicios 🟢/🔴
- **Configuración**: Editor YAML + validación Pydantic
- **API**: Test endpoints REST
- **Alertas**: Eventos tiempo real
- **Métricas**: Dashboards Plotly

## 💾 Assets
- `assets/yolo_models/` - YOLOv8 models
- `assets/dqn_models/` - DQN trained models
- `assets/sumo_maps/` - SUMO maps
- `assets/detection_zones/zones.yaml`

## 🔍 Debug
```bash
# Logs
logs/services/{service}.log

# Puertos ocupados
netstat -ano | findstr :8501

# GPU check
poetry run python test_verificar_gpu.py
```

## 🎨 Código
- **Python**: Black, type hints obligatorios
- **APIs**: Flask-RESTful + JSON validation
