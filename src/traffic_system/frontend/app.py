"""
Frontend Simplificado para el Sistema de Tráfico

Aplicación Streamlit con 2 páginas: Configuración y Servicios.
Funcionalidad esencial sin sobre-ingeniería.
"""

import time
from typing import Any

import streamlit as st
from streamlit_autorefresh import st_autorefresh

from src.traffic_system.frontend.utils import (
    log_error,
    set_nested_value,
    validate_field,
)


def initialize_session_state() -> None:
    """Inicializar variables de estado de sesión de Streamlit."""
    if "app_initialized" not in st.session_state:
        st.session_state.app_initialized = True

        st.session_state.current_page = "services"
        st.session_state.config_modified = False
        st.session_state.current_config = {}
        st.session_state.config_manager = None
        st.session_state.service_controller = None
        st.session_state.validation_errors = {}

        st.session_state.live_logs_enabled = {}
        st.session_state.logs_refresh_interval = 1.0
        st.session_state.last_logs_update = {}

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

    if "live_logs_enabled" not in st.session_state:
        st.session_state.live_logs_enabled = {}
    if "logs_refresh_interval" not in st.session_state:
        st.session_state.logs_refresh_interval = 1.0
    if "last_logs_update" not in st.session_state:
        st.session_state.last_logs_update = {}


def render_navigation() -> str:
    """Renderizar navegación simple con 2 opciones."""
    st.sidebar.title("🚦 SemaforIA")

    if st.session_state.get("current_page") == "services":
        if "services_summary_cache" in st.session_state:
            cache_time = st.session_state.get("services_summary_cache_time", 0)
            age = int(time.time() - cache_time)
            st.sidebar.info(f"📊 Servicios cacheados ({age}s)")

        if st.sidebar.button(
            "🔄 Reinicializar Controller",
            help="Reinicia ServiceController si hay errores de métodos",
        ):
            if "service_controller" in st.session_state:
                del st.session_state["service_controller"]
            st.sidebar.success("✅ Controller reinicializado")
            st.rerun()

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


def update_service_cache_status(service_name: str, is_running: bool) -> None:
    """Actualizar estado de un servicio en el caché sin verificación completa."""
    if "services_summary_cache" not in st.session_state:
        return

    try:
        cache = st.session_state["services_summary_cache"]

        if service_name in cache["services"]:
            cache["services"][service_name]["is_running"] = is_running

            running_count = sum(
                1
                for service_info in cache["services"].values()
                if service_info["is_running"]
            )
            total_count = len(cache["services"])

            cache["running_services"] = running_count
            cache["stopped_services"] = total_count - running_count
            cache["status_text"] = f"{running_count}/{total_count} servicios activos"
            cache["all_running"] = running_count == total_count
            cache["all_stopped"] = running_count == 0

            st.session_state["services_summary_cache_time"] = time.time()

    except Exception:
        if "services_summary_cache" in st.session_state:
            del st.session_state["services_summary_cache"]


def update_multiple_services_cache_status(
    results: dict[str, tuple[bool, str]], target_state: bool
) -> None:
    """Actualizar el estado de múltiples servicios en el caché."""
    if "services_summary_cache" not in st.session_state:
        return

    try:
        for service_name, (success, _) in results.items():
            if success:
                update_service_cache_status(service_name, target_state)

    except Exception:
        if "services_summary_cache" in st.session_state:
            del st.session_state["services_summary_cache"]


