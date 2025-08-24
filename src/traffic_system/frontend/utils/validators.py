"""
Configuration Validation Utilities

Integrates with existing Pydantic models to provide real-time validation
and user-friendly error formatting for the configuration frontend.
"""

import logging
from typing import Any

from pydantic import ValidationError

from src.traffic_system.core.config_models import AppSettings

logger = logging.getLogger(__name__)


class ConfigValidator:
    """Validates configuration using existing Pydantic models."""

    def __init__(self) -> None:
        """Initialize the validator."""
        self.last_valid_config: dict[str, Any] | None = None

    def validate_full_config(
        self, config: dict[str, Any]
    ) -> tuple[bool, list[str], AppSettings | None]:
        """
        Validate complete configuration using Pydantic models.

        Args:
            config: Configuration dictionary to validate

        Returns:
            Tuple of (is_valid, error_messages, parsed_settings_or_none)
        """
        try:
            # Try to parse the configuration using existing Pydantic models
            settings = AppSettings(**config)

            logger.info("✅ Configuración validada correctamente")
            self.last_valid_config = config
            return True, [], settings

        except ValidationError as e:
            error_messages = self._format_validation_errors(e)
            logger.warning(
                f"⚠️ Errores de validación encontrados: {len(error_messages)}"
            )
            return False, error_messages, None

        except Exception as e:
            error_msg = f"Error inesperado durante validación: {str(e)}"
            logger.error(f"❌ {error_msg}")
            return False, [error_msg], None

    def validate_section(
        self, section_name: str, section_data: Any, full_config: dict[str, Any]
    ) -> tuple[bool, list[str]]:
        """
        Validate a specific configuration section.

        Args:
            section_name: Name of the section to validate
            section_data: Data for the specific section
            full_config: Complete configuration for context

        Returns:
            Tuple of (is_valid, error_messages)
        """
        try:
            # Create a temporary config with the updated section
            temp_config = full_config.copy()
            temp_config[section_name] = section_data

            # Validate the complete config to ensure section compatibility
            is_valid, errors, _ = self.validate_full_config(temp_config)

            # Filter errors to only those related to this section
            section_errors = [
                error
                for error in errors
                if section_name in error.lower() or error.startswith(section_name)
            ]

            return len(section_errors) == 0, section_errors

        except Exception as e:
            error_msg = f"Error validating section {section_name}: {str(e)}"
            logger.error(f"❌ {error_msg}")
            return False, [error_msg]

    def validate_field(
        self, field_path: str, value: Any, full_config: dict[str, Any]
    ) -> tuple[bool, str | None]:
        """
        Validate a specific field value.

        Args:
            field_path: Dot-separated path to the field (e.g., "services.simulation_port")
            value: Value to validate
            full_config: Complete configuration for context

        Returns:
            Tuple of (is_valid, error_message_or_none)
        """
        try:
            # Create a temporary config with the updated field
            temp_config = self._deep_copy_dict(full_config)
            self._set_nested_value(temp_config, field_path, value)

            # Validate the complete config
            is_valid, errors, _ = self.validate_full_config(temp_config)

            if is_valid:
                return True, None

            # Find errors related to this field
            field_errors = [
                error
                for error in errors
                if field_path in error
                or any(part in error for part in field_path.split("."))
            ]

            if field_errors:
                return False, field_errors[0]
            else:
                # If no specific field error, return general validation failure
                return False, "Valor inválido para este campo"

        except Exception as e:
            error_msg = f"Error validating field {field_path}: {str(e)}"
            logger.error(f"❌ {error_msg}")
            return False, error_msg

    def test_config_loading(self, config: dict[str, Any]) -> tuple[bool, str | None]:
        """
        Test if configuration can be loaded using the existing config loader.

        Args:
            config: Configuration to test

        Returns:
            Tuple of (can_load, error_message_or_none)
        """
        try:
            # This would test the actual config loading process
            # For now, we'll use the Pydantic validation as a proxy
            is_valid, errors, _ = self.validate_full_config(config)

            if is_valid:
                return True, None
            else:
                return False, "Configuración no puede ser cargada: " + "; ".join(
                    errors[:3]
                )

        except Exception as e:
            error_msg = f"Error testing config loading: {str(e)}"
            logger.error(f"❌ {error_msg}")
            return False, error_msg

    def _format_validation_errors(self, validation_error: ValidationError) -> list[str]:
        """
        Format Pydantic validation errors for user display.

        Args:
            validation_error: Pydantic ValidationError

        Returns:
            List of formatted error messages
        """
        formatted_errors = []

        for error in validation_error.errors():
            location = " → ".join(str(loc) for loc in error["loc"])
            message = error["msg"]
            error_type = error["type"]

            # Create user-friendly error messages
            if error_type == "missing":
                formatted_msg = f"Campo requerido faltante: {location}"
            elif error_type == "type_error":
                formatted_msg = f"Tipo incorrecto en {location}: {message}"
            elif error_type == "value_error":
                formatted_msg = f"Valor inválido en {location}: {message}"
            elif "greater_than" in error_type:
                formatted_msg = (
                    f"Valor en {location} debe ser mayor que el mínimo permitido"
                )
            elif "less_than" in error_type:
                formatted_msg = (
                    f"Valor en {location} debe ser menor que el máximo permitido"
                )
            else:
                formatted_msg = f"Error en {location}: {message}"

            formatted_errors.append(formatted_msg)

        return formatted_errors

    def _deep_copy_dict(self, original: dict[str, Any]) -> dict[str, Any]:
        """Create a deep copy of a dictionary."""
        import copy

        return copy.deepcopy(original)

    def _set_nested_value(self, config: dict[str, Any], path: str, value: Any) -> None:
        """
        Set a nested value in a dictionary using dot notation.

        Args:
            config: Dictionary to modify
            path: Dot-separated path (e.g., "services.simulation_port")
            value: Value to set
        """
        keys = path.split(".")
        current = config

        # Navigate to the parent of the target key
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]

        # Set the final value
        current[keys[-1]] = value

    def get_field_constraints(self, field_path: str) -> dict[str, Any]:
        """
        Get validation constraints for a specific field from Pydantic models.

        Args:
            field_path: Dot-separated path to the field

        Returns:
            Dictionary with constraint information
        """
        constraints = {
            "type": "unknown",
            "required": False,
            "min_value": None,
            "max_value": None,
            "choices": None,
            "description": None,
        }

        try:
            # This is a simplified version - in a full implementation,
            # you would introspect the Pydantic models to get actual constraints

            # Common field constraints based on known config structure
            field_constraints = {
                "services.simulation_port": {
                    "type": "integer",
                    "min_value": 1024,
                    "max_value": 65535,
                    "description": "Puerto para el servicio de simulación",
                },
                "services.detection_port": {
                    "type": "integer",
                    "min_value": 1024,
                    "max_value": 65535,
                    "description": "Puerto para el servicio de detección",
                },
                "services.reporting_port": {
                    "type": "integer",
                    "min_value": 1024,
                    "max_value": 65535,
                    "description": "Puerto para el servicio de reportes",
                },
                "deteccion.detectar": {
                    "type": "boolean",
                    "description": "Activar detección de objetos",
                },
                "decision.decision": {
                    "type": "boolean",
                    "description": "Activar toma de decisiones",
                },
                "sumo.simular": {
                    "type": "boolean",
                    "description": "Activar simulación SUMO",
                },
                "reporte.generar": {
                    "type": "boolean",
                    "description": "Activar generación de reportes",
                },
            }

            if field_path in field_constraints:
                field_constraint = field_constraints[field_path]
                if isinstance(field_constraint, dict):
                    constraints.update(field_constraint)

        except Exception as e:
            logger.warning(
                f"⚠️ No se pudieron obtener constraints para {field_path}: {e}"
            )

        return constraints


