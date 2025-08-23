# Design Document - Traffic Logic Enhancement

## Overview

This design document outlines the architecture for enhancing the traffic light logic system in the intelligent traffic control project. The design builds upon the existing SUMO integration and DQN decision-making framework while adding advanced traffic management capabilities.

## Architecture

### Enhanced Traffic Logic Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Traffic Logic Layer                          │
├─────────────────────────────────────────────────────────────────┤
│  Advanced Phase Manager  │  Dynamic Duration Controller         │
│  Emergency Handler       │  Pattern Recognition Engine          │
│  Multi-Intersection      │  Real-Time Monitor                   │
└─────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────┐
│                    DQN Integration Layer                        │
├─────────────────────────────────────────────────────────────────┤
│  Enhanced State Space    │  Advanced Action Space               │
│  Reward Function Ext.   │  Learning Integration                │
└─────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────┐
│                    SUMO Integration Layer                       │
├─────────────────────────────────────────────────────────────────┤
│  Phase Validation       │  Safety Enforcement                  │
│  Timing Control         │  State Synchronization               │
└─────────────────────────────────────────────────────────────────┘
```

### Component Integration Flow

```
Traffic Conditions → Pattern Recognition → Phase Strategy Selection
        ↓                      ↓                      ↓
Emergency Detection → Priority Handling → Dynamic Phase Control
        ↓                      ↓                      ↓
DQN Decision Making → Action Validation → SUMO Execution
        ↓                      ↓                      ↓
Performance Monitoring → Learning Feedback → Strategy Optimization
```

## Components and Interfaces

### 1. Enhanced Traffic Phase Models

**File**: `src/traffic_system/simulation/traffic_logic/phase_models.py`

```python
from enum import Enum
from dataclasses import dataclass
from typing import List, Dict, Optional
import numpy as np

class PhaseType(Enum):
    """Traffic light phase types."""
    NORMAL = "normal"
    EMERGENCY = "emergency"
    PRIORITY = "priority"
    TRANSITION = "transition"

class TrafficDirection(Enum):
    """Traffic flow directions."""
    NORTH_SOUTH = "north_south"
    EAST_WEST = "east_west"
    LEFT_TURN = "left_turn"
    RIGHT_TURN = "right_turn"

@dataclass
class TrafficPhase:
    """Enhanced traffic phase definition."""
    phase_id: str
    phase_type: PhaseType
    duration_min: float  # Minimum duration in seconds
    duration_max: float  # Maximum duration in seconds
    duration_optimal: float  # Optimal duration for normal conditions

    # SUMO phase definitions for each traffic light
    semaforo_1: str  # e.g., "GGGGGGrrrrr"
    semaforo_2: str  # e.g., "GGGrrrrrGGg"
    semaforo_3: str  # e.g., "GGgGGGrrrrr"
    semaforo_4: str  # e.g., "GGGrrrrGGg"

    # Traffic flow characteristics
    primary_directions: List[TrafficDirection]
    conflicting_phases: List[str]  # Phases that cannot run simultaneously

    # Performance metrics
    expected_throughput: float  # Vehicles per minute
    safety_clearance: float  # Clearance time in seconds

    def validate_phase_definition(self) -> List[str]:
        """Validate phase definition for safety and consistency."""
        errors = []

        # Validate SUMO phase strings
        for semaforo_name, phase_str in [
            ("semaforo_1", self.semaforo_1),
            ("semaforo_2", self.semaforo_2),
            ("semaforo_3", self.semaforo_3),
            ("semaforo_4", self.semaforo_4)
        ]:
            if not self._validate_sumo_phase(phase_str):
                errors.append(f"Invalid SUMO phase for {semaforo_name}: {phase_str}")

        # Validate duration constraints
        if self.duration_min >= self.duration_max:
            errors.append("Minimum duration must be less than maximum duration")

        if not (self.duration_min <= self.duration_optimal <= self.duration_max):
            errors.append("Optimal duration must be between min and max durations")

        return errors

    def _validate_sumo_phase(self, phase_str: str) -> bool:
        """Validate SUMO phase string format."""
        valid_chars = set('Ggyro')  # Green, yellow, red, off
        return all(c in valid_chars for c in phase_str)

