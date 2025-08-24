"""
Configuration Editor Components

Advanced widget generation system for editing configuration with
proper validation, nested object support, and array/list management.
"""

import logging
from typing import Any

import streamlit as st

from src.traffic_system.frontend.utils.validators import (
    ConfigValidator,
    format_validation_error_for_ui,
    get_validation_status_color,
    get_validation_status_icon,
)

logger = logging.getLogger(__name__)


class ConfigWidgetFactory:
    """Factory for creating configuration editing widgets."""

    def __init__(self, validator: ConfigValidator):
        """
        Initialize the widget factory.

        Args:
            validator: Configuration validator instance
        """
        self.validator = validator
        self._widget_counter = 0

    def create_widget(
        self,
        key: str,
        value: Any,
        path: str,
        full_config: dict[str, Any],
        constraints: dict[str, Any] | None = None,
    ) -> Any:
        """
        Create appropriate widget for a configuration value.

        Args:
            key: Configuration key name
            value: Current value
            path: Full dot-separated path to the field
            full_config: Complete configuration for validation context
            constraints: Field constraints from validator

        Returns:
            New value from widget
        """
        if constraints is None:
            constraints = self.validator.get_field_constraints(path)

        widget_key = f"config_widget_{path}_{self._widget_counter}"
        self._widget_counter += 1

        # Create widget based on type
        if isinstance(value, bool):
            return self._create_boolean_widget(key, value, widget_key, constraints)
        elif isinstance(value, int):
            return self._create_integer_widget(key, value, widget_key, constraints)
        elif isinstance(value, float):
            return self._create_float_widget(key, value, widget_key, constraints)
        elif isinstance(value, str):
            return self._create_string_widget(key, value, widget_key, constraints)
        elif isinstance(value, list):
            return self._create_list_widget(key, value, widget_key, path, full_config)
        elif isinstance(value, dict):
            return self._create_dict_widget(key, value, path, full_config)
        else:
            return self._create_generic_widget(key, value, widget_key)

    def _create_boolean_widget(
        self, key: str, value: bool, widget_key: str, constraints: dict[str, Any]
    ) -> bool:
        """Create a boolean checkbox widget."""
        col1, col2 = st.columns([3, 1])

        with col1:
            new_value = st.checkbox(
                label=f"**{key}**",
                value=value,
                key=widget_key,
                help=constraints.get("description", f"Boolean setting: {key}"),
            )

        with col2:
            if constraints.get("required", False):
                st.caption("🔴 Requerido")

        return new_value

    def _create_integer_widget(
        self, key: str, value: int, widget_key: str, constraints: dict[str, Any]
    ) -> int:
        """Create an integer number input widget."""
        col1, col2 = st.columns([3, 1])

        with col1:
            new_value = st.number_input(
                label=f"**{key}**",
                value=value,
                min_value=constraints.get("min_value"),
                max_value=constraints.get("max_value"),
                step=1,
                key=widget_key,
                help=constraints.get("description", f"Integer setting: {key}"),
            )

        with col2:
            if constraints.get("required", False):
                st.caption("🔴 Requerido")

            # Show range if available
            min_val = constraints.get("min_value")
            max_val = constraints.get("max_value")
            if min_val is not None or max_val is not None:
                range_text = f"{min_val or '∞'} - {max_val or '∞'}"
                st.caption(f"📊 {range_text}")

        return int(new_value)

    def _create_float_widget(
        self, key: str, value: float, widget_key: str, constraints: dict[str, Any]
    ) -> float:
        """Create a float number input widget."""
        col1, col2 = st.columns([3, 1])

        with col1:
            new_value = st.number_input(
                label=f"**{key}**",
                value=value,
                min_value=constraints.get("min_value"),
                max_value=constraints.get("max_value"),
                format="%.6f",
                key=widget_key,
                help=constraints.get("description", f"Float setting: {key}"),
            )

        with col2:
            if constraints.get("required", False):
                st.caption("🔴 Requerido")

        return float(new_value)

    def _create_string_widget(
        self, key: str, value: str, widget_key: str, constraints: dict[str, Any]
    ) -> str:
        """Create a string input widget."""
        choices = constraints.get("choices")

        col1, col2 = st.columns([3, 1])

        with col1:
            if choices:
                # Use selectbox for predefined choices
                new_value = st.selectbox(
                    label=f"**{key}**",
                    options=choices,
                    index=choices.index(value) if value in choices else 0,
                    key=widget_key,
                    help=constraints.get("description", f"String setting: {key}"),
                )
            elif len(value) > 100 or "\n" in value:
                # Use text area for long strings
                new_value = st.text_area(
                    label=f"**{key}**",
                    value=value,
                    key=widget_key,
                    help=constraints.get("description", f"String setting: {key}"),
                )
            else:
                # Use text input for short strings
                new_value = st.text_input(
                    label=f"**{key}**",
                    value=value,
                    key=widget_key,
                    help=constraints.get("description", f"String setting: {key}"),
                )

        with col2:
            if constraints.get("required", False):
                st.caption("🔴 Requerido")

        return new_value

    def _create_list_widget(
        self,
        key: str,
        value: list[Any],
        widget_key: str,
        path: str,
        full_config: dict[str, Any],
    ) -> list[Any]:
        """Create a list editing widget with add/remove functionality."""
        st.write(f"**{key}** (Lista - {len(value)} elementos)")

        # Determine list item type
        item_type = type(value[0]) if value else str

        # Container for list items
        list_container = st.container()

        with list_container:
            new_list = []

            # Edit existing items
            for i, item in enumerate(value):
                col1, col2, col3 = st.columns([4, 1, 1])

                with col1:
                    if item_type == bool:
                        new_item = st.checkbox(
                            f"Elemento {i+1}", value=item, key=f"{widget_key}_item_{i}"
                        )
                    elif item_type in (int, float):
                        new_item = st.number_input(
                            f"Elemento {i+1}", value=item, key=f"{widget_key}_item_{i}"
                        )
                    else:
                        new_item = st.text_input(
                            f"Elemento {i+1}",
                            value=str(item),
                            key=f"{widget_key}_item_{i}",
                        )
                        # Convert back to original type if needed
                        if item_type != str:
                            try:
                                new_item = item_type(new_item)
                            except (ValueError, TypeError):
                                new_item = item  # Keep original if conversion fails

                with col2:
                    # Move up button
                    if st.button("⬆️", key=f"{widget_key}_up_{i}", disabled=i == 0):
                        # This would require state management to reorder
                        pass

                with col3:
                    # Remove button
                    if st.button("🗑️", key=f"{widget_key}_remove_{i}"):
                        # Skip this item (effectively removing it)
                        continue

                new_list.append(new_item)

            # Add new item section
            st.markdown("---")
            col1, col2 = st.columns([3, 1])

            with col1:
                if item_type == bool:
                    new_item_value = st.checkbox(
                        "Nuevo elemento", key=f"{widget_key}_new_item"
                    )
                elif item_type in (int, float):
                    new_item_value = st.number_input(
                        "Nuevo elemento",
                        value=item_type(0),
                        key=f"{widget_key}_new_item",
                    )
                else:
                    new_item_value = st.text_input(
                        "Nuevo elemento", key=f"{widget_key}_new_item"
                    )

            with col2:
                if st.button("➕ Agregar", key=f"{widget_key}_add"):
                    if new_item_value or item_type == bool:
                        new_list.append(new_item_value)
                        st.rerun()

        return new_list

    def _create_dict_widget(
        self, key: str, value: dict[str, Any], path: str, full_config: dict[str, Any]
    ) -> dict[str, Any]:
        """Create a nested dictionary widget."""
        with st.expander(f"📁 **{key}** ({len(value)} campos)", expanded=False):
            new_dict = {}

            for sub_key, sub_value in value.items():
                sub_path = f"{path}.{sub_key}" if path else sub_key
                new_dict[sub_key] = self.create_widget(
                    sub_key, sub_value, sub_path, full_config
                )

        return new_dict

    def _create_generic_widget(self, key: str, value: Any, widget_key: str) -> Any:
        """Create a generic widget for unsupported types."""
        st.write(f"**{key}**: `{value}` (tipo: {type(value).__name__})")
        st.caption("⚠️ Tipo no soportado para edición")
        return value


