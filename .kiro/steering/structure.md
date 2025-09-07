# Project Structure & Organization

## Root Level Structure

```
traffic-system/
├── run_*.py                 # Service entry points
├── config.yaml             # Main configuration file
├── pyproject.toml          # Poetry dependencies & tool config
├── src/traffic_system/     # Main source code
├── assets/                 # Models, maps, datasets
├── results/                # Generated outputs
├── docs/                   # Documentation
├── .github/                # AI instructions & workflows
└── tests/                  # Test scripts
```

## Source Code Organization (`src/traffic_system/`)

### Core Module (`core/`)
- **`config_models.py`**: Pydantic models - **SOURCE OF TRUTH** for configuration
- **`config_loader.py`**: Configuration loading and validation logic
- **`api_models.py`**: Request/response DTOs for APIs
- **`config_exceptions.py`**: Custom configuration exceptions
- **`types.py`**: Common type definitions

### Service Modules
Each service follows the same pattern:
```
{service}/
├── app.py              # Main application logic
├── {service}_service.py # Core business logic
└── {specific_modules}/ # Service-specific components
```

### API Layer (`api/`)
- **`simulation_server.py`**: SUMO simulation REST API
- **`detection_server.py`**: YOLOv8 detection REST API
- Flask-based microservices with standardized response format

### API Clients (`api_client/`)
- **`data_source_client.py`**: Client for consuming simulation API
- **`reporting_client.py`**: Client for reporting services
- HTTP clients for inter-service communication

## Service Architecture

### 1. Simulation Provider (`simulation/`)
- **Purpose**: SUMO traffic simulation management
- **Entry Point**: `run_simulation_provider.py`
- **API Port**: 5000
- **Key Components**:
  - `app.py`: SumoApp class for simulation control
  - `zones/`: Traffic zone definitions (A-L)
  - `comparison_logger.py`: RL vs fixed-time comparison

### 2. Decision Agent (`decision/`)
- **Purpose**: DQN reinforcement learning for traffic control
- **Entry Point**: `run_decision_agent.py`
- **Key Components**:
  - `DQN/`: Deep Q-Network implementation
  - `SARSA/`: Alternative RL algorithm (legacy)
  - `trainer/`: Training pipeline and evaluation

### 3. Detection Provider (`detection/`)
- **Purpose**: YOLOv8 vehicle detection from video
- **Entry Point**: `run_detection_provider.py`
- **API Port**: 5000 (shared with simulation)
- **Key Components**:
  - `App.py`: DetectionApp for video processing
  - `zones/`: Detection zone definitions
  - `stream_processing/`: Video analysis pipeline

### 4. Reporting Service (`reporting/`)
- **Purpose**: Analytics and performance metrics
- **Entry Point**: `run_reporting_service.py`
- **API Port**: 5001

## Assets Organization (`assets/`)

```
assets/
├── dqn_models/             # Trained DQN models (.h5 files)
├── sumo_maps/              # SUMO simulation maps
│   └── MapaDe0/           # Main intersection map
├── dataset-*/             # Video datasets for detection
└── yolo_models/           # YOLOv8 model files
```

## Results Organization (`results/`)

```
results/
├── training/              # DQN training outputs
├── detection_results/     # YOLO detection outputs
├── reportes/             # Simulation reports
└── deteccion_dataset/    # Batch detection results
```

## Configuration Hierarchy

### 1. Configuration Flow
```
config.yaml → config_models.py → AppSettings → Service Apps
```

### 2. Configuration Sections
- **`services`**: Port configuration for microservices (5000, 5001)
- **`deteccion`**: YOLOv8 detection settings, video processing, zones
- **`decision`**: DQN agent and training parameters (extensive ML config)
- **`sumo`**: SUMO simulation configuration, GUI, comparison mode
- **`reporte`**: Reporting and analytics settings, thresholds

### 3. Configuration Rules (CRITICAL)
- **Always update `config_models.py` FIRST** when adding new config
- **Then update `config.yaml`** with the new values
- **Use Pydantic validation** for all configuration access
- **Never hardcode values** - everything comes from config
- **Validate with Pydantic models** - type safety is mandatory

