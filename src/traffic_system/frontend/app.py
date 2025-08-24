"""
Main Streamlit Application for Traffic System Configuration

Provides web interface for managing configuration and controlling services.
"""

import logging
import traceback
from typing import Any

import streamlit as st

from src.traffic_system.frontend.utils.config_handler import ConfigHandler
from src.traffic_system.frontend.utils.service_manager import ServiceManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def initialize_session_state() -> None:
    """Initialize Streamlit session state variables."""
    if "config_handler" not in st.session_state:
        st.session_state.config_handler = ConfigHandler()

    if "service_manager" not in st.session_state:
        st.session_state.service_manager = ServiceManager()

    if "validator" not in st.session_state:
        try:
            from src.traffic_system.frontend.utils.validation_utils import (
                ValidationFeedbackUI,
            )

            st.session_state.validator = ValidationFeedbackUI(
                st.session_state.config_handler
            )
        except Exception as e:
            logger.error(f"Error importing ValidationFeedbackUI: {e}")
            # Create a dummy validation UI to prevent crashes
            st.session_state.validator = None

    if "current_config" not in st.session_state:
        try:
            st.session_state.current_config = (
                st.session_state.config_handler.read_config()
            )
        except Exception as e:
            st.error(f"❌ Error cargando configuración: {e}")
            st.session_state.current_config = {}

    if "config_modified" not in st.session_state:
        st.session_state.config_modified = False

    if "last_validation_result" not in st.session_state:
        st.session_state.last_validation_result = (True, [], None)


def render_sidebar() -> str:
    """
    Render navigation sidebar.

    Returns:
        Selected page name
    """
    st.sidebar.title("🚦 Traffic System")
    st.sidebar.markdown("---")

    # Navigation menu
    pages = {
        "🏠 Dashboard": "dashboard",
        "⚙️ Configuración": "config",
        "🔧 Servicios": "services",
        "📦 Backups": "backups",
        "ℹ️ Información": "info",
    }

    selected_page = st.sidebar.selectbox(
        "Navegación", options=list(pages.keys()), index=0
    )

    st.sidebar.markdown("---")

    # Quick status indicators
    st.sidebar.subheader("Estado Rápido")

    try:
        service_status = st.session_state.service_manager.get_all_services_status()
        running_count = sum(
            1 for status in service_status.values() if status.is_running
        )
        total_count = len(service_status)

        if running_count == total_count:
            st.sidebar.success(
                f"✅ Todos los servicios activos ({running_count}/{total_count})"
            )
        elif running_count > 0:
            st.sidebar.warning(
                f"⚠️ Algunos servicios activos ({running_count}/{total_count})"
            )
        else:
            st.sidebar.error(
                f"❌ Ningún servicio activo ({running_count}/{total_count})"
            )

    except Exception as e:
        st.sidebar.error(f"❌ Error verificando servicios: {e}")

    # Configuration status
    if st.session_state.config_modified:
        st.sidebar.warning("⚠️ Configuración modificada")
    else:
        st.sidebar.info("ℹ️ Configuración guardada")

    return pages[selected_page]


def render_dashboard() -> None:
    """Render the main dashboard page."""
    st.title("🚦 Dashboard del Sistema de Tráfico")

    # System overview
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Servicios Activos", "0/4", "0")

    with col2:
        st.metric("CPU Sistema", "0%", "0%")

    with col3:
        st.metric("Memoria Sistema", "0%", "0%")

    st.markdown("---")

    # Quick actions
    st.subheader("🚀 Acciones Rápidas")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("▶️ Iniciar Todos", use_container_width=True):
            with st.spinner("Iniciando servicios..."):
                results = st.session_state.service_manager.start_all_services()
                for service, (success, msg) in results.items():
                    if success:
                        st.success(f"✅ {service}: {msg}")
                    else:
                        st.error(f"❌ {service}: {msg}")

    with col2:
        if st.button("⏹️ Detener Todos", use_container_width=True):
            with st.spinner("Deteniendo servicios..."):
                results = st.session_state.service_manager.stop_all_services()
                for service, (success, msg) in results.items():
                    if success:
                        st.success(f"✅ {service}: {msg}")
                    else:
                        st.error(f"❌ {service}: {msg}")

    with col3:
        if st.button("🔄 Recargar Config", use_container_width=True):
            try:
                st.session_state.current_config = (
                    st.session_state.config_handler.read_config()
                )
                st.session_state.config_modified = False
                st.success("✅ Configuración recargada")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error recargando configuración: {e}")

    with col4:
        if st.button("📦 Backup Rápido", use_container_width=True):
            try:
                backup_path = st.session_state.config_handler.create_backup("manual")
                st.success(f"✅ Backup creado: {backup_path.name}")
            except Exception as e:
                st.error(f"❌ Error creando backup: {e}")

    st.markdown("---")

    # Recent activity placeholder
    st.subheader("📊 Actividad Reciente")
    st.info("🔄 Implementación pendiente: logs y actividad del sistema")


