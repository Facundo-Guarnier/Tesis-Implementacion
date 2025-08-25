"""
Frontend Simplificado para el Sistema de Tráfico

Aplicación Streamlit con 2 páginas: Configuración y Servicios.
Funcionalidad esencial sin sobre-ingeniería.
"""

import time
from typing import Any

import streamlit as st

from src.traffic_system.frontend.utils import (
    log_error,
    log_info,
)


def initialize_session_state() -> None:
    """Inicializar variables de estado de sesión de Streamlit."""
    # Flag para controlar inicialización única
    if "app_initialized" not in st.session_state:
        st.session_state.app_initialized = True

        # Inicialización que solo debe ocurrir una vez
        st.session_state.current_page = "services"
        st.session_state.config_modified = False
        st.session_state.current_config = {}
        st.session_state.config_manager = None
        st.session_state.service_controller = None
        st.session_state.validation_errors = {}

        # Log de inicialización única - solo una vez por sesión
        log_info("Frontend simplificado iniciado")

    # Asegurar que las variables existen (sin logs adicionales)
    if "current_page" not in st.session_state:
        st.session_state.current_page = "services"
    if "config_modified" not in st.session_state:
        st.session_state.config_modified = False
    if "current_config" not in st.session_state:
        st.session_state.current_config = {}
    if "config_manager" not in st.session_state:
        st.session_state.config_manager = None
    if "service_controller" not in st.session_state:
        st.session_state.service_controller = None
    if "validation_errors" not in st.session_state:
        st.session_state.validation_errors = {}


def render_navigation() -> str:
    """Renderizar navegación simple con 2 opciones."""
    st.sidebar.title("🚦 Sistema de Tráfico")
    st.sidebar.markdown("---")

    pages = {"🔧 Servicios": "services", "⚙️ Configuración": "config"}
    current_page: str = st.session_state.current_page

    for page_title, page_key in pages.items():
        if page_key == current_page:
            st.sidebar.button(
                f"▶ {page_title} ◀",
                key=f"nav_active_{page_key}",
                use_container_width=True,
                type="primary",
                disabled=True,
            )
        else:
            if st.sidebar.button(
                page_title, key=f"nav_{page_key}", use_container_width=True
            ):
                st.session_state.current_page = page_key
                st.rerun()

    return current_page


def render_services_page() -> None:
    """Renderizar página de control de servicios."""
    st.title("🔧 Control de Servicios")

    # Inicializar ServiceController (solo una vez)
    if st.session_state.service_controller is None:
        from src.traffic_system.frontend.service_controller import ServiceController

        st.session_state.service_controller = ServiceController()
        # Solo log si es la primera inicialización de la sesión
        if "service_controller_initialized" not in st.session_state:
            st.session_state.service_controller_initialized = True
            log_info("ServiceController inicializado")

    controller = st.session_state.service_controller

    try:
        summary = controller.get_services_summary()

        # Resumen general
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(
                "Servicios Activos",
                f"{summary['running_services']}/{summary['total_services']}",
            )
        with col2:
            if summary["all_running"]:
                st.success("✅ Todos activos")
            elif summary["all_stopped"]:
                st.error("❌ Todos detenidos")
            else:
                st.warning("⚠️ Algunos activos")
        with col3:
            if st.button("🔄 Actualizar"):
                st.rerun()

        st.markdown("---")

        # Controles masivos
        col1, col2 = st.columns(2)
        with col1:
            if st.button("▶️ Iniciar Todos", use_container_width=True):
                with st.spinner("Iniciando servicios..."):
                    results = controller.start_all_services()
                    for service, (success, message) in results.items():
                        if success:
                            st.success(
                                f"✅ {controller.get_service_display_name(service)}"
                            )
                        else:
                            st.error(
                                f"❌ {controller.get_service_display_name(service)}: {message}"
                            )
                st.rerun()

        with col2:
            if st.button("⏹️ Detener Todos", use_container_width=True):
                with st.spinner("Deteniendo servicios..."):
                    results = controller.stop_all_services()
                    for service, (success, message) in results.items():
                        if success:
                            st.success(
                                f"✅ {controller.get_service_display_name(service)}"
                            )
                        else:
                            st.error(
                                f"❌ {controller.get_service_display_name(service)}: {message}"
                            )
                st.rerun()

        st.markdown("---")

        # Servicios individuales
        for service_name, service_info in summary["services"].items():
            display_name = service_info["display_name"]
            is_running = service_info["is_running"]

            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                if is_running:
                    st.write(f"🟢 **{display_name}**")
                    if service_info.get("pid"):
                        st.caption(f"PID: {service_info['pid']}")
                else:
                    st.write(f"🔴 **{display_name}**")
                    st.caption("Detenido")

            with col2:
                if not is_running:
                    if st.button("▶️ Iniciar", key=f"start_{service_name}"):
                        with st.spinner(f"Iniciando {display_name}..."):
                            success, message = controller.start_service(service_name)
                            if success:
                                st.success(f"✅ {message}")
                            else:
                                st.error(f"❌ {message}")
                        time.sleep(1)
                        st.rerun()

            with col3:
                if is_running:
                    if st.button("⏹️ Detener", key=f"stop_{service_name}"):
                        with st.spinner(f"Deteniendo {display_name}..."):
                            success, message = controller.stop_service_graceful(
                                service_name
                            )
                            if success:
                                st.success(f"✅ {message}")
                            else:
                                st.error(f"❌ {message}")
                        time.sleep(1)
                        st.rerun()

            st.markdown("---")

    except Exception as e:
        st.error(f"❌ Error: {e}")
        log_error(f"Error en servicios: {e}")


