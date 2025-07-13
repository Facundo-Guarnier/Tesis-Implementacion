# Development Quick Start

Guía rápida para que los agentes de IA puedan comenzar a trabajar inmediatamente.

## ⚡ Inicio Rápido

### 1. Configuración del Entorno

```powershell
# Crear entorno virtual
python -m venv venv
.\venv\Scripts\Activate.ps1

# Instalar dependencias
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Configurar pre-commit hooks
git config core.hooksPath .githooks
```

### 2. Ejecutar el Sistema

```powershell
# Terminal 1: Simulación
python run_simulation_provider.py

# Terminal 2: Agente de decisión
python run_decision_agent.py
```

### 3. Pruebas Rápidas

```powershell
# Probar sincronización
python test_sync.py

# Probar reinicio de API
python test_reinicio_api.py

# Entrenamiento completo
python test_entrenamiento_dqn_completo.py
```

## 🎯 Flujos de Trabajo Comunes

### Entrenar un Nuevo Modelo DQN

1. Editar `config.yaml`:
   ```yaml
   decision:
     entrenamiento:
       entrenar: True
       num_epocas: 25
   ```
2. Ejecutar: `python run_decision_agent.py`
3. Cada epoca del modelos se guarda en `results/training/`

### Usar un Modelo Entrenado

1. Editar `config.yaml`:
   ```yaml
   decision:
     entrenamiento:
       entrenar: False
     path_modelo_entrenado: "assets/dqn_models/modelo.h5"
   ```
2. Ejecutar: `python run_decision_agent.py`

### Procesar Videos con YOLO

1. Editar `config.yaml`:
   ```yaml
   deteccion:
     un_video:
       procesar: True
       path_origen: "ruta/al/video.mp4"
       zona: "Zona A"
   ```
2. Ejecutar: `python run_detection_provider.py`

## 🔧 Comandos de Desarrollo

### Calidad de Código

```powershell
# Ejecutar todas las herramientas
powershell -ExecutionPolicy Bypass -File .githooks/pre-commit.ps1

# Solo Black
black src/

# Solo Ruff
ruff check src/ --fix

# Solo MyPy
mypy src/
```

### Estructura de Archivos Importantes

- **Configuración**: `config.yaml` + `src/traffic_system/core/config_models.py`
- **APIs**: `src/traffic_system/api/`
- **Lógica de negocio**: `src/traffic_system/{detection,simulation,decision}/app.py`
- **Modelo DQN en uso**: `​assets/dqn_models/`
- **Epocas de modelos DQN entrenados**: `results/training/`
- **Mapas SUMO**: `assets/sumo_maps/MapaDe0/`

## 🚨 Problemas Comunes

### La simulación no inicia

- Verificar que SUMO esté instalado: `sumo-gui --version`
- Revisar rutas en `config.yaml`

### Error de sincronización

- Verificar endpoint `/sincronizacion`
- Reinicar con `POST /simulacion/reiniciar`

### Pre-commit falla

- Ejecutar `black src/` y `ruff check src/ --fix`
- Hacer commit nuevamente

## 📊 URLs de Desarrollo

- API Simulación: http://127.0.0.1:5000
- Ver sincronización: http://127.0.0.1:5000/sincronizacion
- Estado general: http://127.0.0.1:5000/reporte
