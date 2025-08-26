"""
Utilidades básicas y logging para el frontend simplificado.

Este módulo implementa un patrón de inyección de dependencias para el manejo
de loggers, eliminando variables globales y mejorando la mantenibilidad:

- LoggerProvider: Protocolo para definir contratos de proveedores de logger
- StreamlitLoggerProvider: Implementación específica para entornos Streamlit
- StandardLoggerProvider: Implementación para entornos sin Streamlit
- LoggerFactory: Factory para crear el proveedor apropiado según el contexto

Beneficios:
- Eliminación de variables globales problemáticas
- Facilita testing mediante inyección de mocks
- Cumple principios SOLID (Single Responsibility, Dependency Inversion)
- Mantenibilidad mejorada y bajo acoplamiento
"""

import logging
from typing import Any, Protocol


class LoggerProvider(Protocol):
    """Protocolo para proveedores de logger (dependency injection)."""

    def get_logger(self) -> logging.Logger:
        """Obtener instancia del logger."""
        ...


class StreamlitLoggerProvider:
    """Proveedor de logger optimizado para Streamlit."""

    def __init__(self) -> None:
        self._logger: logging.Logger | None = None

    def get_logger(self) -> logging.Logger:
        """Obtener logger configurado para Streamlit."""
        if self._logger is None:
            self._logger = self._setup_streamlit_logger()
        return self._logger

    def _setup_streamlit_logger(self) -> logging.Logger:
        """Configurar logger específicamente para Streamlit."""
        try:
            import streamlit as st

            # Solo configurar si no se ha hecho antes en esta sesión
            if "logging_configured" not in st.session_state:
                st.session_state.logging_configured = True
                return self._create_configured_logger()
            else:
                # Retornar logger existente sin reconfigurar
                return logging.getLogger("frontend_simple")
        except ImportError:
            # Si no hay Streamlit disponible, usar configuración normal
            return self._create_configured_logger()

    def _create_configured_logger(self) -> logging.Logger:
        """Crear logger con configuración completa."""
        logger = logging.getLogger("frontend_simple")

        # Solo configurar si no tiene handlers (evita duplicación)
        if not logger.handlers:
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


class StandardLoggerProvider:
    """Proveedor de logger estándar (sin Streamlit)."""

    def __init__(self) -> None:
        self._logger: logging.Logger | None = None

    def get_logger(self) -> logging.Logger:
        """Obtener logger configurado estándar."""
        if self._logger is None:
            self._logger = self._setup_standard_logger()
        return self._logger

    def _setup_standard_logger(self) -> logging.Logger:
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


class LoggerFactory:
    """Factory para crear proveedores de logger apropiados."""

    @staticmethod
    def create_provider() -> LoggerProvider:
        """Crear proveedor de logger apropiado según el contexto."""
        import importlib.util

        # Verificar si Streamlit está disponible sin importarlo
        if importlib.util.find_spec("streamlit") is not None:
            return StreamlitLoggerProvider()
        else:
            return StandardLoggerProvider()


# Instancia singleton del proveedor de logger
_logger_provider_instance: LoggerProvider | None = None


def get_logger_provider() -> LoggerProvider:
    """Obtener proveedor de logger usando inyección de dependencias."""
    global _logger_provider_instance
    if _logger_provider_instance is None:
        _logger_provider_instance = LoggerFactory.create_provider()
    return _logger_provider_instance


def set_logger_provider(provider: LoggerProvider) -> None:
    """Establecer proveedor de logger customizado (útil para testing)."""
    global _logger_provider_instance
    _logger_provider_instance = provider


def reset_logger_provider() -> None:
    """Resetear proveedor de logger (útil para testing)."""
    global _logger_provider_instance
    _logger_provider_instance = None


def setup_logging() -> logging.Logger:
    """Configurar logging básico para el frontend."""
    return StandardLoggerProvider().get_logger()


def setup_logging_once() -> logging.Logger:
    """Configurar logging solo una vez por sesión usando Streamlit session_state."""
    return StreamlitLoggerProvider().get_logger()


def get_logger() -> logging.Logger:
    """Obtener logger configurado usando inyección de dependencias."""
    return get_logger_provider().get_logger()


def get_cached_logger() -> logging.Logger:
    """Obtener logger con cache para evitar múltiples inicializaciones."""
    return get_logger_provider().get_logger()


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