def render_service_logs(service_name: str, controller: Any) -> None:
    """Renderizar logs de un servicio específico con controles de actualización."""
    try:
        required_methods = [
            "get_service_logs",
            "get_service_log_path",
            "clear_service_logs",
        ]
        missing_methods = [
            method for method in required_methods if not hasattr(controller, method)
        ]

        if missing_methods:
            st.error(f"❌ ServiceController falta métodos: {missing_methods}")
            st.info("🔄 Recarga la página para actualizar el ServiceController")
            return

        col1, col2, col3, col4 = st.columns([1.5, 1, 1, 1])

        with col1:
            max_lines = st.slider(
                "Líneas a mostrar",
                min_value=10,
                max_value=500,
                value=100,
                step=10,
                key=f"log_lines_{service_name}",
            )

        with col2:
            if st.button("🔄 Actualizar", key=f"refresh_logs_{service_name}"):
                st.session_state.last_logs_update[service_name] = time.time()
                st.rerun()

        with col3:
            if st.button("🗑️ Limpiar", key=f"clear_logs_{service_name}"):
                try:
                    if controller.clear_service_logs(service_name):
                        st.success("✅ Logs limpiados")
                    else:
                        st.error("❌ No se pudieron limpiar los logs")
                except Exception as clear_error:
                    st.error(f"❌ Error limpiando logs: {clear_error}")
                st.rerun()

        with col4:
            live_logs_key = f"live_logs_{service_name}"
            current_live_state = st.session_state.live_logs_enabled.get(
                service_name, False
            )

            live_logs_enabled = st.checkbox(
                "Auto-refresh",
                value=current_live_state,
                key=live_logs_key,
                help="Actualizar logs automáticamente cada pocos segundos",
            )

            st.session_state.live_logs_enabled[service_name] = live_logs_enabled

        if live_logs_enabled:
            col1, col2, _ = st.columns([2, 1, 1])

            with col1:
                refresh_interval = st.slider(
                    "Intervalo actualización (seg)",
                    min_value=0.5,
                    max_value=30.0,
                    value=float(st.session_state.logs_refresh_interval),
                    step=0.5,
                    key=f"refresh_interval_{service_name}",
                    help="Intervalos más cortos (0.5-1s) proporcionan logs casi en tiempo real",
                )
                st.session_state.logs_refresh_interval = refresh_interval

            with col2:
                service_running = controller.get_service_status(service_name)
                if service_running:
                    st.success("🟢 Servicio activo")
                else:
                    st.warning("⚠️ Servicio detenido")
                    st.caption("Live logs pausado")

        try:
            log_path = controller.get_service_log_path(service_name)
            st.caption(f"📁 Archivo: {log_path}")
        except Exception as path_error:
            st.error(f"❌ Error obteniendo ruta de log: {path_error}")
            return

        try:
            logs = controller.get_service_logs(service_name, max_lines)
        except Exception as logs_error:
            st.error(f"❌ Error obteniendo logs: {logs_error}")
            return

        if not logs:
            st.info("📭 No hay logs disponibles para este servicio")
        elif logs and logs[0].startswith("No se encontró archivo"):
            st.warning(
                "⚠️ Archivo de log no encontrado. El servicio puede haber sido iniciado antes de esta sesión."
            )
        elif logs and logs[0].startswith("Error"):
            st.error(f"❌ {logs[0]}")
        else:
            show_recent_first = st.checkbox(
                "📄 Mostrar recientes primero",
                value=False,
                key=f"recent_first_{service_name}",
                help="Los logs más nuevos aparecen arriba (evita hacer scroll manual)",
            )

            if show_recent_first:
                logs_to_show = list(reversed(logs))
            else:
                logs_to_show = logs

            log_text = "\n".join(logs_to_show)

            if not show_recent_first:
                content_signature = f"{len(logs)}_{hash(logs[-1] if logs else '')}"
                text_area_key = f"logs_display_{service_name}_{content_signature}"
            else:
                text_area_key = f"logs_display_inverted_{service_name}"

            st.text_area(
                "🖥️ Logs del servicio",
                value=log_text,
                height=300,
                key=text_area_key,
                help="Los logs se actualizan automáticamente. El orden cronológico intenta mostrar desde el final por defecto.",
                disabled=True,
            )

            if st.button(
                "💾 Descargar logs completos", key=f"download_logs_{service_name}"
            ):
                try:
                    full_logs = controller.get_service_logs(service_name, 10000)
                    full_log_text = "\n".join(full_logs)

                    st.download_button(
                        label="📥 Descargar archivo de log",
                        data=full_log_text,
                        file_name=f"{service_name}_logs_{time.strftime('%Y%m%d_%H%M%S')}.txt",
                        mime="text/plain",
                        key=f"download_button_{service_name}",
                    )
                except Exception as download_error:
                    st.error(f"❌ Error preparando descarga: {download_error}")

        if live_logs_enabled and controller.get_service_status(service_name):
            refresh_interval_ms = int(refresh_interval * 1000)

            auto_refresh_count = st_autorefresh(
                interval=refresh_interval_ms,
                limit=10000,
                key=f"autorefresh_{service_name}",
            )

            if auto_refresh_count > 0:
                st.session_state.last_logs_update[service_name] = time.time()

                if auto_refresh_count % 10 == 0:
                    st.caption(
                        f"🔄 Auto-refresh activo: {auto_refresh_count} actualizaciones"
                    )

    except Exception as e:
        st.error(f"❌ Error mostrando logs de {service_name}: {e}")
        log_error(f"Error en render_service_logs para {service_name}: {e}")

        st.info("🔍 Información de debugging:")
        st.code(f"ServiceController type: {type(controller)}")
        if hasattr(controller, "__dict__"):
            available_methods = [
                method for method in dir(controller) if not method.startswith("_")
            ]
            st.code(f"Métodos disponibles: {available_methods}")