class ConfigSectionRenderer:
    """Renders configuration sections with validation and organization."""

    def __init__(self, validator: ConfigValidator):
        """
        Initialize the section renderer.

        Args:
            validator: Configuration validator instance
        """
        self.validator = validator
        self.widget_factory = ConfigWidgetFactory(validator)

    def render_section(
        self,
        section_name: str,
        section_data: dict[str, Any],
        full_config: dict[str, Any],
        expanded: bool = False,
    ) -> tuple[dict[str, Any], bool]:
        """
        Render a configuration section with validation.

        Args:
            section_name: Name of the section
            section_data: Section configuration data
            full_config: Complete configuration for validation
            expanded: Whether section should be expanded by default

        Returns:
            Tuple of (updated_section_data, has_changes)
        """
        # Validate section
        is_valid, errors = self.validator.validate_section(
            section_name, section_data, full_config
        )

        # Section header with validation status
        status_icon = get_validation_status_icon(is_valid)
        status_color = get_validation_status_color(is_valid)

        section_title = f"{status_icon} **{section_name}**"
        if not is_valid:
            section_title += f" ({len(errors)} errores)"

        with st.expander(section_title, expanded=expanded):
            # Show validation errors if any
            if not is_valid:
                st.error("❌ Errores de validación:")
                for error in errors:
                    st.error(f"• {format_validation_error_for_ui(error)}")
                st.markdown("---")

            # Render section fields
            new_section_data = {}
            has_changes = False

            for key, value in section_data.items():
                field_path = f"{section_name}.{key}"

                # Create widget for field
                new_value = self.widget_factory.create_widget(
                    key, value, field_path, full_config
                )

                # Check for changes
                if new_value != value:
                    has_changes = True

                new_section_data[key] = new_value

                # Add field-level validation
                field_valid, field_error = self.validator.validate_field(
                    field_path, new_value, full_config
                )

                if not field_valid and field_error:
                    st.error(f"⚠️ {format_validation_error_for_ui(field_error)}")

                # Add spacing between fields
                st.markdown("")

        return new_section_data, has_changes

    def render_config_overview(self, config: dict[str, Any]) -> None:
        """
        Render configuration overview with summary statistics.

        Args:
            config: Complete configuration
        """
        # Validate entire configuration
        is_valid, errors, _ = self.validator.validate_full_config(config)

        # Overview metrics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Secciones", len(config))

        with col2:
            total_fields = sum(
                len(section) if isinstance(section, dict) else 1
                for section in config.values()
            )
            st.metric("Campos Totales", total_fields)

        with col3:
            if is_valid:
                st.metric("Estado", "✅ Válido", delta="Sin errores")
            else:
                st.metric("Estado", "❌ Inválido", delta=f"{len(errors)} errores")

        with col4:
            # Configuration size estimate
            import json

            config_size = len(json.dumps(config, indent=2))
            st.metric("Tamaño Config", f"{config_size} chars")

        # Show validation summary
        if not is_valid:
            with st.expander("❌ Errores de Validación", expanded=False):
                for i, error in enumerate(errors[:10], 1):  # Show first 10 errors
                    st.error(f"{i}. {format_validation_error_for_ui(error)}")

                if len(errors) > 10:
                    st.warning(f"... y {len(errors) - 10} errores más")