### 4. Advanced Configuration Features
- **Comparison Mode**: Run two SUMO simulations (S1 RL-controlled, S2 fixed-time)
- **Seed Management**: Fixed, random, or persistent random seeds for reproducibility
- **Training vs Inference**: Extensive DQN training parameters vs simple model path
- **Multi-platform**: Different TensorFlow configs for Linux (GPU) vs Windows (CPU)

## Import Patterns

### Absolute Imports (Required)
```python
# ✅ Correct
from src.traffic_system.core.config_loader import load_app_settings
from src.traffic_system.api.simulation_server import SumoAPI

# ❌ Incorrect
from ..core.config_loader import load_app_settings
```

### Service Communication
```python
# Services communicate via HTTP APIs, not direct imports
# Use api_client/ modules for inter-service communication
```

## File Naming Conventions

### Python Files
- **Service entry points**: `run_{service}_provider.py`
- **Main app logic**: `{service}/app.py` or `{service}/App.py`
- **API servers**: `{service}_server.py`
- **API clients**: `{service}_client.py`

### Configuration Files
- **Main config**: `config.yaml`
- **Pydantic models**: `config_models.py`
- **Tool configs**: `pyproject.toml`, `.pre-commit-config.yaml`

### Asset Files
- **DQN models**: `{ModelType}_{timestamp}_epoch_{n}.h5`
- **SUMO maps**: `mapa.sumocfg` (main config file)
- **YOLO models**: `yolov8n.pt` (standard naming)

## Zone System (Traffic Areas)

The system uses a 12-zone layout (A through L) for traffic monitoring:
- **Zones A-L**: Represent different traffic areas at the intersection
- **Consistent across services**: Same zone definitions in simulation and detection
- **Configuration**: Zone weights and parameters in `config.yaml`

## Testing Structure

### Integration Tests (Root Level)
- **`test_sincronizacion_completo.py`**: Verify S1-S2 simulation synchronization
- **`test_reinicio_api.py`**: Test API restart functionality
- **`test_entrenamiento_dqn_completo.py`**: Full DQN training validation
- **`test_semaforo_sync.py`**: Traffic light synchronization logic
- **`test_dispositivo_dqn.py`**: DQN model functionality
- **`test_verificar_gpu.py`**: GPU availability and TensorFlow configuration

### Test Patterns
- **Logging with emojis**: ✅ ❌ ⚠️ 🧪 for visual identification
- **API validation**: Check endpoints, status codes, response structure
- **Timeout handling**: 5-second timeouts for HTTP requests
- **Service dependencies**: Tests require running services (simulation, decision)

### Test Execution
```bash
poetry run python test_sincronizacion_completo.py
poetry run python test_reinicio_api.py
```

## Documentation Structure (`docs/`)

### Setup Documentation (`docs/1_setup/`)
- **`dependencies.md`**: Poetry and system dependencies
- **`project_structure.md`**: High-level architecture overview
- **`vscode_setup.md`**: IDE configuration and extensions

### Development Guides (`docs/2_guides/`)
- **`code_style.md`**: Python conventions (snake_case, PascalCase, logging)
- **`contributing.md`**: Git workflow, conventional commits, branching
- **`tooling.md`**: Black, Ruff, MyPy configuration and usage

### Technical Reference (`docs/3_reference/`)
- **`dqn_complete_guide.md`**: Comprehensive DQN implementation guide (2600+ lines)
- **`traffic_logic.md`**: Traffic light phases and SUMO state definitions
- **`yolo_model_info.md`**: YOLOv8 model classes and detection capabilities
- **`external_references.md`**: SUMO documentation and external resources

## AI Agent Guidelines (`.github/`)

### Core Instructions
- **`copilot-instructions.md`**: Master document with all AI agent rules
- **`instructions/`**: File-type specific instructions (Python, config, testing)
- **`prompts/`**: Reusable prompts for common tasks

### Key AI Rules from Documentation
- **Configuration Management**: Always update `config_models.py` before `config.yaml`
- **Type Safety**: Never use `typing.cast()`, always use Pydantic validation
- **Logging**: Use structured logging with emojis, never `print()`
- **Dependencies**: Only use Poetry, never `pip install`
- **Code Quality**: Never execute linting tools, only modify code