def render_services_page() -> None:
    """Renderizar página de control de servicios."""
    st.title("🔧 Control de Servicios")

    if st.session_state.service_controller is None or not hasattr(
        st.session_state.service_controller, "get_service_log_path"
    ):
        from src.traffic_system.frontend.service_controller import ServiceController

        st.session_state.service_controller = ServiceController()
        if "service_controller_initialized" not in st.session_state:
            st.session_state.service_controller_initialized = True

    controller = st.session_state.service_controller

    def get_services_summary_manual() -> dict[str, Any] | None:
        """Obtener resumen de servicios solo cuando se solicite manualmente."""
        cache_key = "services_summary_cache"

        if cache_key in st.session_state:
            return st.session_state[cache_key]

        return None

    def force_services_check() -> dict[str, Any]:
        """Forzar verificación manual de servicios."""
        cache_key = "services_summary_cache"
        cache_time_key = "services_summary_cache_time"

        with st.spinner("🔍 Verificando estado de servicios..."):
            summary = controller.get_services_summary()

        st.session_state[cache_key] = summary
        st.session_state[cache_time_key] = time.time()

        return summary

    try:
        summary = get_services_summary_manual()

        if summary is None:
            if st.button(
                "🔍 Verificar Servicios", use_container_width=True, type="primary"
            ):
                summary = force_services_check()
                st.rerun()

        if summary:
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
                if st.button(
                    "🔄 Actualizar Estado",
                    help="Verificar estado real de todos los servicios",
                ):
                    summary = force_services_check()
                    st.rerun()

            st.markdown("---")

            col1, col2 = st.columns(2)
            with col1:
                if st.button("▶️ Iniciar Todos", use_container_width=True):
                    with st.spinner("⚙️ Iniciando todos los servicios..."):
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
                    update_multiple_services_cache_status(results, True)
                    st.rerun()

            with col2:
                if st.button("⏹️ Detener Todos", use_container_width=True):
                    with st.spinner("🛑 Deteniendo todos los servicios..."):
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
                    update_multiple_services_cache_status(results, False)
                    st.rerun()

            st.markdown("---")

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
                            with st.spinner(f"⚙️ Iniciando {display_name}..."):
                                success, message = controller.start_service(
                                    service_name
                                )
                                if success:
                                    st.success(f"✅ {message}")
                                    update_service_cache_status(service_name, True)
                                else:
                                    st.error(f"❌ {message}")
                                    if "services_summary_cache" in st.session_state:
                                        del st.session_state["services_summary_cache"]
                            time.sleep(1)
                            st.rerun()

                with col3:
                    if is_running:
                        if st.button("⏹️ Detener", key=f"stop_{service_name}"):
                            with st.spinner(f"🛑 Deteniendo {display_name}..."):
                                success, message = controller.stop_service_graceful(
                                    service_name
                                )
                                if success:
                                    st.success(f"✅ {message}")
                                    update_service_cache_status(service_name, False)
                                else:
                                    st.error(f"❌ {message}")
                                    if "services_summary_cache" in st.session_state:
                                        del st.session_state["services_summary_cache"]
                            time.sleep(1)
                            st.rerun()

                if is_running:
                    with st.expander(f"📋 Logs de {display_name}", expanded=False):
                        render_service_logs(service_name, controller)

                st.markdown("---")

    except Exception as e:
        st.error(f"❌ Error: {e}")
        log_error(f"Error en servicios: {e}")


def render_config_page() -> None:
    """Renderizar página de configuración."""
    st.title("⚙️ Configuración del Sistema")

    if st.session_state.config_manager is None:
        from src.traffic_system.frontend.config_manager import ConfigManager

        st.session_state.config_manager = ConfigManager()
        config = st.session_state.config_manager.load_config()
        if config:
            st.session_state.current_config = config

        if "config_manager_initialized" not in st.session_state:
            st.session_state.config_manager_initialized = True

    manager = st.session_state.config_manager

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
        has_changes = st.session_state.config_modified
        has_validation_errors = len(st.session_state.validation_errors) > 0

        if st.session_state.current_config:
            is_valid, errors = manager.validate_with_pydantic(
                st.session_state.current_config
            )

            if not has_changes:
                button_text = "💾 Guardar"
                can_save = False
            elif has_validation_errors:
                error_count = len(st.session_state.validation_errors)
                button_text = f"⚠️ Guardar ({error_count} errores)"
                can_save = False
            elif not is_valid:
                button_text = f"⚠️ Guardar ({len(errors)} errores)"
                can_save = False
            else:
                button_text = "💾 Guardar"
                can_save = True

            if st.button(button_text, use_container_width=True, disabled=not can_save):
                success, save_errors = manager.save_config(
                    st.session_state.current_config
                )
                if success:
                    st.session_state.config_modified = False
                    st.session_state.validation_errors.clear()
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

    error_count = len(st.session_state.validation_errors)

    if error_count > 0:
        st.error(f"❌ {error_count} errores de validación")
    elif st.session_state.config_modified:
        st.warning("⚠️ Cambios sin guardar")
    else:
        st.success("✅ Sincronizado")

    if st.session_state.current_config:
        is_valid, errors = manager.validate_with_pydantic(
            st.session_state.current_config
        )
        if not is_valid:
            with st.expander(f"❌ Errores ({len(errors)})", expanded=True):
                for error in errors:
                    st.error(error)

    st.markdown("---")

    if st.session_state.current_config:
        render_simple_config(manager, st.session_state.current_config)


