# Technology Stack & Build System

## Build System & Package Management

**Primary Package Manager**: Poetry (modern Python dependency management)
- **NEVER use `pip install`** - always use Poetry commands
- Dependencies defined in `pyproject.toml`
- Lock file: `poetry.lock` (committed to version control)
- **AI Agents**: NEVER execute pre-commit, black, ruff, mypy commands - only modify code

### Essential Commands

```bash
# Environment setup
poetry install                    # Install all dependencies
poetry shell                     # Activate virtual environment
poetry add <package>             # Add runtime dependency
poetry add <package> --group dev # Add development dependency

# System execution (microservices architecture)
poetry run python run_simulation_provider.py  # Terminal 1: SUMO simulation + API
poetry run python run_decision_agent.py       # Terminal 2: DQN agent
poetry run python run_detection_provider.py   # Optional: YOLOv8 detection
poetry run python run_reporting_service.py    # Optional: Analytics

# Integration testing
poetry run python test_sincronizacion_completo.py  # Verify S1-S2 sync
poetry run python test_reinicio_api.py            # Test API restart
poetry run python test_entrenamiento_dqn_completo.py  # Full DQN training
poetry run pre-commit install   # Setup code quality hooks (human only)
```

## Core Technology Stack

### Machine Learning & AI
- **TensorFlow 2.19.0**: Deep learning framework for DQN training
  - Linux: `tensorflow[and-cuda]` (GPU support)
  - Windows: `tensorflow` (CPU only to avoid config complexity)
- **Ultralytics YOLOv8**: Real-time object detection for vehicle counting
- **NumPy**: Numerical computing and array operations
- **Pandas**: Data manipulation and analysis
- **SciPy**: Scientific computing utilities

### Traffic Simulation
- **SUMO**: Simulation of Urban Mobility (external dependency)
  - Linux: `/usr/share/sumo`
  - Windows: `C:\sumo`
- **TraCI**: Traffic Control Interface for SUMO communication

### Web Framework & APIs
- **Flask**: Lightweight web framework for REST APIs
- **Requests**: HTTP client for inter-service communication
- **Pydantic**: Data validation and settings management

### Computer Vision
- **OpenCV**: Image and video processing
- **Pillow**: Image manipulation
- **Supervision**: Computer vision utilities

### Configuration & Data
- **PyYAML**: YAML configuration file parsing
- **Pydantic**: Configuration validation and type safety

## Code Quality & Development Tools

### Automated Code Quality (Pre-commit)
- **Black**: Code formatter (88 character line limit)
- **Ruff**: Fast linter (replaces flake8, pylint, isort) with auto-fix
- **MyPy**: Static type checking with strict configuration
- **Pre-commit hooks**: Run automatically on git commit

### Critical Rules for AI Agents
- **NEVER execute** formatting/linting commands (`black`, `ruff`, `mypy`, `pre-commit`)
- **NEVER use `print()`** - always use logging with emojis (✅❌⚠️🧪)
- **NEVER use `typing.cast()`** - use Pydantic validation instead
- **Always handle ValidationError** from Pydantic models

### Configuration Files
- `pyproject.toml`: Project metadata, dependencies, tool configuration
- `config.yaml`: Application configuration (validated by Pydantic)
- `.pre-commit-config.yaml`: Code quality automation
- `.github/copilot-instructions.md`: Comprehensive AI agent guidelines

## Python Version & Type Safety

- **Python 3.11-3.12**: Required version range
- **Strict typing**: All functions must have type annotations
- **Pydantic validation**: All configuration uses Pydantic models
- **Error handling**: Robust exception handling required

### Critical Type Safety Rules
- **NEVER use `typing.cast()`** - use Pydantic validation instead
- **Always handle ValidationError** from Pydantic
- **Use union types** (`str | None`) instead of Optional
- **Strict typing**: All functions must have type annotations
- **Robust error handling**: Capture ValidationError and RequestException

## Architecture Patterns

### Microservices Architecture
- **Service isolation**: Each service runs independently
- **REST API communication**: Services communicate via HTTP APIs
- **Configuration-driven**: All behavior controlled via `config.yaml`

### Configuration Management
- **Single source of truth**: `config.yaml` validated by `config_models.py`
- **Pydantic models**: Type-safe configuration with validation
- **Environment-specific**: Different configs for dev/prod

### Logging Standards
- **Structured logging**: Consistent format across services
- **Emoji indicators**: Visual identification (✅❌⚠️🧪)
- **No print statements**: Always use logging module

## File Structure Conventions

```
src/traffic_system/
├── core/                    # Shared utilities and configuration
│   ├── config_models.py    # Pydantic models (source of truth)
│   ├── config_loader.py    # Configuration loading logic
│   └── api_models.py       # API request/response models
├── api/                    # Flask REST APIs
├── api_client/            # HTTP clients for consuming APIs
├── {service}/app.py       # Main application logic per service
└── {service}/            # Service-specific modules
```

### Import Conventions
- **Absolute imports**: Always from `src/` root
- **Example**: `from src.traffic_system.core.config_loader import load_app_settings`

## External Dependencies

### SUMO Installation
- **Linux**: Package manager installation to `/usr/share/sumo`
- **Windows**: Manual installation to `C:\sumo`
- **Configuration**: Path specified in `config.yaml`

### GPU Support
- **Linux**: Automatic CUDA support via `tensorflow[and-cuda]`
- **Windows**: CPU-only to avoid configuration complexity
- **Training**: GPU recommended for DQN training performance

## DQN Training & Optimization

### Key DQN Concepts
- **Experience Replay**: Stores (state, action, reward, next_state) tuples for training
- **Target Network**: Separate network updated every 100 steps for stability
- **Double DQN**: Reduces Q-value overestimation using two networks
- **Dueling DQN**: Separates state value V(s) and action advantage A(s,a)
- **Prioritized Experience Replay (PER)**: Samples important experiences more frequently

### Critical Training Parameters
- **Batch Dynamic**: Start training with 32 experiences (not 256) for 5.3x faster start
- **Warmup Steps**: 250 initial steps without training to populate traffic
- **Learning Rate**: 0.0005 with adaptive decay and plateau detection
- **Gradient Clipping**: `clipnorm=1.0` (NEVER use clipvalue - causes TensorFlow conflicts)
- **Huber Loss**: More robust than MSE for outlier handling

### Anti-Gradient Vanishing Solutions
- **He Initialization**: Optimized weight initialization for ReLU networks
- **Batch Normalization**: Normalizes layer inputs for stable gradients
- **LeakyReLU**: Prevents dying neurons with small negative gradients
- **Residual Connections**: Skip connections for deep networks

### Performance Optimizations
- **JIT Compilation**: XLA acceleration for GPU (+10-15% speed)
- **Mixed Precision**: FP16 training for modern GPUs
- **Early Stopping**: Automatic convergence detection
- **Evaluation Frequency**: Every 10 epochs (not 5) for +2-5% speed