def render_config_page() -> None:
    """Renderizar página de configuración."""
    st.title("⚙️ Configuración del Sistema")

    # Inicializar ConfigManager (solo una vez)
    if st.session_state.config_manager is None:
        from src.traffic_system.frontend.config_manager import ConfigManager

        st.session_state.config_manager = ConfigManager()
        config = st.session_state.config_manager.load_config()
        if config:
            st.session_state.current_config = config

        # Solo log si es la primera inicialización de la sesión
        if "config_manager_initialized" not in st.session_state:
            st.session_state.config_manager_initialized = True
            log_info("ConfigManager inicializado")

    manager = st.session_state.config_manager

    # Controles principales
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("🔄 Recargar", use_container_width=True):
            config = manager.load_config()
            if config:
                st.session_state.current_config = config
                st.session_state.config_modified = False
                st.success("✅ Recargado")
                st.rerun()

    with col2:
        can_save = st.session_state.config_modified
        if st.session_state.current_config:
            is_valid, errors = manager.validate_with_pydantic(
                st.session_state.current_config
            )
            button_text = (
                "💾 Guardar" if is_valid else f"⚠️ Guardar ({len(errors)} errores)"
            )

            if st.button(button_text, use_container_width=True, disabled=not can_save):
                success, save_errors = manager.save_config(
                    st.session_state.current_config
                )
                if success:
                    st.session_state.config_modified = False
                    st.success("✅ Guardado")
                    st.balloons()
                    st.rerun()
                else:
                    for error in save_errors:
                        st.error(f"❌ {error}")

    with col3:
        if st.button(
            "❌ Cancelar",
            use_container_width=True,
            disabled=not st.session_state.config_modified,
        ):
            config = manager.load_config()
            if config:
                st.session_state.current_config = config
                st.session_state.config_modified = False
                st.success("✅ Cancelado")
                st.rerun()

    # Estado
    if st.session_state.config_modified:
        st.warning("⚠️ Cambios sin guardar")
    else:
        st.success("✅ Sincronizado")

    # Validación
    if st.session_state.current_config:
        is_valid, errors = manager.validate_with_pydantic(
            st.session_state.current_config
        )
        if not is_valid:
            with st.expander(f"❌ Errores ({len(errors)})", expanded=True):
                for error in errors:
                    st.error(error)

    st.markdown("---")

    # Configuración simplificada
    if st.session_state.current_config:
        render_simple_config(manager, st.session_state.current_config)


def on_config_change(field_path: str) -> None:
    """Callback ejecutado cuando cambia un campo de configuración."""
    st.session_state.config_modified = True

    # Inicializar validation_errors si no existe
    if "validation_errors" not in st.session_state:
        st.session_state.validation_errors = {}

    # Validar el campo específico usando la nueva función
    try:
        if st.session_state.current_config:
            # Obtener el valor actual del campo desde session_state
            widget_key = f"config_{field_path.replace('.', '_')}"
            if widget_key in st.session_state:
                field_value = st.session_state[widget_key]

                # Validar campo individual
                is_valid, message = validate_field(
                    field_path, field_value, st.session_state.current_config
                )

                # Actualizar errores de validación por campo
                if is_valid:
                    # Remover error de este campo si existe
                    if field_path in st.session_state.validation_errors:
                        del st.session_state.validation_errors[field_path]
                else:
                    # Agregar error para este campo
                    st.session_state.validation_errors[field_path] = message

    except Exception as e:
        log_error(f"Error validando campo {field_path}: {e}")
        st.session_state.validation_errors[field_path] = (
            f"❌ Error de validación: {str(e)}"
        )

    # Log solo en modo debug para evitar spam
    # log_info(f"Campo modificado: {field_path}")