def render_config_page() -> None:
    """Render the configuration editing page with enhanced validation integration."""
    st.title("⚙️ Configuración del Sistema")

    # Import the advanced config editor
    from src.traffic_system.frontend.components.config_editor import (
        render_advanced_config_editor,
    )

    # Create validation alert system in sidebar
    create_validation_alert_system()

    # Enhanced save/cancel buttons with validation status
    col1, col2, col3, col4 = st.columns([1, 1, 1, 3])

    with col1:
        # Check validation status for save button
        try:
            is_valid, errors, _ = st.session_state.validator.validate_full_config(
                st.session_state.current_config
            )
            pydantic_valid, pydantic_errors, _ = (
                st.session_state.config_handler.validate_config_with_pydantic(
                    st.session_state.current_config
                )
            )

            total_errors = len(errors) + len(pydantic_errors)
            overall_valid = is_valid and pydantic_valid

            # Save button with validation-aware styling
            if overall_valid:
                save_button_type = "primary"
                save_button_text = "💾 Guardar"
            else:
                save_button_type = "secondary"
                save_button_text = f"⚠️ Guardar ({total_errors} errores)"

        except Exception:
            save_button_type = "secondary"
            save_button_text = "💾 Guardar"
            overall_valid = False

        if st.button(
            save_button_text,
            use_container_width=True,
            disabled=not st.session_state.config_modified,
            type=save_button_type,
            help=(
                "Guardar configuración con validación completa"
                if overall_valid
                else "Guardar con errores de validación"
            ),
        ):
            save_configuration()

    with col2:
        if st.button(
            "❌ Cancelar",
            use_container_width=True,
            disabled=not st.session_state.config_modified,
            help="Descartar cambios y revertir a la configuración guardada",
        ):
            cancel_changes()

    with col3:
        if st.button(
            "🔄 Recargar",
            use_container_width=True,
            help="Recargar configuración desde archivo",
        ):
            reload_configuration()

    # Enhanced status indicator with validation info
    if st.session_state.config_modified:
        if overall_valid:
            st.warning("⚠️ Hay cambios sin guardar (configuración válida)")
        else:
            st.error(
                f"❌ Hay cambios sin guardar ({total_errors} errores de validación)"
            )
    else:
        st.success("✅ Configuración sincronizada y válida")

    # Quick validation panel
    with st.expander("🔍 Estado de Validación", expanded=not overall_valid):
        show_validation_summary()

    # Validation help panel
    create_validation_help_panel()

    # Configuration audit log
    with st.expander("📋 Log de Cambios", expanded=False):
        show_configuration_audit_log()

    st.markdown("---")

    # Advanced configuration editor with real-time validation
    try:
        new_config, has_changes = render_advanced_config_editor(
            st.session_state.current_config, st.session_state.validator
        )

        # Update session state if there are changes
        if has_changes:
            st.session_state.current_config = new_config
            st.session_state.config_modified = True

            # Auto-validation if enabled
            if st.session_state.get("auto_validation", True):
                # Trigger validation in background
                try:
                    validate_field_value("", "")  # Trigger validation cache refresh
                except Exception:
                    pass  # Ignore validation errors during auto-validation

    except Exception as e:
        st.error(f"❌ Error renderizando editor de configuración: {e}")
        logger.error(f"Error in config editor: {e}")

        # Show fallback configuration editor
        st.warning("⚠️ Usando editor de configuración básico")
        with st.expander("Editor Básico", expanded=True):
            st.text_area(
                "Configuración YAML",
                value=str(st.session_state.current_config),
                height=400,
                help="Editor de texto básico para configuración",
            )

        # Fallback to basic editor
        st.warning("⚠️ Usando editor básico como respaldo")
        render_basic_config_editor()


def render_config_section(section_keys: list[str]) -> None:
    """
    Render a configuration section with appropriate widgets.

    Args:
        section_keys: List of configuration keys to render
    """
    config = st.session_state.current_config

    for key in section_keys:
        if key in config:
            render_config_field(key, config[key], key)


def render_config_field(key: str, value: Any, path: str) -> None:
    """
    Render a configuration field with appropriate widget and real-time validation.

    Args:
        key: Configuration key name
        value: Current value
        path: Full path to the field
    """
    new_value: Any = None
    validation_key = f"validation_{path}"

    # Create columns for field and validation feedback
    col1, col2 = st.columns([3, 1])

    with col1:
        if isinstance(value, bool):
            new_value = st.checkbox(f"{key}", value=value, key=f"config_{path}")
        elif isinstance(value, int):
            new_value = st.number_input(f"{key}", value=value, key=f"config_{path}")
        elif isinstance(value, float):
            new_value = st.number_input(
                f"{key}", value=value, format="%.6f", key=f"config_{path}"
            )
        elif isinstance(value, str):
            new_value = st.text_input(f"{key}", value=value, key=f"config_{path}")
        elif isinstance(value, list):
            st.write(f"**{key}** (Lista):")
            text_value = st.text_area(
                "Valores separados por líneas",
                value="\n".join(str(item) for item in value),
                key=f"config_{path}",
            )
            new_value = text_value.split("\n")
            # Convert back to appropriate types if needed
            if value and isinstance(value[0], int | float):
                try:
                    new_value = [
                        type(value[0])(item.strip())
                        for item in new_value
                        if item.strip()
                    ]
                except ValueError:
                    st.error(f"❌ Error: valores inválidos en {key}")
                    new_value = value
        elif isinstance(value, dict):
            st.write(f"**{key}** (Sección):")
            with st.container():
                for sub_key, sub_value in value.items():
                    render_config_field(sub_key, sub_value, f"{path}.{sub_key}")
            return  # Don't update value for dict sections
        else:
            st.write(f"**{key}**: {value} (tipo no soportado)")
            return

    with col2:
        # Real-time validation feedback
        if new_value != value and new_value is not None:
            # Validate the new value
            is_valid, error_msg = validate_field_value(path, new_value)

            if is_valid:
                st.success("✅")
            else:
                st.error("❌")
                if error_msg:
                    st.caption(error_msg)
        else:
            # Show current validation status
            is_valid, _ = validate_field_value(path, value)
            if is_valid:
                st.success("✅")
            else:
                st.warning("⚠️")

    # Update configuration if value changed
    if new_value != value:
        update_config_value(path, new_value)