@dataclass
class PhaseTransition:
    """Traffic phase transition definition."""
    from_phase: str
    to_phase: str
    transition_time: float  # Time required for safe transition
    transition_phases: List[str]  # Intermediate phases (e.g., yellow phases)
    safety_validated: bool = False

    def validate_transition(self, phase_registry: Dict[str, TrafficPhase]) -> bool:
        """Validate that transition is safe and feasible."""
        if self.from_phase not in phase_registry or self.to_phase not in phase_registry:
            return False

        from_phase = phase_registry[self.from_phase]
        to_phase = phase_registry[self.to_phase]

        # Check if phases are conflicting
        if to_phase.phase_id in from_phase.conflicting_phases:
            return len(self.transition_phases) > 0  # Requires intermediate phases

        return True
```

### 2. Advanced Phase Manager

**File**: `src/traffic_system/simulation/traffic_logic/phase_manager.py`

```python
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class AdvancedPhaseManager:
    """Advanced traffic phase management with dynamic control."""

    def __init__(self, config: TrafficLogicSettings):
        self.config = config
        self.phase_registry: Dict[str, TrafficPhase] = {}
        self.transition_registry: Dict[Tuple[str, str], PhaseTransition] = {}
        self.current_phases: Dict[str, str] = {}  # intersection_id -> phase_id
        self.phase_start_times: Dict[str, datetime] = {}
        self.emergency_mode: bool = False

        self._initialize_phases()
        self._initialize_transitions()

    def _initialize_phases(self):
        """Initialize traffic phases from configuration."""
        # Standard phases based on existing traffic_logic.md
        self.phase_registry.update({
            "ns_main": TrafficPhase(
                phase_id="ns_main",
                phase_type=PhaseType.NORMAL,
                duration_min=15.0,
                duration_max=60.0,
                duration_optimal=30.0,
                semaforo_1="GGGGGGrrrrr",
                semaforo_2="GgGGrrrrGgGg",
                semaforo_3="GgGgGgGGrrrr",
                semaforo_4="GGGrrrrGGg",
                primary_directions=[TrafficDirection.NORTH_SOUTH],
                conflicting_phases=["ew_main", "left_turn_all"],
                expected_throughput=45.0,
                safety_clearance=3.0
            ),
            "ew_main": TrafficPhase(
                phase_id="ew_main",
                phase_type=PhaseType.NORMAL,
                duration_min=15.0,
                duration_max=60.0,
                duration_optimal=25.0,
                semaforo_1="rrrrrrGGgGG",
                semaforo_2="GGGGGGrrrrrr",
                semaforo_3="rrrrrrGGGGG",
                semaforo_4="rrrGGGGrrr",
                primary_directions=[TrafficDirection.EAST_WEST],
                conflicting_phases=["ns_main", "left_turn_all"],
                expected_throughput=38.0,
                safety_clearance=3.0
            ),
            "emergency_ns": TrafficPhase(
                phase_id="emergency_ns",
                phase_type=PhaseType.EMERGENCY,
                duration_min=10.0,
                duration_max=30.0,
                duration_optimal=15.0,
                semaforo_1="GGGGGGrrrrr",
                semaforo_2="GGGrrrrrGGg",
                semaforo_3="GGgGGGrrrrr",
                semaforo_4="GGGrrrrGGg",
                primary_directions=[TrafficDirection.NORTH_SOUTH],
                conflicting_phases=[],  # Emergency phases override conflicts
                expected_throughput=60.0,
                safety_clearance=1.0
            )
        })

        # Validate all phases
        for phase_id, phase in self.phase_registry.items():
            errors = phase.validate_phase_definition()
            if errors:
                logger.error(f"❌ Phase validation errors for {phase_id}: {errors}")
            else:
                logger.info(f"✅ Phase {phase_id} validated successfully")

    def select_optimal_phase(self, intersection_id: str, traffic_state: Dict[str, float],
                           emergency_detected: bool = False) -> str:
        """Select optimal phase based on current traffic conditions."""
        if emergency_detected and not self.emergency_mode:
            return self._handle_emergency_phase_selection(traffic_state)

        if self.emergency_mode and not emergency_detected:
            self._exit_emergency_mode()

        # Normal phase selection logic
        current_phase = self.current_phases.get(intersection_id)
        phase_duration = self._get_current_phase_duration(intersection_id)

        # Check if current phase should continue
        if current_phase and self._should_continue_phase(current_phase, phase_duration, traffic_state):
            return current_phase

        # Select new optimal phase
        return self._calculate_optimal_phase(traffic_state)

    def _calculate_optimal_phase(self, traffic_state: Dict[str, float]) -> str:
        """Calculate optimal phase based on traffic conditions."""
        phase_scores = {}

        for phase_id, phase in self.phase_registry.items():
            if phase.phase_type == PhaseType.EMERGENCY:
                continue  # Skip emergency phases in normal selection

            # Calculate phase score based on traffic demand
            score = 0.0

            # Score based on traffic in primary directions
            for direction in phase.primary_directions:
                direction_demand = self._get_direction_demand(direction, traffic_state)
                score += direction_demand * phase.expected_throughput

            # Penalty for conflicting traffic
            for conflicting_phase_id in phase.conflicting_phases:
                conflicting_phase = self.phase_registry[conflicting_phase_id]
                for direction in conflicting_phase.primary_directions:
                    conflicting_demand = self._get_direction_demand(direction, traffic_state)
                    score -= conflicting_demand * 0.3  # Penalty factor

            phase_scores[phase_id] = score

        # Select phase with highest score
        optimal_phase = max(phase_scores.keys(), key=lambda p: phase_scores[p])
        logger.info(f"🎯 Optimal phase selected: {optimal_phase} (score: {phase_scores[optimal_phase]:.2f})")

        return optimal_phase

    def _handle_emergency_phase_selection(self, traffic_state: Dict[str, float]) -> str:
        """Handle emergency vehicle phase selection."""
        self.emergency_mode = True
        logger.warning("🚨 Emergency mode activated")

        # Determine emergency direction from traffic state
        # This would integrate with emergency vehicle detection system
        emergency_direction = self._detect_emergency_direction(traffic_state)

        if emergency_direction == TrafficDirection.NORTH_SOUTH:
            return "emergency_ns"
        elif emergency_direction == TrafficDirection.EAST_WEST:
            return "emergency_ew"  # Would need to be defined

        # Default emergency phase
        return "emergency_ns"

    def apply_phase_transition(self, intersection_id: str, new_phase_id: str) -> bool:
        """Apply phase transition with safety validation."""
        current_phase_id = self.current_phases.get(intersection_id)

        if current_phase_id == new_phase_id:
            return True  # No transition needed

        # Validate transition
        if current_phase_id:
            transition_key = (current_phase_id, new_phase_id)
            if transition_key in self.transition_registry:
                transition = self.transition_registry[transition_key]
                if not transition.validate_transition(self.phase_registry):
                    logger.error(f"❌ Invalid transition from {current_phase_id} to {new_phase_id}")
                    return False

        # Apply transition
        self.current_phases[intersection_id] = new_phase_id
        self.phase_start_times[intersection_id] = datetime.now()

        phase = self.phase_registry[new_phase_id]
        logger.info(f"🚦 Phase transition: {intersection_id} -> {new_phase_id} ({phase.phase_type.value})")

        return True

    def get_phase_states(self, phase_id: str) -> Dict[str, str]:
        """Get SUMO phase states for all traffic lights."""
        if phase_id not in self.phase_registry:
            logger.error(f"❌ Unknown phase ID: {phase_id}")
            return {}

        phase = self.phase_registry[phase_id]
        return {
            "semaforo_1": phase.semaforo_1,
            "semaforo_2": phase.semaforo_2,
            "semaforo_3": phase.semaforo_3,
            "semaforo_4": phase.semaforo_4
        }

    def get_dynamic_duration(self, phase_id: str, traffic_state: Dict[str, float]) -> float:
        """Calculate dynamic phase duration based on traffic conditions."""
        if phase_id not in self.phase_registry:
            return 30.0  # Default duration

        phase = self.phase_registry[phase_id]

        # Base duration
        duration = phase.duration_optimal

        # Adjust based on traffic demand
        total_demand = sum(traffic_state.get(f"zone_{i}_wait_time", 0) for i in range(12))
        demand_factor = min(total_demand / 100.0, 2.0)  # Cap at 2x

        # Calculate adjusted duration
        adjusted_duration = duration * (0.7 + 0.6 * demand_factor)

        # Enforce min/max constraints
        final_duration = max(phase.duration_min,
                           min(phase.duration_max, adjusted_duration))

        logger.debug(f"🕐 Dynamic duration for {phase_id}: {final_duration:.1f}s (demand factor: {demand_factor:.2f})")

        return final_duration
