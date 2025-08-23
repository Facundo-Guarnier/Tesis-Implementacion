# Design Document - API Endpoint Enhancement

## Overview

This design document outlines the architecture for enhancing the REST API system in the intelligent traffic light project. The design maintains consistency with the existing microservices architecture while adding new capabilities for system monitoring, control, and data access.

## Architecture

### Current Microservices Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   SUMO S1       │    │  Decision Agent  │    │   SUMO S2       │
│  (Controlled)   │◄──►│      (DQN)       │    │  (Comparison)   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                        │                        │
         │                        │                        │
         ▼                        ▼                        ▼
┌─────────────────────────────────────────────────────────────────┐
│                    API Layer (Flask)                            │
│  Simulation API (Port 5000) | Detection API (Port 5000)        │
│  Reporting API (Port 5001)  | New Enhanced APIs                │
└─────────────────────────────────────────────────────────────────┘
```

### Enhanced API Architecture

```
API Gateway Layer
├── Simulation Service (Port 5000)
│   ├── Existing Endpoints (/simulacion, /reporte, /avanzar, etc.)
│   └── Enhanced Endpoints (/metrics, /health, /config, /debug)
├── Detection Service (Port 5000 - shared)
│   ├── Existing Endpoints (/cantidad, /espera)
│   └── Enhanced Endpoints (/zones, /detection-stats, /calibration)
└── Reporting Service (Port 5001)
    ├── Existing Endpoints (report generation)
    └── Enhanced Endpoints (/analytics, /export, /comparison, /alerts)
```

## Components and Interfaces

### 1. Enhanced DTO Models

**File**: `src/traffic_system/core/api_models.py` (extensions)

```python
# System Health and Monitoring DTOs
class SystemHealthResponse(BaseModel):
    """System health status response."""
    status: str  # "healthy", "degraded", "unhealthy"
    timestamp: str
    services: Dict[str, ServiceStatus]
    uptime_seconds: int
    memory_usage_mb: float
    cpu_usage_percent: float

class ServiceStatus(BaseModel):
    """Individual service status."""
    name: str
    status: str  # "running", "stopped", "error"
    last_heartbeat: str
    response_time_ms: float
    error_count: int

# Advanced Metrics DTOs
class DetailedMetricsResponse(BaseModel):
    """Detailed system metrics response."""
    simulation_metrics: SimulationMetrics
    dqn_metrics: DQNMetrics
    performance_metrics: PerformanceMetrics
    timestamp: str

class SimulationMetrics(BaseModel):
    """Simulation-specific metrics."""
    current_step: int
    simulation_time: float
    vehicles_spawned: int
    vehicles_completed: int
    average_wait_time: float
    throughput_vehicles_per_hour: float

class DQNMetrics(BaseModel):
    """DQN training and inference metrics."""
    model_loaded: bool
    last_action: int
    q_values: List[float]
    epsilon: float
    learning_rate: float
    memory_size: int
    training_active: bool

# Configuration Management DTOs
class ConfigurationResponse(BaseModel):
    """Configuration information response."""
    config_version: str
    last_modified: str
    validation_status: str
    active_services: List[str]
    dqn_parameters: Dict[str, Any]
    simulation_parameters: Dict[str, Any]

class ConfigurationUpdateRequest(BaseModel):
    """Configuration update request."""
    section: str  # "decision", "sumo", "deteccion", etc.
    parameters: Dict[str, Any]
    validate_only: bool = False

# Zone Management DTOs
class ZoneDetailResponse(BaseModel):
    """Detailed zone information response."""
    zone_id: str
    zone_name: str
    current_vehicles: int
    average_wait_time: float
    detection_confidence: float
    last_detection_time: str
    calibration_status: str

class ZoneCalibrationRequest(BaseModel):
    """Zone calibration request."""
    zone_id: str
    calibration_type: str  # "reset", "adjust", "optimize"
    parameters: Dict[str, float]
