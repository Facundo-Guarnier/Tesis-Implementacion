# Design Document - New DQN Optimization Implementation

## Overview

This design document outlines the architecture for implementing new DQN optimizations in the intelligent traffic light system. The design follows the established patterns from the comprehensive DQN guide and ensures seamless integration with the existing training pipeline.

## Architecture

### High-Level Architecture

```
Configuration Layer (config.yaml + config_models.py)
    ↓
Optimization Factory (optimization_factory.py)
    ↓
Optimization Implementations (optimizations/)
    ↓
DQN Training Pipeline (DQN/trainer/)
    ↓
Performance Monitoring (metrics and logging)
```

### Component Integration

The new optimization system integrates with existing components:

- **Configuration System**: Extends `config_models.py` with optimization-specific settings
- **DQN Trainer**: Modifies training loop to apply optimizations
- **Model Architecture**: Allows optimizations to modify network structure
- **Logging System**: Captures optimization-specific metrics

## Components and Interfaces

### 1. Configuration Models Extension

**File**: `src/traffic_system/core/config_models.py`

```python
class OptimizationSettings(BaseModel):
    """Configuration for DQN optimizations."""

    # Base optimization control
    enabled: bool = False
    optimization_type: str = "baseline"  # baseline, advanced, experimental

    # Specific optimization parameters
    use_spectral_normalization: bool = False
    spectral_norm_power_iterations: int = 1

    use_self_attention: bool = False
    attention_heads: int = 4

    use_layer_normalization: bool = False
    layer_norm_epsilon: float = 1e-6

    # Performance tuning
    optimization_frequency: int = 1  # Apply every N training steps
    warmup_steps: int = 100  # Steps before optimization activates

    # Monitoring
    log_optimization_metrics: bool = True
    save_optimization_checkpoints: bool = False

class EntrenamientoSettings(BaseModel):
    # ... existing fields ...

    # New optimization section
    optimizations: OptimizationSettings = OptimizationSettings()
```

### 2. Optimization Factory

**File**: `src/traffic_system/decision/DQN/optimizations/optimization_factory.py`

```python
from abc import ABC, abstractmethod
from typing import Dict, Any
import tensorflow as tf

class BaseOptimization(ABC):
    """Base class for all DQN optimizations."""

    def __init__(self, config: OptimizationSettings):
        self.config = config
        self.metrics: Dict[str, float] = {}

    @abstractmethod
    def apply_to_model(self, model: tf.keras.Model) -> tf.keras.Model:
        """Apply optimization to model architecture."""
        pass

    @abstractmethod
    def apply_to_training(self, training_step: Dict[str, Any]) -> Dict[str, Any]:
        """Apply optimization to training step."""
        pass

    @abstractmethod
    def get_metrics(self) -> Dict[str, float]:
        """Return optimization-specific metrics."""
        pass

class OptimizationFactory:
    """Factory for creating and managing DQN optimizations."""

    _optimizations: Dict[str, type] = {}

    @classmethod
    def register(cls, name: str, optimization_class: type):
        """Register a new optimization."""
        cls._optimizations[name] = optimization_class

    @classmethod
    def create(cls, config: OptimizationSettings) -> BaseOptimization:
        """Create optimization based on configuration."""
        if not config.enabled:
            return BaselineOptimization(config)

        optimization_class = cls._optimizations.get(config.optimization_type)
        if not optimization_class:
            raise ValueError(f"Unknown optimization type: {config.optimization_type}")

        return optimization_class(config)
```

### 3. Example Optimization Implementation

**File**: `src/traffic_system/decision/DQN/optimizations/spectral_normalization.py`

```python
import tensorflow as tf
from .optimization_factory import BaseOptimization, OptimizationFactory

class SpectralNormalizationOptimization(BaseOptimization):
    """Spectral normalization for improved training stability."""

    def apply_to_model(self, model: tf.keras.Model) -> tf.keras.Model:
        """Apply spectral normalization to dense layers."""
        if not self.config.use_spectral_normalization:
            return model

        # Modify model layers to include spectral normalization
        for layer in model.layers:
            if isinstance(layer, tf.keras.layers.Dense):
                # Apply spectral normalization wrapper
                layer.kernel_constraint = tf.keras.constraints.UnitNorm(axis=0)

        return model

    def apply_to_training(self, training_step: Dict[str, Any]) -> Dict[str, Any]:
        """Apply spectral normalization during training."""
        # Add spectral norm metrics to training step
        if 'metrics' not in training_step:
            training_step['metrics'] = {}

        training_step['metrics']['spectral_norm_active'] = True
        return training_step

    def get_metrics(self) -> Dict[str, float]:
        """Return spectral normalization metrics."""
        return {
            'spectral_norm_power_iterations': self.config.spectral_norm_power_iterations,
            'spectral_norm_enabled': float(self.config.use_spectral_normalization)
        }

# Register the optimization
OptimizationFactory.register('spectral_norm', SpectralNormalizationOptimization)
```

