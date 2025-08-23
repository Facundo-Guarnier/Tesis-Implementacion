# Product Overview

## Sistema de Semáforos Inteligentes

This is a graduate thesis project for "Ingeniería en Informática" that addresses traffic congestion at intersections in Guaymallén, Mendoza, Argentina. The system proposes intelligent traffic lights to optimize traffic flow, reduce waiting times, and improve vehicular efficiency.

### Core Components

The system integrates three main technologies:
- **Vehicle Detection**: YOLOv8 for real-time vehicle detection from video streams
- **Traffic Simulation**: SUMO (Simulation of Urban Mobility) for traffic modeling and evaluation
- **Decision Making**: Deep Q-Network (DQN) reinforcement learning for real-time traffic light control

### System Architecture

The system follows a microservices architecture with four main services:
- **Detection Provider** (`run_detection_provider.py`): Handles vehicle detection using YOLOv8
- **Simulation Provider** (`run_simulation_provider.py`): Manages SUMO traffic simulation
- **Decision Agent** (`run_decision_agent.py`): Runs the DQN model for traffic light decisions
- **Reporting Service** (`run_reporting_service.py`): Generates simulation reports and analytics

### Key Features

- **Real-time vehicle detection**: YOLOv8-based counting across 12 traffic zones (A-L)
- **Reinforcement learning control**: DQN agent optimizes traffic light phases
- **Comparison mode**: Simultaneous RL vs fixed-time evaluation (S1 vs S2)
- **Advanced DQN variants**: Double DQN, Dueling DQN, Prioritized Experience Replay
- **GPU acceleration**: TensorFlow with CUDA support for training
- **Comprehensive analytics**: Detailed reporting and performance metrics

### Technical Achievements

- **5.3x faster training start**: Batch dynamic optimization (570 vs 3000+ steps)
- **50-67% training time reduction**: From 1200s to 400-650s
- **Anti-gradient vanishing**: He initialization, Batch normalization, LeakyReLU
- **Robust synchronization**: Dual simulation management with <1s tolerance
- **Type-safe configuration**: Pydantic validation for all settings

### Real-World Application

The system addresses traffic congestion at the intersection of Rondeau/Arenales with Acceso Este in Guaymallén, Mendoza. The DQN agent learns to optimize traffic flow by:

1. **State observation**: 12 traffic zones with wait times and vehicle counts
2. **Action selection**: 16 possible traffic light phase combinations
3. **Reward optimization**: Minimizing total vehicle wait times
4. **Continuous learning**: Adapting to traffic patterns through experience

### Data Flow

```
SUMO Simulation ↔ DQN Agent ↔ REST APIs ↔ Detection System
     ↓                ↓           ↓           ↓
  Traffic State → Decision → Action → Validation
```

The system operates as a closed loop where the DQN agent continuously observes traffic states, makes decisions about traffic light phases, and receives feedback through reward signals based on traffic flow improvement.