```

### 3. DQN Integration Enhancement

**File**: `src/traffic_system/decision/DQN/enhanced_dqn_integration.py`

```python
import numpy as np
from typing import Dict, List, Tuple, Any

class EnhancedDQNIntegration:
    """Enhanced DQN integration with advanced traffic logic."""

    def __init__(self, phase_manager: AdvancedPhaseManager, config: DQNSettings):
        self.phase_manager = phase_manager
        self.config = config
        self.state_history: List[Dict[str, float]] = []
        self.action_history: List[int] = []
        self.pattern_detector = TrafficPatternDetector()

    def get_enhanced_state_space(self, base_state: np.ndarray,
                               traffic_context: Dict[str, Any]) -> np.ndarray:
        """Create enhanced state space with traffic logic features."""
        # Base state: [wait_times(12), vehicle_counts(12), previous_wait_times(12), previous_counts(12)]
        enhanced_features = []

        # Add phase timing features
        current_phase = traffic_context.get("current_phase")
        if current_phase:
            phase_duration = traffic_context.get("phase_duration", 0)
            phase_info = self.phase_manager.phase_registry.get(current_phase)
            if phase_info:
                # Normalized phase progress (0-1)
                phase_progress = min(phase_duration / phase_info.duration_optimal, 2.0)
                enhanced_features.append(phase_progress)

                # Phase efficiency (actual vs expected throughput)
                actual_throughput = traffic_context.get("actual_throughput", 0)
                efficiency = actual_throughput / max(phase_info.expected_throughput, 1.0)
                enhanced_features.append(efficiency)
        else:
            enhanced_features.extend([0.0, 0.0])

        # Add traffic pattern features
        pattern_features = self.pattern_detector.extract_pattern_features(
            self.state_history[-10:] if len(self.state_history) >= 10 else self.state_history
        )
        enhanced_features.extend(pattern_features)

        # Add emergency context
        emergency_detected = traffic_context.get("emergency_detected", False)
        enhanced_features.append(float(emergency_detected))

        # Combine base state with enhanced features
        enhanced_state = np.concatenate([base_state, np.array(enhanced_features)])

        return enhanced_state

    def map_action_to_phase(self, dqn_action: int, traffic_context: Dict[str, Any]) -> str:
        """Map DQN action to optimal traffic phase."""
        # Get available phases (excluding emergency phases unless needed)
        available_phases = []
        emergency_detected = traffic_context.get("emergency_detected", False)

        for phase_id, phase in self.phase_manager.phase_registry.items():
            if phase.phase_type == PhaseType.EMERGENCY and not emergency_detected:
                continue
            if phase.phase_type != PhaseType.EMERGENCY or emergency_detected:
                available_phases.append(phase_id)

        # Map action index to phase
        if available_phases:
            phase_index = dqn_action % len(available_phases)
            selected_phase = available_phases[phase_index]
        else:
            selected_phase = "ns_main"  # Fallback

        logger.debug(f"🤖 DQN action {dqn_action} mapped to phase {selected_phase}")
        return selected_phase

    def calculate_enhanced_reward(self, base_reward: float,
                                traffic_state: Dict[str, float],
                                action_context: Dict[str, Any]) -> float:
        """Calculate enhanced reward with traffic logic considerations."""
        enhanced_reward = base_reward

        # Phase efficiency bonus/penalty
        current_phase = action_context.get("current_phase")
        if current_phase and current_phase in self.phase_manager.phase_registry:
            phase_info = self.phase_manager.phase_registry[current_phase]
            actual_throughput = action_context.get("actual_throughput", 0)
            expected_throughput = phase_info.expected_throughput

            efficiency_ratio = actual_throughput / max(expected_throughput, 1.0)
            efficiency_bonus = (efficiency_ratio - 1.0) * 10.0  # Bonus for exceeding expectations
            enhanced_reward += efficiency_bonus

        # Emergency handling reward
        if action_context.get("emergency_detected", False):
            emergency_response_time = action_context.get("emergency_response_time", 0)
            if emergency_response_time < 5.0:  # Quick response bonus
                enhanced_reward += 20.0
            elif emergency_response_time > 15.0:  # Slow response penalty
                enhanced_reward -= 10.0

        # Pattern recognition reward
        if self.pattern_detector.is_pattern_optimized(self.state_history, self.action_history):
            enhanced_reward += 5.0  # Pattern optimization bonus

        # Safety compliance reward
        if action_context.get("safety_violations", 0) == 0:
            enhanced_reward += 2.0
        else:
            enhanced_reward -= action_context.get("safety_violations", 0) * 5.0

        return enhanced_reward

