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
        st.session_state.logs_refresh_interval = 4.0
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
        st.session_state.logs_refresh_interval = 4.0
    if "last_logs_update" not in st.session_state:
        st.session_state.last_logs_update = {}


def render_navigation() -> str:
    """Renderizar navegación simple con 2 opciones."""
    st.sidebar.title("🚦 SemaforIA")

    pages = {"🔧 Servicios": "services", "⚙️ Configuración": "config"}
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
                    # Verificar estado automáticamente después de la operación
                    auto_refresh_services_status()
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
                    # Verificar estado automáticamente después de la operación
                    auto_refresh_services_status()
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


# Diccionario de tooltips basado en comentarios del config.yaml
CONFIG_TOOLTIPS = {
    # Configuración global
    "base_url": "URL base del servidor Flask: dirección completa donde se expondrán las APIs REST (ej: http://localhost:5000)",
    "base_ip": "Dirección IP base: IP donde escucharán los servicios. 127.0.0.1 = solo local, 0.0.0.0 = todas las interfaces de red",
    # Servicios
    "services.simulation_port": "Puerto para API de simulación SUMO: donde se expone el control de la simulación de tráfico (típicamente 5000)",
    "services.detection_port": "Puerto para API de detección YOLO: donde se expone el servicio de detección de vehículos (típicamente 5001)",
    "services.reporting_port": "Puerto para API de reportes: donde se exponen métricas y estadísticas post-simulación (típicamente 5002)",
    # Detección
    "deteccion.detectar": "Activar detección de objetos: iniciar el procesamiento de video con YOLO para detectar vehículos en tiempo real",
    "deteccion.modelo": "Modelo YOLO: versión del modelo de detección. yolov8n.pt = nano (rápido), yolov8s.pt = small, yolov8m.pt = medium (más preciso)",
    "deteccion.path_resultados_deteccion": "Directorio de resultados: carpeta donde se guardan videos procesados, imágenes con detecciones y archivos CSV con estadísticas",
    "deteccion.forced_rotation_degrees": "Rotación forzada: rotar frames del video. 0° = sin rotación, 90° = sentido horario, 180° = voltear, 270° = anti-horario",
    "deteccion.window_fixed": "Ventana fija: True = tamaño constante de ventana, False = ventana se redimensiona automáticamente según contenido",
    "deteccion.window_size": "Tamaño de ventana: [ancho, alto] en píxeles para mostrar el video procesado. [460, 820] = formato vertical típico",
    # Detección - Carpeta dataset
    "deteccion.carpeta_dataset.procesar": "Procesar todos los videos de la carpeta del dataset",
    "deteccion.carpeta_dataset.path_origen": "Carpeta con los videos a procesar",
    "deteccion.carpeta_dataset.path_destino": "Carpeta donde se guardarán los resultados",
    # Detección - Un video
    "deteccion.un_video.procesar": "Procesar un video en específico",
    "deteccion.un_video.guardar": "Guardar el video con los resultados de detección",
    "deteccion.un_video.zona": "Zona de detección para el video",
    "deteccion.un_video.path_origen": "Ruta del video a procesar",
    "deteccion.un_video.path_destino": "Carpeta donde se guardará el resultado",
    # Detección - Cámara
    "deteccion.procesar_camara": "Procesar la cámara en tiempo real",
    # Decisión
    "decision.decision": "Activar agente de decisión: iniciar el algoritmo de aprendizaje por refuerzo (DQN) para controlar semáforos inteligentemente",
    "decision.path_modelo_entrenado": "Modelo DQN entrenado: ruta del archivo .h5 o .keras con los pesos de la red neuronal ya entrenada para inferencia",
    "decision.steps": "Intervalo de decisión: cada cuántos steps de simulación el agente toma una nueva decisión. 10 = decisiones frecuentes, 20 = menos frecuentes",
    "decision.ponderaciones_zonas": "Pesos por zona: valores de importancia para las 12 zonas de detección. [1.0]*12 = todas iguales, valores mayores = más importantes",
    # Entrenamiento Simplificado
    "decision.entrenamiento_simplificado.entrenar": "Activar entrenamiento DQN simplificado: configuración básica y rápida para pruebas iniciales y aprendizaje del algoritmo.",
    "decision.entrenamiento_simplificado.path_resultado": "Directorio donde se guardan modelos entrenados (.h5/.keras), logs de entrenamiento (.csv) y métricas de evaluación.",
    "decision.entrenamiento_simplificado.num_epocas": "Épocas de entrenamiento: cada época = un episodio completo de simulación. 100 épocas permiten ver tendencias claras de aprendizaje.",
    "decision.entrenamiento_simplificado.batch_size": "Tamaño del lote para entrenamiento: número de experiencias que se procesan juntas. 256 = balance entre estabilidad y velocidad.",
    "decision.entrenamiento_simplificado.steps": "Steps por acción: cuántos pasos de simulación transcurren antes de que el agente tome una nueva decisión. Mayor valor = decisiones menos frecuentes.",
    "decision.entrenamiento_simplificado.memory": "Capacidad del buffer de experiencias: memoria que almacena experiencias (estado, acción, recompensa) para entrenar. 50000 = ~200 épocas de historia.",
    "decision.entrenamiento_simplificado.min_replay_size": "Experiencias mínimas para iniciar entrenamiento: evita entrenar con muy pocos datos. 2000 = suficiente diversidad inicial.",
    "decision.entrenamiento_simplificado.learning_rate": "Tasa de aprendizaje: qué tan rápido cambian los pesos de la red neuronal. 0.001 = conservador y estable, 0.1 = agresivo, 0.00001 = muy lento.",
    "decision.entrenamiento_simplificado.epsilon": "Probabilidad de exploración inicial: 1.0 = 100% acciones aleatorias (exploración total), 0.0 = solo acciones óptimas conocidas.",
    "decision.entrenamiento_simplificado.epsilon_decay": "Factor de reducción de exploración: 0.995 = reduce epsilon gradualmente, 0.9 = reduce rápido, 0.999 = reduce muy lento.",
    "decision.entrenamiento_simplificado.epsilon_min": "Exploración mínima: límite inferior para epsilon. 0.1 = siempre 10% de acciones aleatorias, 0.01 = solo 1% exploración.",
    "decision.entrenamiento_simplificado.gamma": "Factor de descuento: importancia de recompensas futuras. 0.85 = valora futuro cercano, 0.99 = valora futuro lejano, 0.1 = solo presente.",
    "decision.entrenamiento_simplificado.hidden_layers": "Arquitectura de red neuronal: capas ocultas y neuronas por capa. [128, 128] = 2 capas de 128 neuronas cada una.",
    "decision.entrenamiento_simplificado.use_double_dqn": "Double DQN: usa dos redes para evitar sobreestimación de valores Q. True = más estable, False = DQN clásico.",
    "decision.entrenamiento_simplificado.use_dueling_dqn": "Dueling DQN: separa valor del estado y ventaja de acciones. True = mejor para muchas acciones, False = arquitectura estándar.",
    "decision.entrenamiento_simplificado.target_update_frequency": "Frecuencia de actualización de red objetivo: cada cuántos steps se actualiza. 200 = estable, 100 = más dinámico, 500 = muy estable.",
    "decision.entrenamiento_simplificado.warmup_steps": "Steps de calentamiento: pasos iniciales sin entrenamiento para llenar el buffer. 250 = permite que aparezcan vehículos antes de decidir.",
    "decision.entrenamiento_simplificado.use_gradient_clipping": "Recorte de gradientes: previene gradientes explosivos que desestabilizan el entrenamiento. True = más estable.",
    "decision.entrenamiento_simplificado.gradient_clip_norm": "Norma máxima de gradientes: valor límite para recortar gradientes. 0.8 = conservador, 1.0 = estándar, 0.5 = muy restrictivo.",
    "decision.entrenamiento_simplificado.use_huber_loss": "Función de pérdida Huber: más robusta a valores atípicos que MSE. True = menos sensible a errores grandes.",
    "decision.entrenamiento_simplificado.use_he_initialization": "Inicialización He: método óptimo para activaciones ReLU. True = mejores gradientes iniciales.",
    "decision.entrenamiento_simplificado.enable_evaluation": "Activar evaluación periódica: mide rendimiento real sin exploración durante el entrenamiento.",
    "decision.entrenamiento_simplificado.evaluation_episodes": "Episodios de evaluación: cuántas simulaciones completas sin exploración para medir rendimiento real. 10 = estadísticamente suficiente.",
    "decision.entrenamiento_simplificado.evaluation_frequency": "Frecuencia de evaluación: cada cuántas épocas evaluar. 5 = balance entre monitoreo y velocidad de entrenamiento.",
    "decision.entrenamiento_simplificado.patience": "Paciencia para early stopping: épocas sin mejora antes de detener entrenamiento. 10 = evita sobreentrenamiento.",
    "decision.entrenamiento_simplificado.min_improvement": "Mejora mínima requerida: cambio mínimo en métrica para considerar que hay progreso. 0.01 = 1% de mejora mínima.",
    # Entrenamiento Completo
    "decision.entrenamiento_completo.entrenar": "Activar entrenamiento DQN avanzado: configuración completa con técnicas state-of-the-art para máximo rendimiento.",
    "decision.entrenamiento_completo.path_resultado": "Directorio donde se guardan modelos entrenados (.h5/.keras), logs detallados (.csv) y métricas completas de evaluación.",
    # Hiperparámetros básicos
    "decision.entrenamiento_completo.num_epocas": "Épocas de entrenamiento: cada época = episodio completo de simulación. 35 épocas optimizadas para convergencia rápida.",
    "decision.entrenamiento_completo.batch_size": "Tamaño del lote: número de experiencias procesadas juntas. 256 = potencia de 2 óptima para GPU, balance memoria/convergencia.",
    "decision.entrenamiento_completo.steps": "Steps por acción del agente: intervalo entre decisiones. 10 = decisiones frecuentes, 20 = menos frecuentes pero más estables.",
    "decision.entrenamiento_completo.memory": "Buffer de experiencias: 5000 = ~20 épocas de memoria, balance entre diversidad y eficiencia computacional.",
    # Optimización y learning rate
    "decision.entrenamiento_completo.learning_rate": "Tasa de aprendizaje inicial: velocidad de cambio de pesos. 0.0005 = conservador para evitar inestabilidad, 0.001 = estándar, 0.0001 = muy lento.",
    "decision.entrenamiento_completo.learning_rate_decay": "Factor de decay del LR por época: 0.99 = reducción gradual conservadora, 0.95 = más agresiva, 0.999 = muy gradual.",
    "decision.entrenamiento_completo.learning_rate_min": "LR mínimo: límite inferior para mantener aprendizaje. 0.00005 = 10% del LR inicial, evita estancamiento completo.",
    # Exploración epsilon-greedy
    "decision.entrenamiento_completo.epsilon": "Probabilidad inicial de exploración: 1.0 = 100% acciones aleatorias al inicio para explorar todas las posibilidades.",
    "decision.entrenamiento_completo.epsilon_decay": "Factor de decay de epsilon por step: 0.99995 = reducción muy gradual durante todo el entrenamiento para mantener exploración.",
    "decision.entrenamiento_completo.epsilon_min": "Exploración mínima residual: 0.1 = siempre 10% de acciones aleatorias para evitar convergencia prematura.",
    # Descuento y arquitectura
    "decision.entrenamiento_completo.gamma": "Factor de descuento: importancia de recompensas futuras. 0.85 = valora futuro cercano, evita inestabilidad de 0.99.",
    "decision.entrenamiento_completo.hidden_layers": "Arquitectura de red neuronal: [64, 64, 64] = 3 capas de 64 neuronas, menos profunda para evitar gradient vanishing.",
    # Mejoras algorítmicas DQN
    "decision.entrenamiento_completo.use_double_dqn": "Double DQN: reduce sobreestimación de Q-values usando red target separada. True = más estable que DQN clásico.",
    "decision.entrenamiento_completo.use_dueling_dqn": "Dueling DQN: separa valor del estado V(s) y ventaja de acciones A(s,a). True = mejor para problemas con muchas acciones.",
    "decision.entrenamiento_completo.target_update_frequency": "Actualización de red target: cada 100 pasos. Menor = más dinámico, mayor = más estable pero menos responsive.",
    # Estabilidad del entrenamiento
    "decision.entrenamiento_completo.warmup_steps": "Steps de calentamiento: pasos iniciales sin entrenamiento. 250 = espera a que lleguen vehículos desde spawn points.",
    "decision.entrenamiento_completo.min_replay_size": "Experiencias mínimas para entrenar: 32 = batch dinámico que crece hasta 256, evita entrenar con muy pocos datos.",
    "decision.entrenamiento_completo.use_gradient_clipping": "Recorte de gradientes: previene gradientes explosivos. True = clipnorm=1.0, entrenamiento más estable.",
    "decision.entrenamiento_completo.use_huber_loss": "Función de pérdida Huber: más robusta a outliers que MSE. True = menos sensible a errores grandes.",
    "decision.entrenamiento_completo.normalize_rewards": "Normalización de recompensas: escala recompensas para estabilidad numérica. True = mejores gradientes.",
    # Prioritized Experience Replay (PER)
    "decision.entrenamiento_completo.use_prioritized_replay": "Prioritized Experience Replay: entrena más con experiencias 'sorprendentes' (alto TD-error). True = aprendizaje más eficiente.",
    "decision.entrenamiento_completo.per_alpha": "Exponente de priorización PER: 0.0 = uniforme (sin prioridad), 1.0 = totalmente priorizado, 0.6 = balance óptimo.",
    "decision.entrenamiento_completo.per_beta_start": "Importance sampling inicial: corrige sesgo de PER. 0.4 = inicio conservador, crece hasta 1.0 para corrección completa.",
    "decision.entrenamiento_completo.per_beta_frames": "Steps para beta=1.0: tiempo para corrección completa de sesgo PER. 100000 = crecimiento gradual durante entrenamiento.",
    # Noisy Networks
    "decision.entrenamiento_completo.use_noisy_networks": "Noisy Networks: exploración mediante ruido en pesos de la red. True = reemplaza epsilon-greedy, exploración más inteligente.",
    "decision.entrenamiento_completo.noise_std": "Desviación estándar del ruido: intensidad del ruido paramétrico. 0.3 = balance entre exploración y estabilidad.",
    # Regularización
    "decision.entrenamiento_completo.use_dropout": "Dropout: previene overfitting desactivando neuronas aleatoriamente durante entrenamiento. True = mejor generalización.",
    "decision.entrenamiento_completo.dropout_rate": "Tasa de dropout: fracción de neuronas desactivadas. 0.02 = 2% muy suave para redes menos profundas.",
    # Learning Rate Adaptativo
    "decision.entrenamiento_completo.adaptive_lr": "Learning Rate Scheduling: ajusta LR según progreso. True = plateau detection, reduce LR cuando se estanca.",
    # Configuraciones anti-gradient vanishing
    "decision.entrenamiento_completo.use_batch_normalization": "Batch Normalization: normaliza entradas de cada capa. True = gradientes más estables, entrena más rápido.",
    "decision.entrenamiento_completo.use_he_initialization": "He Initialization: inicialización óptima para ReLU. True = mejores gradientes iniciales, convergencia más rápida.",
    "decision.entrenamiento_completo.use_residual_connections": "Residual Connections: skip connections para redes profundas. True = evita gradient vanishing en redes complejas.",
    "decision.entrenamiento_completo.gradient_clip_norm": "Norma de recorte de gradientes: límite máximo para gradientes. 1.0 = estándar, 0.5 = más restrictivo.",
    "decision.entrenamiento_completo.use_leaky_relu": "LeakyReLU: evita 'dying ReLU' problem. True = α=0.01, permite pequeños gradientes en valores negativos.",
    # Evaluación y métricas
    "decision.entrenamiento_completo.enable_evaluation": "Sistema de evaluación: mide progreso real del modelo sin exploración durante entrenamiento.",
    "decision.entrenamiento_completo.evaluation_episodes": "Episodios de evaluación: simulaciones completas sin exploración para medir rendimiento real. 10 = estadísticamente suficiente.",
    "decision.entrenamiento_completo.evaluation_frequency": "Frecuencia de evaluación: cada 10 épocas para balance entre monitoreo y velocidad de entrenamiento.",
    "decision.entrenamiento_completo.baseline_comparison": "Comparación con baseline: mide rendimiento vs modelo aleatorio o rule-based. True = contexto de mejora.",
    "decision.entrenamiento_completo.save_evaluation_data": "Guardar datos de evaluación: métricas históricas para análisis posterior. True = CSV con progreso temporal.",
    # SUMO
    "sumo.simular": "Activar simulación SUMO: iniciar la simulación de tráfico con el simulador microscópico para entrenar o evaluar el agente",
    "sumo.gui": "Interfaz gráfica SUMO: True = mostrar ventana visual de simulación, False = modo headless (más rápido, para servidores)",
    "sumo.comparar": "Modo comparación: contrastar rendimiento del control RL vs detección YOLO vs semáforos fijos para evaluar mejoras",
    "sumo.path_sumo": "Directorio de instalación SUMO: ruta donde está instalado SUMO. Linux: /usr/share/sumo, Windows: C:\\sumo o similar",
    "sumo.simulation_time_limit": "Límite temporal: duración máxima de simulación en segundos. 19500s ≈ 5.4 horas de simulación virtual",
    "sumo.fixed_seed": "Semilla específica: valor fijo para reproducibilidad exacta. null = usar default SUMO (23423), número = semilla custom",
    "sumo.use_random_seed": "Semilla aleatoria: True = generar semilla basada en tiempo actual, False = usar fixed_seed o default SUMO",
    "sumo.persist_random_seed": "Persistir semilla: si use_random_seed=True, reutilizar misma semilla en reinicios (True) o generar nueva cada vez (False)",
    # Reportes
    "reporte.generar": "Generar reportes: activar la creación automática de estadísticas, gráficos y análisis post-simulación",
    "reporte.steps": "Intervalo de reporte: cada cuántos steps de simulación recopilar métricas. 60 = cada minuto de simulación virtual",
    "reporte.tiempo_total_espera_maximo": "Tiempo máximo total: límite de espera acumulada en segundos para considerar congestión crítica (600s = 10 min)",
    "reporte.tiempo_zona_espera_maximo": "Tiempo máximo por zona: límite de espera por zona individual para detectar cuellos de botella (300s = 5 min)",
    "reporte.total_vehiculos_maximo": "Umbral de vehículos totales: número mínimo de vehículos en el sistema para considerar que hay tráfico significativo",
    "reporte.zona_vehiculos_maximo": "Umbral por zona: número máximo de vehículos por zona antes de considerar saturación crítica",
    "reporte.path_reporte": "Directorio de reportes: carpeta donde se guardan archivos CSV, gráficos PNG y análisis estadísticos post-simulación",
    "reporte.db_path_base": "Base de datos: directorio donde se almacena la BD SQLite con métricas históricas para análisis temporal",
}


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

    # Obtener tooltip del diccionario
    tooltip = CONFIG_TOOLTIPS.get(field_path, None)

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