def update_config_value(path: str, new_value: Any) -> None:
    """
    Update a configuration value and mark as modified.

    Args:
        path: Dot-separated path to the field
        new_value: New value to set
    """
    keys = path.split(".")
    config = st.session_state.current_config

    # Navigate to parent
    current = config
    for key in keys[:-1]:
        if key not in current:
            current[key] = {}
        current = current[key]

    # Set the value
    current[keys[-1]] = new_value
    st.session_state.config_modified = True


def save_configuration() -> None:
    """Save the current configuration to file with comprehensive validation and rollback."""
    try:
        # Step 1: Enhanced pre-save validation
        st.info("🔍 Ejecutando validación completa...")

        with st.spinner("Validando configuración..."):
            is_valid, validation_errors, backup_path = validate_config_before_save(
                st.session_state.current_config
            )

        if not is_valid:
            st.error("❌ La configuración no es válida:")

            # Show detailed validation errors
            with st.expander("Ver errores de validación", expanded=True):
                for i, error in enumerate(validation_errors, 1):
                    st.error(f"{i}. {error}")

            # Ask user if they want to proceed anyway
            st.warning("⚠️ **¿Deseas guardar la configuración con errores?**")

            col1, col2, col3 = st.columns([1, 1, 2])

            with col1:
                if st.button("💾 Guardar Anyway", type="primary"):
                    st.warning("⚠️ Guardando configuración con errores...")
                    # Continue with save process
                else:
                    return

            with col2:
                if st.button("❌ Cancelar"):
                    st.info("Guardado cancelado - Corrige los errores primero")
                    return

        # Step 2: Save configuration
        st.info("💾 Guardando configuración...")

        with st.spinner("Escribiendo archivo..."):
            success, save_errors = (
                st.session_state.config_handler.validate_and_write_config(
                    st.session_state.current_config
                )
            )

        if not success:
            st.error("❌ Error durante el guardado:")
            for error in save_errors:
                st.error(f"• {error}")

            # Attempt rollback if we have a backup
            if backup_path:
                st.warning("🔄 Intentando rollback...")
                rollback_success = handle_validation_failure_rollback(backup_path)
                if rollback_success:
                    st.success("✅ Rollback completado - configuración restaurada")
                else:
                    st.error("❌ Error durante rollback - revisa manualmente")

            return

        # Step 3: Post-save verification
        st.info("✅ Verificando configuración guardada...")

        with st.spinner("Verificando integridad..."):
            verification_success = verify_saved_configuration()

        if verification_success:
            # Success - update session state
            st.session_state.config_modified = False
            st.success("✅ Configuración guardada y verificada correctamente")

            # Log successful save
            log_configuration_change(
                "save", "success", "Configuración guardada exitosamente"
            )

            # Show success metrics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Estado", "✅ Guardado")
            with col2:
                st.metric("Validación", "✅ Exitosa")
            with col3:
                st.metric("Verificación", "✅ Completa")

            st.balloons()
            st.rerun()

        else:
            # Verification failed - attempt rollback
            st.error("❌ Error en la verificación post-guardado")

            if backup_path:
                st.warning("🔄 Ejecutando rollback automático...")
                rollback_success = handle_validation_failure_rollback(backup_path)

                if rollback_success:
                    st.success(
                        "✅ Rollback completado - configuración restaurada al estado anterior"
                    )
                    log_configuration_change(
                        "rollback",
                        "success",
                        "Rollback automático después de fallo de verificación",
                    )
                else:
                    st.error(
                        "❌ Error crítico durante rollback - configuración puede estar corrupta"
                    )
                    st.error("🚨 Revisa manualmente el archivo config.yaml")
                    log_configuration_change(
                        "rollback", "error", "Fallo de rollback automático"
                    )
            else:
                st.error("❌ No hay backup disponible para rollback")
                log_configuration_change(
                    "save", "error", "Error de verificación sin backup disponible"
                )

    except Exception as e:
        st.error(f"❌ Error crítico guardando configuración: {e}")
        logger.error(f"Critical error saving configuration: {e}")

        # Log critical error
        log_configuration_change("save", "error", f"Error crítico: {e}")

        # Log the error
        log_configuration_change("save", "error", f"Error crítico: {e}")

        # Attempt rollback
        attempt_configuration_rollback()


def cancel_changes() -> None:
    """Cancel configuration changes and reload from file."""
    try:
        st.session_state.current_config = st.session_state.config_handler.read_config()
        st.session_state.config_modified = False
        st.success("✅ Cambios cancelados")
        st.rerun()
    except Exception as e:
        st.error(f"❌ Error cancelando cambios: {e}")


def reload_configuration() -> None:
    """Reload configuration from file, discarding any unsaved changes."""
    try:
        st.session_state.current_config = st.session_state.config_handler.read_config()
        st.session_state.config_modified = False
        st.success("✅ Configuración recargada desde archivo")
        st.rerun()
    except Exception as e:
        st.error(f"❌ Error recargando configuración: {e}")