class TrafficPatternDetector:
    """Detect and analyze traffic patterns for optimization."""

    def __init__(self):
        self.pattern_memory: List[Dict[str, Any]] = []
        self.recognized_patterns: Dict[str, Dict[str, Any]] = {}

    def extract_pattern_features(self, state_history: List[Dict[str, float]]) -> List[float]:
        """Extract pattern features from state history."""
        if len(state_history) < 3:
            return [0.0] * 6  # Return zeros if insufficient history

        features = []

        # Traffic trend (increasing/decreasing/stable)
        recent_total = sum(state_history[-1].get(f"zone_{i}_wait_time", 0) for i in range(12))
        older_total = sum(state_history[-3].get(f"zone_{i}_wait_time", 0) for i in range(12))
        trend = (recent_total - older_total) / max(older_total, 1.0)
        features.append(np.clip(trend, -1.0, 1.0))

        # Traffic variance (stability measure)
        wait_times = [sum(state.get(f"zone_{i}_wait_time", 0) for i in range(12))
                     for state in state_history]
        variance = np.var(wait_times) / max(np.mean(wait_times), 1.0)
        features.append(min(variance, 2.0))

        # Directional imbalance
        ns_traffic = sum(state_history[-1].get(f"zone_{i}_wait_time", 0) for i in [0, 1, 6, 7])
        ew_traffic = sum(state_history[-1].get(f"zone_{i}_wait_time", 0) for i in [2, 3, 4, 5, 8, 9, 10, 11])
        imbalance = (ns_traffic - ew_traffic) / max(ns_traffic + ew_traffic, 1.0)
        features.append(np.clip(imbalance, -1.0, 1.0))

        # Peak detection (simple)
        is_peak = float(recent_total > np.mean(wait_times) + np.std(wait_times))
        features.append(is_peak)

        # Congestion level
        max_possible_wait = 12 * 100  # Assume max 100 seconds per zone
        congestion_level = recent_total / max_possible_wait
        features.append(min(congestion_level, 1.0))

        # Pattern stability
        if len(self.pattern_memory) > 0:
            stability = self._calculate_pattern_stability(state_history)
            features.append(stability)
        else:
            features.append(0.0)

        return features

    def is_pattern_optimized(self, state_history: List[Dict[str, float]],
                           action_history: List[int]) -> bool:
        """Check if current pattern is being optimized effectively."""
        if len(state_history) < 5 or len(action_history) < 5:
            return False

        # Simple optimization check: are wait times generally decreasing?
        recent_performance = [sum(state.get(f"zone_{i}_wait_time", 0) for i in range(12))
                            for state in state_history[-5:]]

        # Check for improvement trend
        improvement_count = sum(1 for i in range(1, len(recent_performance))
                              if recent_performance[i] < recent_performance[i-1])

        return improvement_count >= 3  # At least 3 out of 4 improvements
