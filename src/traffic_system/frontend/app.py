"""
Frontend Simplificado para el Sistema de Tráfico

Aplicación Streamlit con 3 páginas: Configuración, Servicios y Base de Datos.
Funcionalidad esencial sin sobre-ingeniería.
"""

import atexit
import datetime
import glob
import os
import sqlite3
import time
from typing import Any

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from streamlit_autorefresh import st_autorefresh

from src.traffic_system.frontend.config import get_tooltip
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
        st.session_state.logs_refresh_interval = 4.0
        st.session_state.last_logs_update = {}

    # Asegurar que todas las variables estén inicializadas
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
        st.session_state.logs_refresh_interval = 4.0
    if "last_logs_update" not in st.session_state:
        st.session_state.last_logs_update = {}


def cleanup_on_exit() -> None:
    """Función para limpiar recursos al cerrar la aplicación."""
    try:
        # Intentar acceder al service_controller desde session_state si Streamlit está disponible
        if "st" in globals():
            import streamlit as st_import

            if hasattr(st_import, "session_state") and hasattr(
                st_import.session_state, "service_controller"
            ):
                controller = st_import.session_state.service_controller
                if controller and hasattr(controller, "cleanup_resources"):
                    controller.cleanup_resources()
    except Exception:
        # Silenciar errores durante el cleanup para evitar problemas en el shutdown
        pass


# Registrar función de cleanup para cuando se cierre la aplicación
atexit.register(cleanup_on_exit)


