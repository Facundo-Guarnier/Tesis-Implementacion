"""
Service Error Handling Utilities

Provides comprehensive error handling, timeout management, and user-friendly
error messages for service operations with debugging information.
"""

import logging
import time
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from typing import Any

import streamlit as st

logger = logging.getLogger(__name__)


class ServiceErrorType(Enum):
    """Types of service errors."""

    UNKNOWN_SERVICE = "unknown_service"
    ALREADY_RUNNING = "already_running"
    NOT_RUNNING = "not_running"
    PORT_CONFLICT = "port_conflict"
    POETRY_NOT_FOUND = "poetry_not_found"
    STARTUP_FAILED = "startup_failed"
    SHUTDOWN_FAILED = "shutdown_failed"
    TIMEOUT = "timeout"
    PERMISSION_DENIED = "permission_denied"
    RESOURCE_UNAVAILABLE = "resource_unavailable"
    CONFIGURATION_ERROR = "configuration_error"
    NETWORK_ERROR = "network_error"
    UNEXPECTED_ERROR = "unexpected_error"


@dataclass
class ServiceError:
    """Represents a service operation error."""

    error_type: ServiceErrorType
    service_name: str
    message: str
    technical_details: str = ""
    suggested_actions: list[str] | None = None
    is_recoverable: bool = True

    def __post_init__(self) -> None:
        if self.suggested_actions is None:
            self.suggested_actions = []


