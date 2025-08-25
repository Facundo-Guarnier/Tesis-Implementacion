"""
Utilidades básicas y logging para el frontend simplificado.
"""

import logging
from typing import Any


def setup_logging() -> logging.Logger:
    """Configurar logging básico para el frontend."""
    logger = logging.getLogger("frontend_simple")

    # Solo configurar si no tiene handlers (evita duplicación)
    if not logger.handlers:
        # Configurar handler con encoding UTF-8 explícito
        import sys

        handler = logging.StreamHandler(sys.stdout)

        # En Windows, forzar UTF-8 para soportar emojis
        if hasattr(handler.stream, "reconfigure"):
            try:
                handler.stream.reconfigure(encoding="utf-8")
            except Exception:
                # Si falla, usar handler sin emojis
                pass

        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

        # Evitar propagación para prevenir logs duplicados
        logger.propagate = False

    return logger


def setup_logging_once() -> logging.Logger:
    """Configurar logging solo una vez por sesión usando Streamlit session_state."""
    try:
        import streamlit as st

        # Solo configurar si no se ha hecho antes en esta sesión
        if "logging_configured" not in st.session_state:
            st.session_state.logging_configured = True

            # Configurar logger con control de duplicación mejorado
            logger = logging.getLogger("frontend_simple")

            # Limpiar handlers existentes para evitar duplicación
            logger.handlers.clear()

            # Configurar handler con encoding UTF-8 explícito
            import sys

            handler = logging.StreamHandler(sys.stdout)

            # En Windows, forzar UTF-8 para soportar emojis
            if hasattr(handler.stream, "reconfigure"):
                try:
                    handler.stream.reconfigure(encoding="utf-8")
                except Exception:
                    # Si falla, usar handler sin emojis
                    pass

            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)

            # Evitar propagación para prevenir logs duplicados
            logger.propagate = False

            return logger
        else:
            # Retornar logger existente sin reconfigurar
            return logging.getLogger("frontend_simple")
    except ImportError:
        # Si no hay Streamlit disponible, usar configuración normal
        return setup_logging()


def get_logger() -> logging.Logger:
    """Obtener logger configurado, asegurando configuración única por sesión."""
    try:
        import streamlit as st

        # Si ya está configurado en esta sesión, retornar logger existente
        if "logging_configured" in st.session_state:
            return logging.getLogger("frontend_simple")
        else:
            # Primera vez en esta sesión, configurar
            return setup_logging_once()
    except ImportError:
        # Sin Streamlit, usar configuración estándar
        return setup_logging()


# Logger global - inicializar de forma lazy para evitar problemas de importación
_logger_instance = None


def get_cached_logger() -> logging.Logger:
    """Obtener logger con cache para evitar múltiples inicializaciones."""
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = get_logger()
    return _logger_instance


def log_error(message: str) -> None:
    """Log de errores con emoji ❌."""
    try:
        current_logger = get_cached_logger()
        current_logger.error(f"❌ {message}")
    except Exception:
        # Fallback silencioso si hay problemas con logging
        pass


def log_warning(message: str) -> None:
    """Log de advertencias con emoji ⚠️."""
    try:
        current_logger = get_cached_logger()
        current_logger.warning(f"⚠️ {message}")
    except Exception:
        # Fallback silencioso si hay problemas con logging
        pass


def log_success(message: str) -> None:
    """Log de éxito con emoji ✅."""
    try:
        current_logger = get_cached_logger()
        current_logger.info(f"✅ {message}")
    except Exception:
        # Fallback silencioso si hay problemas con logging
        pass


def log_info(message: str) -> None:
    """Log de información con emoji ℹ️."""
    try:
        current_logger = get_cached_logger()
        current_logger.info(f"ℹ️ {message}")
    except Exception:
        # Fallback silencioso si hay problemas con logging
        pass


def log_debug(message: str) -> None:
    """Log de debug con emoji 🐛 - solo visible en modo debug."""
    try:
        current_logger = get_cached_logger()
        current_logger.debug(f"🐛 {message}")
    except Exception:
        # Fallback silencioso si hay problemas con logging
        pass


def validate_field(
    field_key: str, value: Any, current_config: dict[str, Any]
) -> tuple[bool, str]:
    """
    Validar un campo individual usando Pydantic.

    Args:
        field_key: Clave del campo (ej: 'simulation_port')
        value: Valor a validar
        current_config: Configuración actual completa

    Returns:
        Tupla (es_válido, mensaje)
    """
    try:
        from pydantic import ValidationError

        from src.traffic_system.core.config_models import AppSettings

        # Crear configuración temporal con el nuevo valor
        temp_config = current_config.copy()
        set_nested_value(temp_config, field_key, value)

        # Validar con Pydantic
        AppSettings(**temp_config)
        return True, "✅ Válido"

    except ValidationError as e:
        # Buscar error específico para este campo
        for error in e.errors():
            error_field_path = ".".join(str(loc) for loc in error["loc"])
            if field_key in error_field_path or error_field_path in field_key:
                return False, f"❌ {error['msg']}"

        # Si no se encuentra error específico, devolver error genérico
        return False, "❌ Error de validación"

    except Exception as e:
        log_error(f"Error validando campo {field_key}: {e}")
        return False, f"❌ Error: {str(e)}"


def set_nested_value(config: dict[str, Any], field_path: str, value: Any) -> None:
    """
    Establecer un valor anidado en un diccionario usando notación de puntos.

    Args:
        config: Diccionario de configuración
        field_path: Ruta del campo (ej: 'services.simulation_port')
        value: Valor a establecer
    """
    keys = field_path.split(".")
    current = config

    # Navegar hasta el penúltimo nivel
    for key in keys[:-1]:
        if key not in current:
            current[key] = {}
        current = current[key]

    # Establecer el valor final
    current[keys[-1]] = value


def get_nested_value(config: dict[str, Any], field_path: str) -> Any:
    """
    Obtener un valor anidado de un diccionario usando notación de puntos.

    Args:
        config: Diccionario de configuración
        field_path: Ruta del campo (ej: 'services.simulation_port')

    Returns:
        Valor del campo o None si no existe
    """
    keys = field_path.split(".")
    current = config

    try:
        for key in keys:
            current = current[key]
        return current
    except (KeyError, TypeError):
        return None