def on_config_change(field_path: str) -> None:
    """Callback ejecutado cuando cambia un campo de configuración."""
    st.session_state.config_modified = True

    if "validation_errors" not in st.session_state:
        st.session_state.validation_errors = {}

    try:
        widget_key = f"config_{field_path.replace('.', '_')}"
        if widget_key in st.session_state and st.session_state.current_config:
            field_value = st.session_state[widget_key]

            is_valid, message = validate_field(
                field_path, field_value, st.session_state.current_config
            )

            if is_valid:
                st.session_state.validation_errors.pop(field_path, None)
            else:
                st.session_state.validation_errors[field_path] = message

    except Exception:
        st.session_state.validation_errors[field_path] = "❌ Error de validación"


def render_field_widget(
    field_path: str, field_name: str, value: Any, config: dict[str, Any]
) -> None:
    """
    Renderizar widget apropiado para un campo basándose en su tipo.

    Args:
        field_path: Ruta completa del campo (ej: 'services.simulation_port')
        field_name: Nombre del campo para mostrar (ej: 'Puerto Simulación')
        value: Valor actual del campo
        config: Configuración completa para actualización
    """
    widget_key = f"config_{field_path.replace('.', '_')}"

    try:
        if isinstance(value, bool):
            st.checkbox(
                field_name,
                value=value,
                key=widget_key,
                on_change=on_config_change,
                args=(field_path,),
            )
        elif isinstance(value, int):
            if "port" in field_path.lower():
                min_val, max_val = 1, 65535
            elif "degrees" in field_path.lower() or "rotation" in field_path.lower():
                min_val, max_val = 0, 360
            else:
                min_val, max_val = 0, 999999

            st.number_input(
                field_name,
                min_value=min_val,
                max_value=max_val,
                value=value,
                key=widget_key,
                on_change=on_config_change,
                args=(field_path,),
            )
        elif isinstance(value, float):
            step = 0.01 if value < 10 else 1.0
            st.number_input(
                field_name,
                value=value,
                step=step,
                key=widget_key,
                on_change=on_config_change,
                args=(field_path,),
            )
        elif isinstance(value, str) or value is None:
            display_value = "" if value is None else value
            st.text_input(
                field_name,
                value=display_value,
                key=widget_key,
                on_change=on_config_change,
                args=(field_path,),
                help="Dejar vacío para None/null" if value is None else None,
            )
        elif isinstance(value, list):
            if value and isinstance(value[0], int | float):
                list_str = ", ".join(str(v) for v in value)
                st.text_area(
                    f"{field_name} (separados por comas)",
                    value=list_str,
                    key=widget_key,
                    on_change=on_config_change,
                    args=(field_path,),
                    help="Valores separados por comas",
                )
            elif value and isinstance(value[0], str):
                list_str = ", ".join(value)
                st.text_area(
                    f"{field_name} (separados por comas)",
                    value=list_str,
                    key=widget_key,
                    on_change=on_config_change,
                    args=(field_path,),
                    help="Valores separados por comas",
                )
            else:
                st.text_input(
                    field_name,
                    value=str(value),
                    key=widget_key,
                    on_change=on_config_change,
                    args=(field_path,),
                )
        else:
            st.text_input(
                field_name,
                value=str(value),
                key=widget_key,
                on_change=on_config_change,
                args=(field_path,),
            )

        if field_path in st.session_state.validation_errors:
            st.error(st.session_state.validation_errors[field_path])

        if widget_key in st.session_state:
            new_value = st.session_state[widget_key]

            if isinstance(value, list) and isinstance(new_value, str):
                try:
                    if value and isinstance(value[0], int):
                        new_value = [
                            int(x.strip()) for x in new_value.split(",") if x.strip()
                        ]
                    elif value and isinstance(value[0], float):
                        new_value = [
                            float(x.strip()) for x in new_value.split(",") if x.strip()
                        ]
                    elif value and isinstance(value[0], str):
                        new_value = [
                            x.strip() for x in new_value.split(",") if x.strip()
                        ]
                except (ValueError, IndexError):
                    new_value = value

            if value is None and isinstance(new_value, str) and new_value.strip() == "":
                new_value = None
            elif (
                value is None and isinstance(new_value, str) and new_value.strip() != ""
            ):
                if "seed" in field_path and new_value.strip().isdigit():
                    new_value = int(new_value.strip())

            set_nested_value(config, field_path, new_value)

    except Exception as e:
        st.error(f"Error renderizando campo {field_name}: {e}")


