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
from src.traffic_system.frontend.utils.validators import ConfigValidator

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
        st.session_state.validator = ConfigValidator()

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
    Render a configuration field with appropriate widget.

    Args:
        key: Configuration key name
        value: Current value
        path: Full path to the field
    """
    new_value: Any = None

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
                    type(value[0])(item.strip()) for item in new_value if item.strip()
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
    """Save the current configuration to file."""
    try:
        # Validate configuration
        is_valid, errors, _ = st.session_state.validator.validate_full_config(
            st.session_state.current_config
        )

        if not is_valid:
            st.error("❌ No se puede guardar: configuración inválida")
            for error in errors[:5]:  # Show first 5 errors
                st.error(f"• {error}")
            return

        # Save to file
        success = st.session_state.config_handler.write_config(
            st.session_state.current_config
        )

        if success:
            st.session_state.config_modified = False
            st.success("✅ Configuración guardada correctamente")
            st.rerun()
        else:
            st.error("❌ Error guardando configuración")

    except Exception as e:
        st.error(f"❌ Error guardando configuración: {e}")
        logger.error(f"Error saving configuration: {e}")


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