def render_simple_config(manager: Any, config: dict[str, Any]) -> None:
    """Renderizar configuración simplificada."""

    # Servicios (siempre visible)
    with st.expander("📡 Servicios", expanded=True):
        if "services" in config:
            services = config["services"]
            col1, col2, col3 = st.columns(3)

            with col1:
                st.number_input(
                    "Puerto Simulación",
                    min_value=1,
                    max_value=65535,
                    value=services.get("simulation_port", 5000),
                    key="config_services_simulation_port",
                    on_change=on_config_change,
                    args=("services.simulation_port",),
                )
                # Mostrar validación en tiempo real
                field_key = "services.simulation_port"
                if field_key in st.session_state.validation_errors:
                    st.error(st.session_state.validation_errors[field_key])

                # Actualizar valor en config si cambió
                if "config_services_simulation_port" in st.session_state:
                    services["simulation_port"] = (
                        st.session_state.config_services_simulation_port
                    )

            with col2:
                st.number_input(
                    "Puerto Detección",
                    min_value=1,
                    max_value=65535,
                    value=services.get("detection_port", 5000),
                    key="config_services_detection_port",
                    on_change=on_config_change,
                    args=("services.detection_port",),
                )
                # Mostrar validación en tiempo real
                field_key = "services.detection_port"
                if field_key in st.session_state.validation_errors:
                    st.error(st.session_state.validation_errors[field_key])

                # Actualizar valor en config si cambió
                if "config_services_detection_port" in st.session_state:
                    services["detection_port"] = (
                        st.session_state.config_services_detection_port
                    )

            with col3:
                st.number_input(
                    "Puerto Reportes",
                    min_value=1,
                    max_value=65535,
                    value=services.get("reporting_port", 5001),
                    key="config_services_reporting_port",
                    on_change=on_config_change,
                    args=("services.reporting_port",),
                )
                # Mostrar validación en tiempo real
                field_key = "services.reporting_port"
                if field_key in st.session_state.validation_errors:
                    st.error(st.session_state.validation_errors[field_key])

                # Actualizar valor en config si cambió
                if "config_services_reporting_port" in st.session_state:
                    services["reporting_port"] = (
                        st.session_state.config_services_reporting_port
                    )

    # Configuraciones principales
    with st.expander("🔧 Configuraciones Principales", expanded=False):
        col1, col2 = st.columns(2)

        with col1:
            # Detección
            if "deteccion" in config:
                st.checkbox(
                    "Activar Detección",
                    value=config["deteccion"].get("detectar", True),
                    key="config_deteccion_detectar",
                    on_change=on_config_change,
                    args=("deteccion.detectar",),
                )
                # Actualizar valor en config si cambió
                if "config_deteccion_detectar" in st.session_state:
                    config["deteccion"][
                        "detectar"
                    ] = st.session_state.config_deteccion_detectar

            # Decisión
            if "decision" in config:
                st.checkbox(
                    "Activar Decisión",
                    value=config["decision"].get("decision", True),
                    key="config_decision_decision",
                    on_change=on_config_change,
                    args=("decision.decision",),
                )
                # Actualizar valor en config si cambió
                if "config_decision_decision" in st.session_state:
                    config["decision"][
                        "decision"
                    ] = st.session_state.config_decision_decision

        with col2:
            # SUMO
            if "sumo" in config:
                st.checkbox(
                    "Activar Simulación",
                    value=config["sumo"].get("simular", True),
                    key="config_sumo_simular",
                    on_change=on_config_change,
                    args=("sumo.simular",),
                )
                # Actualizar valor en config si cambió
                if "config_sumo_simular" in st.session_state:
                    config["sumo"]["simular"] = st.session_state.config_sumo_simular

                st.checkbox(
                    "Mostrar GUI",
                    value=config["sumo"].get("gui", True),
                    key="config_sumo_gui",
                    on_change=on_config_change,
                    args=("sumo.gui",),
                )
                # Actualizar valor en config si cambió
                if "config_sumo_gui" in st.session_state:
                    config["sumo"]["gui"] = st.session_state.config_sumo_gui

            # Reportes
            if "reporte" in config:
                st.checkbox(
                    "Generar Reportes",
                    value=config["reporte"].get("generar", True),
                    key="config_reporte_generar",
                    on_change=on_config_change,
                    args=("reporte.generar",),
                )
                # Actualizar valor en config si cambió
                if "config_reporte_generar" in st.session_state:
                    config["reporte"][
                        "generar"
                    ] = st.session_state.config_reporte_generar

    st.info("💡 Para configuración completa, edita config.yaml directamente.")


def main() -> None:
    """Función principal de la aplicación."""
    st.set_page_config(
        page_title="Sistema de Tráfico - Frontend",
        page_icon="🚦",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    initialize_session_state()

    try:
        current_page = render_navigation()

        if current_page == "services":
            render_services_page()
        elif current_page == "config":
            render_config_page()
        else:
            st.error("❌ Página no encontrada")

    except Exception as e:
        st.error(f"❌ Error en aplicación: {e}")
        log_error(f"Error en aplicación: {e}")


if __name__ == "__main__":
    main()