def render_simple_config(manager: Any, config: dict[str, Any]) -> None:
    """Renderizar configuración completa de config.yaml."""

    with st.expander("🌐 Configuración Global", expanded=False):
        col1, col2 = st.columns(2)

        with col1:
            render_field_widget(
                "base_url", "URL Base", config.get("base_url", ""), config
            )
        with col2:
            render_field_widget("base_ip", "IP Base", config.get("base_ip", ""), config)

    with st.expander("📡 Servicios", expanded=False):
        if "services" in config:
            services = config["services"]
            col1, col2, col3 = st.columns(3)

            with col1:
                render_field_widget(
                    "services.simulation_port",
                    "Puerto Simulación",
                    services.get("simulation_port", 5000),
                    config,
                )
            with col2:
                render_field_widget(
                    "services.detection_port",
                    "Puerto Detección",
                    services.get("detection_port", 5000),
                    config,
                )
            with col3:
                render_field_widget(
                    "services.reporting_port",
                    "Puerto Reportes",
                    services.get("reporting_port", 5001),
                    config,
                )

    with st.expander("🔍 Detección de Objetos", expanded=False):
        if "deteccion" in config:
            deteccion = config["deteccion"]

            st.subheader("Configuración Principal")
            col1, col2 = st.columns(2)

            with col1:
                render_field_widget(
                    "deteccion.modelo",
                    "Modelo YOLO",
                    deteccion.get("modelo", "yolov8n.pt"),
                    config,
                )
                render_field_widget(
                    "deteccion.path_resultados_deteccion",
                    "Path Resultados",
                    deteccion.get("path_resultados_deteccion", ""),
                    config,
                )
                render_field_widget(
                    "deteccion.window_fixed",
                    "Ventana Fija",
                    deteccion.get("window_fixed", True),
                    config,
                )

            with col2:
                render_field_widget(
                    "deteccion.forced_rotation_degrees",
                    "Rotación (grados)",
                    deteccion.get("forced_rotation_degrees", 0),
                    config,
                )
                render_field_widget(
                    "deteccion.window_size",
                    "Tamaño Ventana [ancho, alto]",
                    deteccion.get("window_size", [460, 820]),
                    config,
                )

            st.markdown("---")

            if "carpeta_dataset" in deteccion:
                st.subheader("Procesamiento Carpeta Dataset")
                col1, col2 = st.columns(2)

                with col1:
                    # TODO: Si este se activa, procesar la cámara en tiempo real y Procesamiento Video Individual deben desactivarse
                    render_field_widget(
                        "deteccion.carpeta_dataset.procesar",
                        "Procesar Carpeta",
                        deteccion["carpeta_dataset"].get("procesar", False),
                        config,
                    )
                    render_field_widget(
                        "deteccion.carpeta_dataset.path_origen",
                        "Path Origen",
                        deteccion["carpeta_dataset"].get("path_origen", ""),
                        config,
                    )
                with col2:
                    render_field_widget(
                        "deteccion.carpeta_dataset.path_destino",
                        "Path Destino",
                        deteccion["carpeta_dataset"].get("path_destino", ""),
                        config,
                    )

            st.markdown("---")

            if "un_video" in deteccion:
                st.subheader("Procesamiento Video Individual")
                col1, col2 = st.columns(2)

                with col1:
                    render_field_widget(
                        "deteccion.un_video.procesar",
                        "Procesar Video",
                        deteccion["un_video"].get("procesar", False),
                        config,
                    )
                    render_field_widget(
                        "deteccion.un_video.guardar",
                        "Guardar Video",
                        deteccion["un_video"].get("guardar", False),
                        config,
                    )
                    # TODO: Modificar para que se pueda elegir una zona (Zona A, Zona B, ..., Zona J)
                    render_field_widget(
                        "deteccion.un_video.zona",
                        "Zona",
                        deteccion["un_video"].get("zona", "Zona A"),
                        config,
                    )

                with col2:
                    render_field_widget(
                        "deteccion.un_video.path_origen",
                        "Path Video Origen",
                        deteccion["un_video"].get("path_origen", ""),
                        config,
                    )
                    render_field_widget(
                        "deteccion.un_video.path_destino",
                        "Path Destino",
                        deteccion["un_video"].get("path_destino", ""),
                        config,
                    )

            st.markdown("---")

            if "procesar_camara" in deteccion:
                st.subheader("Procesamiento Cámara")
                render_field_widget(
                    "deteccion.procesar_camara",
                    "Procesar Cámara",
                    deteccion.get("procesar_camara", False),
                    config,
                )

    with st.expander("🧠 Decisión y Aprendizaje", expanded=False):
        if "decision" in config:
            decision = config["decision"]

            st.subheader("Configuración Principal")
            col1, col2 = st.columns(2)
            with col1:
                render_field_widget(
                    "decision.path_modelo_entrenado",
                    "Path Modelo Entrenado",
                    decision.get("path_modelo_entrenado", ""),
                    config,
                )
                render_field_widget(
                    "decision.steps",
                    "Steps por Decisión",
                    decision.get("steps", 10),
                    config,
                )
            with col2:
                render_field_widget(
                    "decision.ponderaciones_zonas",
                    "Ponderaciones Zonas (12 valores)",
                    decision.get("ponderaciones_zonas", [1.0] * 12),
                    config,
                )

            st.markdown("---")

            if "entrenamiento" in decision:
                st.subheader("Entrenamiento DQN")
                entrenamiento = decision["entrenamiento"]

                st.markdown("**Configuración Básica**")
                col1, col2, col3 = st.columns(3)

                with col1:
                    render_field_widget(
                        "decision.entrenamiento.entrenar",
                        "Activar Entrenamiento",
                        entrenamiento.get("entrenar", False),
                        config,
                    )
                    render_field_widget(
                        "decision.entrenamiento.path_resultado",
                        "Path Resultados",
                        entrenamiento.get("path_resultado", ""),
                        config,
                    )
                    render_field_widget(
                        "decision.entrenamiento.num_epocas",
                        "Número Épocas",
                        entrenamiento.get("num_epocas", 35),
                        config,
                    )
                    render_field_widget(
                        "decision.entrenamiento.batch_size",
                        "Batch Size",
                        entrenamiento.get("batch_size", 256),
                        config,
                    )

                with col2:
                    render_field_widget(
                        "decision.entrenamiento.steps",
                        "Steps",
                        entrenamiento.get("steps", 10),
                        config,
                    )
                    render_field_widget(
                        "decision.entrenamiento.memory",
                        "Memory",
                        entrenamiento.get("memory", 5000),
                        config,
                    )
                    render_field_widget(
                        "decision.entrenamiento.learning_rate",
                        "Learning Rate",
                        entrenamiento.get("learning_rate", 0.0005),
                        config,
                    )
                    render_field_widget(
                        "decision.entrenamiento.learning_rate_decay",
                        "LR Decay",
                        entrenamiento.get("learning_rate_decay", 0.99),
                        config,
                    )

                with col3:
                    render_field_widget(
                        "decision.entrenamiento.learning_rate_min",
                        "LR Mínimo",
                        entrenamiento.get("learning_rate_min", 0.00005),
                        config,
                    )
                    render_field_widget(
                        "decision.entrenamiento.epsilon",
                        "Epsilon",
                        entrenamiento.get("epsilon", 1.0),
                        config,
                    )
                    render_field_widget(
                        "decision.entrenamiento.epsilon_decay",
                        "Epsilon Decay",
                        entrenamiento.get("epsilon_decay", 0.99995),
                        config,
                    )
                    render_field_widget(
                        "decision.entrenamiento.epsilon_min",
                        "Epsilon Mín",
                        entrenamiento.get("epsilon_min", 0.1),
                        config,
                    )

                st.markdown("**Parámetros Avanzados**")
                col1, col2, col3 = st.columns(3)

                with col1:
                    render_field_widget(
                        "decision.entrenamiento.gamma",
                        "Gamma",
                        entrenamiento.get("gamma", 0.85),
                        config,
                    )
                    render_field_widget(
                        "decision.entrenamiento.hidden_layers",
                        "Capas Ocultas",
                        entrenamiento.get("hidden_layers", [64, 64, 64]),
                        config,
                    )
                    render_field_widget(
                        "decision.entrenamiento.use_double_dqn",
                        "Double DQN",
                        entrenamiento.get("use_double_dqn", True),
                        config,
                    )
                    render_field_widget(
                        "decision.entrenamiento.use_dueling_dqn",
                        "Dueling DQN",
                        entrenamiento.get("use_dueling_dqn", True),
                        config,
                    )

                with col2:
                    render_field_widget(
                        "decision.entrenamiento.target_update_frequency",
                        "Target Update Freq",
                        entrenamiento.get("target_update_frequency", 100),
                        config,
                    )
                    render_field_widget(
                        "decision.entrenamiento.use_prioritized_replay",
                        "Prioritized Replay",
                        entrenamiento.get("use_prioritized_replay", True),
                        config,
                    )
                    render_field_widget(
                        "decision.entrenamiento.per_alpha",
                        "PER Alpha",
                        entrenamiento.get("per_alpha", 0.6),
                        config,
                    )
                    render_field_widget(
                        "decision.entrenamiento.per_beta_start",
                        "PER Beta Start",
                        entrenamiento.get("per_beta_start", 0.4),
                        config,
                    )

                with col3:
                    render_field_widget(
                        "decision.entrenamiento.use_noisy_networks",
                        "Noisy Networks",
                        entrenamiento.get("use_noisy_networks", True),
                        config,
                    )
                    render_field_widget(
                        "decision.entrenamiento.noise_std",
                        "Noise STD",
                        entrenamiento.get("noise_std", 0.3),
                        config,
                    )
                    render_field_widget(
                        "decision.entrenamiento.use_dropout",
                        "Dropout",
                        entrenamiento.get("use_dropout", True),
                        config,
                    )
                    render_field_widget(
                        "decision.entrenamiento.dropout_rate",
                        "Dropout Rate",
                        entrenamiento.get("dropout_rate", 0.02),
                        config,
                    )

                with st.expander("Optimizaciones de Estabilidad", expanded=False):
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        render_field_widget(
                            "decision.entrenamiento.warmup_steps",
                            "Warmup Steps",
                            entrenamiento.get("warmup_steps", 250),
                            config,
                        )
                        render_field_widget(
                            "decision.entrenamiento.min_replay_size",
                            "Min Replay Size",
                            entrenamiento.get("min_replay_size", 32),
                            config,
                        )
                        render_field_widget(
                            "decision.entrenamiento.use_batch_normalization",
                            "Batch Normalization",
                            entrenamiento.get("use_batch_normalization", True),
                            config,
                        )
                        render_field_widget(
                            "decision.entrenamiento.use_he_initialization",
                            "He Initialization",
                            entrenamiento.get("use_he_initialization", True),
                            config,
                        )

                    with col2:
                        render_field_widget(
                            "decision.entrenamiento.use_residual_connections",
                            "Residual Connections",
                            entrenamiento.get("use_residual_connections", True),
                            config,
                        )
                        render_field_widget(
                            "decision.entrenamiento.gradient_clip_norm",
                            "Gradient Clip Norm",
                            entrenamiento.get("gradient_clip_norm", 1.0),
                            config,
                        )
                        render_field_widget(
                            "decision.entrenamiento.use_leaky_relu",
                            "Leaky ReLU",
                            entrenamiento.get("use_leaky_relu", True),
                            config,
                        )
                        render_field_widget(
                            "decision.entrenamiento.use_gradient_clipping",
                            "Gradient Clipping",
                            entrenamiento.get("use_gradient_clipping", True),
                            config,
                        )

                    with col3:
                        render_field_widget(
                            "decision.entrenamiento.use_huber_loss",
                            "Huber Loss",
                            entrenamiento.get("use_huber_loss", True),
                            config,
                        )
                        render_field_widget(
                            "decision.entrenamiento.normalize_rewards",
                            "Normalize Rewards",
                            entrenamiento.get("normalize_rewards", True),
                            config,
                        )
                        render_field_widget(
                            "decision.entrenamiento.per_beta_frames",
                            "PER Beta Frames",
                            entrenamiento.get("per_beta_frames", 100000),
                            config,
                        )
                        render_field_widget(
                            "decision.entrenamiento.adaptive_lr",
                            "Adaptive LR",
                            entrenamiento.get("adaptive_lr", True),
                            config,
                        )

                with st.expander("Evaluación y Métricas", expanded=False):
                    col1, col2 = st.columns(2)
                    with col1:
                        render_field_widget(
                            "decision.entrenamiento.enable_evaluation",
                            "Activar Evaluación",
                            entrenamiento.get("enable_evaluation", True),
                            config,
                        )
                        render_field_widget(
                            "decision.entrenamiento.evaluation_episodes",
                            "Episodios Evaluación",
                            entrenamiento.get("evaluation_episodes", 10),
                            config,
                        )
                        render_field_widget(
                            "decision.entrenamiento.evaluation_frequency",
                            "Frecuencia Evaluación",
                            entrenamiento.get("evaluation_frequency", 10),
                            config,
                        )
                        render_field_widget(
                            "decision.entrenamiento.baseline_comparison",
                            "Comparación Baseline",
                            entrenamiento.get("baseline_comparison", True),
                            config,
                        )

                    with col2:
                        render_field_widget(
                            "decision.entrenamiento.save_evaluation_data",
                            "Guardar Datos Evaluación",
                            entrenamiento.get("save_evaluation_data", True),
                            config,
                        )
                        render_field_widget(
                            "decision.entrenamiento.metrics_window_size",
                            "Ventana Métricas",
                            entrenamiento.get("metrics_window_size", 100),
                            config,
                        )
                        render_field_widget(
                            "decision.entrenamiento.statistical_tests",
                            "Tests Estadísticos",
                            entrenamiento.get("statistical_tests", True),
                            config,
                        )
                        render_field_widget(
                            "decision.entrenamiento.generate_plots",
                            "Generar Gráficos",
                            entrenamiento.get("generate_plots", True),
                            config,
                        )

                with st.expander("Optimizaciones de Rendimiento", expanded=False):
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        render_field_widget(
                            "decision.entrenamiento.lr_schedule_type",
                            "Tipo Schedule LR",
                            entrenamiento.get("lr_schedule_type", "plateau"),
                            config,
                        )
                        render_field_widget(
                            "decision.entrenamiento.enable_jit_compilation",
                            "JIT Compilation",
                            entrenamiento.get("enable_jit_compilation", True),
                            config,
                        )
                        render_field_widget(
                            "decision.entrenamiento.dropout_mode",
                            "Modo Dropout",
                            entrenamiento.get("dropout_mode", "optimized"),
                            config,
                        )
                        render_field_widget(
                            "decision.entrenamiento.dropout_layers",
                            "Layers Dropout",
                            entrenamiento.get("dropout_layers", "strategic"),
                            config,
                        )

                    with col2:
                        render_field_widget(
                            "decision.entrenamiento.noisy_implementation",
                            "Implementación Noisy",
                            entrenamiento.get("noisy_implementation", "efficient"),
                            config,
                        )
                        render_field_widget(
                            "decision.entrenamiento.double_dqn_batch_optimization",
                            "Double DQN Batch Opt",
                            entrenamiento.get("double_dqn_batch_optimization", False),
                            config,
                        )
                        render_field_widget(
                            "decision.entrenamiento.target_update_batch_size",
                            "Target Update Batch Size",
                            entrenamiento.get("target_update_batch_size", 1024),
                            config,
                        )
                        render_field_widget(
                            "decision.entrenamiento.per_batch_processing",
                            "PER Batch Processing",
                            entrenamiento.get("per_batch_processing", False),
                            config,
                        )

                    with col3:
                        render_field_widget(
                            "decision.entrenamiento.per_update_frequency",
                            "PER Update Frequency",
                            entrenamiento.get("per_update_frequency", 4),
                            config,
                        )
                        render_field_widget(
                            "decision.entrenamiento.per_importance_annealing",
                            "PER Importance Annealing",
                            entrenamiento.get("per_importance_annealing", False),
                            config,
                        )
                        render_field_widget(
                            "decision.entrenamiento.dueling_stream_simplification",
                            "Dueling Stream Simplification",
                            entrenamiento.get("dueling_stream_simplification", False),
                            config,
                        )
                        render_field_widget(
                            "decision.entrenamiento.hidden_layers_optimization",
                            "Hidden Layers Optimization",
                            entrenamiento.get("hidden_layers_optimization", False),
                            config,
                        )

    with st.expander("🚦 SUMO Simulación", expanded=False):
        if "sumo" in config:
            sumo = config["sumo"]

            st.subheader("Configuración Principal")
            col1, col2 = st.columns(2)
            with col1:
                render_field_widget(
                    "sumo.gui", "Mostrar GUI", sumo.get("gui", True), config
                )
                render_field_widget(
                    "sumo.path_sumo",
                    "Path SUMO",
                    sumo.get("path_sumo", "/usr/share/sumo"),
                    config,
                )
            with col2:
                render_field_widget(
                    "sumo.comparar",
                    "Modo Comparación",
                    sumo.get("comparar", False),
                    config,
                )
                render_field_widget(
                    "sumo.simulation_time_limit",
                    "Límite Tiempo Simulación",
                    sumo.get("simulation_time_limit", 19500),
                    config,
                )

            st.markdown("---")
            st.subheader("Configuración de Semilla")
            col1, col2 = st.columns(2)
            with col1:
                render_field_widget(
                    "sumo.use_random_seed",
                    "Usar Semilla Aleatoria",
                    sumo.get("use_random_seed", True),
                    config,
                )
                render_field_widget(
                    "sumo.persist_random_seed",
                    "Persistir Semilla",
                    sumo.get("persist_random_seed", False),
                    config,
                )
            with col2:
                render_field_widget(
                    "sumo.fixed_seed",
                    "Semilla Fija",
                    sumo.get("fixed_seed", None),
                    config,
                )

    with st.expander("📊 Reportes", expanded=False):
        if "reporte" in config:
            reporte = config["reporte"]
            col1, col2 = st.columns(2)

            with col1:
                render_field_widget(
                    "reporte.steps",
                    "Steps por Reporte",
                    reporte.get("steps", 60),
                    config,
                )
                render_field_widget(
                    "reporte.tiempo_total_espera_maximo",
                    "Tiempo Espera Total Máx",
                    reporte.get("tiempo_total_espera_maximo", 600),
                    config,
                )
                render_field_widget(
                    "reporte.tiempo_zona_espera_maximo",
                    "Tiempo Espera Zona Máx",
                    reporte.get("tiempo_zona_espera_maximo", 300),
                    config,
                )
                render_field_widget(
                    "reporte.total_vehiculos_maximo",
                    "Vehículos Totales Máx",
                    reporte.get("total_vehiculos_maximo", 50),
                    config,
                )
            with col2:
                render_field_widget(
                    "reporte.zona_vehiculos_maximo",
                    "Vehículos Zona Máx",
                    reporte.get("zona_vehiculos_maximo", 200.0),
                    config,
                )
                render_field_widget(
                    "reporte.path_reporte",
                    "Path Reportes",
                    reporte.get("path_reporte", "results/reportes"),
                    config,
                )
                render_field_widget(
                    "reporte.db_path_base",
                    "Path Base DB",
                    reporte.get("db_path_base", "results/reportes/db"),
                    config,
                )


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