```

## Data Models

### Enhanced Configuration Schema

```yaml
# config.yaml extension
traffic_logic:
  enabled: true

  # Phase management
  phase_management:
    dynamic_duration: true
    min_phase_duration: 10.0
    max_phase_duration: 120.0
    safety_clearance_time: 3.0

  # Emergency handling
  emergency_handling:
    enabled: true
    detection_method: "api"  # "api", "simulation", "external"
    priority_override: true
    emergency_phase_duration: 15.0

  # Pattern recognition
  pattern_recognition:
    enabled: true
    history_length: 50
    pattern_threshold: 0.8
    adaptation_rate: 0.1

  # Multi-intersection coordination
  coordination:
    enabled: false
    coordination_radius: 500.0  # meters
    sync_tolerance: 2.0  # seconds

  # Performance monitoring
  monitoring:
    real_time_metrics: true
    performance_alerts: true
    optimization_logging: true
```

## Error Handling

### Traffic Logic Validation

```python
def validate_traffic_logic_config(config: TrafficLogicSettings) -> List[str]:
    """Validate traffic logic configuration."""
    errors = []

    if config.phase_management.min_phase_duration >= config.phase_management.max_phase_duration:
        errors.append("min_phase_duration debe ser menor que max_phase_duration")

    if config.phase_management.safety_clearance_time < 1.0:
        errors.append("safety_clearance_time debe ser al menos 1.0 segundos")

    if config.pattern_recognition.history_length < 10:
        errors.append("pattern_recognition.history_length debe ser al menos 10")

    return errors

