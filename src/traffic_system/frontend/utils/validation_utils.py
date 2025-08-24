"""
Validation Utilities for Configuration Frontend

Provides comprehensive validation feedback and error handling
for configuration management with user-friendly messages.
"""

import logging
from typing import Any

import streamlit as st
from pydantic import ValidationError

from src.traffic_system.frontend.utils.config_handler import ConfigHandler

logger = logging.getLogger(__name__)


class ValidationFeedbackUI:
    """User interface for validation feedback and error display."""

    def __init__(self, config_handler: ConfigHandler):
        """
        Initialize validation feedback UI.

        Args:
            config_handler: Configuration handler instance
        """
        self.config_handler = config_handler

    def validate_and_show_feedback(
        self, config: dict[str, Any], show_success: bool = True
    ) -> bool:
        """
        Validate configuration and show feedback in UI.

        Args:
            config: Configuration to validate
            show_success: Whether to show success message

        Returns:
            True if validation passed, False otherwise
        """
        try:
            # Perform validation
            is_valid, errors = self.config_handler.test_load_config(config)

            if is_valid:
                if show_success:
                    st.success("✅ Configuración válida - Sin errores encontrados")
                return True
            else:
                # Show validation errors
                self._display_validation_errors(errors)
                return False

        except Exception as e:
            st.error(f"❌ Error durante validación: {e}")
            logger.error(f"Error during validation: {e}")
            return False

    def _display_validation_errors(self, errors: list[str]) -> None:
        """Display validation errors in a user-friendly format."""
        st.error("❌ **Errores de Validación Encontrados**")

        # Group errors by category
        field_errors = []
        type_errors = []
        missing_errors = []
        other_errors = []

        for error in errors:
            error_lower = error.lower()
            if "campo" in error_lower or "->" in error:
                field_errors.append(error)
            elif "missing" in error_lower or "required" in error_lower:
                missing_errors.append(error)
            elif "must be" in error_lower or "invalid" in error_lower:
                type_errors.append(error)
            else:
                other_errors.append(error)

        # Display errors by category
        if missing_errors:
            with st.expander("❌ Campos Requeridos Faltantes", expanded=True):
                for error in missing_errors:
                    st.write(f"• {error}")

        if type_errors:
            with st.expander("⚠️ Errores de Tipo de Datos", expanded=True):
                for error in type_errors:
                    st.write(f"• {error}")

        if field_errors:
            with st.expander("🔍 Errores de Campos Específicos", expanded=True):
                for error in field_errors:
                    st.write(f"• {error}")

        if other_errors:
            with st.expander("📋 Otros Errores", expanded=True):
                for error in other_errors:
                    st.write(f"• {error}")

        # Show recommendations
        st.info(
            "**💡 Recomendaciones:**\n"
            "• Revisa los campos marcados con errores\n"
            "• Verifica que los tipos de datos sean correctos\n"
            "• Asegúrate de que todos los campos requeridos estén completos\n"
            "• Usa los valores por defecto como referencia"
        )

    def show_validation_summary(self, config: dict[str, Any]) -> None:
        """Show a comprehensive validation summary."""
        st.subheader("🔍 Resumen de Validación")

        col1, col2, col3 = st.columns(3)

        # Basic structure validation
        with col1:
            basic_valid, basic_errors = self.config_handler.validate_config_structure(
                config
            )
            if basic_valid:
                st.success("✅ Estructura Básica")
            else:
                st.error(f"❌ Estructura ({len(basic_errors)} errores)")

        # Pydantic validation
        with col2:
            pydantic_valid, pydantic_errors, _ = (
                self.config_handler.validate_config_with_pydantic(config)
            )
            if pydantic_valid:
                st.success("✅ Validación Completa")
            else:
                st.error(f"❌ Validación ({len(pydantic_errors)} errores)")

        # Overall status
        with col3:
            overall_valid = basic_valid and pydantic_valid
            if overall_valid:
                st.success("✅ Todo Válido")
            else:
                total_errors = len(basic_errors) + len(pydantic_errors)
                st.error(f"❌ {total_errors} Errores Total")

        # Detailed breakdown if there are errors
        if not overall_valid:
            st.markdown("---")
            all_errors = basic_errors + pydantic_errors
            self._display_validation_errors(all_errors)

    def validate_before_save_dialog(self, config: dict[str, Any]) -> bool:
        """
        Show validation dialog before saving configuration.

        Args:
            config: Configuration to validate

        Returns:
            True if user confirms save despite errors, False otherwise
        """
        is_valid, errors = self.config_handler.test_load_config(config)

        if is_valid:
            st.success("✅ Configuración válida - Lista para guardar")
            return True

        # Show errors and ask for confirmation
        st.error("❌ **Errores de Validación Encontrados**")
        self._display_validation_errors(errors)

        st.warning(
            "⚠️ **¿Deseas guardar la configuración con errores?**\n\n"
            "**Advertencia:** Guardar una configuración inválida puede causar:\n"
            "• Fallos en el inicio de servicios\n"
            "• Comportamiento inesperado del sistema\n"
            "• Pérdida de funcionalidad\n\n"
            "**Recomendación:** Corrige los errores antes de guardar."
        )

        col1, col2, col3 = st.columns([1, 1, 2])

        with col1:
            if st.button("💾 Guardar Anyway", type="primary"):
                st.warning("⚠️ Guardando configuración con errores...")
                return True

        with col2:
            if st.button("❌ Cancelar"):
                st.info("Guardado cancelado - Corrige los errores primero")
                return False

        return False

    def show_field_validation_status(
        self, field_path: str, value: Any, expected_type: type = None
    ) -> None:
        """
        Show validation status for a specific field.

        Args:
            field_path: Path to the field (e.g., "services.simulation_port")
            value: Current field value
            expected_type: Expected type for the field
        """
        try:
            # Basic type checking
            if expected_type and not isinstance(value, expected_type):
                st.error(f"❌ Tipo incorrecto: esperado {expected_type.__name__}")
                return

            # Field-specific validation
            if "port" in field_path.lower():
                if isinstance(value, int) and 1024 <= value <= 65535:
                    st.success("✅ Puerto válido")
                else:
                    st.error("❌ Puerto debe estar entre 1024-65535")
            elif "path" in field_path.lower():
                if isinstance(value, str) and value.strip():
                    st.success("✅ Ruta especificada")
                else:
                    st.error("❌ Ruta requerida")
            elif field_path.endswith(("detectar", "decision", "simular", "generar")):
                if isinstance(value, bool):
                    st.success("✅ Valor booleano válido")
                else:
                    st.error("❌ Debe ser verdadero o falso")
            else:
                st.success("✅ Campo válido")

        except Exception as e:
            st.error(f"❌ Error validando campo: {e}")

    def validate_field(
        self, field_path: str, value: Any, config: dict[str, Any]
    ) -> tuple[bool, str | None]:
        """
        Validate a specific field in the configuration.

        Args:
            field_path: Path to the field (e.g., "services.simulation_port")
            value: Current field value
            config: Full configuration dictionary

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Field-specific validation
            if "port" in field_path.lower():
                if isinstance(value, int) and 1024 <= value <= 65535:
                    return True, None
                else:
                    return False, "Puerto debe estar entre 1024-65535"
            elif "path" in field_path.lower():
                if isinstance(value, str) and value.strip():
                    return True, None
                else:
                    return False, "Ruta requerida"
            elif field_path.endswith(("detectar", "decision", "simular", "generar")):
                if isinstance(value, bool):
                    return True, None
                else:
                    return False, "Debe ser verdadero o falso"
            else:
                return True, None

        except Exception as e:
            return False, f"Error validando campo: {e}"

    def validate_full_config(
        self, config: dict[str, Any]
    ) -> tuple[bool, list[str], list[str]]:
        """
        Validate the full configuration.

        Args:
            config: Configuration dictionary to validate

        Returns:
            Tuple of (is_valid, errors, warnings)
        """
        try:
            is_valid, errors = self.config_handler.test_load_config(config)
            warnings = []  # Could add warnings logic here if needed
            return is_valid, errors, warnings
        except Exception as e:
            return False, [f"Error during validation: {e}"], []

    def create_validation_help_section(self) -> None:
        """Create a help section explaining validation rules."""
        with st.expander("❓ Ayuda de Validación", expanded=False):
            st.markdown(
                """
                ### 🔍 Reglas de Validación

                **Campos Requeridos:**
                - Todas las secciones principales deben estar presentes
                - Los campos marcados como obligatorios no pueden estar vacíos

                **Tipos de Datos:**
                - **Puertos**: Números enteros entre 1024 y 65535
                - **Rutas**: Cadenas de texto no vacías
                - **Booleanos**: Verdadero (true) o Falso (false)
                - **Números**: Valores numéricos válidos
                - **Listas**: Arrays con elementos del tipo correcto

                **Validaciones Específicas:**
                - **Zonas de Tráfico**: Deben ser exactamente 12 zonas (A-L)
                - **Estados de Semáforos**: Deben ser exactamente 4 estados
                - **Ponderaciones**: Deben sumar valores coherentes
                - **Rutas de Archivos**: Deben apuntar a ubicaciones válidas

                **Consejos:**
                - Usa los valores por defecto como referencia
                - Revisa los mensajes de error específicos
                - Valida antes de guardar para evitar problemas
                - Crea backups antes de cambios importantes
                """
            )


def create_validation_feedback_ui(
    config_handler: ConfigHandler,
) -> ValidationFeedbackUI:
    """
    Factory function to create validation feedback UI.

    Args:
        config_handler: Configuration handler instance

    Returns:
        ValidationFeedbackUI instance
    """
    return ValidationFeedbackUI(config_handler)


def validate_config_section(
    section_name: str, section_data: dict[str, Any], show_feedback: bool = True
) -> bool:
    """
    Validate a specific configuration section.

    Args:
        section_name: Name of the configuration section
        section_data: Section data to validate
        show_feedback: Whether to show validation feedback

    Returns:
        True if section is valid, False otherwise
    """
    try:
        # Import the specific section models
        from src.traffic_system.core.config_models import (
            DecisionSettings,
            DeteccionSettings,
            ReporteSettings,
            ServicesSettings,
            SumoSettings,
        )

        # Map section names to their specific Pydantic models
        section_models = {
            "services": ServicesSettings,
            "deteccion": DeteccionSettings,
            "decision": DecisionSettings,
            "sumo": SumoSettings,
            "reporte": ReporteSettings,
        }

        if section_name not in section_models:
            if show_feedback:
                st.warning(f"⚠️ Sección desconocida: {section_name}")
            return False

        # Validate section directly with its specific model
        section_models[section_name](**section_data)

        if show_feedback:
            st.success(f"✅ Sección '{section_name}' válida")
        return True

    except ValidationError as e:
        if show_feedback:
            st.error(f"❌ Errores en sección '{section_name}':")
            for error in e.errors():
                field_path = " -> ".join(str(loc) for loc in error["loc"])
                st.write(f"• {field_path}: {error['msg']}")
        return False

    except Exception as e:
        if show_feedback:
            st.error(f"❌ Error validando sección '{section_name}': {e}")
        return False