```

### 2. Enhanced Simulation API

**File**: `src/traffic_system/api/simulation_server.py` (extensions)

```python
class EnhancedSumoAPI(SumoAPI):
    """Enhanced simulation API with additional endpoints."""

    @app.route('/health', methods=['GET'])
    def get_system_health():
        """Get comprehensive system health status."""
        try:
            health_data = {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "services": _get_service_statuses(),
                "uptime_seconds": _get_uptime(),
                "memory_usage_mb": _get_memory_usage(),
                "cpu_usage_percent": _get_cpu_usage()
            }

            response = SystemHealthResponse(**health_data)
            return jsonify(response.model_dump()), 200

        except Exception as e:
            logger.error(f"❌ Error getting system health: {e}")
            error_response = ErrorResponse(error=f"Health check failed: {str(e)}")
            return jsonify(error_response.model_dump()), 500

    @app.route('/metrics/detailed', methods=['GET'])
    def get_detailed_metrics():
        """Get detailed system metrics."""
        try:
            metrics_data = {
                "simulation_metrics": _get_simulation_metrics(),
                "dqn_metrics": _get_dqn_metrics(),
                "performance_metrics": _get_performance_metrics(),
                "timestamp": datetime.now().isoformat()
            }

            response = DetailedMetricsResponse(**metrics_data)
            return jsonify(response.model_dump()), 200

        except Exception as e:
            logger.error(f"❌ Error getting detailed metrics: {e}")
            error_response = ErrorResponse(error=f"Metrics collection failed: {str(e)}")
            return jsonify(error_response.model_dump()), 500

    @app.route('/config', methods=['GET'])
    def get_configuration():
        """Get current system configuration."""
        try:
            config_data = {
                "config_version": _get_config_version(),
                "last_modified": _get_config_last_modified(),
                "validation_status": "valid",
                "active_services": _get_active_services(),
                "dqn_parameters": _get_dqn_config(),
                "simulation_parameters": _get_simulation_config()
            }

            response = ConfigurationResponse(**config_data)
            return jsonify(response.model_dump()), 200

        except Exception as e:
            logger.error(f"❌ Error getting configuration: {e}")
            error_response = ErrorResponse(error=f"Configuration access failed: {str(e)}")
            return jsonify(error_response.model_dump()), 500

    @app.route('/config', methods=['PUT'])
    def update_configuration():
        """Update system configuration."""
        try:
            request_data = request.get_json()
            update_request = ConfigurationUpdateRequest(**request_data)

            if update_request.validate_only:
                # Validate configuration without applying
                validation_result = _validate_config_update(update_request)
                return jsonify({"validation": validation_result}), 200
            else:
                # Apply configuration update
                _apply_config_update(update_request)
                return jsonify({"message": "Configuration updated successfully"}), 200

        except ValidationError as e:
            logger.error(f"❌ Configuration validation error: {e}")
            error_response = ErrorResponse(error=f"Invalid configuration: {str(e)}")
            return jsonify(error_response.model_dump()), 400
        except Exception as e:
            logger.error(f"❌ Error updating configuration: {e}")
            error_response = ErrorResponse(error=f"Configuration update failed: {str(e)}")
            return jsonify(error_response.model_dump()), 500
```

### 3. Enhanced Detection API

**File**: `src/traffic_system/api/detection_server.py` (extensions)

```python
class EnhancedDetectionAPI(DetectionAPI):
    """Enhanced detection API with zone management."""

    @app.route('/zones', methods=['GET'])
    def get_all_zones():
        """Get detailed information for all zones."""
        try:
            zones_data = []
            for zone_id in _get_all_zone_ids():
                zone_info = {
                    "zone_id": zone_id,
                    "zone_name": _get_zone_name(zone_id),
                    "current_vehicles": _get_zone_vehicle_count(zone_id),
                    "average_wait_time": _get_zone_wait_time(zone_id),
                    "detection_confidence": _get_detection_confidence(zone_id),
                    "last_detection_time": _get_last_detection_time(zone_id),
                    "calibration_status": _get_calibration_status(zone_id)
                }
                zones_data.append(ZoneDetailResponse(**zone_info))

            return jsonify([zone.model_dump() for zone in zones_data]), 200

        except Exception as e:
            logger.error(f"❌ Error getting zone information: {e}")
            error_response = ErrorResponse(error=f"Zone data access failed: {str(e)}")
            return jsonify(error_response.model_dump()), 500

    @app.route('/zones/<zone_id>/calibrate', methods=['POST'])
    def calibrate_zone(zone_id: str):
        """Calibrate detection for specific zone."""
        try:
            request_data = request.get_json()
            calibration_request = ZoneCalibrationRequest(zone_id=zone_id, **request_data)

            # Perform zone calibration
            calibration_result = _perform_zone_calibration(calibration_request)

            return jsonify({
                "zone_id": zone_id,
                "calibration_type": calibration_request.calibration_type,
                "result": calibration_result,
                "timestamp": datetime.now().isoformat()
            }), 200

        except ValidationError as e:
            logger.error(f"❌ Zone calibration validation error: {e}")
            error_response = ErrorResponse(error=f"Invalid calibration request: {str(e)}")
            return jsonify(error_response.model_dump()), 400
        except Exception as e:
            logger.error(f"❌ Error calibrating zone {zone_id}: {e}")
            error_response = ErrorResponse(error=f"Zone calibration failed: {str(e)}")
            return jsonify(error_response.model_dump()), 500