def safe_phase_transition(from_phase: str, to_phase: str,
                         phase_manager: AdvancedPhaseManager) -> bool:
    """Safely execute phase transition with validation."""
    try:
        return phase_manager.apply_phase_transition("main_intersection", to_phase)
    except Exception as e:
        logger.error(f"❌ Error en transición de fase {from_phase} -> {to_phase}: {e}")
        # Fallback to safe default phase
        return phase_manager.apply_phase_transition("main_intersection", "ns_main")
```

## Testing Strategy

### Traffic Logic Integration Tests

```python
def test_advanced_phase_management():
    """Test advanced phase management functionality."""
    logger.info("🧪 Testing advanced phase management...")

    # Initialize phase manager
    config = load_test_config()
    phase_manager = AdvancedPhaseManager(config.traffic_logic)

    # Test phase selection
    traffic_state = {
        "zone_0_wait_time": 45.0,
        "zone_1_wait_time": 30.0,
        # ... more zones
    }

    optimal_phase = phase_manager.select_optimal_phase("main", traffic_state)
    assert optimal_phase in phase_manager.phase_registry

    # Test phase transition
    success = phase_manager.apply_phase_transition("main", optimal_phase)
    assert success

    # Test dynamic duration
    duration = phase_manager.get_dynamic_duration(optimal_phase, traffic_state)
    assert 10.0 <= duration <= 120.0

    logger.info("✅ Advanced phase management test passed")

def test_emergency_handling():
    """Test emergency vehicle handling."""
    logger.info("🧪 Testing emergency handling...")

    phase_manager = AdvancedPhaseManager(load_test_config().traffic_logic)

    # Simulate emergency detection
    traffic_state = {"emergency_detected": True}
    emergency_phase = phase_manager.select_optimal_phase("main", traffic_state, emergency_detected=True)

    assert "emergency" in emergency_phase
    assert phase_manager.emergency_mode

    logger.info("✅ Emergency handling test passed")

def test_dqn_integration():
    """Test DQN integration with enhanced traffic logic."""
    logger.info("🧪 Testing DQN integration...")

    phase_manager = AdvancedPhaseManager(load_test_config().traffic_logic)
    dqn_integration = EnhancedDQNIntegration(phase_manager, load_test_config().decision)

    # Test enhanced state space
    base_state = np.random.rand(48)  # Standard DQN state
    traffic_context = {
        "current_phase": "ns_main",
        "phase_duration": 25.0,
        "actual_throughput": 42.0,
        "emergency_detected": False
    }

    enhanced_state = dqn_integration.get_enhanced_state_space(base_state, traffic_context)
    assert len(enhanced_state) > len(base_state)

    # Test action mapping
    dqn_action = 5
    selected_phase = dqn_integration.map_action_to_phase(dqn_action, traffic_context)
    assert selected_phase in phase_manager.phase_registry

    logger.info("✅ DQN integration test passed")
```

This design provides a comprehensive enhancement to the traffic logic system while maintaining compatibility with the existing DQN framework and SUMO integration.
