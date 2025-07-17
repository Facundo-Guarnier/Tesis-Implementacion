"""
Modelos Pydantic para APIs del sistema de tráfico.

Este módulo define los DTOs (Data Transfer Objects) utilizados en las APIs
para garantizar type safety y validación automática de datos.
"""

from typing import Any

from pydantic import BaseModel, Field

# ============================================================================
# Modelos de respuesta base
# ============================================================================


class BaseResponse(BaseModel):
    """Respuesta base para todas las APIs."""

    status: str = "success"
    timestamp: float | None = None


class SuccessResponse(BaseResponse):
    """Respuesta exitosa genérica."""

    message: str | None = None
    data: dict[str, Any] | None = None


class ErrorResponse(BaseModel):
    """Respuesta de error estándar."""

    error: str
    status: str = "error"
    details: dict[str, Any] | None = None
    code: str | None = None


# ============================================================================
# Modelos específicos de simulación
# ============================================================================


class SimulationStepResponse(BaseResponse):
    """Respuesta del endpoint de avanzar simulación."""

    done: bool
    current_time: float
    vehicles_count: int | None = None
    step_count: int | None = None


class TrafficLightStatesResponse(BaseResponse):
    """Respuesta para estados de todos los semáforos."""

    estados: dict[str, str]
    total_lights: int | None = None


class TrafficLightStateResponse(BaseResponse):
    """Respuesta para estado de un semáforo específico."""

    estado: str
    light_id: str | None = None


class WaitTimesResponse(BaseResponse):
    """Respuesta con tiempos de espera."""

    tiempos_espera: list[float]
    tiempo_espera_total: float
    promedio_espera: float | None = None


class VehicleQuantitiesResponse(BaseResponse):
    """Respuesta con cantidades de vehículos por zona."""

    cantidades: dict[str, int]
    total_vehicles: int | None = None


class SimulationStatusResponse(BaseResponse):
    """Respuesta del estado de la simulación."""

    simulacion: bool
    tiempo_actual: float | None = None
    modo_comparacion: bool | None = None


class SynchronizationResponse(BaseResponse):
    """Respuesta del estado de sincronización."""

    sincronizado: bool
    diferencia_tiempo: float
    s1_time: float
    s2_time: float | None = None
    tolerancia: float | None = None


class ReportResponse(BaseResponse):
    """Respuesta con datos de reporte."""

    report_data: dict[str, Any]
    generated_at: str | None = None


# ============================================================================
# Modelos de request
# ============================================================================


class StepRequest(BaseModel):
    """Request para avanzar simulación."""

    steps: int = Field(gt=0, le=1000, description="Número de pasos a avanzar")


class TrafficLightChangeRequest(BaseModel):
    """Request para cambiar estado de semáforo."""

    estado: str = Field(
        description="Nuevo estado del semáforo",
        pattern="^[rgyY]{4}$",  # Patrón para 4 caracteres: r/g/y/Y
    )


class ReportDataRequest(BaseModel):
    """Request para enviar datos de reporte."""

    data: dict[str, Any]
    source: str | None = None
    timestamp: float | None = None


class ZoneConfigRequest(BaseModel):
    """Request para configurar zonas de detección."""

    zone_id: str
    coordinates: list[list[float]]
    active: bool = True


# ============================================================================
# Modelos específicos para DQN/RL
# ============================================================================


class DQNStateResponse(BaseResponse):
    """Respuesta con estado para el agente DQN."""

    state: list[float]
    action_space_size: int
    normalized: bool = True


class DQNActionRequest(BaseModel):
    """Request con acción del agente DQN."""

    action: int = Field(ge=0, description="Índice de la acción a ejecutar")
    confidence: float | None = Field(ge=0.0, le=1.0, default=None)


class DQNRewardResponse(BaseResponse):
    """Respuesta con recompensa para el agente."""

    reward: float
    done: bool
    info: dict[str, Any] | None = None


# ============================================================================
# Modelos para detección de vehículos
# ============================================================================


class DetectionZoneResponse(BaseResponse):
    """Respuesta con cantidades detectadas por zona."""

    zone_quantities: dict[str, int]
    total_detected: int
    detection_timestamp: float | None = None


class DetectionConfigResponse(BaseResponse):
    """Respuesta con configuración de detección."""

    zones_active: list[str]
    model_info: dict[str, str]
    confidence_threshold: float


# ============================================================================
# Funciones de utilidad
# ============================================================================


def create_error_response(
    error_message: str,
    details: dict[str, Any] | None = None,
    code: str | None = None,
) -> ErrorResponse:
    """
    Función helper para crear respuestas de error consistentes.

    Args:
        error_message: Mensaje de error descriptivo
        details: Detalles adicionales del error
        code: Código de error específico

    Returns:
        ErrorResponse configurada
    """
    return ErrorResponse(error=error_message, details=details, code=code)


def create_success_response(
    message: str | None = None, data: dict[str, Any] | None = None
) -> SuccessResponse:
    """
    Función helper para crear respuestas exitosas consistentes.

    Args:
        message: Mensaje descriptivo opcional
        data: Datos adicionales opcionales

    Returns:
        SuccessResponse configurada
    """
    return SuccessResponse(message=message, data=data)