def test_configuration_loading(config_data: dict[str, Any]) -> bool:
    """Test if configuration can be loaded by the system."""
    try:
        # Import the config models to test loading
        from src.traffic_system.core.config_models import TrafficSystemConfig

        # Try to create a config object
        test_config = TrafficSystemConfig(**config_data)

        # Basic sanity checks
        if not test_config.services:
            st.warning("⚠️ No hay configuración de servicios")
            return False

        # Check required sections
        required_sections = ["services", "deteccion", "decision", "sumo", "reporte"]
        missing_sections = [
            section
            for section in required_sections
            if not getattr(test_config, section, None)
        ]

        if missing_sections:
            st.warning(f"⚠️ Secciones faltantes: {', '.join(missing_sections)}")
            # Don't fail, just warn

        return True

    except Exception as e:
        st.error(f"❌ Error en prueba de carga: {e}")
        logger.error(f"Error testing configuration loading: {e}")
        return False


def verify_saved_configuration() -> bool:
    """Verify that the saved configuration is valid."""
    try:
        # Reload from file to verify it was saved correctly
        reloaded_config = st.session_state.config_handler.read_config()

        if not reloaded_config:
            st.error("❌ No se pudo recargar la configuración guardada")
            return False

        # Validate the reloaded configuration using new validation system
        is_valid, errors = st.session_state.config_handler.test_load_config(
            reloaded_config
        )

        if not is_valid:
            st.error("❌ La configuración guardada no es válida")
            for error in errors[:3]:
                st.error(f"• {error}")
            return False

        return True

    except Exception as e:
        st.error(f"❌ Error verificando configuración guardada: {e}")
        logger.error(f"Error verifying saved configuration: {e}")
        return False


def attempt_configuration_rollback() -> None:
    """Attempt to rollback configuration to last known good state."""
    try:
        st.warning("🔄 Intentando rollback automático...")

        # Try to find the most recent backup
        backups = st.session_state.config_handler.list_backups()

        if not backups:
            st.error("❌ No hay backups disponibles para rollback")
            return

        # Get the most recent backup
        latest_backup = max(backups, key=lambda x: x["created"])

        # Attempt restore
        success = st.session_state.config_handler.restore_backup(
            latest_backup["filename"]
        )

        if success:
            st.success(
                f"✅ Rollback exitoso usando backup: {latest_backup['filename']}"
            )
            st.session_state.current_config = (
                st.session_state.config_handler.read_config()
            )
            st.session_state.config_modified = False
            log_configuration_change(
                "rollback", "success", f"Rollback usando {latest_backup['filename']}"
            )
        else:
            st.error("❌ Rollback falló")
            log_configuration_change("rollback", "error", "Rollback falló")

    except Exception as e:
        st.error(f"❌ Error durante rollback: {e}")
        logger.error(f"Error during rollback: {e}")
        log_configuration_change("rollback", "error", f"Error durante rollback: {e}")


def log_configuration_change(operation: str, status: str, message: str) -> None:
    """Log configuration changes for audit trail."""
    try:
        if "config_change_log" not in st.session_state:
            st.session_state.config_change_log = []

        log_entry = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "operation": operation,
            "status": status,
            "message": message,
            "user": "frontend_user",  # Could be enhanced with actual user info
        }

        st.session_state.config_change_log.append(log_entry)

        # Keep only last 100 entries
        if len(st.session_state.config_change_log) > 100:
            st.session_state.config_change_log = st.session_state.config_change_log[
                -100:
            ]

    except Exception as e:
        logger.error(f"Error logging configuration change: {e}")