class ServiceErrorHandler:
    """Handles service operation errors with user-friendly feedback."""

    # Error type to user-friendly message mapping
    ERROR_MESSAGES = {
        ServiceErrorType.UNKNOWN_SERVICE: {
            "title": "Servicio Desconocido",
            "message": "El servicio especificado no existe en el sistema",
            "icon": "❓",
            "actions": [
                "Verifica el nombre del servicio",
                "Consulta la lista de servicios disponibles",
            ],
        },
        ServiceErrorType.ALREADY_RUNNING: {
            "title": "Servicio Ya Ejecutándose",
            "message": "El servicio ya está en funcionamiento",
            "icon": "ℹ️",
            "actions": [
                "Verifica el estado del servicio",
                "Detén el servicio antes de reiniciarlo",
            ],
        },
        ServiceErrorType.NOT_RUNNING: {
            "title": "Servicio No Ejecutándose",
            "message": "El servicio no está actualmente en funcionamiento",
            "icon": "⏹️",
            "actions": [
                "Inicia el servicio primero",
                "Verifica que el servicio se haya iniciado correctamente",
            ],
        },
        ServiceErrorType.PORT_CONFLICT: {
            "title": "Conflicto de Puerto",
            "message": "El puerto requerido ya está siendo utilizado por otro proceso",
            "icon": "🔌",
            "actions": [
                "Detén otros servicios que usen el mismo puerto",
                "Cambia el puerto en la configuración",
                "Verifica qué proceso está usando el puerto",
            ],
        },
        ServiceErrorType.POETRY_NOT_FOUND: {
            "title": "Poetry No Encontrado",
            "message": "Poetry no está instalado o no está en el PATH del sistema",
            "icon": "📦",
            "actions": [
                "Instala Poetry siguiendo la documentación oficial",
                "Verifica que Poetry esté en el PATH",
                "Reinicia la terminal después de instalar Poetry",
            ],
        },
        ServiceErrorType.STARTUP_FAILED: {
            "title": "Fallo en el Inicio",
            "message": "El servicio falló al iniciar correctamente",
            "icon": "🚫",
            "actions": [
                "Revisa los logs del servicio para más detalles",
                "Verifica la configuración del servicio",
                "Asegúrate de que todas las dependencias estén instaladas",
            ],
        },
        ServiceErrorType.SHUTDOWN_FAILED: {
            "title": "Fallo en el Cierre",
            "message": "El servicio no pudo cerrarse correctamente",
            "icon": "⚠️",
            "actions": [
                "Intenta forzar el cierre del servicio",
                "Verifica si el proceso sigue ejecutándose",
                "Reinicia el sistema si es necesario",
            ],
        },
        ServiceErrorType.TIMEOUT: {
            "title": "Tiempo de Espera Agotado",
            "message": "La operación tardó más tiempo del esperado",
            "icon": "⏰",
            "actions": [
                "Intenta la operación nuevamente",
                "Verifica la carga del sistema",
                "Aumenta el tiempo de espera si es posible",
            ],
        },
        ServiceErrorType.PERMISSION_DENIED: {
            "title": "Permisos Insuficientes",
            "message": "No tienes permisos suficientes para realizar esta operación",
            "icon": "🔒",
            "actions": [
                "Ejecuta como administrador",
                "Verifica los permisos del directorio",
                "Contacta al administrador del sistema",
            ],
        },
        ServiceErrorType.RESOURCE_UNAVAILABLE: {
            "title": "Recursos No Disponibles",
            "message": "Los recursos del sistema necesarios no están disponibles",
            "icon": "💾",
            "actions": [
                "Libera memoria cerrando otras aplicaciones",
                "Verifica el espacio en disco disponible",
                "Reinicia el sistema si es necesario",
            ],
        },
        ServiceErrorType.CONFIGURATION_ERROR: {
            "title": "Error de Configuración",
            "message": "Hay un problema con la configuración del servicio",
            "icon": "⚙️",
            "actions": [
                "Revisa el archivo de configuración",
                "Valida la configuración antes de iniciar",
                "Restaura una configuración de backup válida",
            ],
        },
        ServiceErrorType.NETWORK_ERROR: {
            "title": "Error de Red",
            "message": "Problema de conectividad de red",
            "icon": "🌐",
            "actions": [
                "Verifica la conexión a internet",
                "Revisa la configuración de firewall",
                "Verifica que los puertos no estén bloqueados",
            ],
        },
        ServiceErrorType.UNEXPECTED_ERROR: {
            "title": "Error Inesperado",
            "message": "Ocurrió un error inesperado durante la operación",
            "icon": "❌",
            "actions": [
                "Intenta la operación nuevamente",
                "Revisa los logs para más información",
                "Reporta el error si persiste",
            ],
        },
    }

    def __init__(self) -> None:
        """Initialize the error handler."""
        self.error_history: list[ServiceError] = []

    def handle_service_error(
        self,
        error_type: ServiceErrorType,
        service_name: str,
        technical_details: str = "",
        show_in_ui: bool = True,
    ) -> ServiceError:
        """
        Handle a service error with comprehensive feedback.

        Args:
            error_type: Type of error that occurred
            service_name: Name of the service
            technical_details: Technical error details
            show_in_ui: Whether to show error in UI

        Returns:
            ServiceError object
        """
        error_info = self.ERROR_MESSAGES.get(
            error_type, self.ERROR_MESSAGES[ServiceErrorType.UNEXPECTED_ERROR]
        )

        service_error = ServiceError(
            error_type=error_type,
            service_name=service_name,
            message=str(error_info["message"]),
            technical_details=technical_details,
            suggested_actions=list(error_info["actions"]),
            is_recoverable=error_type
            not in [
                ServiceErrorType.POETRY_NOT_FOUND,
                ServiceErrorType.PERMISSION_DENIED,
            ],
        )

        # Log the error
        logger.error(
            f"{error_info['icon']} {error_info['title']} - {service_name}: {technical_details}"
        )

        # Add to error history
        self.error_history.append(service_error)

        # Show in UI if requested
        if show_in_ui:
            self.display_error_in_ui(service_error, error_info)

        return service_error

    def display_error_in_ui(
        self, error: ServiceError, error_info: dict[str, Any]
    ) -> None:
        """Display error information in the UI."""
        error_title = f"{error_info['icon']} **{error_info['title']}**"
        logger.error(f"Service error displayed: {error.service_name} - {error.message}")
        st.error(error_title)

        # Error message
        st.write(f"**Servicio:** {error.service_name}")
        st.write(f"**Problema:** {error.message}")

        # Technical details if available
        if error.technical_details:
            with st.expander("🔍 Detalles Técnicos", expanded=False):
                st.code(error.technical_details)

        # Suggested actions
        if error.suggested_actions:
            st.write("**💡 Acciones Sugeridas:**")
            for action in error.suggested_actions:
                st.write(f"• {action}")

        # Recovery options
        if error.is_recoverable:
            info_msg = (
                "🔄 Este error puede ser recuperable. Intenta las acciones sugeridas."
            )
            logger.info(
                f"Recoverable error for service {error.service_name}: {error.message}"
            )
            st.info(info_msg)
        else:
            warning_msg = "⚠️ Este error requiere intervención manual para resolverse."
            logger.warning(
                f"Non-recoverable error for service {error.service_name}: {error.message}"
            )
            st.warning(warning_msg)

    def create_timeout_handler(
        self, operation_name: str, timeout_seconds: int = 30
    ) -> Callable:
        """
        Create a timeout handler for service operations.

        Args:
            operation_name: Name of the operation
            timeout_seconds: Timeout in seconds

        Returns:
            Timeout handler function
        """

        def timeout_handler(func: Callable) -> Callable:
            def wrapper(*args: Any, **kwargs: Any) -> Any:
                start_time = time.time()

                try:
                    # Show progress indicator
                    progress_placeholder = st.empty()
                    progress_placeholder.info(f"⏳ {operation_name} en progreso...")

                    result = func(*args, **kwargs)

                    # Clear progress indicator
                    progress_placeholder.empty()

                    return result

                except Exception as e:
                    elapsed_time = time.time() - start_time

                    # Clear progress indicator
                    progress_placeholder.empty()

                    if elapsed_time >= timeout_seconds:
                        # Timeout occurred
                        self.handle_service_error(
                            ServiceErrorType.TIMEOUT,
                            kwargs.get("service_name", "unknown"),
                            f"Operación '{operation_name}' excedió {timeout_seconds}s",
                        )
                    else:
                        # Other error
                        self.handle_service_error(
                            ServiceErrorType.UNEXPECTED_ERROR,
                            kwargs.get("service_name", "unknown"),
                            str(e),
                        )

                    raise

            return wrapper

        return timeout_handler

    def get_common_service_issues(self, service_name: str) -> list[dict[str, str]]:
        """
        Get common issues and solutions for a specific service.

        Args:
            service_name: Name of the service

        Returns:
            List of common issues and solutions
        """
        common_issues = {
            "simulation": [
                {
                    "issue": "SUMO no encontrado",
                    "solution": "Instala SUMO y configura la ruta en config.yaml",
                },
                {
                    "issue": "Puerto 5000 ocupado",
                    "solution": "Cambia el puerto en la configuración o detén el proceso que lo usa",
                },
                {
                    "issue": "Archivos de mapa faltantes",
                    "solution": "Verifica que los archivos .sumocfg estén en assets/sumo_maps/",
                },
            ],
            "decision": [
                {
                    "issue": "TensorFlow no instalado",
                    "solution": "Instala TensorFlow con: poetry add tensorflow",
                },
                {
                    "issue": "Modelo DQN no encontrado",
                    "solution": "Entrena un modelo o especifica la ruta correcta en config.yaml",
                },
                {
                    "issue": "GPU no disponible",
                    "solution": "Verifica la instalación de CUDA o usa CPU",
                },
            ],
            "detection": [
                {
                    "issue": "YOLOv8 no instalado",
                    "solution": "Instala Ultralytics con: poetry add ultralytics",
                },
                {
                    "issue": "Modelo YOLO no encontrado",
                    "solution": "Descarga el modelo yolov8n.pt a assets/yolo_models/",
                },
                {
                    "issue": "OpenCV no funciona",
                    "solution": "Reinstala OpenCV con: poetry add opencv-python",
                },
            ],
            "reporting": [
                {
                    "issue": "Puerto 5001 ocupado",
                    "solution": "Cambia el puerto de reporting en la configuración",
                },
                {
                    "issue": "Base de datos no accesible",
                    "solution": "Verifica la configuración de la base de datos",
                },
            ],
        }

        return common_issues.get(service_name, [])

    def show_service_troubleshooting(self, service_name: str) -> None:
        """Show troubleshooting guide for a specific service."""
        st.subheader(f"🔧 Solución de Problemas - {service_name}")

        # Common issues
        common_issues = self.get_common_service_issues(service_name)

        if common_issues:
            st.write("**Problemas Comunes:**")
            for issue in common_issues:
                with st.expander(f"❓ {issue['issue']}", expanded=False):
                    st.write(f"**Solución:** {issue['solution']}")

        # Error history for this service
        service_errors = [
            error for error in self.error_history if error.service_name == service_name
        ]

        if service_errors:
            st.write("**Errores Recientes:**")
            for i, error in enumerate(service_errors[-3:], 1):  # Show last 3 errors
                error_info = self.ERROR_MESSAGES.get(
                    error.error_type,
                    self.ERROR_MESSAGES[ServiceErrorType.UNEXPECTED_ERROR],
                )
                with st.expander(
                    f"{error_info['icon']} {error_info['title']} #{i}", expanded=False
                ):
                    st.write(f"**Mensaje:** {error.message}")
                    if error.technical_details:
                        st.code(error.technical_details)

    def clear_error_history(self) -> None:
        """Clear the error history."""
        self.error_history.clear()
        logger.info("🧹 Historial de errores limpiado")

    def get_error_statistics(self) -> dict[str, int]:
        """Get error statistics."""
        stats: dict[str, int] = {}
        for error in self.error_history:
            error_type = error.error_type.value
            stats[error_type] = stats.get(error_type, 0) + 1
        return stats


def create_service_error_handler() -> ServiceErrorHandler:
    """
    Factory function to create service error handler.

    Returns:
        ServiceErrorHandler instance
    """
    return ServiceErrorHandler()


def with_service_timeout(timeout_seconds: int = 30) -> Any:
    """
    Decorator to add timeout handling to service operations.

    Args:
        timeout_seconds: Timeout in seconds

    Returns:
        Decorator function
    """

    def decorator(func: Callable) -> Callable:
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            start_time = time.time()

            try:
                result = func(*args, **kwargs)
                return result

            except Exception as err:
                elapsed_time = time.time() - start_time

                if elapsed_time >= timeout_seconds:
                    raise TimeoutError(
                        f"Operación '{func.__name__}' excedió {timeout_seconds} segundos"
                    ) from err
                else:
                    raise

        return wrapper

    return decorator