```

### 4. Enhanced API Clients

**File**: `src/traffic_system/api_client/enhanced_client.py`

```python
class EnhancedDecisionAPI(DecisionAPI):
    """Enhanced API client with additional endpoints."""

    def get_system_health(self) -> SystemHealthResponse | None:
        """Get system health status."""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            if response.status_code == 200:
                return SystemHealthResponse.model_validate(response.json())
            else:
                logger.error(f"❌ Health check failed: {response.status_code}")
                return None
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Health check request failed: {e}")
            return None

    def get_detailed_metrics(self) -> DetailedMetricsResponse | None:
        """Get detailed system metrics."""
        try:
            response = requests.get(f"{self.base_url}/metrics/detailed", timeout=10)
            if response.status_code == 200:
                return DetailedMetricsResponse.model_validate(response.json())
            else:
                logger.error(f"❌ Metrics request failed: {response.status_code}")
                return None
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Metrics request failed: {e}")
            return None

    def get_configuration(self) -> ConfigurationResponse | None:
        """Get current system configuration."""
        try:
            response = requests.get(f"{self.base_url}/config", timeout=5)
            if response.status_code == 200:
                return ConfigurationResponse.model_validate(response.json())
            else:
                logger.error(f"❌ Configuration request failed: {response.status_code}")
                return None
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Configuration request failed: {e}")
            return None

    def update_configuration(self, section: str, parameters: Dict[str, Any],
                           validate_only: bool = False) -> bool:
        """Update system configuration."""
        try:
            update_data = {
                "section": section,
                "parameters": parameters,
                "validate_only": validate_only
            }

            response = requests.put(
                f"{self.base_url}/config",
                json=update_data,
                timeout=10
            )

            if response.status_code == 200:
                logger.info(f"✅ Configuration updated: {section}")
                return True
            else:
                logger.error(f"❌ Configuration update failed: {response.status_code}")
                return False

        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Configuration update request failed: {e}")
            return False
```

## Data Models

### Enhanced API Response Schema

```python
# Health monitoring schema
{
    "status": "healthy",
    "timestamp": "2025-01-15T10:30:00",
    "services": {
        "simulation": {"status": "running", "response_time_ms": 45.2},
        "decision": {"status": "running", "response_time_ms": 12.8},
        "detection": {"status": "running", "response_time_ms": 89.1}
    },
    "uptime_seconds": 3600,
    "memory_usage_mb": 2048.5,
    "cpu_usage_percent": 15.3
}

# Detailed metrics schema
{
    "simulation_metrics": {
        "current_step": 1500,
        "simulation_time": 750.0,
        "vehicles_spawned": 245,
        "vehicles_completed": 198,
        "average_wait_time": 45.2,
        "throughput_vehicles_per_hour": 792
    },
    "dqn_metrics": {
        "model_loaded": true,
        "last_action": 7,
        "q_values": [-12.5, -8.3, -15.7, -9.1],
        "epsilon": 0.15,
        "learning_rate": 0.0005,
        "memory_size": 1250,
        "training_active": false
    },
    "performance_metrics": {
        "inference_time_ms": 8.2,
        "api_response_time_ms": 25.1,
        "memory_usage_mb": 1024.3
    }
}
```

## Error Handling

### Enhanced Error Response System

```python
class DetailedErrorResponse(BaseModel):
    """Enhanced error response with debugging information."""
    error: str
    error_code: str
    timestamp: str
    service: str
    endpoint: str
    details: Dict[str, Any] = {}
    suggestions: List[str] = []

def handle_api_error(error: Exception, endpoint: str) -> Tuple[Dict, int]:
    """Enhanced error handling with detailed information."""
    error_details = {
        "error": str(error),
        "error_code": _get_error_code(error),
        "timestamp": datetime.now().isoformat(),
        "service": "simulation",
        "endpoint": endpoint,
        "details": _extract_error_details(error),
        "suggestions": _get_error_suggestions(error)
    }

    response = DetailedErrorResponse(**error_details)
    status_code = _get_http_status_code(error)

    return response.model_dump(), status_code
```

## Testing Strategy

### Enhanced Integration Tests

```python
def test_enhanced_health_endpoint():
    """Test system health endpoint."""
    logger.info("🧪 Testing enhanced health endpoint...")

    response = requests.get("http://127.0.0.1:5000/health", timeout=5)
    assert response.status_code == 200

    health_data = SystemHealthResponse.model_validate(response.json())
    assert health_data.status in ["healthy", "degraded", "unhealthy"]
    assert "simulation" in health_data.services

    logger.info("✅ Health endpoint test passed")

def test_detailed_metrics_endpoint():
    """Test detailed metrics endpoint."""
    logger.info("🧪 Testing detailed metrics endpoint...")

    response = requests.get("http://127.0.0.1:5000/metrics/detailed", timeout=10)
    assert response.status_code == 200

    metrics_data = DetailedMetricsResponse.model_validate(response.json())
    assert metrics_data.simulation_metrics.current_step >= 0
    assert len(metrics_data.dqn_metrics.q_values) > 0

    logger.info("✅ Detailed metrics test passed")

def test_configuration_management():
    """Test configuration management endpoints."""
    logger.info("🧪 Testing configuration management...")

    # Get current configuration
    response = requests.get("http://127.0.0.1:5000/config", timeout=5)
    assert response.status_code == 200

    config_data = ConfigurationResponse.model_validate(response.json())
    assert config_data.validation_status == "valid"

    # Test configuration validation
    update_data = {
        "section": "decision",
        "parameters": {"learning_rate": 0.001},
        "validate_only": True
    }

    response = requests.put("http://127.0.0.1:5000/config", json=update_data, timeout=10)
    assert response.status_code == 200

    logger.info("✅ Configuration management test passed")
```

This design ensures that API enhancements maintain consistency with existing patterns while providing powerful new capabilities for system monitoring, configuration management, and advanced data access.