def validate_field_value(field_path: str, value: Any) -> tuple[bool, str | None]:
    """
    Validate a single field value with enhanced Pydantic integration.

    Args:
        field_path: Path to the field (e.g., 'services.port')
        value: Value to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        # Use the validator to check the field
        is_valid, error = st.session_state.validator.validate_field(
            field_path, value, st.session_state.current_config
        )

        # If basic validation passes, try Pydantic validation for more detailed feedback
        if is_valid:
            # Create a test configuration with the new value
            test_config = st.session_state.current_config.copy()
            _set_nested_value(test_config, field_path, value)

            # Test with Pydantic
            pydantic_valid, pydantic_errors, _ = (
                st.session_state.config_handler.validate_config_with_pydantic(
                    test_config
                )
            )

            if not pydantic_valid:
                # Find errors related to this field
                field_errors = [err for err in pydantic_errors if field_path in err]
                if field_errors:
                    return False, field_errors[0]

        return is_valid, error

    except Exception as e:
        logger.error(f"Error validating field {field_path}: {e}")
        return False, f"Error de validación: {e}"


def _set_nested_value(config: dict, field_path: str, value: Any) -> None:
    """Set a nested value in configuration dictionary."""
    keys = field_path.split(".")
    current = config

    for key in keys[:-1]:
        if key not in current:
            current[key] = {}
        current = current[key]

    current[keys[-1]] = value


def validate_config_before_save(
    config: dict[str, Any]
) -> tuple[bool, list[str], str | None]:
    """
    Comprehensive validation before saving configuration.

    Args:
        config: Configuration to validate

    Returns:
        Tuple of (is_valid, errors, backup_path_if_created)
    """
    try:
        # Step 1: Create backup before validation
        backup_path = None
        try:
            backup_path = st.session_state.config_handler.create_backup(
                "pre_save_validation"
            )
            logger.info(f"📦 Backup de seguridad creado: {backup_path}")
        except Exception as e:
            logger.warning(f"⚠️ No se pudo crear backup de seguridad: {e}")

        # Step 2: Test load configuration with Pydantic
        is_valid, errors, validated_model = (
            st.session_state.config_handler.validate_config_with_pydantic(config)
        )

        if not is_valid:
            return False, errors, str(backup_path) if backup_path else None

        # Step 3: Test save and reload cycle
        try:
            # Save to temporary file first
            import tempfile

            import yaml

            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".yaml", delete=False
            ) as temp_file:
                yaml.dump(
                    config, temp_file, default_flow_style=False, allow_unicode=True
                )
                temp_path = temp_file.name

            # Try to reload from temp file
            with open(temp_path, encoding="utf-8") as temp_file:
                reloaded_config = yaml.safe_load(temp_file)

            # Validate reloaded config
            reload_valid, reload_errors, _ = (
                st.session_state.config_handler.validate_config_with_pydantic(
                    reloaded_config
                )
            )

            # Clean up temp file
            import os

            os.unlink(temp_path)

            if not reload_valid:
                errors.extend(
                    [f"Error en ciclo save/reload: {err}" for err in reload_errors]
                )
                return False, errors, str(backup_path) if backup_path else None

        except Exception as e:
            errors.append(f"Error en test de save/reload: {e}")
            return False, errors, str(backup_path) if backup_path else None

        # Step 4: All validations passed
        return True, [], str(backup_path) if backup_path else None

    except Exception as e:
        logger.error(f"Error en validación pre-guardado: {e}")
        return False, [f"Error crítico en validación: {e}"], None


def handle_validation_failure_rollback(backup_path: str | None) -> bool:
    """
    Handle rollback in case of validation failure.

    Args:
        backup_path: Path to backup file for rollback

    Returns:
        True if rollback successful, False otherwise
    """
    if not backup_path:
        logger.warning("⚠️ No hay backup disponible para rollback")
        return False

    try:
        # Restore from backup
        success = st.session_state.config_handler.restore_backup(backup_path)

        if success:
            # Update session state
            st.session_state.current_config = (
                st.session_state.config_handler.read_config()
            )
            st.session_state.config_modified = False
            logger.info("✅ Rollback exitoso desde backup")
            return True
        else:
            logger.error("❌ Error durante rollback")
            return False

    except Exception as e:
        logger.error(f"❌ Error crítico durante rollback: {e}")
        return False


def show_validation_summary() -> None:
    """Show a comprehensive summary of current validation status with enhanced feedback."""
    st.subheader("🔍 Estado de Validación")

    try:
        # Get validation results
        is_valid, errors, warnings = st.session_state.validator.validate_full_config(
            st.session_state.current_config
        )

        # Get Pydantic validation for more detailed feedback
        pydantic_valid, pydantic_errors, validated_model = (
            st.session_state.config_handler.validate_config_with_pydantic(
                st.session_state.current_config
            )
        )

        # Overall status with enhanced display
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            if is_valid and pydantic_valid:
                st.metric("Estado General", "✅ Válida", delta="Sin errores")
            else:
                total_errors = len(errors) + len(pydantic_errors)
                st.metric(
                    "Estado General", "❌ Inválida", delta=f"{total_errors} errores"
                )

        with col2:
            st.metric("Errores Básicos", len(errors))

        with col3:
            st.metric("Errores Pydantic", len(pydantic_errors))

        with col4:
            st.metric("Advertencias", len(warnings))

        # Detailed validation results
        if not is_valid or not pydantic_valid or warnings:
            st.markdown("---")

            # Basic validation errors
            if errors:
                with st.expander("❌ Errores de Validación Básica", expanded=True):
                    for i, error in enumerate(errors, 1):
                        st.error(f"{i}. {error}")

            # Pydantic validation errors (more detailed)
            if pydantic_errors:
                with st.expander("🔍 Errores de Validación Pydantic", expanded=True):
                    for i, error in enumerate(pydantic_errors, 1):
                        st.error(f"{i}. {error}")

                        # Try to provide helpful suggestions
                        suggestion = _get_validation_suggestion(error)
                        if suggestion:
                            st.info(f"💡 Sugerencia: {suggestion}")

            # Warnings
            if warnings:
                with st.expander("⚠️ Advertencias", expanded=False):
                    for i, warning in enumerate(warnings, 1):
                        st.warning(f"{i}. {warning}")

        # Validation health check
        if is_valid and pydantic_valid:
            st.success("🎉 **Configuración completamente válida**")
            st.info("✅ Lista para guardar sin problemas")

            # Show configuration summary
            with st.expander("📊 Resumen de Configuración", expanded=False):
                _show_config_summary(st.session_state.current_config)
        else:
            st.error("🚨 **Configuración requiere correcciones**")
            st.warning("⚠️ Corrige los errores antes de guardar para evitar problemas")

    except Exception as e:
        st.error(f"❌ Error obteniendo estado de validación: {e}")
        logger.error(f"Error getting validation summary: {e}")


def _get_validation_suggestion(error_message: str) -> str | None:
    """Get helpful suggestion based on validation error."""
    error_lower = error_message.lower()

    if "port" in error_lower:
        return "Los puertos deben estar entre 1024 y 65535"
    elif "path" in error_lower or "ruta" in error_lower:
        return "Verifica que la ruta sea válida y accesible"
    elif "boolean" in error_lower or "bool" in error_lower:
        return "Este campo debe ser verdadero (true) o falso (false)"
    elif "integer" in error_lower or "int" in error_lower:
        return "Este campo debe ser un número entero"
    elif "float" in error_lower:
        return "Este campo debe ser un número decimal"
    elif "required" in error_lower or "missing" in error_lower:
        return "Este campo es obligatorio y no puede estar vacío"
    elif "list" in error_lower or "array" in error_lower:
        return "Este campo debe ser una lista de valores"
    elif "dict" in error_lower or "object" in error_lower:
        return "Este campo debe ser un objeto con propiedades"
    else:
        return None


def _show_config_summary(config: dict[str, Any]) -> None:
    """Show a summary of configuration sections."""
    sections = ["services", "deteccion", "decision", "sumo", "reporte"]

    for section in sections:
        if section in config:
            section_data = config[section]
            if isinstance(section_data, dict):
                field_count = len(section_data)
                st.write(f"• **{section}**: {field_count} campos configurados")
            else:
                st.write(f"• **{section}**: configurado")
        else:
            st.write(f"• **{section}**: ❌ faltante")


def show_real_time_field_validation(field_path: str, value: Any) -> None:
    """
    Show real-time validation feedback for a specific field.

    Args:
        field_path: Path to the field being validated
        value: Current value of the field
    """
    try:
        is_valid, error_message = validate_field_value(field_path, value)

        if is_valid:
            st.success("✅ Campo válido")
        else:
            st.error(f"❌ {error_message}")

            # Show suggestion if available
            suggestion = _get_validation_suggestion(error_message or "")
            if suggestion:
                st.info(f"💡 {suggestion}")

    except Exception as e:
        st.error(f"❌ Error validando campo: {e}")
        logger.error(f"Error in real-time field validation: {e}")


def show_configuration_audit_log() -> None:
    """Show configuration change audit log."""
    st.subheader("📋 Log de Cambios de Configuración")

    if (
        "config_change_log" not in st.session_state
        or not st.session_state.config_change_log
    ):
        st.info("ℹ️ No hay cambios registrados")
        return

    # Show recent changes
    import pandas as pd

    log_df = pd.DataFrame(st.session_state.config_change_log)

    # Display with color coding
    for _, entry in log_df.tail(20).iterrows():
        if entry["status"] == "success":
            st.success(
                f"✅ {entry['timestamp']} - {entry['operation']}: {entry['message']}"
            )
        elif entry["status"] == "error":
            st.error(
                f"❌ {entry['timestamp']} - {entry['operation']}: {entry['message']}"
            )
        else:
            st.info(
                f"ℹ️ {entry['timestamp']} - {entry['operation']}: {entry['message']}"
            )

    # Clear log button
    if st.button("🧹 Limpiar Log"):
        st.session_state.config_change_log = []
        st.success("✅ Log limpiado")
        st.rerun()


def render_basic_config_editor() -> None:
    """Render basic configuration editor as fallback."""
    # Configuration sections
    config_sections = {
        "🌐 Configuración Base": ["base_url", "base_ip"],
        "🔌 Servicios": ["services"],
        "👁️ Detección": ["deteccion"],
        "🧠 Decisión/DQN": ["decision"],
        "🚗 Simulación SUMO": ["sumo"],
        "📊 Reportes": ["reporte"],
    }

    # Configuration sections
    for section_title, section_keys in config_sections.items():
        with st.expander(section_title, expanded=False):
            render_config_section(section_keys)


def render_services_page() -> None:
    """Render the services management page."""
    st.title("🔧 Gestión de Servicios")

    # Import the advanced service dashboard
    from src.traffic_system.frontend.components.service_dashboard import (
        render_advanced_service_dashboard,
    )

    try:
        # Use the advanced service dashboard
        render_advanced_service_dashboard(st.session_state.service_manager)

    except Exception as e:
        st.error(f"❌ Error en el dashboard de servicios: {e}")
        logger.error(f"Error in service dashboard: {e}")

        # Fallback to basic service interface
        st.warning("⚠️ Usando interfaz básica de servicios como respaldo")
        render_basic_services_interface()


def render_basic_services_interface() -> None:
    """Render basic services interface as fallback."""
    # Auto-refresh toggle
    auto_refresh = st.checkbox("🔄 Actualización automática", value=False)

    if auto_refresh:
        # Auto-refresh every 5 seconds
        import time

        time.sleep(5)
        st.rerun()

    # Manual refresh button
    if st.button("🔄 Actualizar Estado"):
        st.session_state.service_manager.clear_cache()
        st.rerun()

    st.markdown("---")

    # Service status table
    try:
        services_status = st.session_state.service_manager.get_all_services_status()

        for service_name, status in services_status.items():
            with st.container():
                col1, col2, col3, col4 = st.columns([2, 1, 2, 1])

                with col1:
                    status_icon = "🟢" if status.is_running else "🔴"
                    st.write(f"{status_icon} **{service_name.title()}**")
                    if status.is_running and status.process_id:
                        st.caption(
                            f"PID: {status.process_id} | Runtime: {status.runtime_seconds}s"
                        )

                with col2:
                    if status.is_running:
                        st.success("Activo")
                    else:
                        st.error("Inactivo")

                with col3:
                    # Control buttons
                    button_col1, button_col2, button_col3 = st.columns(3)

                    with button_col1:
                        if st.button(
                            "▶️",
                            key=f"start_{service_name}",
                            disabled=status.is_running,
                            help="Iniciar servicio",
                        ):
                            start_service_action(service_name)

                    with button_col2:
                        if st.button(
                            "⏹️",
                            key=f"stop_{service_name}",
                            disabled=not status.is_running,
                            help="Detener servicio",
                        ):
                            stop_service_action(service_name)

                    with button_col3:
                        if st.button(
                            "🔄",
                            key=f"restart_{service_name}",
                            help="Reiniciar servicio",
                        ):
                            restart_service_action(service_name)

                with col4:
                    if status.is_running:
                        st.metric("CPU", f"{status.cpu_percent:.1f}%")
                        st.metric("RAM", f"{status.memory_mb:.0f}MB")

                st.markdown("---")

    except Exception as e:
        st.error(f"❌ Error obteniendo estado de servicios: {e}")


def start_service_action(service_name: str) -> None:
    """Start a service and show result."""
    with st.spinner(f"Iniciando {service_name}..."):
        success, message = st.session_state.service_manager.start_service(service_name)
        if success:
            st.success(f"✅ {message}")
        else:
            st.error(f"❌ {message}")
        st.rerun()


def stop_service_action(service_name: str) -> None:
    """Stop a service and show result."""
    with st.spinner(f"Deteniendo {service_name}..."):
        success, message = st.session_state.service_manager.stop_service(service_name)
        if success:
            st.success(f"✅ {message}")
        else:
            st.error(f"❌ {message}")
        st.rerun()


def restart_service_action(service_name: str) -> None:
    """Restart a service and show result."""
    with st.spinner(f"Reiniciando {service_name}..."):
        success, message = st.session_state.service_manager.restart_service(
            service_name
        )
        if success:
            st.success(f"✅ {message}")
        else:
            st.error(f"❌ {message}")
        st.rerun()


def render_backups_page() -> None:
    """Render the backups management page."""
    st.title("📦 Gestión de Backups")

    # Import the advanced backup manager
    from src.traffic_system.frontend.components.backup_manager import (
        render_advanced_backup_manager,
    )

    try:
        # Use the advanced backup management interface
        render_advanced_backup_manager(st.session_state.config_handler)

    except Exception as e:
        st.error(f"❌ Error en el gestor de backups: {e}")
        logger.error(f"Error in backup manager: {e}")

        # Fallback to basic backup interface
        st.warning("⚠️ Usando interfaz básica de backups como respaldo")
        render_basic_backups_interface()


def create_backup_action(custom_name: str | None) -> None:
    """Create a backup with optional custom name."""
    try:
        backup_path = st.session_state.config_handler.create_backup(custom_name)
        st.success(f"✅ Backup creado: {backup_path.name}")
        st.rerun()
    except Exception as e:
        st.error(f"❌ Error creando backup: {e}")


def restore_backup_action(backup_path: str) -> None:
    """Restore a backup after confirmation."""
    if st.button("⚠️ Confirmar Restauración", key=f"confirm_restore_{backup_path}"):
        try:
            success = st.session_state.config_handler.restore_backup(backup_path)
            if success:
                # Reload configuration
                st.session_state.current_config = (
                    st.session_state.config_handler.read_config()
                )
                st.session_state.config_modified = False
                st.success("✅ Backup restaurado correctamente")
                st.rerun()
            else:
                st.error("❌ Error restaurando backup")
        except Exception as e:
            st.error(f"❌ Error restaurando backup: {e}")


def render_info_page() -> None:
    """Render the information/about page."""
    st.title("ℹ️ Información del Sistema")

    st.markdown(
        """
    ## 🚦 Sistema de Semáforos Inteligentes

    **Versión**: 1.0.0
    **Autor**: Facundo Guarnier
    **Proyecto**: Tesis de Ingeniería en Informática

    ### 📋 Descripción
    Sistema inteligente de control de tráfico que utiliza:
    - **YOLOv8** para detección de vehículos
    - **SUMO** para simulación de tráfico
    - **DQN** (Deep Q-Network) para toma de decisiones
    - **Streamlit** para interfaz de configuración

    ### 🔧 Servicios del Sistema
    - **Simulation Provider**: Gestiona la simulación SUMO
    - **Decision Agent**: Ejecuta el agente DQN
    - **Detection Provider**: Procesa detección con YOLOv8
    - **Reporting Service**: Genera reportes y análisis

    ### 📚 Documentación
    Para más información, consulta la documentación del proyecto.
    """
    )

    # System information
    st.subheader("💻 Información del Sistema")

    try:
        import platform
        import sys

        col1, col2 = st.columns(2)

        with col1:
            st.write(f"**SO**: {platform.system()} {platform.release()}")
            st.write(f"**Python**: {sys.version.split()[0]}")
            st.write(f"**Streamlit**: {st.__version__}")

        with col2:
            # System resources
            resources = st.session_state.service_manager.get_system_resources()
            st.write(f"**CPU**: {resources['cpu_percent']:.1f}%")
            st.write(f"**Memoria**: {resources['memory_percent']:.1f}%")
            st.write(f"**Disco**: {resources['disk_percent']:.1f}%")

    except Exception as e:
        st.error(f"❌ Error obteniendo información del sistema: {e}")


def handle_page_routing(page: str) -> None:
    """
    Route to appropriate page component.

    Args:
        page: Selected page name
    """
    try:
        if page == "dashboard":
            render_dashboard()
        elif page == "config":
            render_config_page()
        elif page == "services":
            render_services_page()
        elif page == "backups":
            render_backups_page()
        elif page == "info":
            render_info_page()
        else:
            st.error(f"❌ Página desconocida: {page}")

    except Exception as e:
        st.error(f"❌ Error renderizando página {page}: {e}")
        logger.error(f"Error rendering page {page}: {e}")
        st.code(traceback.format_exc())


def main() -> None:
    """Main Streamlit application entry point."""
    # Configure page
    st.set_page_config(
        page_title="Traffic System Config",
        page_icon="🚦",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Initialize session state
    initialize_session_state()

    # Render sidebar and get selected page
    selected_page = render_sidebar()

    # Route to appropriate page
    handle_page_routing(selected_page)


if __name__ == "__main__":
    main()


def render_basic_backups_interface() -> None:
    """Render basic backup interface as fallback."""
    # Create backup section
    st.subheader("Crear Backup")
    col1, col2 = st.columns([3, 1])

    with col1:
        backup_name = st.text_input(
            "Nombre del backup (opcional)", placeholder="backup_manual"
        )

    with col2:
        if st.button("📦 Crear Backup", use_container_width=True):
            create_backup_action(backup_name if backup_name else None)

    st.markdown("---")

    # List existing backups
    st.subheader("Backups Disponibles")

    try:
        backups = st.session_state.config_handler.list_backups()

        if not backups:
            st.info("📭 No hay backups disponibles")
        else:
            for backup in backups:
                with st.container():
                    col1, col2, col3, col4 = st.columns([3, 2, 2, 1])

                    with col1:
                        st.write(f"📄 **{backup['filename']}**")

                    with col2:
                        st.write(f"📅 {backup['created'].strftime('%Y-%m-%d %H:%M')}")

                    with col3:
                        st.write(f"💾 {backup['size'] / 1024:.1f} KB")

                    with col4:
                        if st.button(
                            "🔄",
                            key=f"restore_{backup['filename']}",
                            help="Restaurar backup",
                        ):
                            restore_backup_action(backup["path"])

                    st.markdown("---")

    except Exception as e:
        st.error(f"❌ Error listando backups: {e}")


def create_validation_alert_system() -> None:
    """Create a persistent validation alert system in the sidebar."""
    with st.sidebar:
        st.markdown("---")
        st.subheader("🔍 Estado de Validación")

        try:
            # Quick validation check
            is_valid, errors, warnings = (
                st.session_state.validator.validate_full_config(
                    st.session_state.current_config
                )
            )

            # Pydantic validation
            pydantic_valid, pydantic_errors, _ = (
                st.session_state.config_handler.validate_config_with_pydantic(
                    st.session_state.current_config
                )
            )

            total_errors = len(errors) + len(pydantic_errors)
            overall_valid = is_valid and pydantic_valid

            # Status indicator
            if overall_valid:
                st.success("✅ Configuración Válida")
                st.info("Lista para guardar")
            else:
                st.error(f"❌ {total_errors} Errores")
                st.warning("Requiere correcciones")

                # Quick error preview
                if total_errors > 0:
                    with st.expander("Ver errores", expanded=False):
                        all_errors = errors + pydantic_errors
                        for error in all_errors[:3]:  # Show first 3 errors
                            st.error(f"• {error}")

                        if total_errors > 3:
                            st.info(f"... y {total_errors - 3} errores más")

            # Warnings
            if warnings:
                st.warning(f"⚠️ {len(warnings)} Advertencias")

            # Auto-refresh toggle
            auto_refresh = st.checkbox(
                "🔄 Auto-validación",
                value=st.session_state.get("auto_validation", True),
                help="Validar automáticamente al cambiar configuración",
            )
            st.session_state.auto_validation = auto_refresh

        except Exception as e:
            st.error("❌ Error en validación")
            logger.error(f"Error in validation alert system: {e}")


def show_validation_progress_indicator(
    current_step: str, total_steps: int, current_step_num: int
) -> None:
    """
    Show validation progress indicator during save process.

    Args:
        current_step: Description of current step
        total_steps: Total number of steps
        current_step_num: Current step number
    """
    progress = current_step_num / total_steps

    st.progress(progress)
    st.info(f"🔄 Paso {current_step_num}/{total_steps}: {current_step}")

    # Show progress bar with steps
    steps = [
        "Validación inicial",
        "Backup de seguridad",
        "Test de configuración",
        "Guardado",
        "Verificación",
    ]

    cols = st.columns(total_steps)
    for i, step in enumerate(steps[:total_steps]):
        with cols[i]:
            if i < current_step_num - 1:
                st.success(f"✅ {step}")
            elif i == current_step_num - 1:
                st.info(f"🔄 {step}")
            else:
                st.write(f"⏳ {step}")


def create_validation_help_panel() -> None:
    """Create a help panel with validation tips and common fixes."""
    with st.expander("❓ Ayuda de Validación", expanded=False):
        st.markdown(
            """
        ### 🔍 Guía de Validación

        **Errores Comunes y Soluciones:**

        **🔌 Puertos:**
        - Deben estar entre 1024 y 65535
        - No pueden estar duplicados
        - Ejemplo: `5000`, `5001`, `5002`

        **📁 Rutas:**
        - Deben ser rutas válidas del sistema
        - Usar barras `/` o barras invertidas `\\` según el SO
        - Ejemplo: `C:\\sumo` o `/usr/share/sumo`

        **✅ Booleanos:**
        - Solo `true` o `false`
        - No usar `1`, `0`, `yes`, `no`

        **🔢 Números:**
        - Enteros: `100`, `256`, `1024`
        - Decimales: `0.001`, `0.95`, `1.5`

        **📋 Listas:**
        - Formato: `[item1, item2, item3]`
        - Todos los elementos del mismo tipo

        **💡 Consejos:**
        - Usa la validación en tiempo real
        - Crea backups antes de cambios importantes
        - Revisa los mensajes de error específicos
        - Usa los valores por defecto como referencia
        """
        )

        # Quick validation button
        if st.button("🔍 Validar Ahora", use_container_width=True):
            show_validation_summary()