### 4. Training Pipeline Integration

**File**: `src/traffic_system/decision/DQN/trainer/dqn_trainer.py` (modifications)

```python
from ..optimizations.optimization_factory import OptimizationFactory

class DQNTrainer:
    def __init__(self, config: EntrenamientoSettings):
        # ... existing initialization ...

        # Initialize optimization
        self.optimization = OptimizationFactory.create(config.optimizations)
        logger.info(f"🧪 DQN Optimization: {config.optimizations.optimization_type}")

    def _build_model(self) -> tf.keras.Model:
        """Build DQN model with optimizations."""
        # ... existing model building ...

        # Apply optimization to model
        model = self.optimization.apply_to_model(model)

        return model

    def _training_step(self, batch: Dict[str, Any]) -> Dict[str, float]:
        """Execute single training step with optimizations."""
        # Apply optimization to training step
        batch = self.optimization.apply_to_training(batch)

        # ... existing training logic ...

        # Collect optimization metrics
        optimization_metrics = self.optimization.get_metrics()
        metrics.update(optimization_metrics)

        return metrics
```

## Data Models

### Optimization Configuration Schema

```yaml
# config.yaml extension
decision:
  entrenamiento:
    optimizations:
      enabled: true
      optimization_type: "spectral_norm"

      # Spectral Normalization
      use_spectral_normalization: true
      spectral_norm_power_iterations: 1

      # Self-Attention
      use_self_attention: false
      attention_heads: 4

      # Layer Normalization
      use_layer_normalization: false
      layer_norm_epsilon: 1e-6

      # Performance
      optimization_frequency: 1
      warmup_steps: 100

      # Monitoring
      log_optimization_metrics: true
      save_optimization_checkpoints: false
```

### Metrics Data Model

```python
class OptimizationMetrics(BaseModel):
    """Metrics for optimization monitoring."""

    optimization_type: str
    enabled: bool
    training_step: int

    # Performance metrics
    forward_pass_time: float
    backward_pass_time: float
    memory_usage_mb: float

    # Optimization-specific metrics
    spectral_norm_violations: int = 0
    attention_weights_entropy: float = 0.0
    layer_norm_variance: float = 0.0

    # Training impact
    gradient_norm: float
    loss_improvement: float
    q_value_stability: float
```

## Error Handling

### Configuration Validation

```python
def validate_optimization_config(config: OptimizationSettings) -> List[str]:
    """Validate optimization configuration and return errors."""
    errors = []

    if config.enabled and not config.optimization_type:
        errors.append("optimization_type es requerido cuando optimizations.enabled=true")

    if config.use_spectral_normalization and config.spectral_norm_power_iterations < 1:
        errors.append("spectral_norm_power_iterations debe ser >= 1")

    if config.use_self_attention and config.attention_heads < 1:
        errors.append("attention_heads debe ser >= 1")

    return errors
```

### Runtime Error Handling

```python
def safe_apply_optimization(optimization: BaseOptimization, model: tf.keras.Model) -> tf.keras.Model:
    """Safely apply optimization with fallback."""
    try:
        return optimization.apply_to_model(model)
    except Exception as e:
        logger.error(f"❌ Error aplicando optimización: {e}")
        logger.warning("⚠️ Usando configuración baseline como fallback")
        return model  # Return unmodified model
```

## Testing Strategy

### Unit Tests

1. **Configuration Validation Tests**: Test Pydantic model validation
2. **Optimization Factory Tests**: Test registration and creation
3. **Individual Optimization Tests**: Test each optimization implementation
4. **Integration Tests**: Test optimization with DQN trainer

### Performance Tests

1. **Benchmark Tests**: Compare optimization performance vs baseline
2. **Memory Usage Tests**: Monitor GPU/CPU memory consumption
3. **Training Speed Tests**: Measure impact on training time
4. **Convergence Tests**: Validate that optimizations improve convergence

### Integration Tests

```python
def test_optimization_integration():
    """Test complete optimization integration."""
    # Load configuration with optimization enabled
    config = load_test_config_with_optimization()

    # Create trainer with optimization
    trainer = DQNTrainer(config.decision.entrenamiento)

    # Verify optimization is applied
    assert trainer.optimization.config.enabled

    # Run short training session
    metrics = trainer.train_single_epoch()

    # Verify optimization metrics are collected
    assert 'spectral_norm_enabled' in metrics

    logger.info("✅ Optimization integration test passed")
```

This design ensures that new DQN optimizations can be added systematically while maintaining the project's standards for configuration management, error handling, and performance monitoring.