def render_advanced_config_editor(
    config: dict[str, Any], validator: ConfigValidator
) -> tuple[dict[str, Any], bool]:
    """
    Render the advanced configuration editor.

    Args:
        config: Current configuration
        validator: Configuration validator

    Returns:
        Tuple of (updated_config, has_changes)
    """
    renderer = ConfigSectionRenderer(validator)

    # Configuration overview
    st.subheader("📊 Resumen de Configuración")
    renderer.render_config_overview(config)

    st.markdown("---")

    # Configuration sections
    st.subheader("⚙️ Secciones de Configuración")

    # Define section metadata
    section_metadata = {
        "services": {
            "title": "🔌 Servicios y Puertos",
            "description": "Configuración de puertos para microservicios",
            "expanded": True,
        },
        "deteccion": {
            "title": "👁️ Detección YOLOv8",
            "description": "Configuración de detección de vehículos",
            "expanded": False,
        },
        "decision": {
            "title": "🧠 Decisión y DQN",
            "description": "Configuración del agente de decisión y entrenamiento",
            "expanded": False,
        },
        "sumo": {
            "title": "🚗 Simulación SUMO",
            "description": "Configuración de simulación de tráfico",
            "expanded": False,
        },
        "reporte": {
            "title": "📊 Reportes y Análisis",
            "description": "Configuración de generación de reportes",
            "expanded": False,
        },
    }

    new_config = {}
    overall_has_changes = False

    # Render base configuration fields (non-dict values)
    base_fields = {k: v for k, v in config.items() if not isinstance(v, dict)}
    if base_fields:
        st.subheader("🌐 Configuración Base")
        for key, value in base_fields.items():
            new_value = renderer.widget_factory.create_widget(key, value, key, config)
            if new_value != value:
                overall_has_changes = True
            new_config[key] = new_value

        st.markdown("---")

    # Render configuration sections
    for section_name, section_data in config.items():
        if isinstance(section_data, dict):
            metadata = section_metadata.get(
                section_name,
                {
                    "title": f"📁 {section_name.title()}",
                    "description": f"Configuración de {section_name}",
                    "expanded": False,
                },
            )

            st.write(f"### {metadata['title']}")
            st.caption(metadata["description"])

            new_section_data, section_has_changes = renderer.render_section(
                section_name, section_data, config, expanded=metadata["expanded"]
            )

            if section_has_changes:
                overall_has_changes = True

            new_config[section_name] = new_section_data

            st.markdown("---")

    return new_config, overall_has_changes
