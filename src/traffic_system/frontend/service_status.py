"""
Estados estandarizados y mapeos para servicios locales y remotos.

Unifica la forma de mostrar estados, emojis y mensajes en toda la aplicación.
"""

from enum import Enum


class ServiceState(Enum):
    """Estados estandarizados para todos los servicios."""

    RUNNING = "running"
    STOPPED = "stopped"
    TIMEOUT = "timeout"
    ERROR = "error"
    CONNECTION_ERROR = "connection_error"
    UNKNOWN = "unknown"


class ServiceDisplayInfo:
    """Información de display estandarizada para estados de servicios."""

    # Mapeo de estados a emojis
    STATE_EMOJIS = {
        ServiceState.RUNNING: "🟢",
        ServiceState.STOPPED: "🔴",
        ServiceState.TIMEOUT: "⏱️",
        ServiceState.ERROR: "⚠️",
        ServiceState.CONNECTION_ERROR: "🔴",
        ServiceState.UNKNOWN: "❓",
    }

    # Mapeo de estados a textos legibles
    STATE_TEXTS = {
        ServiceState.RUNNING: "Ejecutándose",
        ServiceState.STOPPED: "Detenido",
        ServiceState.TIMEOUT: "Tiempo agotado",
        ServiceState.ERROR: "Error",
        ServiceState.CONNECTION_ERROR: "Sin conexión",
        ServiceState.UNKNOWN: "Estado desconocido",
    }

    # Mapeo de estados a descripciones adicionales (para servicios remotos)
    STATE_DESCRIPTIONS = {
        ServiceState.RUNNING: "Servicio disponible",
        ServiceState.STOPPED: "Servicio no iniciado",
        ServiceState.TIMEOUT: "No responde en tiempo límite",
        ServiceState.ERROR: "Error en la respuesta",
        ServiceState.CONNECTION_ERROR: "No se puede conectar",
        ServiceState.UNKNOWN: "Estado no determinado",
    }

    @classmethod
    def get_emoji(cls, state: ServiceState) -> str:
        """Obtener emoji para un estado."""
        return cls.STATE_EMOJIS.get(state, cls.STATE_EMOJIS[ServiceState.UNKNOWN])

    @classmethod
    def get_text(cls, state: ServiceState) -> str:
        """Obtener texto legible para un estado."""
        return cls.STATE_TEXTS.get(state, cls.STATE_TEXTS[ServiceState.UNKNOWN])

    @classmethod
    def get_description(cls, state: ServiceState) -> str:
        """Obtener descripción adicional para un estado."""
        return cls.STATE_DESCRIPTIONS.get(
            state, cls.STATE_DESCRIPTIONS[ServiceState.UNKNOWN]
        )

    @classmethod
    def format_local_status(cls, state: ServiceState, service_name: str) -> str:
        """Formatear estado para servicios locales."""
        emoji = cls.get_emoji(state)
        return f"{emoji} **{service_name}** (Local)"

    @classmethod
    def format_remote_status(cls, state: ServiceState, service_name: str) -> str:
        """Formatear estado para servicios remotos."""
        emoji = cls.get_emoji(state)
        return f"{emoji} **{service_name}** (Remoto)"

    @classmethod
    def get_caption_text(cls, state: ServiceState, is_remote: bool = False) -> str:
        """Obtener texto de caption según el tipo de servicio."""
        # Estandarizar formato: siempre "Estado: [descripción]"
        if is_remote:
            return f"Estado: {cls.get_description(state)}"
        else:
            # Para servicios locales, usar también el formato "Estado: [texto]"
            return f"Estado: {cls.get_text(state)}"


def map_boolean_to_state(is_running: bool) -> ServiceState:
    """Convertir estado booleano a ServiceState."""
    return ServiceState.RUNNING if is_running else ServiceState.STOPPED


def map_remote_status_to_state(status: str) -> ServiceState:
    """Convertir estado remoto string a ServiceState."""
    status_mapping = {
        "running": ServiceState.RUNNING,
        "stopped": ServiceState.STOPPED,
        "timeout": ServiceState.TIMEOUT,
        "error": ServiceState.ERROR,
        "connection_error": ServiceState.CONNECTION_ERROR,
    }
    return status_mapping.get(status, ServiceState.UNKNOWN)


def get_toast_message_for_operation(
    operation: str, service_name: str, success: bool, message: str = ""
) -> str:
    """
    Generar mensaje estandarizado para toasts de operaciones.

    Args:
        operation: Tipo de operación ('start', 'stop', 'check')
        service_name: Nombre del servicio
        success: Si la operación fue exitosa
        message: Mensaje adicional (opcional)

    Returns:
        Mensaje formateado sin emojis (el emoji va en el icon del toast)
    """
    operation_texts = {
        "start": "iniciado",
        "stop": "detenido",
        "check": "verificado",
    }

    op_text = operation_texts.get(operation, operation)

    if success:
        base_message = f"{service_name} {op_text} correctamente"
        return f"{base_message}: {message}" if message else base_message
    else:
        base_message = f"Error al {operation} {service_name}"
        return f"{base_message}: {message}" if message else base_message


def get_toast_icon_for_state(state: ServiceState) -> str:
    """Obtener icono de toast para un estado."""
    icon_mapping = {
        ServiceState.RUNNING: "✅",
        ServiceState.STOPPED: "⏹️",
        ServiceState.TIMEOUT: "⏱️",
        ServiceState.ERROR: "❌",
        ServiceState.CONNECTION_ERROR: "❌",
        ServiceState.UNKNOWN: "❓",
    }
    return icon_mapping.get(state, "❓")
