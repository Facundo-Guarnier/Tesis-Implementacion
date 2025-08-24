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
    """Render the configuration editing page."""
    st.title("⚙️ Configuración del Sistema")

    # Import the advanced config editor
    from src.traffic_system.frontend.components.config_editor import (
        render_advanced_config_editor,
    )

    # Save/Cancel buttons at top
    col1, col2, col3, col4 = st.columns([1, 1, 1, 3])

    with col1:
        if st.button(
            "💾 Guardar",
            use_container_width=True,
            disabled=not st.session_state.config_modified,
        ):
            save_configuration()

    with col2:
        if st.button(
            "❌ Cancelar",
            use_container_width=True,
            disabled=not st.session_state.config_modified,
        ):
            cancel_changes()

    with col3:
        if st.button("🔄 Recargar", use_container_width=True):
            reload_configuration()

    # Status indicator
    if st.session_state.config_modified:
        st.warning("⚠️ Hay cambios sin guardar en la configuración")
    else:
        st.success("✅ Configuración sincronizada")

    # Validation summary
    with st.expander("🔍 Estado de Validación", expanded=False):
        show_validation_summary()

    # Configuration audit log
    with st.expander("📋 Log de Cambios", expanded=False):
        show_configuration_audit_log()

    st.markdown("---")

    # Advanced configuration editor
    try:
        new_config, has_changes = render_advanced_config_editor(
            st.session_state.current_config, st.session_state.validator
        )

        # Update session state if there are changes
        if has_changes:
            st.session_state.current_config = new_config
            st.session_state.config_modified = True

    except Exception as e:
        st.error(f"❌ Error renderizando editor de configuración: {e}")
        logger.error(f"Error in config editor: {e}")

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
    """Save the current configuration to file with comprehensive validation."""
    try:
        # Step 1: Pre-save validation using new validation system
        st.info("🔍 Validando configuración...")

        # Use the validation dialog to check if user wants to proceed
        if st.session_state.validation_ui is not None:
            if not st.session_state.validation_ui.validate_before_save_dialog(
                st.session_state.current_config
            ):
                return  # User cancelled save due to validation errors
        else:
            st.warning(
                "⚠️ Sistema de validación no disponible, guardando sin validación avanzada..."
            )

            return

        # Step 2: Create backup before saving
        st.info("📦 Creando backup de seguridad...")
        try:
            backup_path = st.session_state.config_handler.create_backup("pre_save")
            st.success(f"✅ Backup creado: {backup_path.name}")
        except Exception as backup_error:
            st.warning(f"⚠️ No se pudo crear backup: {backup_error}")
            # Continue with save anyway

        # Step 3: Test configuration loading
        st.info("🧪 Probando configuración...")
        test_success = test_configuration_loading(st.session_state.current_config)

        if not test_success:
            st.error("❌ La configuración no pasa las pruebas de carga")
            return

        # Step 2: Save to file with validation
        st.info("💾 Guardando configuración...")
        success, save_errors = (
            st.session_state.config_handler.validate_and_write_config(
                st.session_state.current_config
            )
        )

        if not success and save_errors:
            st.error("❌ Error durante el guardado:")
            for error in save_errors:
                st.error(f"• {error}")
            return

        if success:
            # Step 5: Verify saved configuration
            st.info("✅ Verificando configuración guardada...")
            verification_success = verify_saved_configuration()

            if verification_success:
                st.session_state.config_modified = False
                st.success("✅ Configuración guardada y verificada correctamente")
                st.balloons()

                # Log the save operation
                log_configuration_change(
                    "save", "success", "Configuración guardada exitosamente"
                )

                st.rerun()
            else:
                st.error("❌ Error en la verificación post-guardado")
                # Attempt rollback
                attempt_configuration_rollback()
        else:
            st.error("❌ Error guardando configuración")
            log_configuration_change("save", "error", "Error durante el guardado")

    except Exception as e:
        st.error(f"❌ Error crítico guardando configuración: {e}")
        logger.error(f"Critical error saving configuration: {e}")

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
    Validate a single field value.

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

        return is_valid, error

    except Exception as e:
        logger.error(f"Error validating field {field_path}: {e}")
        return False, f"Error de validación: {e}"


def show_validation_summary() -> None:
    """Show a summary of current validation status."""
    st.subheader("🔍 Estado de Validación")

    try:
        is_valid, errors, warnings = st.session_state.validator.validate_full_config(
            st.session_state.current_config
        )

        # Overall status
        if is_valid:
            st.success("✅ Configuración válida")
        else:
            st.error(f"❌ Configuración inválida ({len(errors)} errores)")

        # Warnings
        if warnings:
            st.warning(f"⚠️ {len(warnings)} advertencias encontradas")
            with st.expander("Ver advertencias", expanded=False):
                for warning in warnings:
                    st.warning(f"• {warning}")

        # Errors
        if errors:
            st.error(f"❌ {len(errors)} errores encontrados")
            with st.expander("Ver errores", expanded=True):
                for error in errors:
                    st.error(f"• {error}")

        # Validation statistics
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Errores", len(errors))

        with col2:
            st.metric("Advertencias", len(warnings))

        with col3:
            status = "Válida" if is_valid else "Inválida"
            st.metric("Estado", status)

    except Exception as e:
        st.error(f"❌ Error obteniendo estado de validación: {e}")
        logger.error(f"Error getting validation summary: {e}")


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