def render_navigation() -> str:
    """Renderizar navegación simple con 3 opciones."""
    st.sidebar.title("🚦 SemaforIA")

    pages = {
        "🔧 Servicios": "services",
        "⚙️ Configuración": "config",
        "⚠️ Alertas": "database",
        "📊 Comparaciones": "comparisons",
    }
    current_page: str = st.session_state.current_page
    st.sidebar.markdown("---")

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

    if st.session_state.get("current_page") == "services":
        st.sidebar.markdown("---")
        if st.session_state.get("controller_just_reset", False):
            st.toast("🔄 ServiceController reinicializado exitosamente", icon="✅")
            st.session_state.controller_just_reset = False

        if st.sidebar.button(
            "🔄 Reinicializar Controller",
            use_container_width=True,
            help="Reinicia ServiceController si hay errores de métodos",
        ):
            if "service_controller" in st.session_state:
                del st.session_state["service_controller"]

            st.session_state.controller_just_reset = True

            if "services_summary_cache" in st.session_state:
                del st.session_state["services_summary_cache"]
            if "service_controller_initialized" in st.session_state:
                del st.session_state["service_controller_initialized"]
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

        col1, col2, col3 = st.columns([1.5, 1, 1])

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
                value=True,
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
                height=400,
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

    def get_services_summary_manual() -> Any:
        """Obtener resumen de servicios solo cuando se solicite manualmente."""
        cache_key = "services_summary_cache"

        if cache_key in st.session_state:
            return st.session_state[cache_key]

        return None

    def force_services_check() -> Any:
        """Forzar verificación manual de servicios."""
        cache_key = "services_summary_cache"
        cache_time_key = "services_summary_cache_time"

        with st.spinner("🔍 Verificando estado de servicios..."):
            summary = controller.get_services_summary()

        st.session_state[cache_key] = summary
        st.session_state[cache_time_key] = time.time()

        return summary

    def auto_refresh_services_status() -> None:
        """Actualizar estado de servicios en segundo plano después de operaciones."""
        cache_key = "services_summary_cache"
        cache_time_key = "services_summary_cache_time"

        # Actualizar cache silenciosamente sin spinner
        summary = controller.get_services_summary()
        st.session_state[cache_key] = summary
        st.session_state[cache_time_key] = time.time()

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
            with col3:
                if st.button(
                    "🔄 Actualizar Estado",
                    help="Verificar estado real de todos los servicios",
                ):
                    summary = force_services_check()
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
                            # Verificar estado automáticamente después de la operación
                            time.sleep(1)
                            auto_refresh_services_status()
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
                            # Verificar estado automáticamente después de la operación
                            time.sleep(1)
                            auto_refresh_services_status()
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

    # Obtener tooltip del módulo de configuración externo
    tooltip = get_tooltip(field_path)

    try:
        if isinstance(value, bool):
            st.checkbox(
                field_name,
                value=value,
                key=widget_key,
                on_change=on_config_change,
                args=(field_path,),
                help=tooltip,
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
                help=tooltip,
            )
        elif isinstance(value, float):
            # Determinar precisión basada en el tipo de campo
            if "learning_rate" in field_path.lower() or "lr" in field_path.lower():
                # Learning rates necesitan más precisión
                step = 0.00001 if value < 0.01 else 0.0001
                format_str = "%.6f"
            elif "epsilon" in field_path.lower() or "gamma" in field_path.lower():
                # Parámetros de RL típicos
                step = 0.001
                format_str = "%.4f"
            elif "rate" in field_path.lower() or "decay" in field_path.lower():
                # Otros rates y decays
                step = 0.001
                format_str = "%.4f"
            elif "alpha" in field_path.lower() or "beta" in field_path.lower():
                # Parámetros alpha/beta
                step = 0.01
                format_str = "%.3f"
            else:
                # Valores generales
                step = 0.01 if value < 10 else 1.0
                format_str = "%.3f" if value < 10 else "%.1f"

            st.number_input(
                field_name,
                value=value,
                step=step,
                format=format_str,
                key=widget_key,
                on_change=on_config_change,
                args=(field_path,),
                help=tooltip,
            )
        elif isinstance(value, str) or value is None:
            display_value = "" if value is None else value
            # Usar tooltip personalizado o el genérico para None
            help_text = (
                tooltip
                if tooltip
                else ("Dejar vacío para None/null" if value is None else None)
            )
            st.text_input(
                field_name,
                value=display_value,
                key=widget_key,
                on_change=on_config_change,
                args=(field_path,),
                help=help_text,
            )
        elif isinstance(value, list):
            if value and isinstance(value[0], int | float):
                list_str = ", ".join(str(v) for v in value)
                help_text = tooltip if tooltip else "Valores separados por comas"
                st.text_area(
                    f"{field_name} (separados por comas)",
                    value=list_str,
                    key=widget_key,
                    on_change=on_config_change,
                    args=(field_path,),
                    help=help_text,
                )
            elif value and isinstance(value[0], str):
                list_str = ", ".join(value)
                help_text = tooltip if tooltip else "Valores separados por comas"
                st.text_area(
                    f"{field_name} (separados por comas)",
                    value=list_str,
                    key=widget_key,
                    on_change=on_config_change,
                    args=(field_path,),
                    help=help_text,
                )
            else:
                st.text_input(
                    field_name,
                    value=str(value),
                    key=widget_key,
                    on_change=on_config_change,
                    args=(field_path,),
                    help=tooltip,
                )
        else:
            st.text_input(
                field_name,
                value=str(value),
                key=widget_key,
                on_change=on_config_change,
                args=(field_path,),
                help=tooltip,
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

                    zonas_disponibles = [
                        "Zona A",
                        "Zona B",
                        "Zona C",
                        "Zona D",
                        "Zona E",
                        "Zona F",
                        "Zona G",
                        "Zona H",
                        "Zona I",
                        "Zona J",
                        "Zona K",
                        "Zona L",
                    ]

                    zona_actual = deteccion["un_video"].get("zona", "Zona A")
                    if zona_actual not in zonas_disponibles:
                        zona_actual = "Zona A"

                    zona_seleccionada = st.selectbox(
                        "Zona",
                        options=zonas_disponibles,
                        index=zonas_disponibles.index(zona_actual),
                        key="config_deteccion_un_video_zona",
                        help="Selecciona la zona de detección para el video",
                    )

                    # Actualizar configuración si cambió
                    if zona_seleccionada != deteccion["un_video"].get("zona"):
                        st.session_state.config_modified = True
                        set_nested_value(
                            config, "deteccion.un_video.zona", zona_seleccionada
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

            # === ENTRENAMIENTO SIMPLIFICADO ===
            if "entrenamiento_simplificado" in decision:
                with st.expander("🔬 Entrenamiento Simplificado DQN", expanded=False):
                    entrenamiento_simplificado = decision["entrenamiento_simplificado"]

                    st.markdown("**Configuración Básica Simplificada**")
                    col1, col2, col3 = st.columns(3)

                    with col1:
                        render_field_widget(
                            "decision.entrenamiento_simplificado.entrenar",
                            "Activar Entrenamiento Simplificado",
                            entrenamiento_simplificado.get("entrenar", False),
                            config,
                        )
                        render_field_widget(
                            "decision.entrenamiento_simplificado.path_resultado",
                            "Path Resultados",
                            entrenamiento_simplificado.get("path_resultado", ""),
                            config,
                        )
                        render_field_widget(
                            "decision.entrenamiento_simplificado.num_epocas",
                            "Número Épocas",
                            entrenamiento_simplificado.get("num_epocas", 100),
                            config,
                        )
                        render_field_widget(
                            "decision.entrenamiento_simplificado.batch_size",
                            "Batch Size",
                            entrenamiento_simplificado.get("batch_size", 256),
                            config,
                        )

                    with col2:
                        render_field_widget(
                            "decision.entrenamiento_simplificado.steps",
                            "Steps",
                            entrenamiento_simplificado.get("steps", 10),
                            config,
                        )
                        render_field_widget(
                            "decision.entrenamiento_simplificado.memory",
                            "Memory",
                            entrenamiento_simplificado.get("memory", 50000),
                            config,
                        )
                        render_field_widget(
                            "decision.entrenamiento_simplificado.min_replay_size",
                            "Min Replay Size",
                            entrenamiento_simplificado.get("min_replay_size", 2000),
                            config,
                        )
                        render_field_widget(
                            "decision.entrenamiento_simplificado.learning_rate",
                            "Learning Rate",
                            entrenamiento_simplificado.get("learning_rate", 0.001),
                            config,
                        )

                    with col3:
                        render_field_widget(
                            "decision.entrenamiento_simplificado.epsilon",
                            "Epsilon",
                            entrenamiento_simplificado.get("epsilon", 1.0),
                            config,
                        )
                        render_field_widget(
                            "decision.entrenamiento_simplificado.epsilon_decay",
                            "Epsilon Decay",
                            entrenamiento_simplificado.get("epsilon_decay", 0.995),
                            config,
                        )
                        render_field_widget(
                            "decision.entrenamiento_simplificado.epsilon_min",
                            "Epsilon Mín",
                            entrenamiento_simplificado.get("epsilon_min", 0.1),
                            config,
                        )
                        render_field_widget(
                            "decision.entrenamiento_simplificado.gamma",
                            "Gamma",
                            entrenamiento_simplificado.get("gamma", 0.85),
                            config,
                        )

                    st.markdown("**Arquitectura y Algoritmos Simplificados**")
                    col1, col2, col3 = st.columns(3)

                    with col1:
                        render_field_widget(
                            "decision.entrenamiento_simplificado.hidden_layers",
                            "Capas Ocultas",
                            entrenamiento_simplificado.get("hidden_layers", [128, 128]),
                            config,
                        )
                        render_field_widget(
                            "decision.entrenamiento_simplificado.use_double_dqn",
                            "Double DQN",
                            entrenamiento_simplificado.get("use_double_dqn", True),
                            config,
                        )

                    with col2:
                        render_field_widget(
                            "decision.entrenamiento_simplificado.use_dueling_dqn",
                            "Dueling DQN",
                            entrenamiento_simplificado.get("use_dueling_dqn", True),
                            config,
                        )
                        render_field_widget(
                            "decision.entrenamiento_simplificado.target_update_frequency",
                            "Target Update Freq",
                            entrenamiento_simplificado.get(
                                "target_update_frequency", 200
                            ),
                            config,
                        )

                    with col3:
                        render_field_widget(
                            "decision.entrenamiento_simplificado.warmup_steps",
                            "Warmup Steps",
                            entrenamiento_simplificado.get("warmup_steps", 250),
                            config,
                        )
                        render_field_widget(
                            "decision.entrenamiento_simplificado.use_gradient_clipping",
                            "Gradient Clipping",
                            entrenamiento_simplificado.get(
                                "use_gradient_clipping", True
                            ),
                            config,
                        )

                    st.markdown("**Estabilidad y Evaluación**")
                    col1, col2, col3 = st.columns(3)

                    with col1:
                        render_field_widget(
                            "decision.entrenamiento_simplificado.gradient_clip_norm",
                            "Gradient Clip Norm",
                            entrenamiento_simplificado.get("gradient_clip_norm", 0.8),
                            config,
                        )
                        render_field_widget(
                            "decision.entrenamiento_simplificado.use_huber_loss",
                            "Huber Loss",
                            entrenamiento_simplificado.get("use_huber_loss", True),
                            config,
                        )

                    with col2:
                        render_field_widget(
                            "decision.entrenamiento_simplificado.use_he_initialization",
                            "He Initialization",
                            entrenamiento_simplificado.get(
                                "use_he_initialization", True
                            ),
                            config,
                        )
                        render_field_widget(
                            "decision.entrenamiento_simplificado.enable_evaluation",
                            "Activar Evaluación",
                            entrenamiento_simplificado.get("enable_evaluation", True),
                            config,
                        )

                    with col3:
                        render_field_widget(
                            "decision.entrenamiento_simplificado.evaluation_episodes",
                            "Episodios Evaluación",
                            entrenamiento_simplificado.get("evaluation_episodes", 10),
                            config,
                        )
                        render_field_widget(
                            "decision.entrenamiento_simplificado.evaluation_frequency",
                            "Frecuencia Evaluación",
                            entrenamiento_simplificado.get("evaluation_frequency", 5),
                            config,
                        )

                    st.markdown("**Early Stopping**")
                    col1, col2 = st.columns(2)

                    with col1:
                        render_field_widget(
                            "decision.entrenamiento_simplificado.patience",
                            "Patience",
                            entrenamiento_simplificado.get("patience", 10),
                            config,
                        )

                    with col2:
                        render_field_widget(
                            "decision.entrenamiento_simplificado.min_improvement",
                            "Mejora Mínima",
                            entrenamiento_simplificado.get("min_improvement", 0.01),
                            config,
                        )

            # === ENTRENAMIENTO COMPLETO ===
            if "entrenamiento_completo" in decision:
                with st.expander("⚗️ Entrenamiento Completo DQN", expanded=False):
                    entrenamiento = decision["entrenamiento_completo"]

                    st.markdown("**Configuración Básica**")
                    col1, col2, col3 = st.columns(3)

                    with col1:
                        render_field_widget(
                            "decision.entrenamiento_completo.entrenar",
                            "Activar Entrenamiento",
                            entrenamiento.get("entrenar", False),
                            config,
                        )
                        render_field_widget(
                            "decision.entrenamiento_completo.path_resultado",
                            "Path Resultados",
                            entrenamiento.get("path_resultado", ""),
                            config,
                        )
                        render_field_widget(
                            "decision.entrenamiento_completo.num_epocas",
                            "Número Épocas",
                            entrenamiento.get("num_epocas", 35),
                            config,
                        )
                        render_field_widget(
                            "decision.entrenamiento_completo.batch_size",
                            "Batch Size",
                            entrenamiento.get("batch_size", 256),
                            config,
                        )

                    with col2:
                        render_field_widget(
                            "decision.entrenamiento_completo.steps",
                            "Steps",
                            entrenamiento.get("steps", 10),
                            config,
                        )
                        render_field_widget(
                            "decision.entrenamiento_completo.memory",
                            "Memory",
                            entrenamiento.get("memory", 5000),
                            config,
                        )
                        render_field_widget(
                            "decision.entrenamiento_completo.learning_rate",
                            "Learning Rate",
                            entrenamiento.get("learning_rate", 0.0005),
                            config,
                        )
                        render_field_widget(
                            "decision.entrenamiento_completo.learning_rate_decay",
                            "LR Decay",
                            entrenamiento.get("learning_rate_decay", 0.99),
                            config,
                        )

                    with col3:
                        render_field_widget(
                            "decision.entrenamiento_completo.learning_rate_min",
                            "LR Mínimo",
                            entrenamiento.get("learning_rate_min", 0.00005),
                            config,
                        )
                        render_field_widget(
                            "decision.entrenamiento_completo.epsilon",
                            "Epsilon",
                            entrenamiento.get("epsilon", 1.0),
                            config,
                        )
                        render_field_widget(
                            "decision.entrenamiento_completo.epsilon_decay",
                            "Epsilon Decay",
                            entrenamiento.get("epsilon_decay", 0.99995),
                            config,
                        )
                        render_field_widget(
                            "decision.entrenamiento_completo.epsilon_min",
                            "Epsilon Mín",
                            entrenamiento.get("epsilon_min", 0.1),
                            config,
                        )

                    st.markdown("**Parámetros Avanzados**")
                    col1, col2, col3 = st.columns(3)

                    with col1:
                        render_field_widget(
                            "decision.entrenamiento_completo.gamma",
                            "Gamma",
                            entrenamiento.get("gamma", 0.85),
                            config,
                        )
                        render_field_widget(
                            "decision.entrenamiento_completo.hidden_layers",
                            "Capas Ocultas",
                            entrenamiento.get("hidden_layers", [64, 64, 64]),
                            config,
                        )
                        render_field_widget(
                            "decision.entrenamiento_completo.use_double_dqn",
                            "Double DQN",
                            entrenamiento.get("use_double_dqn", True),
                            config,
                        )
                        render_field_widget(
                            "decision.entrenamiento_completo.use_dueling_dqn",
                            "Dueling DQN",
                            entrenamiento.get("use_dueling_dqn", True),
                            config,
                        )

                    with col2:
                        render_field_widget(
                            "decision.entrenamiento_completo.target_update_frequency",
                            "Target Update Freq",
                            entrenamiento.get("target_update_frequency", 100),
                            config,
                        )
                        render_field_widget(
                            "decision.entrenamiento_completo.use_prioritized_replay",
                            "Prioritized Replay",
                            entrenamiento.get("use_prioritized_replay", True),
                            config,
                        )
                        render_field_widget(
                            "decision.entrenamiento_completo.per_alpha",
                            "PER Alpha",
                            entrenamiento.get("per_alpha", 0.6),
                            config,
                        )
                        render_field_widget(
                            "decision.entrenamiento_completo.per_beta_start",
                            "PER Beta Start",
                            entrenamiento.get("per_beta_start", 0.4),
                            config,
                        )

                    with col3:
                        render_field_widget(
                            "decision.entrenamiento_completo.use_noisy_networks",
                            "Noisy Networks",
                            entrenamiento.get("use_noisy_networks", True),
                            config,
                        )
                        render_field_widget(
                            "decision.entrenamiento_completo.noise_std",
                            "Noise STD",
                            entrenamiento.get("noise_std", 0.3),
                            config,
                        )
                        render_field_widget(
                            "decision.entrenamiento_completo.use_dropout",
                            "Dropout",
                            entrenamiento.get("use_dropout", True),
                            config,
                        )
                        render_field_widget(
                            "decision.entrenamiento_completo.dropout_rate",
                            "Dropout Rate",
                            entrenamiento.get("dropout_rate", 0.02),
                            config,
                        )

                    with st.expander("Optimizaciones de Estabilidad", expanded=False):
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            render_field_widget(
                                "decision.entrenamiento_completo.warmup_steps",
                                "Warmup Steps",
                                entrenamiento.get("warmup_steps", 250),
                                config,
                            )
                            render_field_widget(
                                "decision.entrenamiento_completo.min_replay_size",
                                "Min Replay Size",
                                entrenamiento.get("min_replay_size", 32),
                                config,
                            )
                            render_field_widget(
                                "decision.entrenamiento_completo.use_batch_normalization",
                                "Batch Normalization",
                                entrenamiento.get("use_batch_normalization", True),
                                config,
                            )
                            render_field_widget(
                                "decision.entrenamiento_completo.use_he_initialization",
                                "He Initialization",
                                entrenamiento.get("use_he_initialization", True),
                                config,
                            )

                        with col2:
                            render_field_widget(
                                "decision.entrenamiento_completo.use_residual_connections",
                                "Residual Connections",
                                entrenamiento.get("use_residual_connections", True),
                                config,
                            )
                            render_field_widget(
                                "decision.entrenamiento_completo.gradient_clip_norm",
                                "Gradient Clip Norm",
                                entrenamiento.get("gradient_clip_norm", 1.0),
                                config,
                            )
                            render_field_widget(
                                "decision.entrenamiento_completo.use_leaky_relu",
                                "Leaky ReLU",
                                entrenamiento.get("use_leaky_relu", True),
                                config,
                            )
                            render_field_widget(
                                "decision.entrenamiento_completo.use_gradient_clipping",
                                "Gradient Clipping",
                                entrenamiento.get("use_gradient_clipping", True),
                                config,
                            )

                        with col3:
                            render_field_widget(
                                "decision.entrenamiento_completo.use_huber_loss",
                                "Huber Loss",
                                entrenamiento.get("use_huber_loss", True),
                                config,
                            )
                            render_field_widget(
                                "decision.entrenamiento_completo.normalize_rewards",
                                "Normalize Rewards",
                                entrenamiento.get("normalize_rewards", True),
                                config,
                            )
                            render_field_widget(
                                "decision.entrenamiento_completo.per_beta_frames",
                                "PER Beta Frames",
                                entrenamiento.get("per_beta_frames", 100000),
                                config,
                            )
                            render_field_widget(
                                "decision.entrenamiento_completo.adaptive_lr",
                                "Adaptive LR",
                                entrenamiento.get("adaptive_lr", True),
                                config,
                            )

                    with st.expander("Evaluación y Métricas", expanded=False):
                        col1, col2 = st.columns(2)
                        with col1:
                            render_field_widget(
                                "decision.entrenamiento_completo.enable_evaluation",
                                "Activar Evaluación",
                                entrenamiento.get("enable_evaluation", True),
                                config,
                            )
                            render_field_widget(
                                "decision.entrenamiento_completo.evaluation_episodes",
                                "Episodios Evaluación",
                                entrenamiento.get("evaluation_episodes", 10),
                                config,
                            )
                            render_field_widget(
                                "decision.entrenamiento_completo.evaluation_frequency",
                                "Frecuencia Evaluación",
                                entrenamiento.get("evaluation_frequency", 10),
                                config,
                            )
                            render_field_widget(
                                "decision.entrenamiento_completo.baseline_comparison",
                                "Comparación Baseline",
                                entrenamiento.get("baseline_comparison", True),
                                config,
                            )

                        with col2:
                            render_field_widget(
                                "decision.entrenamiento_completo.save_evaluation_data",
                                "Guardar Datos Evaluación",
                                entrenamiento.get("save_evaluation_data", True),
                                config,
                            )
                            render_field_widget(
                                "decision.entrenamiento_completo.metrics_window_size",
                                "Ventana Métricas",
                                entrenamiento.get("metrics_window_size", 100),
                                config,
                            )
                            render_field_widget(
                                "decision.entrenamiento_completo.statistical_tests",
                                "Tests Estadísticos",
                                entrenamiento.get("statistical_tests", True),
                                config,
                            )
                            render_field_widget(
                                "decision.entrenamiento_completo.generate_plots",
                                "Generar Gráficos",
                                entrenamiento.get("generate_plots", True),
                                config,
                            )

                    with st.expander("Optimizaciones de Rendimiento", expanded=False):
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            render_field_widget(
                                "decision.entrenamiento_completo.lr_schedule_type",
                                "Tipo Schedule LR",
                                entrenamiento.get("lr_schedule_type", "plateau"),
                                config,
                            )
                            render_field_widget(
                                "decision.entrenamiento_completo.enable_jit_compilation",
                                "JIT Compilation",
                                entrenamiento.get("enable_jit_compilation", True),
                                config,
                            )
                            render_field_widget(
                                "decision.entrenamiento_completo.dropout_mode",
                                "Modo Dropout",
                                entrenamiento.get("dropout_mode", "optimized"),
                                config,
                            )
                            render_field_widget(
                                "decision.entrenamiento_completo.dropout_layers",
                                "Layers Dropout",
                                entrenamiento.get("dropout_layers", "strategic"),
                                config,
                            )

                        with col2:
                            render_field_widget(
                                "decision.entrenamiento_completo.noisy_implementation",
                                "Implementación Noisy",
                                entrenamiento.get("noisy_implementation", "efficient"),
                                config,
                            )
                            render_field_widget(
                                "decision.entrenamiento_completo.double_dqn_batch_optimization",
                                "Double DQN Batch Opt",
                                entrenamiento.get(
                                    "double_dqn_batch_optimization", False
                                ),
                                config,
                            )
                            render_field_widget(
                                "decision.entrenamiento_completo.target_update_batch_size",
                                "Target Update Batch Size",
                                entrenamiento.get("target_update_batch_size", 1024),
                                config,
                            )
                            render_field_widget(
                                "decision.entrenamiento_completo.per_batch_processing",
                                "PER Batch Processing",
                                entrenamiento.get("per_batch_processing", False),
                                config,
                            )

                        with col3:
                            render_field_widget(
                                "decision.entrenamiento_completo.per_update_frequency",
                                "PER Update Frequency",
                                entrenamiento.get("per_update_frequency", 4),
                                config,
                            )
                            render_field_widget(
                                "decision.entrenamiento_completo.per_importance_annealing",
                                "PER Importance Annealing",
                                entrenamiento.get("per_importance_annealing", False),
                                config,
                            )
                            render_field_widget(
                                "decision.entrenamiento_completo.dueling_stream_simplification",
                                "Dueling Stream Simplification",
                                entrenamiento.get(
                                    "dueling_stream_simplification", False
                                ),
                                config,
                            )
                            render_field_widget(
                                "decision.entrenamiento_completo.hidden_layers_optimization",
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
                render_field_widget(
                    "sumo.path_mapa",
                    "Path Mapa",
                    sumo.get("path_mapa", "assets/sumo_maps/MapaDe0/mapa.sumocfg"),
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

            st.markdown("---")
            st.subheader("Exportación de Comparaciones")
            if "comparacion_export" in sumo:
                comparacion = sumo["comparacion_export"]
                col1, col2 = st.columns(2)
                with col1:
                    render_field_widget(
                        "sumo.comparacion_export.enabled",
                        "Exportar Comparaciones a SQLite",
                        comparacion.get("enabled", False),
                        config,
                    )
                with col2:
                    render_field_widget(
                        "sumo.comparacion_export.db_path",
                        "Ruta Base de Datos",
                        comparacion.get("db_path", "results/comparacion_metrics.db"),
                        config,
                    )

    with st.expander("📊 Reportes", expanded=False):
        if "reporte" in config:
            reporte = config["reporte"]
            col1, col2 = st.columns(2)

            with col1:
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
                    "reporte.db_path_base",
                    "Path Base DB",
                    reporte.get("db_path_base", "results/reportes/db"),
                    config,
                )
                render_field_widget(
                    "reporte.steps",
                    "Steps por Reporte",
                    reporte.get("steps", 60),
                    config,
                )
            with col2:
                render_field_widget(
                    "reporte.total_vehiculos_maximo",
                    "Vehículos Totales Máx",
                    reporte.get("total_vehiculos_maximo", 50),
                    config,
                )
                render_field_widget(
                    "reporte.zona_vehiculos_maximo",
                    "Vehículos Zona Máx",
                    reporte.get("zona_vehiculos_maximo", 200),
                    config,
                )
                render_field_widget(
                    "reporte.path_reporte",
                    "Path Reportes",
                    reporte.get("path_reporte", "results/reportes"),
                    config,
                )


def render_database_page() -> None:
    """Renderizar página de visualización de alertas de congestión."""
    st.title("⚠️ Alertas de Congestión")

    if st.button(
        "🔄 Refrescar Datos",
        help="Actualizar lista de archivos de alertas",
        key="refresh_alerts",
    ):
        # Limpiar cache si existe
        if "last_alerts_refresh" in st.session_state:
            del st.session_state["last_alerts_refresh"]
        st.session_state["last_alerts_refresh"] = datetime.datetime.now().strftime(
            "%H:%M:%S"
        )
        st.rerun()

    last_refresh = st.session_state.get("last_alerts_refresh", "Nunca")
    st.caption(f"🕒 Última actualización: {last_refresh}")

    try:
        # Buscar archivos de base de datos
        db_pattern = "results/reportes/*/reporte.db"
        db_files = glob.glob(db_pattern)

        # Ordenar por fecha de modificación (más reciente primero)
        if db_files:
            db_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)

        # Mostrar información de archivos encontrados
        if not db_files:
            st.warning("⚠️ No se encontraron registros de alertas de congestión")
            st.info(f"📁 Buscando en: `{db_pattern}`")
            st.info(
                "💡 Ejecuta el servicio de reportes para generar datos cuando se superen umbrales"
            )
            return

        # Selección de archivo de DB
        st.sidebar.markdown("---")
        st.sidebar.subheader("📊 Seleccionar Sesión")

        # Crear nombres amigables para los archivos
        db_names = []
        for db_file in db_files:
            # Extraer el nombre del directorio padre (timestamp del reporte)
            parent_dir = os.path.basename(os.path.dirname(db_file))

            # Intentar parsear la fecha del nombre del directorio para formato más amigable
            try:
                # El formato típico es report_YYYY-MM-DD_HH-MM-SS
                if parent_dir.startswith("report_"):
                    date_part = parent_dir.replace("report_", "")
                    # Reemplazar guiones por formato más legible
                    formatted_date = (
                        date_part.replace("_", " ")
                        .replace("-", "/", 2)
                        .replace("-", ":")
                    )
                    db_names.append(f"📅 {formatted_date}")
                else:
                    db_names.append(f"📁 {parent_dir}")
            except Exception:
                # Si no se puede parsear, usar el nombre original
                db_names.append(f"📁 {parent_dir}")

        selected_idx = st.sidebar.selectbox(
            "Sesión de alertas:",
            range(len(db_files)),
            format_func=lambda x: f"🆕 {db_names[x]}" if x == 0 else db_names[x],
            help="Ordenadas por fecha: la más reciente aparece primero",
        )

        selected_db = db_files[selected_idx]
        st.sidebar.info(f"📄 Archivo: `{os.path.basename(selected_db)}`")

        # Mostrar información adicional de la sesión seleccionada
        try:
            file_time = os.path.getmtime(selected_db)
            formatted_time = datetime.datetime.fromtimestamp(file_time).strftime(
                "%d/%m/%Y %H:%M:%S"
            )
            st.sidebar.caption(f"🕒 Última modificación: {formatted_time}")

        except Exception:
            pass

        # Conectar a la base de datos
        try:
            conn = sqlite3.connect(selected_db)

            # Obtener información básica de la tabla
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM reporte")
            total_records = cursor.fetchone()[0]

            cursor.execute(
                "SELECT MIN(step_simulacion), MAX(step_simulacion) FROM reporte"
            )
            min_step, max_step = cursor.fetchone()

            # Mostrar estadísticas básicas
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("⚠️ Total Alertas", total_records)
            with col2:
                st.metric("⏮️ Step Mínimo", min_step if min_step else 0)
            with col3:
                st.metric("⏭️ Step Máximo", max_step if max_step else 0)

            st.markdown("---")

            # Opciones de visualización
            st.subheader("🔍 Opciones de Visualización")

            col1, col2 = st.columns(2)

            with col1:
                # Filtro por rango de steps
                use_step_filter = st.checkbox("📈 Filtrar por rango de steps")
                if use_step_filter and min_step is not None and max_step is not None:
                    step_range = st.slider(
                        "Rango de steps:",
                        min_value=int(min_step),
                        max_value=int(max_step),
                        value=(int(min_step), int(max_step)),
                        step=1,
                    )
                else:
                    step_range = None

            with col2:
                # Límite de registros
                limit_records = st.number_input(
                    "📝 Límite de registros a mostrar:",
                    min_value=10,
                    max_value=10000,
                    value=500,
                    step=50,
                )

                # Orden de resultados
                order_desc = st.checkbox("📅 Más recientes primero", value=True)

            # Construir consulta SQL
            query = "SELECT * FROM reporte"
            params = []

            if use_step_filter and step_range:
                query += " WHERE step_simulacion BETWEEN ? AND ?"
                params.extend([step_range[0], step_range[1]])

            query += f" ORDER BY step_simulacion {'DESC' if order_desc else 'ASC'}"
            query += f" LIMIT {limit_records}"

            # Cargar datos
            with st.spinner("📊 Cargando datos..."):
                df = pd.read_sql_query(query, conn, params=params)

            if df.empty:
                st.warning("⚠️ No se encontraron datos con los filtros aplicados")
                return

            # Mostrar tabla de datos
            st.subheader(f"⚠️ Alertas de Congestión ({len(df)} registros)")

            st.info(
                "💡 Estos datos representan momentos donde se superaron umbrales críticos de tiempo de espera o cantidad de vehículos"
            )

            # Configurar columnas para mejor visualización
            display_df = df.copy()

            # Renombrar columnas para mejor legibilidad
            column_mapping = {
                "step_simulacion": "Step",
                "estado_simulacion": "Estado",
                "timestamp_simulacion": "Timestamp",
                "total_tiempo_espera": "Tiempo Espera Total",
                "total_vehiculos": "Vehículos Total",
                "generado_en": "Generado En",
            }

            # Agregar columnas de zonas más legibles
            for zone in ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l"]:
                column_mapping[f"zona_{zone}_tiempo_espera"] = (
                    f"Zona {zone.upper()} - Tiempo"
                )
                column_mapping[f"zona_{zone}_vehiculos"] = (
                    f"Zona {zone.upper()} - Vehículos"
                )
                column_mapping[
                    f'estado_semaforo_{["1", "2", "3", "4"][ord(zone) - ord("a")] if ord(zone) - ord("a") < 4 else "1"}'
                ] = f'Semáforo {["1", "2", "3", "4"][ord(zone) - ord("a")] if ord(zone) - ord("a") < 4 else "1"}'

            # Aplicar renombrado solo a columnas que existen
            existing_mapping = {
                k: v for k, v in column_mapping.items() if k in display_df.columns
            }
            display_df = display_df.rename(columns=existing_mapping)

            # Mostrar tabla interactiva
            st.dataframe(display_df, use_container_width=True, height=400)

            # Gráficos de análisis
            st.markdown("---")
            st.subheader("📈 Análisis Visual")

            tab1, tab2 = st.tabs(["🕐 Tiempos de Espera", "🚗 Cantidad de Vehículos"])

            with tab1:
                st.subheader("⏱️ Evolución de Tiempos de Espera")

                if (
                    "Tiempo Espera Total" in display_df.columns
                    and "Step" in display_df.columns
                ):
                    # Gráfico de tiempo total
                    chart_data = display_df.set_index("Step")["Tiempo Espera Total"]
                    st.line_chart(chart_data)

                    # Gráfico por zonas (primeras 6 zonas para no saturar)
                    zone_columns = [
                        col
                        for col in display_df.columns
                        if "Zona" in col and "Tiempo" in col
                    ][:6]
                    if zone_columns:
                        st.subheader("🗺️ Tiempos de Espera por Zona (A-F)")
                        zone_data = display_df.set_index("Step")[zone_columns]
                        st.line_chart(zone_data)

            with tab2:
                st.subheader("🚗 Evolución de Cantidad de Vehículos")

                if (
                    "Vehículos Total" in display_df.columns
                    and "Step" in display_df.columns
                ):
                    # Gráfico de vehículos total
                    chart_data = display_df.set_index("Step")["Vehículos Total"]
                    st.line_chart(chart_data)

                    # Gráfico por zonas (primeras 6 zonas)
                    vehicle_columns = [
                        col
                        for col in display_df.columns
                        if "Zona" in col and "Vehículos" in col
                    ][:6]
                    if vehicle_columns:
                        st.subheader("🗺️ Vehículos por Zona (A-F)")
                        vehicle_data = display_df.set_index("Step")[vehicle_columns]
                        st.line_chart(vehicle_data)

            # Opción de descarga
            st.markdown("---")
            st.subheader("💾 Exportar Alertas")

            col1, col2 = st.columns(2)

            with col1:
                # Descargar CSV
                csv_data = df.to_csv(index=False)
                st.download_button(
                    label="📥 Descargar alertas como CSV",
                    data=csv_data,
                    file_name=f"alertas_congestion_{db_names[selected_idx]}.csv",
                    mime="text/csv",
                )

            with col2:
                # Información del archivo
                st.info(f"📍 Ubicación: `{selected_db}`")
                file_size = os.path.getsize(selected_db)
                st.caption(f"💿 Tamaño: {file_size / 1024:.1f} KB")

            conn.close()

        except sqlite3.Error as e:
            st.error(f"❌ Error conectando a la base de datos: {e}")
        except Exception as e:
            st.error(f"❌ Error procesando datos: {e}")

    except Exception as e:
        st.error(f"❌ Error en página de base de datos: {e}")
        log_error(f"Error en render_database_page: {e}")


def render_comparisons_page() -> None:
    """Renderizar página de visualización de comparaciones S1 vs S2."""
    st.title("📊 Comparaciones S1 vs S2")

    # Botón de refresco para actualizar datos
    if st.button(
        "🔄 Refrescar Datos",
        help="Actualizar lista de comparaciones disponibles",
        key="refresh_comparisons",
    ):
        # Limpiar cache si existe
        if "last_comparisons_refresh" in st.session_state:
            del st.session_state["last_comparisons_refresh"]
        st.session_state["last_comparisons_refresh"] = datetime.datetime.now().strftime(
            "%H:%M:%S"
        )
        st.rerun()

    last_refresh = st.session_state.get("last_comparisons_refresh", "Nunca")
    st.caption(f"🕒 Última actualización: {last_refresh}")

    try:
        # Buscar bases de datos de comparaciones (patrón similar a reportes)
        db_pattern = "results/comparisons/*/comparison.db"
        db_files = glob.glob(db_pattern)

        # Mostrar información de archivos encontrados
        if db_files:
            # Ordenar por fecha de modificación (más nueva primero)
            db_files.sort(key=os.path.getmtime, reverse=True)
        else:
            st.warning(
                "📭 No se encontraron bases de datos de comparaciones.\n\n"
                "Para generar datos:\n"
                "1. Activar `sumo.comparacion_export.enabled` en Configuración\n"
                "2. Ejecutar una simulación con `sumo.comparar=True`\n"
                "3. Cada simulación creará su propio directorio: `results/comparisons/comparison_YYYY-MM-DD_HH-MM-SS/`"
            )
            return

        # Sidebar para selección de base de datos
        st.sidebar.markdown("---")
        st.sidebar.markdown("### 📊 Sesión de Comparaciones")

        db_names = []
        for db_file in db_files:
            try:
                parent_dir = os.path.basename(os.path.dirname(db_file))
                # El formato típico es comparison_YYYY-MM-DD_HH-MM-SS
                if parent_dir.startswith("comparison_"):
                    date_part = parent_dir.replace("comparison_", "")
                    try:
                        # Intentar parsear el timestamp del nombre del directorio
                        parsed_time = datetime.datetime.strptime(
                            date_part, "%Y-%m-%d_%H-%M-%S"
                        )
                        formatted_time = parsed_time.strftime("%d/%m %H:%M")
                        db_names.append(f"{formatted_time} - {parent_dir}")
                    except ValueError:
                        # Si no se puede parsear, usar fecha de archivo
                        file_time = os.path.getmtime(db_file)
                        formatted_time = datetime.datetime.fromtimestamp(
                            file_time
                        ).strftime("%d/%m %H:%M")
                        db_names.append(f"{formatted_time} - {parent_dir}")
                else:
                    # Para directorios que no siguen el patrón
                    file_time = os.path.getmtime(db_file)
                    formatted_time = datetime.datetime.fromtimestamp(
                        file_time
                    ).strftime("%d/%m %H:%M")
                    db_names.append(f"{formatted_time} - {parent_dir}")
            except Exception:
                # Si no se puede parsear, usar el nombre original
                parent_dir = os.path.basename(os.path.dirname(db_file))
                db_names.append(f"📁 {parent_dir}")

        selected_idx = st.sidebar.selectbox(
            "Sesión de comparaciones:",
            range(len(db_files)),
            format_func=lambda x: f"🆕 {db_names[x]}" if x == 0 else db_names[x],
            help="Ordenadas por fecha: la más reciente aparece primero",
        )

        selected_db = db_files[selected_idx]
        st.sidebar.info(f"📄 Archivo: `{os.path.basename(selected_db)}`")

        # Mostrar información adicional de la sesión seleccionada
        try:
            file_time = os.path.getmtime(selected_db)
            formatted_time = datetime.datetime.fromtimestamp(file_time).strftime(
                "%d/%m/%Y %H:%M:%S"
            )
            st.sidebar.caption(f"🕒 Última modificación: {formatted_time}")
        except Exception:
            pass

        # Conectar a la base de datos y mostrar contenido
        conn = sqlite3.connect(selected_db)

        # Verificar qué tablas existen
        tables_query = "SELECT name FROM sqlite_master WHERE type='table';"
        tables_df = pd.read_sql_query(tables_query, conn)

        if tables_df.empty:
            st.warning("📭 No se encontraron tablas en la base de datos seleccionada")
            conn.close()
            return

        # Solo métricas temporales - eliminamos pestañas innecesarias
        if "comparacion_metricas" in tables_df["name"].values:
            metrics_df = pd.read_sql_query(
                "SELECT * FROM comparacion_metricas ORDER BY timestamp_simulacion", conn
            )

            if not metrics_df.empty:
                # Convertir timestamp_simulacion a datetime para gráficas
                metrics_df["datetime"] = pd.to_datetime(
                    metrics_df["timestamp_simulacion"], unit="s"
                )

                # Selector de sesión
                if "session_id" in metrics_df.columns:
                    sessions = metrics_df["session_id"].unique()
                    if len(sessions) > 1:
                        selected_session = st.selectbox(
                            "🎯 Seleccionar Sesión de Simulación:",
                            sessions,
                            help="Cada sesión representa una ejecución completa de simulación",
                        )
                        metrics_df = metrics_df[
                            metrics_df["session_id"] == selected_session
                        ]

                # Gráfico de tiempo de espera - PANTALLA COMPLETA
                st.markdown("#### ⏱️ Tiempo de Espera Promedio")
                if (
                    "s1_tiempo_actual" in metrics_df.columns
                    and "s2_tiempo_actual" in metrics_df.columns
                ):
                    fig_wait = create_comparison_chart(
                        metrics_df,
                        "s1_tiempo_actual",
                        "s2_tiempo_actual",
                        "S1 (DQN)",
                        "S2 (Fijo)",
                        "Tiempo de Espera (s)",
                    )
                    st.plotly_chart(fig_wait, use_container_width=True, height=500)

                # Gráfico de vehículos - PANTALLA COMPLETA
                st.markdown("#### � Número de Vehículos Esperando")
                if (
                    "s1_vehiculos_actual" in metrics_df.columns
                    and "s2_vehiculos_actual" in metrics_df.columns
                ):
                    fig_stops = create_comparison_chart(
                        metrics_df,
                        "s1_vehiculos_actual",
                        "s2_vehiculos_actual",
                        "S1 (DQN)",
                        "S2 (Fijo)",
                        "Número de Vehículos",
                    )
                    st.plotly_chart(fig_stops, use_container_width=True, height=500)

                    # Métricas adicionales si existen
                    if "s1_tiempo_promedio" in metrics_df.columns:
                        st.markdown("#### 📊 Tiempo de Espera Acumulado")
                        fig_speed = create_comparison_chart(
                            metrics_df,
                            "s1_tiempo_acumulado",
                            "s2_tiempo_acumulado",
                            "S1 (DQN)",
                            "S2 (Fijo)",
                            "Tiempo Acumulado (s)",
                        )
                        st.plotly_chart(fig_speed, use_container_width=True)

                # Organizar estadísticas en tablas claras por métrica
                st.markdown("---")

                # Obtener la última fila para estadísticas
                latest_metrics = metrics_df.iloc[-1] if not metrics_df.empty else None

                if latest_metrics is not None:
                    # TABLA 1: TIEMPO DE ESPERA
                    st.markdown("### ⏱️ Estadísticas de Tiempo de Espera")

                    # Obtener valores para calcular porcentajes
                    s1_tiempo_promedio = latest_metrics.get("s1_tiempo_promedio", 0)
                    s2_tiempo_promedio = latest_metrics.get("s2_tiempo_promedio", 0)
                    s1_tiempo_mediana = latest_metrics.get("s1_tiempo_mediana", 0)
                    s2_tiempo_mediana = latest_metrics.get("s2_tiempo_mediana", 0)
                    s1_tiempo_p95 = latest_metrics.get("s1_tiempo_p95", 0)
                    s2_tiempo_p95 = latest_metrics.get("s2_tiempo_p95", 0)
                    s1_tiempo_std = latest_metrics.get("s1_tiempo_std", 0)
                    s2_tiempo_std = latest_metrics.get("s2_tiempo_std", 0)

                    # Calcular porcentajes de mejora (valores positivos = mejora para DQN)
                    def calcular_mejora_porcentual(s1_val: float, s2_val: float) -> str:
                        """Calcular porcentaje de mejora de S1 respecto a S2."""
                        if s2_val == 0:
                            return "N/A"
                        mejora = ((s2_val - s1_val) / s2_val) * 100
                        return f"{mejora:+.1f}%"

                    tiempo_stats = {
                        "Métrica Estadística": [
                            "Promedio (Media)",
                            "Experiencia Típica (Mediana)",
                            "Peor de los Casos (P95)",
                            "Consistencia (Desv. Estándar)",
                        ],
                        "🤖 S1 (DQN)": [
                            f"{s1_tiempo_promedio:.1f} s",
                            f"{s1_tiempo_mediana:.1f} s",
                            f"{s1_tiempo_p95:.1f} s",
                            f"{s1_tiempo_std:.1f} s",
                        ],
                        "⏰ S2 (Tiempos Fijos)": [
                            f"{s2_tiempo_promedio:.1f} s",
                            f"{s2_tiempo_mediana:.1f} s",
                            f"{s2_tiempo_p95:.1f} s",
                            f"{s2_tiempo_std:.1f} s",
                        ],
                        "📈 Diferencia (S1 - S2)": [
                            f"{s1_tiempo_promedio - s2_tiempo_promedio:+.1f} s",
                            f"{s1_tiempo_mediana - s2_tiempo_mediana:+.1f} s",
                            f"{s1_tiempo_p95 - s2_tiempo_p95:+.1f} s",
                            f"{s1_tiempo_std - s2_tiempo_std:+.1f} s",
                        ],
                        "📊 % Mejora": [
                            calcular_mejora_porcentual(
                                s1_tiempo_promedio, s2_tiempo_promedio
                            ),
                            calcular_mejora_porcentual(
                                s1_tiempo_mediana, s2_tiempo_mediana
                            ),
                            calcular_mejora_porcentual(s1_tiempo_p95, s2_tiempo_p95),
                            calcular_mejora_porcentual(s1_tiempo_std, s2_tiempo_std),
                        ],
                    }

                    tiempo_df = pd.DataFrame(tiempo_stats)
                    st.dataframe(tiempo_df, use_container_width=True, hide_index=True)

                    # TABLA 2: CANTIDAD DE VEHÍCULOS
                    st.markdown("### 🚗 Estadísticas de Cantidad de Vehículos")

                    # Obtener valores para calcular porcentajes
                    s1_vehiculos_promedio = latest_metrics.get(
                        "s1_vehiculos_promedio", 0
                    )
                    s2_vehiculos_promedio = latest_metrics.get(
                        "s2_vehiculos_promedio", 0
                    )
                    s1_vehiculos_mediana = latest_metrics.get("s1_vehiculos_mediana", 0)
                    s2_vehiculos_mediana = latest_metrics.get("s2_vehiculos_mediana", 0)
                    s1_vehiculos_p95 = latest_metrics.get("s1_vehiculos_p95", 0)
                    s2_vehiculos_p95 = latest_metrics.get("s2_vehiculos_p95", 0)
                    s1_vehiculos_std = latest_metrics.get("s1_vehiculos_std", 0)
                    s2_vehiculos_std = latest_metrics.get("s2_vehiculos_std", 0)

                    vehiculos_stats = {
                        "Métrica Estadística": [
                            "Promedio (Media)",
                            "Experiencia Típica (Mediana)",
                            "Peor de los Casos (P95)",
                            "Consistencia (Desv. Estándar)",
                        ],
                        "🤖 S1 (DQN)": [
                            f"{s1_vehiculos_promedio:.1f}",
                            f"{s1_vehiculos_mediana:.1f}",
                            f"{s1_vehiculos_p95:.1f}",
                            f"{s1_vehiculos_std:.1f}",
                        ],
                        "⏰ S2 (Tiempos Fijos)": [
                            f"{s2_vehiculos_promedio:.1f}",
                            f"{s2_vehiculos_mediana:.1f}",
                            f"{s2_vehiculos_p95:.1f}",
                            f"{s2_vehiculos_std:.1f}",
                        ],
                        "📈 Diferencia (S1 - S2)": [
                            f"{s1_vehiculos_promedio - s2_vehiculos_promedio:+.1f}",
                            f"{s1_vehiculos_mediana - s2_vehiculos_mediana:+.1f}",
                            f"{s1_vehiculos_p95 - s2_vehiculos_p95:+.1f}",
                            f"{s1_vehiculos_std - s2_vehiculos_std:+.1f}",
                        ],
                        "📊 % Mejora": [
                            calcular_mejora_porcentual(
                                s1_vehiculos_promedio, s2_vehiculos_promedio
                            ),
                            calcular_mejora_porcentual(
                                s1_vehiculos_mediana, s2_vehiculos_mediana
                            ),
                            calcular_mejora_porcentual(
                                s1_vehiculos_p95, s2_vehiculos_p95
                            ),
                            calcular_mejora_porcentual(
                                s1_vehiculos_std, s2_vehiculos_std
                            ),
                        ],
                    }

                    vehiculos_df = pd.DataFrame(vehiculos_stats)
                    st.dataframe(
                        vehiculos_df, use_container_width=True, hide_index=True
                    )

                    # Interpretación de las estadísticas
                    st.markdown("### 💡 ¿Qué significan estas métricas?")

                    st.markdown(
                        """
                    **📊 Estadísticas:**
                    - **Promedio**: Valor típico esperado
                    - **Mediana**: 50% de casos están por debajo
                    - **P95**: Solo el 5% de casos superan este valor
                    - **Desv. Estándar**: Qué tan variable es el sistema (menor = más predecible)
                    """
                    )

            else:
                st.info("📭 No hay datos de métricas temporales disponibles")
        else:
            st.info("📭 Tabla 'comparacion_metricas' no encontrada")

        conn.close()

    except Exception as e:
        st.error(f"❌ Error al cargar comparaciones: {e}")
        log_error(f"Error en render_comparisons_page: {e}")


def create_comparison_table(summary_df: pd.DataFrame, metrics_df: pd.DataFrame) -> None:
    """Crear tabla comparativa clara con porcentajes de mejora."""
    if summary_df.empty:
        st.warning("📭 No hay datos de resumen para comparar")
        return

    if metrics_df.empty:
        st.warning("📭 No hay datos de métricas para comparar")
        return

    # Calcular promedios de las métricas temporales para la tabla
    s1_tiempo_promedio = metrics_df["s1_tiempo_actual"].mean()
    s2_tiempo_promedio = metrics_df["s2_tiempo_actual"].mean()
    s1_vehiculos_promedio = metrics_df["s1_vehiculos_actual"].mean()
    s2_vehiculos_promedio = metrics_df["s2_vehiculos_actual"].mean()

    # Estadísticas adicionales de las métricas temporales
    s1_tiempo_std = metrics_df["s1_tiempo_actual"].std()
    s2_tiempo_std = metrics_df["s2_tiempo_actual"].std()
    s1_tiempo_p95 = metrics_df["s1_tiempo_actual"].quantile(0.95)
    s2_tiempo_p95 = metrics_df["s2_tiempo_actual"].quantile(0.95)
    s1_tiempo_mediana = metrics_df["s1_tiempo_actual"].median()
    s2_tiempo_mediana = metrics_df["s2_tiempo_actual"].median()

    # Extraer datos para la tabla
    data_comparison = {
        "Métrica": [
            "⏱️ Tiempo Promedio (s)",
            "🚗 Congestión Promedio",
            "📊 Consistencia Tiempo (Desv.Est)",
            "📈 P95 Tiempo Espera (s)",
            "🎯 Mediana Tiempo (s)",
        ],
        "🤖 DQN": [
            f"{s1_tiempo_promedio:.1f}",
            f"{s1_vehiculos_promedio:.1f}",
            f"{s1_tiempo_std:.1f}",
            f"{s1_tiempo_p95:.1f}",
            f"{s1_tiempo_mediana:.1f}",
        ],
        "⏰ Tiempos Fijos": [
            f"{s2_tiempo_promedio:.1f}",
            f"{s2_vehiculos_promedio:.1f}",
            f"{s2_tiempo_std:.1f}",
            f"{s2_tiempo_p95:.1f}",
            f"{s2_tiempo_mediana:.1f}",
        ],
        "📈 Mejora (%)": [],
    }

    # Calcular mejoras y estados
    metricas_valores = [
        (s1_tiempo_promedio, s2_tiempo_promedio),
        (s1_vehiculos_promedio, s2_vehiculos_promedio),
        (s1_tiempo_std, s2_tiempo_std),  # Para desviación, menor es mejor
        (s1_tiempo_p95, s2_tiempo_p95),
        (s1_tiempo_mediana, s2_tiempo_mediana),
    ]

    for _, (s1_val, s2_val) in enumerate(metricas_valores):
        if s2_val > 0:
            mejora = ((s2_val - s1_val) / s2_val) * 100
            data_comparison["📈 Mejora (%)"].append(f"{mejora:+.1f}%")

        else:
            data_comparison["📈 Mejora (%)"].append("N/A")

    comparison_df = pd.DataFrame(data_comparison)

    st.markdown("### 📊 Tabla Comparativa Detallada")
    st.dataframe(comparison_df, use_container_width=True, hide_index=True)


def create_executive_summary(
    summary_df: pd.DataFrame, metrics_df: pd.DataFrame
) -> None:
    """Crear un resumen ejecutivo fácil de entender con los hallazgos principales."""
    st.markdown("## 🎯 Resumen Ejecutivo")

    if summary_df.empty or metrics_df.empty:
        st.warning("📭 No hay datos suficientes para el resumen ejecutivo")
        return

    # Obtener la última fila del resumen
    latest_summary = summary_df.iloc[-1]

    # Usar las columnas que realmente existen en la base de datos
    mejora_tiempo = latest_summary.get("mejora_tiempo_porcentual", 0)
    mejora_congestion = latest_summary.get("mejora_vehiculos_porcentual", 0)

    # Calcular promedios de las métricas temporales
    tiempo_s1 = metrics_df["s1_tiempo_actual"].mean()
    tiempo_s2 = metrics_df["s2_tiempo_actual"].mean()
    vehiculos_s1 = metrics_df["s1_vehiculos_actual"].mean()
    vehiculos_s2 = metrics_df["s2_vehiculos_actual"].mean()

    # Crear 3 columnas para métricas principales
    col1, col2, col3 = st.columns(3)

    with col1:
        if mejora_tiempo > 0:
            st.metric(
                label="⏱️ Reducción Tiempo de Espera",
                value=f"{mejora_tiempo:.1f}%",
                delta=f"{tiempo_s2 - tiempo_s1:.1f}s menos",
                delta_color="inverse",
            )
        else:
            st.metric(
                label="⏱️ Tiempo de Espera",
                value=f"{abs(mejora_tiempo):.1f}%",
                delta="Aumentó",
                delta_color="normal",
            )

    with col2:
        if mejora_congestion > 0:
            st.metric(
                label="🚗 Reducción Congestión",
                value=f"{mejora_congestion:.1f}%",
                delta=f"{vehiculos_s2 - vehiculos_s1:.1f} veh. menos",
                delta_color="inverse",
            )
        else:
            st.metric(
                label="🚗 Congestión",
                value=f"{abs(mejora_congestion):.1f}%",
                delta="Aumentó",
                delta_color="normal",
            )

    with col3:
        # Calcular puntuación general
        puntuacion = (mejora_tiempo + mejora_congestion) / 2
        if puntuacion > 50:
            emoji = "🟢"
            estado = "Excelente"
        elif puntuacion > 20:
            emoji = "🟡"
            estado = "Bueno"
        elif puntuacion > 0:
            emoji = "🟠"
            estado = "Regular"
        else:
            emoji = "🔴"
            estado = "Necesita mejoras"

        st.metric(
            label="📊 Rendimiento General",
            value=f"{emoji} {estado}",
            delta=f"Puntuación: {puntuacion:.1f}%",
        )

    # Detalles técnicos en expandible
    with st.expander("🔍 Ver detalles técnicos", expanded=True):
        col_det1, col_det2 = st.columns(2)

        with col_det1:
            st.markdown("**🤖 Sistema DQN (S1)**")
            st.write(f"• Tiempo promedio: {tiempo_s1:.1f}s")
            st.write(f"• Vehículos promedio: {vehiculos_s1:.1f}")

        with col_det2:
            st.markdown("**⏰ Tiempos Fijos (S2)**")
            st.write(f"• Tiempo promedio: {tiempo_s2:.1f}s")
            st.write(f"• Vehículos promedio: {vehiculos_s2:.1f}")

    # Añadir tabla comparativa detallada
    st.markdown("---")
    create_comparison_table(summary_df, metrics_df)


def create_comparison_chart(
    df: pd.DataFrame, col1: str, col2: str, name1: str, name2: str, y_title: str
) -> go.Figure:
    """Crear gráfica comparativa usando timestamp_simulacion real del sistema."""

    # Reducir ruido - tomar cada N puntos para gráficos más limpios
    step = max(1, len(df) // 50)  # Máximo 50 puntos en el gráfico
    if step > 1:
        df_sampled = df.iloc[::step].copy()
    else:
        df_sampled = df.copy()

    # Redondear valores para mayor claridad
    df_sampled[col1] = df_sampled[col1].round(1)
    df_sampled[col2] = df_sampled[col2].round(1)

    # Usar timestamp_simulacion real de la base de datos
    df_sampled = df_sampled.reset_index(drop=True)

    # Verificar si existe la columna timestamp_simulacion
    if "timestamp_simulacion" in df_sampled.columns:
        # Usar los valores reales de timestamp de la simulación (steps, no segundos)
        timestamps = df_sampled["timestamp_simulacion"].values
        df_sampled["time_real"] = timestamps
        x_axis_title = "Step de Simulación"
        time_unit = "step"
    else:
        # Fallback: usar índice como referencia
        df_sampled["time_real"] = range(len(df_sampled))
        x_axis_title = "Índice de Registro"
        time_unit = "idx"

    fig = go.Figure()

    # Usar colores más distinguibles y profesionales
    color1 = "#1f77b4"  # Azul para DQN
    color2 = "#ff7f0e"  # Naranja para tiempos fijos

    # Líneas principales SIN marcadores para mayor claridad
    fig.add_trace(
        go.Scatter(
            x=df_sampled["time_real"],  # Usar timestamp real
            y=df_sampled[col1],
            mode="lines",
            name=name1,
            line={"color": color1, "width": 4},
            hovertemplate=f"<b>{name1}</b><br>Valor: %{{y:.1f}}<br>Tiempo: %{{x}} {time_unit}<extra></extra>",
        )
    )

    fig.add_trace(
        go.Scatter(
            x=df_sampled["time_real"],  # Usar timestamp real
            y=df_sampled[col2],
            mode="lines",
            name=name2,
            line={"color": color2, "width": 4},
            hovertemplate=f"<b>{name2}</b><br>Valor: %{{y:.1f}}<br>Tiempo: %{{x}} {time_unit}<extra></extra>",
        )
    )

    # Agregar líneas de tendencia
    if len(df_sampled) > 2:  # Necesitamos al menos 3 puntos para una tendencia
        x_vals = df_sampled["time_real"].values

        # Calcular tendencia para serie 1 (DQN) usando regresión lineal
        y1_vals = df_sampled[col1].values
        coef1 = np.polyfit(x_vals, y1_vals, 1)  # Regresión lineal (grado 1)
        tendencia1 = np.poly1d(coef1)(x_vals)

        fig.add_trace(
            go.Scatter(
                x=x_vals,
                y=tendencia1,
                mode="lines",
                name=f"Tendencia {name1}",
                line={"color": color1, "width": 2, "dash": "dash"},
                opacity=0.7,
                hovertemplate=f"<b>Tendencia {name1}</b><br>Valor: %{{y:.1f}}<br>Tiempo: %{{x}} {time_unit}<extra></extra>",
            )
        )

        # Calcular tendencia para serie 2 (Tiempos Fijos)
        y2_vals = df_sampled[col2].values
        coef2 = np.polyfit(x_vals, y2_vals, 1)  # Regresión lineal (grado 1)
        tendencia2 = np.poly1d(coef2)(x_vals)

        fig.add_trace(
            go.Scatter(
                x=x_vals,
                y=tendencia2,
                mode="lines",
                name=f"Tendencia {name2}",
                line={"color": color2, "width": 2, "dash": "dash"},
                opacity=0.7,
                hovertemplate=f"<b>Tendencia {name2}</b><br>Valor: %{{y:.1f}}<br>Tiempo: %{{x}} {time_unit}<extra></extra>",
            )
        )  # Calcular mejora porcentual y análisis de tendencias para el título
    if len(df_sampled) > 0:
        avg1 = df_sampled[col1].mean()
        avg2 = df_sampled[col2].mean()

        if avg2 > 0:
            improvement = ((avg2 - avg1) / avg2) * 100
            if improvement > 5:
                improvement_text = f"DQN es {improvement:.1f}% mejor"
            elif improvement < -5:
                improvement_text = f"Tiempos Fijos son {abs(improvement):.1f}% mejores"
            else:
                improvement_text = f"Rendimiento similar ({improvement:.1f}%)"
        else:
            improvement_text = "Sin datos suficientes"

        # Agregar información de tendencia si hay suficientes datos
        if len(df_sampled) > 2:
            x_vals = df_sampled["time_real"].values
            y1_vals = df_sampled[col1].values
            y2_vals = df_sampled[col2].values

            # Calcular pendientes de las tendencias
            coef1 = np.polyfit(x_vals, y1_vals, 1)
            coef2 = np.polyfit(x_vals, y2_vals, 1)

            pendiente1 = coef1[0]  # Pendiente de DQN (por segundo de simulación)
            pendiente2 = coef2[
                0
            ]  # Pendiente de Tiempos Fijos (por segundo de simulación)

            # Determinar tendencias (umbral dinámico basado en rango de datos)
            rango_y1 = y1_vals.max() - y1_vals.min()
            rango_y2 = y2_vals.max() - y2_vals.min()
            rango_x = x_vals.max() - x_vals.min()

            # Umbral dinámico: 0.1% del rango Y por unidad de tiempo
            threshold1 = (rango_y1 * 0.001) / rango_x if rango_x > 0 else 0.001
            threshold2 = (rango_y2 * 0.001) / rango_x if rango_x > 0 else 0.001

            if abs(pendiente1) < threshold1 and abs(pendiente2) < threshold2:
                trend_info = " | Ambos estables"
            elif pendiente1 < -threshold1 and pendiente2 > threshold2:
                trend_info = " | DQN mejorando, Fijos empeorando"
            elif pendiente1 > threshold1 and pendiente2 < -threshold2:
                trend_info = " | DQN empeorando, Fijos mejorando"
            elif pendiente1 < pendiente2:
                trend_info = " | DQN con mejor tendencia"
            else:
                trend_info = " | Tendencias similares"

            improvement_text += trend_info
    else:
        improvement_text = "Sin datos"

    # Layout LIMPIO - sin anotaciones solapadas
    fig.update_layout(
        title={
            "text": f"{y_title}",
            "x": 0.5,
            "xanchor": "center",
            "font": {"size": 18, "color": "white"},
        },
        xaxis_title=x_axis_title,  # Título dinámico basado en datos disponibles
        yaxis_title=y_title,
        legend={
            "orientation": "h",
            "yanchor": "bottom",
            "y": 1.02,
            "xanchor": "center",
            "x": 0.5,
            "font": {"size": 14},
        },
        hovermode="x unified",
        height=500,  # Más alto para mejor visualización
        margin={"t": 100, "b": 60, "l": 80, "r": 60},
    )

    # Grid sutil
    fig.update_xaxes(showgrid=True, tickfont={"size": 12})
    fig.update_yaxes(showgrid=True, tickfont={"size": 12})

    return fig


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
        elif current_page == "database":
            render_database_page()
        elif current_page == "comparisons":
            render_comparisons_page()
        else:
            st.error("❌ Página no encontrada")

    except Exception as e:
        st.error(f"❌ Error en aplicación: {e}")
        log_error(f"Error en aplicación: {e}")


if __name__ == "__main__":
    main()