def format_validation_error_for_ui(error_message: str) -> str:
    """
    Format validation error message for UI display.

    Args:
        error_message: Raw error message

    Returns:
        Formatted error message for user interface
    """
    # Remove technical jargon and make more user-friendly
    replacements = {
        "ensure this value is greater than": "debe ser mayor que",
        "ensure this value is less than": "debe ser menor que",
        "field required": "campo requerido",
        "invalid literal": "valor inválido",
        "not a valid integer": "debe ser un número entero",
        "not a valid boolean": "debe ser verdadero o falso",
        "str type expected": "debe ser texto",
        "int type expected": "debe ser un número entero",
        "float type expected": "debe ser un número decimal",
        "bool type expected": "debe ser verdadero o falso",
    }

    formatted = error_message
    for english, spanish in replacements.items():
        formatted = formatted.replace(english, spanish)

    return formatted


def get_validation_status_color(is_valid: bool) -> str:
    """
    Get color code for validation status display.

    Args:
        is_valid: Whether the validation passed

    Returns:
        Color string for Streamlit
    """
    return "green" if is_valid else "red"


def get_validation_status_icon(is_valid: bool) -> str:
    """
    Get icon for validation status display.

    Args:
        is_valid: Whether the validation passed

    Returns:
        Icon string for display
    """
    return "✅" if is_valid else "❌"
