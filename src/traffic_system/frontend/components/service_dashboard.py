"""
Service Management Dashboard Components

Advanced service monitoring and control interface with real-time updates,
health checks, log viewing, and performance metrics.
"""

import logging
from datetime import datetime

import streamlit as st

from src.traffic_system.frontend.utils.service_manager import (
    ServiceManager,
    ServiceStatus,
)

logger = logging.getLogger(__name__)


class ServiceDashboard:
    """Advanced service management dashboard."""

    def __init__(self, service_manager: ServiceManager) -> None:
        """
        Initialize the service dashboard.

        Args:
            service_manager: Service manager instance
        """
        self.service_manager = service_manager

    def render_dashboard_overview(self) -> None:
        """Render the service dashboard overview with metrics."""
        st.subheader("📊 Resumen de Servicios")

        try:
            services_status = self.service_manager.get_all_services_status()
            system_resources = self.service_manager.get_system_resources()

            # Service metrics
            running_count = sum(
                1 for status in services_status.values() if status.is_running
            )
            total_count = len(services_status)

            # Error statistics
            error_stats = self.service_manager.get_error_statistics()
            total_errors = sum(error_stats.values())

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric(
                    "Servicios Activos",
                    f"{running_count}/{total_count}",
                    delta=f"{running_count - (total_count - running_count)}",
                )

            with col2:
                st.metric(
                    "CPU Sistema",
                    f"{system_resources['cpu_percent']:.1f}%",
                    delta=(
                        f"{system_resources['cpu_percent'] - 50:.1f}%"
                        if system_resources["cpu_percent"] > 50
                        else None
                    ),
                )

            with col3:
                st.metric(
                    "Memoria Sistema",
                    f"{system_resources['memory_percent']:.1f}%",
                    delta=(
                        f"{system_resources['memory_percent'] - 70:.1f}%"
                        if system_resources["memory_percent"] > 70
                        else None
                    ),
                )

            with col4:
                # Calculate total service memory usage
                total_service_memory = sum(
                    status.memory_mb
                    for status in services_status.values()
                    if status.is_running
                )
                st.metric(
                    "RAM Servicios",
                    f"{total_service_memory:.0f}MB",
                    delta=(
                        f"{total_service_memory - 500:.0f}MB"
                        if total_service_memory > 500
                        else None
                    ),
                )

            # Error statistics row
            if total_errors > 0:
                st.markdown("---")
                st.subheader("⚠️ Estadísticas de Errores")

                col1, col2, col3 = st.columns(3)

                with col1:
                    st.metric("Total Errores", total_errors)

                with col2:
                    most_common_error = (
                        max(error_stats.items(), key=lambda x: x[1])
                        if error_stats
                        else ("ninguno", 0)
                    )
                    st.metric(
                        "Error Más Común",
                        most_common_error[0].replace("_", " ").title(),
                    )

                with col3:
                    if st.button("🧹 Limpiar Historial de Errores"):
                        self.service_manager.clear_error_history()
                        st.success("✅ Historial de errores limpiado")
                        st.rerun()

            # System health indicator
            if running_count == total_count:
                st.success("✅ Todos los servicios están funcionando correctamente")
            elif running_count > 0:
                st.warning(f"⚠️ {total_count - running_count} servicios inactivos")
            else:
                st.error("❌ Ningún servicio está activo")

        except Exception as e:
            st.error(f"❌ Error obteniendo métricas del sistema: {e}")
            logger.error(f"Error getting system metrics: {e}")

    def render_service_controls(self) -> None:
        """Render global service control buttons."""
        st.subheader("🎮 Control Global")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            if st.button("▶️ Iniciar Todos", use_container_width=True, type="primary"):
                self._start_all_services_action()

        with col2:
            if st.button("⏹️ Detener Todos", use_container_width=True):
                self._stop_all_services_action()

        with col3:
            if st.button("🔄 Reiniciar Todos", use_container_width=True):
                self._restart_all_services_action()

        with col4:
            if st.button("🧹 Limpiar Cache", use_container_width=True):
                self.service_manager.clear_cache()
                st.success("✅ Cache limpiado")
                st.rerun()

    def render_service_list(self, auto_refresh: bool = False) -> None:
        """
        Render detailed service list with controls and monitoring.

        Args:
            auto_refresh: Whether to enable auto-refresh
        """
        st.subheader("🔧 Servicios Individuales")

        # Auto-refresh controls
        col1, col2, col3 = st.columns([2, 1, 1])

        with col1:
            refresh_interval = st.selectbox(
                "Intervalo de actualización",
                options=[5, 10, 30, 60],
                index=0,
                format_func=lambda x: f"{x} segundos",
            )

        with col2:
            auto_refresh = st.checkbox("🔄 Auto-actualizar", value=auto_refresh)

        with col3:
            if st.button("🔄 Actualizar Ahora", use_container_width=True):
                self.service_manager.clear_cache()
                st.rerun()

        # Auto-refresh logic
        if auto_refresh:
            import time

            time.sleep(refresh_interval)
            st.rerun()

        st.markdown("---")

        try:
            services_status = self.service_manager.get_all_services_status()

            for service_name, status in services_status.items():
                self._render_service_card(service_name, status)

        except Exception as e:
            st.error(f"❌ Error obteniendo estado de servicios: {e}")
            logger.error(f"Error getting services status: {e}")

    def _render_service_card(self, service_name: str, status: ServiceStatus) -> None:
        """
        Render an individual service card with detailed information.

        Args:
            service_name: Name of the service
            status: Service status information
        """
        # Service card container
        with st.container():
            # Header with status
            col1, col2, col3 = st.columns([3, 1, 1])

            with col1:
                status_icon = "🟢" if status.is_running else "🔴"
                service_config = self.service_manager.SERVICES.get(service_name, {})
                description = service_config.get(
                    "description", f"{service_name} service"
                )

                st.write(f"{status_icon} **{service_name.title()}**")
                st.caption(description)

            with col2:
                if status.is_running:
                    st.success("🟢 Activo")
                else:
                    st.error("🔴 Inactivo")

            with col3:
                # Health check
                health = self.service_manager.check_service_health(service_name)
                if health["healthy"]:
                    st.success("💚 Saludable")
                else:
                    st.warning(f"⚠️ {len(health['issues'])} problemas")

            # Service details (expandable)
            with st.expander(f"Detalles de {service_name}", expanded=False):
                self._render_service_details(service_name, status)

            # Control buttons
            col1, col2, col3, col4, col5, col6 = st.columns(6)

            with col1:
                if st.button(
                    "▶️ Iniciar",
                    key=f"start_{service_name}",
                    disabled=status.is_running,
                    use_container_width=True,
                ):
                    self._start_service_action(service_name)

            with col2:
                if st.button(
                    "⏹️ Detener",
                    key=f"stop_{service_name}",
                    disabled=not status.is_running,
                    use_container_width=True,
                ):
                    self._stop_service_action(service_name)

            with col3:
                if st.button(
                    "🔄 Reiniciar",
                    key=f"restart_{service_name}",
                    use_container_width=True,
                ):
                    self._restart_service_action(service_name)

            with col4:
                if st.button(
                    "📋 Logs", key=f"logs_{service_name}", use_container_width=True
                ):
                    self._show_service_logs(service_name)

            with col5:
                if st.button(
                    "🔍 Health", key=f"health_{service_name}", use_container_width=True
                ):
                    self._show_health_check(service_name)

            with col6:
                if st.button(
                    "🔧 Ayuda",
                    key=f"troubleshoot_{service_name}",
                    use_container_width=True,
                ):
                    self._show_troubleshooting(service_name)

            st.markdown("---")

    def _render_service_details(self, service_name: str, status: ServiceStatus) -> None:
        """
        Render detailed service information.

        Args:
            service_name: Name of the service
            status: Service status information
        """
        col1, col2 = st.columns(2)

        with col1:
            st.write("**Información Básica:**")
            st.write(
                f"• **Estado**: {'🟢 Activo' if status.is_running else '🔴 Inactivo'}"
            )
            st.write(f"• **Puerto**: {status.port or 'N/A'}")
            st.write(f"• **Comando**: `{status.command}`")

            if status.is_running:
                st.write(f"• **PID**: {status.process_id}")
                st.write(
                    f"• **Inicio**: {status.start_time.strftime('%Y-%m-%d %H:%M:%S') if status.start_time else 'N/A'}"
                )

                # Runtime formatting
                runtime_str = self._format_runtime(status.runtime_seconds)
                st.write(f"• **Runtime**: {runtime_str}")

        with col2:
            if status.is_running:
                st.write("**Recursos:**")
                st.write(f"• **CPU**: {status.cpu_percent:.1f}%")
                st.write(f"• **Memoria**: {status.memory_mb:.1f} MB")

                # Resource usage bars
                st.progress(min(status.cpu_percent / 100, 1.0))
                st.caption(f"CPU: {status.cpu_percent:.1f}%")

                st.progress(min(status.memory_mb / 2000, 1.0))  # Assuming 2GB max
                st.caption(f"Memoria: {status.memory_mb:.1f} MB")

            # Dependencies
            dependencies = self.service_manager.get_service_dependencies().get(
                service_name, []
            )
            if dependencies:
                st.write("**Dependencias:**")
                for dep in dependencies:
                    dep_status = self.service_manager.get_service_status(dep)
                    dep_icon = "✅" if dep_status.is_running else "❌"
                    st.write(f"• {dep_icon} {dep}")

    def _format_runtime(self, seconds: int) -> str:
        """
        Format runtime seconds into human-readable string.

        Args:
            seconds: Runtime in seconds

        Returns:
            Formatted runtime string
        """
        if seconds < 60:
            return f"{seconds}s"
        elif seconds < 3600:
            minutes = seconds // 60
            secs = seconds % 60
            return f"{minutes}m {secs}s"
        else:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            return f"{hours}h {minutes}m"

    def _start_service_action(self, service_name: str) -> None:
        """Start a service with feedback."""
        with st.spinner(f"Iniciando {service_name}..."):
            success, message = self.service_manager.start_service(service_name)

        # Log the operation
        self._log_service_operation(service_name, "start", success, message)

        if success:
            st.success(f"✅ {message}")
        else:
            st.error(f"❌ {message}")

        st.rerun()

    def _stop_service_action(self, service_name: str) -> None:
        """Stop a service with feedback."""
        with st.spinner(f"Deteniendo {service_name}..."):
            success, message = self.service_manager.stop_service(service_name)

        # Log the operation
        self._log_service_operation(service_name, "stop", success, message)

        if success:
            st.success(f"✅ {message}")
        else:
            st.error(f"❌ {message}")

        st.rerun()

    def _restart_service_action(self, service_name: str) -> None:
        """Restart a service with feedback."""
        with st.spinner(f"Reiniciando {service_name}..."):
            success, message = self.service_manager.restart_service(service_name)

        # Log the operation
        self._log_service_operation(service_name, "restart", success, message)

        if success:
            st.success(f"✅ {message}")
        else:
            st.error(f"❌ {message}")

        st.rerun()

    def _start_all_services_action(self) -> None:
        """Start all services with feedback."""
        with st.spinner("Iniciando todos los servicios..."):
            results = self.service_manager.start_all_services()

        success_count = sum(1 for success, _ in results.values() if success)
        total_count = len(results)

        if success_count == total_count:
            st.success(
                f"✅ Todos los servicios iniciados correctamente ({success_count}/{total_count})"
            )
        else:
            st.warning(f"⚠️ {success_count}/{total_count} servicios iniciados")

        # Show individual results
        for service, (success, message) in results.items():
            if success:
                st.success(f"✅ {service}: {message}")
            else:
                st.error(f"❌ {service}: {message}")

        st.rerun()

    def _stop_all_services_action(self) -> None:
        """Stop all services with feedback."""
        with st.spinner("Deteniendo todos los servicios..."):
            results = self.service_manager.stop_all_services()

        success_count = sum(1 for success, _ in results.values() if success)
        total_count = len(results)

        if success_count == total_count:
            st.success(
                f"✅ Todos los servicios detenidos correctamente ({success_count}/{total_count})"
            )
        else:
            st.warning(f"⚠️ {success_count}/{total_count} servicios detenidos")

        st.rerun()

    def _restart_all_services_action(self) -> None:
        """Restart all services with feedback."""
        st.warning("⚠️ Esta operación reiniciará todos los servicios")

        if st.button("Confirmar Reinicio", type="primary"):
            with st.spinner("Reiniciando todos los servicios..."):
                # Stop all first
                stop_results = self.service_manager.stop_all_services()

                # Log stop operations
                for service, (success, message) in stop_results.items():
                    self._log_service_operation(service, "stop", success, message)

                # Wait a moment
                import time

                time.sleep(3)

                # Start all
                start_results = self.service_manager.start_all_services()

                # Log start operations
                for service, (success, message) in start_results.items():
                    self._log_service_operation(service, "start", success, message)

            st.success("✅ Reinicio completado")
            st.rerun()

    def _show_service_logs(self, service_name: str) -> None:
        """Show service logs in a modal."""
        st.subheader(f"📋 Logs de {service_name}")

        try:
            logs = self.service_manager.get_service_logs(service_name, lines=50)

            if logs:
                # Display logs in code block
                log_text = "\n".join(logs)
                st.code(log_text, language="text")

                # Log statistics
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Líneas", len(logs))
                with col2:
                    st.metric("Caracteres", len(log_text))
                with col3:
                    st.metric("Tamaño", f"{len(log_text.encode('utf-8'))} bytes")
            else:
                st.info("ℹ️ No hay logs disponibles para este servicio")

        except Exception as e:
            st.error(f"❌ Error obteniendo logs: {e}")
            logger.error(f"Error getting logs for {service_name}: {e}")

    def _show_health_check(self, service_name: str) -> None:
        """Show detailed health check information."""
        st.subheader(f"🔍 Health Check: {service_name}")

        try:
            health = self.service_manager.check_service_health(service_name)

            # Health status
            if health["healthy"]:
                st.success("💚 Servicio saludable")
            else:
                st.error("❤️‍🩹 Servicio con problemas")

            # Issues
            if health["issues"]:
                st.write("**Problemas detectados:**")
                for issue in health["issues"]:
                    st.error(f"• {issue}")

            # Recommendations
            if health["recommendations"]:
                st.write("**Recomendaciones:**")
                for rec in health["recommendations"]:
                    st.info(f"• {rec}")

            if not health["issues"] and not health["recommendations"]:
                st.success("✅ No se detectaron problemas")

        except Exception as e:
            st.error(f"❌ Error en health check: {e}")
            logger.error(f"Error in health check for {service_name}: {e}")

    def _show_troubleshooting(self, service_name: str) -> None:
        """Show troubleshooting information for a service."""
        st.subheader(f"🔧 Solución de Problemas: {service_name}")

        # Use the service manager's troubleshooting method
        self.service_manager.show_service_troubleshooting(service_name)

        # Add quick actions
        st.markdown("---")
        st.subheader("⚡ Acciones Rápidas")

        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button(
                f"🔄 Reiniciar {service_name}", key=f"quick_restart_{service_name}"
            ):
                success, message = self.service_manager.restart_service(service_name)
                if success:
                    st.success(f"✅ {message}")
                else:
                    st.error(f"❌ {message}")

        with col2:
            if st.button("📋 Ver Logs", key=f"quick_logs_{service_name}"):
                self._show_service_logs(service_name)

        with col3:
            if st.button("🔍 Health Check", key=f"quick_health_{service_name}"):
                self._show_health_check(service_name)

    def check_performance_alerts(self) -> None:
        """Check for performance issues and show alerts."""
        try:
            services_status = self.service_manager.get_all_services_status()
            system_resources = self.service_manager.get_system_resources()

            # System-wide alerts
            if system_resources["cpu_percent"] > 90:
                st.error("🚨 **Alerta de CPU**: Uso del sistema > 90%")
            elif system_resources["cpu_percent"] > 75:
                st.warning("⚠️ **Advertencia de CPU**: Uso del sistema > 75%")

            if system_resources["memory_percent"] > 90:
                st.error("🚨 **Alerta de Memoria**: Uso del sistema > 90%")
            elif system_resources["memory_percent"] > 80:
                st.warning("⚠️ **Advertencia de Memoria**: Uso del sistema > 80%")

            # Service-specific alerts
            for service_name, status in services_status.items():
                if status.is_running:
                    if status.cpu_percent > 50:
                        st.warning(
                            f"⚠️ **{service_name}**: Alto uso de CPU ({status.cpu_percent:.1f}%)"
                        )

                    if status.memory_mb > 1000:
                        st.warning(
                            f"⚠️ **{service_name}**: Alto uso de memoria ({status.memory_mb:.1f} MB)"
                        )

                    # Check if service has been running for a very long time
                    if status.runtime_seconds > 86400:  # 24 hours
                        st.info(
                            f"ℹ️ **{service_name}**: Ha estado ejecutándose por más de 24 horas. "
                            "Considera reiniciarlo para liberar memoria."
                        )

        except Exception as e:
            logger.error(f"Error checking performance alerts: {e}")

    def check_for_crashes(self) -> None:
        """Check for service crashes and notify user."""
        try:
            services_status = self.service_manager.get_all_services_status()

            # Check if any service that should be running is not running
            for service_name, status in services_status.items():
                if not status.is_running:
                    # Check if this service was running recently (stored in session state)
                    session_key = f"service_was_running_{service_name}"
                    if st.session_state.get(session_key, False):
                        st.error(
                            f"🚨 **Crash detectado**: El servicio {service_name} se ha detenido inesperadamente"
                        )
                        # Log the crash
                        self._log_service_operation(
                            service_name,
                            "crash",
                            False,
                            "Servicio se detuvo inesperadamente",
                        )
                        # Reset the flag
                        st.session_state[session_key] = False
                else:
                    # Mark service as running
                    st.session_state[f"service_was_running_{service_name}"] = True

        except Exception as e:
            logger.error(f"Error checking for crashes: {e}")

    def render_service_startup_log(self) -> None:
        """Render service startup/shutdown log."""
        st.subheader("📝 Log de Operaciones")

        # Initialize operation log in session state
        if "service_operation_log" not in st.session_state:
            st.session_state.service_operation_log = []

        # Display recent operations
        if st.session_state.service_operation_log:
            import pandas as pd

            log_df = pd.DataFrame(st.session_state.service_operation_log)
            st.dataframe(
                log_df.tail(20), use_container_width=True
            )  # Show last 20 operations
        else:
            st.info("ℹ️ No hay operaciones registradas")

        # Clear log button
        if st.button("🧹 Limpiar Log"):
            st.session_state.service_operation_log = []
            st.success("✅ Log limpiado")
            st.rerun()

    def _log_service_operation(
        self, service_name: str, operation: str, success: bool, message: str
    ) -> None:
        """
        Log a service operation.

        Args:
            service_name: Name of the service
            operation: Type of operation (start, stop, restart)
            success: Whether operation was successful
            message: Operation message
        """

        if "service_operation_log" not in st.session_state:
            st.session_state.service_operation_log = []

        log_entry = {
            "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Servicio": service_name,
            "Operación": operation,
            "Estado": "✅ Éxito" if success else "❌ Error",
            "Mensaje": message,
        }

        st.session_state.service_operation_log.append(log_entry)

    def render_uptime_statistics(self) -> None:
        """Render service uptime statistics."""
        st.subheader("📈 Estadísticas de Tiempo de Actividad")

        try:
            services_status = self.service_manager.get_all_services_status()

            # Calculate uptime statistics
            total_services = len(services_status)
            running_services = sum(
                1 for status in services_status.values() if status.is_running
            )
            uptime_percentage = (
                (running_services / total_services) * 100 if total_services > 0 else 0
            )

            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric(
                    "Disponibilidad General",
                    f"{uptime_percentage:.1f}%",
                    delta=(
                        f"{uptime_percentage - 100:.1f}%"
                        if uptime_percentage < 100
                        else None
                    ),
                )

            with col2:
                total_runtime = sum(
                    status.runtime_seconds
                    for status in services_status.values()
                    if status.is_running
                )
                hours = total_runtime // 3600
                minutes = (total_runtime % 3600) // 60
                st.metric("Tiempo Total Activo", f"{hours}h {minutes}m")

            with col3:
                avg_runtime = (
                    total_runtime / running_services if running_services > 0 else 0
                )
                avg_hours = avg_runtime // 3600
                avg_minutes = (avg_runtime % 3600) // 60
                st.metric("Tiempo Promedio", f"{avg_hours:.0f}h {avg_minutes:.0f}m")

            # Individual service uptime
            if services_status:
                st.write("**Tiempo de Actividad por Servicio:**")
                for service_name, status in services_status.items():
                    col1, col2, col3 = st.columns([2, 1, 1])

                    with col1:
                        status_icon = "🟢" if status.is_running else "🔴"
                        st.write(f"{status_icon} **{service_name}**")

                    with col2:
                        if status.is_running and status.runtime_seconds > 0:
                            hours = status.runtime_seconds // 3600
                            minutes = (status.runtime_seconds % 3600) // 60
                            st.write(f"{hours}h {minutes}m")
                        else:
                            st.write("No activo")

                    with col3:
                        if status.is_running:
                            st.write(f"PID: {status.process_id}")
                        else:
                            st.write("---")

        except Exception as e:
            st.error(f"❌ Error calculando estadísticas: {e}")
            logger.error(f"Error in uptime statistics: {e}")

    def show_monitoring_dashboard(self) -> None:
        """Show detailed monitoring dashboard."""
        st.subheader("📊 Dashboard de Monitoreo")

        try:
            services_status = self.service_manager.get_all_services_status()
            system_resources = self.service_manager.get_system_resources()

            # Performance metrics over time (simulated)
            st.write("**Métricas de Rendimiento:**")

            col1, col2 = st.columns(2)

            with col1:
                # CPU usage chart (placeholder)
                import numpy as np
                import pandas as pd

                # Generate sample data for demonstration
                times = pd.date_range(start="now", periods=20, freq="1min")
                cpu_data = np.random.normal(system_resources["cpu_percent"], 10, 20)
                cpu_data = np.clip(cpu_data, 0, 100)

                chart_data = pd.DataFrame({"time": times, "CPU %": cpu_data})

                st.line_chart(chart_data.set_index("time"))

            with col2:
                # Memory usage chart (placeholder)
                memory_data = np.random.normal(
                    system_resources["memory_percent"], 5, 20
                )
                memory_data = np.clip(memory_data, 0, 100)

                chart_data = pd.DataFrame({"time": times, "Memory %": memory_data})

                st.line_chart(chart_data.set_index("time"))

            # Service uptime tracking
            st.write("**Tiempo de Actividad de Servicios:**")

            uptime_data = []
            for service_name, status in services_status.items():
                if status.is_running:
                    uptime_hours = status.runtime_seconds / 3600
                    uptime_data.append(
                        {
                            "Servicio": service_name,
                            "Uptime (horas)": uptime_hours,
                            "Estado": "🟢 Activo",
                        }
                    )
                else:
                    uptime_data.append(
                        {
                            "Servicio": service_name,
                            "Uptime (horas)": 0,
                            "Estado": "🔴 Inactivo",
                        }
                    )

            if uptime_data:
                uptime_df = pd.DataFrame(uptime_data)
                st.dataframe(uptime_df, use_container_width=True)

            # Port usage summary
            st.write("**Uso de Puertos:**")
            port_data = []
            for service_name, status in services_status.items():
                if status.port:
                    port_in_use = self.service_manager.is_port_in_use(status.port)
                    port_data.append(
                        {
                            "Puerto": status.port,
                            "Servicio": service_name,
                            "En Uso": "✅" if port_in_use else "❌",
                            "Estado Servicio": "🟢" if status.is_running else "🔴",
                        }
                    )

            if port_data:
                port_df = pd.DataFrame(port_data)
                st.dataframe(port_df, use_container_width=True)

        except Exception as e:
            st.error(f"❌ Error en dashboard de monitoreo: {e}")
            logger.error(f"Error in monitoring dashboard: {e}")


def render_advanced_service_dashboard(service_manager: ServiceManager) -> None:
    """
    Render the advanced service management dashboard.

    Args:
        service_manager: Service manager instance
    """
    dashboard = ServiceDashboard(service_manager)

    # Dashboard overview
    dashboard.render_dashboard_overview()

    st.markdown("---")

    # Global controls
    dashboard.render_service_controls()

    st.markdown("---")

    # Service list
    dashboard.render_service_list()

    st.markdown("---")

    # Performance alerts
    dashboard.check_performance_alerts()

    st.markdown("---")

    # Crash detection and monitoring
    dashboard.check_for_crashes()

    st.markdown("---")

    # Service operation log
    dashboard.render_service_startup_log()

    st.markdown("---")

    # Uptime statistics
    dashboard.render_uptime_statistics()

    st.markdown("---")

    # Show monitoring dashboard
    try:
        dashboard.show_monitoring_dashboard()
    except Exception as e:
        st.error(f"❌ Error en dashboard de monitoreo: {e}")
        logger.error(f"Error in monitoring dashboard: {e}")
