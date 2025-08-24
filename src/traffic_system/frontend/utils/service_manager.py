"""
Service Management Utilities

Handles monitoring and control of traffic system microservices,
including process management, status monitoring, and health checks.
"""

import logging
import os
import subprocess
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import psutil

from src.traffic_system.frontend.utils.service_error_handler import (
    ServiceErrorHandler,
    ServiceErrorType,
    with_service_timeout,
)

logger = logging.getLogger(__name__)


@dataclass
class ServiceStatus:
    """Represents the status of a service."""

    name: str
    is_running: bool
    process_id: int | None = None
    start_time: datetime | None = None
    command: str = ""
    port: int | None = None
    runtime_seconds: int = 0


class ServiceManager:
    """Manages traffic system microservices."""

    def __init__(self) -> None:
        """Initialize the service manager."""
        self.error_handler = ServiceErrorHandler()
        self._process_cache: dict[str, psutil.Process | None] = {}
        self._cache_timestamp = 0
        self._cache_ttl = 5  # Cache TTL in seconds

    # Service definitions with their run commands and ports
    SERVICES: dict[str, dict[str, Any]] = {
        "simulation": {
            "command": ["poetry", "run", "python", "run_simulation_provider.py"],
            "script": "run_simulation_provider.py",
            "port": 5000,
            "description": "SUMO Traffic Simulation Provider",
        },
        "decision": {
            "command": ["poetry", "run", "python", "run_decision_agent.py"],
            "script": "run_decision_agent.py",
            "port": None,
            "description": "DQN Decision Agent",
        },
        "detection": {
            "command": ["poetry", "run", "python", "run_detection_provider.py"],
            "script": "run_detection_provider.py",
            "port": 5000,  # Shares port with simulation
            "description": "YOLOv8 Detection Provider",
        },
        "reporting": {
            "command": ["poetry", "run", "python", "run_reporting_service.py"],
            "script": "run_reporting_service.py",
            "port": 5001,
            "description": "Analytics and Reporting Service",
        },
    }

    def get_service_status(self, service_name: str) -> ServiceStatus:
        """
        Get current status of a specific service.

        Args:
            service_name: Name of the service to check

        Returns:
            ServiceStatus object with current information
        """
        if service_name not in self.SERVICES:
            logger.warning(f"⚠️ Servicio desconocido: {service_name}")
            return ServiceStatus(
                name=service_name, is_running=False, command="Unknown service"
            )

        service_config = self.SERVICES[service_name]

        try:
            # Find process by script name
            process = self._find_service_process(service_name)

            if process and process.is_running():
                # Get process information
                create_time = datetime.fromtimestamp(process.create_time())
                runtime = int(time.time() - process.create_time())

                return ServiceStatus(
                    name=service_name,
                    is_running=True,
                    process_id=process.pid,
                    start_time=create_time,
                    command=" ".join(service_config["command"]),
                    port=service_config["port"],
                    runtime_seconds=runtime,
                )
            else:
                return ServiceStatus(
                    name=service_name,
                    is_running=False,
                    command=" ".join(service_config["command"]),
                    port=service_config["port"],
                )

        except Exception as e:
            logger.error(f"❌ Error checking status for {service_name}: {e}")
            return ServiceStatus(
                name=service_name,
                is_running=False,
                command=" ".join(service_config["command"]),
                port=service_config["port"],
            )

    def get_all_services_status(self) -> dict[str, ServiceStatus]:
        """
        Get status of all services.

        Returns:
            Dictionary mapping service names to their status
        """
        status_dict = {}

        for service_name in self.SERVICES:
            status_dict[service_name] = self.get_service_status(service_name)

        return status_dict

    def _find_service_process(self, service_name: str) -> psutil.Process | None:
        """
        Find the process for a specific service.

        Args:
            service_name: Name of the service

        Returns:
            psutil.Process if found, None otherwise
        """
        current_time = time.time()

        # Use cache if recent
        if (
            service_name in self._process_cache
            and current_time - self._cache_timestamp < self._cache_ttl
        ):
            try:
                process = self._process_cache[service_name]
                if process and process.is_running():
                    return process
                else:
                    # Process died, remove from cache
                    del self._process_cache[service_name]
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                # Process no longer exists
                if service_name in self._process_cache:
                    del self._process_cache[service_name]

        # Search for process
        service_config = self.SERVICES[service_name]
        script_name = service_config["script"]

        try:
            for process in psutil.process_iter(["pid", "name", "cmdline"]):
                try:
                    cmdline = process.info["cmdline"]
                    if cmdline and any(script_name in arg for arg in cmdline):
                        # Additional check to ensure it's a Python process
                        if any("python" in arg.lower() for arg in cmdline):
                            self._process_cache[service_name] = process
                            self._cache_timestamp = int(current_time)
                            return process

                except (
                    psutil.NoSuchProcess,
                    psutil.AccessDenied,
                    psutil.ZombieProcess,
                ):
                    continue

        except Exception as e:
            logger.error(f"❌ Error searching for process {service_name}: {e}")

        return None

    def is_port_in_use(self, port: int) -> bool:
        """
        Check if a port is currently in use.

        Args:
            port: Port number to check

        Returns:
            True if port is in use, False otherwise
        """
        try:
            for conn in psutil.net_connections():
                if conn.laddr.port == port and conn.status == psutil.CONN_LISTEN:
                    return True
            return False
        except Exception as e:
            logger.warning(f"⚠️ Error checking port {port}: {e}")
            return False

    def get_port_conflicts(self) -> dict[int, list[str]]:
        """
        Check for port conflicts between services.

        Returns:
            Dictionary mapping ports to list of services that use them
        """
        port_usage: dict[int, list[str]] = {}

        for service_name, config in self.SERVICES.items():
            port = config["port"]
            if port:
                if port not in port_usage:
                    port_usage[port] = []
                port_usage[port].append(service_name)

        # Return only ports with conflicts (multiple services)
        conflicts = {
            port: services for port, services in port_usage.items() if len(services) > 1
        }

        return conflicts

    def check_service_health(self, service_name: str) -> dict[str, Any]:
        """
        Perform health check on a service.

        Args:
            service_name: Name of the service to check

        Returns:
            Dictionary with health check results
        """
        health_info: dict[str, Any] = {
            "service": service_name,
            "healthy": False,
            "issues": [],
            "recommendations": [],
        }

        try:
            status = self.get_service_status(service_name)

            if not status.is_running:
                health_info["issues"].append("Servicio no está ejecutándose")
                health_info["recommendations"].append("Iniciar el servicio")
                return health_info

            # Check port availability for services that use ports
            service_config = self.SERVICES[service_name]
            if service_config["port"]:
                if not self.is_port_in_use(service_config["port"]):
                    health_info["issues"].append(
                        f"Puerto {service_config['port']} no está en uso"
                    )
                    health_info["recommendations"].append(
                        "Verificar que el servicio esté escuchando correctamente"
                    )

            # Check runtime (services shouldn't restart frequently)
            if status.runtime_seconds < 60:  # Less than 1 minute
                health_info["issues"].append("Servicio reiniciado recientemente")
                health_info["recommendations"].append("Verificar logs para errores")

            # Service is healthy if no issues found
            health_info["healthy"] = len(health_info["issues"]) == 0

        except Exception as e:
            health_info["issues"].append(f"Error durante health check: {str(e)}")
            logger.error(f"❌ Error in health check for {service_name}: {e}")

        return health_info

    def get_service_logs(self, service_name: str, lines: int = 50) -> list[str]:
        """
        Get recent log entries for a service.

        Args:
            service_name: Name of the service
            lines: Number of recent lines to retrieve

        Returns:
            List of log lines
        """
        # This is a placeholder implementation
        # In a real implementation, you would read from log files or capture stdout/stderr

        logs = [
            f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Service {service_name} log entry",
            f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Status: Running",
            f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] No errors detected",
        ]

        return logs[-lines:] if logs else ["No logs available"]

    def clear_cache(self) -> None:
        """Clear the process cache to force fresh lookups."""
        self._process_cache.clear()
        self._cache_timestamp = 0
        logger.info("🔄 Cache de procesos limpiado")

    def show_service_troubleshooting(self, service_name: str) -> None:
        """Show troubleshooting information for a service."""
        self.error_handler.show_service_troubleshooting(service_name)

    def get_error_statistics(self) -> dict[str, int]:
        """Get error statistics for all services."""
        stats = self.error_handler.get_error_statistics()
        return dict(stats) if stats else {}

    def clear_error_history(self) -> None:
        """Clear the error history."""
        self.error_handler.clear_error_history()

    @with_service_timeout(
        timeout_seconds=45
    )  # Increased timeout for better reliability
    def start_service(self, service_name: str) -> tuple[bool, str]:
        """
        Start a service using poetry run with enhanced error handling and diagnostics.

        Args:
            service_name: Name of the service to start

        Returns:
            Tuple of (success, message)
        """

        if service_name not in self.SERVICES:
            self.error_handler.handle_service_error(
                ServiceErrorType.UNKNOWN_SERVICE, service_name
            )
            return False, f"Servicio desconocido: {service_name}"

        try:
            # Pre-flight checks
            logger.info(f"🔍 Ejecutando verificaciones previas para {service_name}...")

            # Check if service is already running
            status = self.get_service_status(service_name)
            if status.is_running:
                self.error_handler.handle_service_error(
                    ServiceErrorType.ALREADY_RUNNING,
                    service_name,
                    f"PID: {status.process_id}",
                    show_in_ui=False,  # This is not really an error
                )
                msg = f"El servicio {service_name} ya está ejecutándose (PID: {status.process_id})"
                return True, msg

            # Check Poetry availability
            if not self._check_poetry_available():
                self.error_handler.handle_service_error(
                    ServiceErrorType.POETRY_NOT_FOUND,
                    service_name,
                    "Poetry no encontrado en PATH",
                )
                return False, "Poetry no está disponible"

            # Check for port conflicts
            service_config = self.SERVICES[service_name]
            if service_config["port"] and self.is_port_in_use(service_config["port"]):
                conflicting_process = self._get_process_using_port(
                    service_config["port"]
                )
                self.error_handler.handle_service_error(
                    ServiceErrorType.PORT_CONFLICT,
                    service_name,
                    f"Puerto {service_config['port']} usado por: {conflicting_process}",
                )
                return (
                    False,
                    f"Puerto {service_config['port']} ya está en uso por: {conflicting_process}",
                )

            # Check system resources
            if not self._check_system_resources():
                self.error_handler.handle_service_error(
                    ServiceErrorType.RESOURCE_UNAVAILABLE,
                    service_name,
                    "Recursos del sistema insuficientes",
                )
                return False, "Recursos del sistema insuficientes"

            # Check service-specific dependencies
            dependency_check = self._check_service_dependencies(service_name)
            if not dependency_check[0]:
                self.error_handler.handle_service_error(
                    ServiceErrorType.CONFIGURATION_ERROR,
                    service_name,
                    dependency_check[1],
                )
                return False, f"Dependencias faltantes: {dependency_check[1]}"

            # Start the service
            command: list[str] = service_config["command"]
            logger.info(f"🚀 Iniciando servicio {service_name}: {' '.join(command)}")

            # Enhanced process startup with better error capture
            try:
                process = subprocess.Popen(
                    command,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    cwd=os.getcwd(),
                    text=True,  # Enable text mode for better error handling
                    creationflags=(
                        subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0
                    ),
                )
            except FileNotFoundError as e:
                self.error_handler.handle_service_error(
                    ServiceErrorType.STARTUP_FAILED,
                    service_name,
                    f"Comando no encontrado: {e}",
                )
                return False, f"Error ejecutando comando: {e}"
            except PermissionError as e:
                self.error_handler.handle_service_error(
                    ServiceErrorType.PERMISSION_DENIED,
                    service_name,
                    f"Permisos insuficientes: {e}",
                )
                return False, f"Permisos insuficientes: {e}"

            # Enhanced startup verification with progressive checks
            startup_success = self._verify_service_startup(service_name, process)

            if startup_success[0]:
                # Clear cache to force fresh lookup
                self.clear_cache()
                success_msg = f"Servicio {service_name} iniciado correctamente (PID: {process.pid})"
                logger.info(f"✅ {success_msg}")
                return True, success_msg
            else:
                # Startup failed - get detailed error information
                stdout, stderr = process.communicate(timeout=5)
                error_details = self._analyze_startup_failure(
                    service_name, stdout, stderr
                )

                self.error_handler.handle_service_error(
                    ServiceErrorType.STARTUP_FAILED, service_name, error_details
                )
                return False, f"Fallo en el inicio: {error_details}"
                error_msg = f"El servicio {service_name} falló al iniciar"
                if stderr:
                    error_msg += f": {stderr.decode()[:200]}"
                logger.error(f"❌ {error_msg}")
                return False, error_msg

        except FileNotFoundError as e:
            self.error_handler.handle_service_error(
                ServiceErrorType.POETRY_NOT_FOUND, service_name, str(e)
            )
            return (
                False,
                "Poetry no encontrado. Instala Poetry y reinicia la aplicación",
            )
        except PermissionError as e:
            self.error_handler.handle_service_error(
                ServiceErrorType.PERMISSION_DENIED, service_name, str(e)
            )
            return False, "Permisos insuficientes para iniciar el servicio"
        except OSError as e:
            if "No space left on device" in str(e):
                self.error_handler.handle_service_error(
                    ServiceErrorType.RESOURCE_UNAVAILABLE, service_name, str(e)
                )
                return False, "Espacio en disco insuficiente"
            else:
                self.error_handler.handle_service_error(
                    ServiceErrorType.UNEXPECTED_ERROR, service_name, str(e)
                )
                return False, f"Error del sistema: {str(e)}"
        except Exception as e:
            self.error_handler.handle_service_error(
                ServiceErrorType.UNEXPECTED_ERROR, service_name, str(e)
            )
            return False, f"Error inesperado: {str(e)}"

    @with_service_timeout(timeout_seconds=20)
    def stop_service(self, service_name: str) -> tuple[bool, str]:
        """
        Stop a running service gracefully with comprehensive error handling.

        Args:
            service_name: Name of the service to stop

        Returns:
            Tuple of (success, message)
        """

        if service_name not in self.SERVICES:
            self.error_handler.handle_service_error(
                ServiceErrorType.UNKNOWN_SERVICE, service_name
            )
            return False, f"Servicio desconocido: {service_name}"

        try:
            # Find the service process
            process = self._find_service_process(service_name)

            if not process:
                self.error_handler.handle_service_error(
                    ServiceErrorType.NOT_RUNNING,
                    service_name,
                    show_in_ui=False,  # This is not really an error
                )
                msg = f"El servicio {service_name} no está ejecutándose"
                return True, msg

            logger.info(f"🛑 Deteniendo servicio {service_name} (PID: {process.pid})")

            # Try graceful shutdown first
            try:
                process.terminate()

                # Wait for graceful shutdown
                try:
                    process.wait(timeout=10)  # Wait up to 10 seconds
                    self.clear_cache()
                    success_msg = f"Servicio {service_name} detenido correctamente"
                    logger.info(f"✅ {success_msg}")
                    return True, success_msg

                except psutil.TimeoutExpired:
                    # Force kill if graceful shutdown failed
                    logger.warning(f"⚠️ Forzando cierre del servicio {service_name}")
                    process.kill()
                    process.wait(timeout=5)
                    self.clear_cache()
                    success_msg = f"Servicio {service_name} forzado a cerrar"
                    logger.info(f"✅ {success_msg}")
                    return True, success_msg

            except psutil.NoSuchProcess:
                # Process already died
                self.clear_cache()
                msg = f"El servicio {service_name} ya se había detenido"
                logger.info(f"ℹ️ {msg}")
                return True, msg

        except psutil.AccessDenied as e:
            self.error_handler.handle_service_error(
                ServiceErrorType.PERMISSION_DENIED, service_name, str(e)
            )
            return False, "Permisos insuficientes para detener el servicio"
        except psutil.TimeoutExpired as e:
            self.error_handler.handle_service_error(
                ServiceErrorType.TIMEOUT, service_name, str(e)
            )
            return False, "Tiempo de espera agotado al detener el servicio"
        except Exception as e:
            self.error_handler.handle_service_error(
                ServiceErrorType.SHUTDOWN_FAILED, service_name, str(e)
            )
            return False, f"Error deteniendo servicio: {str(e)}"

    def restart_service(self, service_name: str) -> tuple[bool, str]:
        """
        Restart a service (stop then start).

        Args:
            service_name: Name of the service to restart

        Returns:
            Tuple of (success, message)
        """
        if service_name not in self.SERVICES:
            error_msg = f"Servicio desconocido: {service_name}"
            logger.error(f"❌ {error_msg}")
            return False, error_msg

        logger.info(f"🔄 Reiniciando servicio {service_name}")

        # Stop the service first
        stop_success, stop_msg = self.stop_service(service_name)

        if not stop_success:
            error_msg = f"No se pudo detener el servicio para reiniciar: {stop_msg}"
            logger.error(f"❌ {error_msg}")
            return False, error_msg

        # Wait a moment between stop and start
        time.sleep(2)

        # Start the service
        start_success, start_msg = self.start_service(service_name)

        if start_success:
            success_msg = f"Servicio {service_name} reiniciado correctamente"
            logger.info(f"✅ {success_msg}")
            return True, success_msg
        else:
            error_msg = (
                f"No se pudo iniciar el servicio después de detenerlo: {start_msg}"
            )
            logger.error(f"❌ {error_msg}")
            return False, error_msg

    def stop_all_services(self) -> dict[str, tuple[bool, str]]:
        """
        Stop all running services.

        Returns:
            Dictionary mapping service names to (success, message) tuples
        """
        results = {}

        logger.info("🛑 Deteniendo todos los servicios")

        for service_name in self.SERVICES:
            results[service_name] = self.stop_service(service_name)

        return results

    def get_service_startup_order(self) -> list[str]:
        """
        Get recommended startup order for services.

        Returns:
            List of service names in recommended startup order
        """
        # Simulation should start first as other services depend on it
        # Decision agent depends on simulation
        # Detection and reporting can start independently
        return ["simulation", "decision", "detection", "reporting"]

    def start_all_services(self, delay_between: int = 3) -> dict[str, tuple[bool, str]]:
        """
        Start all services in recommended order.

        Args:
            delay_between: Seconds to wait between starting each service

        Returns:
            Dictionary mapping service names to (success, message) tuples
        """
        results = {}
        startup_order = self.get_service_startup_order()

        logger.info("🚀 Iniciando todos los servicios en orden recomendado")

        for service_name in startup_order:
            results[service_name] = self.start_service(service_name)

            # Wait between service starts to avoid conflicts
            if delay_between > 0:
                time.sleep(delay_between)

        return results

    def get_service_dependencies(self) -> dict[str, list[str]]:
        """
        Get service dependency information.

        Returns:
            Dictionary mapping services to their dependencies
        """
        return {
            "simulation": [],  # No dependencies
            "decision": ["simulation"],  # Depends on simulation
            "detection": [],  # Independent
            "reporting": ["simulation"],  # May depend on simulation data
        }

    def check_dependencies(self, service_name: str) -> tuple[bool, list[str]]:
        """
        Check if service dependencies are running.

        Args:
            service_name: Name of the service to check

        Returns:
            Tuple of (all_dependencies_running, list_of_missing_dependencies)
        """
        dependencies = self.get_service_dependencies().get(service_name, [])
        missing = []

        for dep_service in dependencies:
            status = self.get_service_status(dep_service)
            if not status.is_running:
                missing.append(dep_service)

        return len(missing) == 0, missing

    def _check_poetry_available(self) -> bool:
        """Check if Poetry is available in the system."""
        try:
            result = subprocess.run(
                ["poetry", "--version"], capture_output=True, text=True, timeout=10
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False

    def _get_process_using_port(self, port: int) -> str:
        """Get information about the process using a specific port."""
        try:
            for conn in psutil.net_connections():
                if conn.laddr.port == port and conn.status == psutil.CONN_LISTEN:
                    try:
                        process = psutil.Process(conn.pid)
                        return f"{process.name()} (PID: {conn.pid})"
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        return f"PID: {conn.pid}"
            return "Proceso desconocido"
        except Exception:
            return "No se pudo determinar"

    def _check_system_resources(self) -> bool:
        """Check if system has sufficient resources (simplified check)."""
        try:
            # Basic check - just ensure we can access system info
            # Removed detailed resource monitoring as per simplification requirements
            psutil.virtual_memory()
            return True
        except Exception as e:
            logger.warning(f"⚠️ Error checking system availability: {e}")
            return True  # Assume resources are available if check fails

    def _check_service_dependencies(self, service_name: str) -> tuple[bool, str]:
        """Check service-specific dependencies."""
        try:
            if service_name == "simulation":
                # Check SUMO availability
                try:
                    result = subprocess.run(
                        ["sumo", "--version"], capture_output=True, timeout=5
                    )
                    if result.returncode != 0:
                        return False, "SUMO no está instalado o no está en PATH"
                except (subprocess.TimeoutExpired, FileNotFoundError):
                    return False, "SUMO no encontrado"

            elif service_name == "decision":
                # Check TensorFlow availability
                try:
                    import tensorflow as tf

                    # Quick TensorFlow test
                    tf.constant([1, 2, 3])
                except ImportError:
                    return False, "TensorFlow no está instalado"
                except Exception as e:
                    return False, f"Error en TensorFlow: {e}"

            elif service_name == "detection":
                # Check YOLOv8/Ultralytics availability
                try:
                    import importlib.util

                    if importlib.util.find_spec("ultralytics") is None:
                        logger.warning(
                            "❌ Ultralytics (YOLOv8) dependency missing for detection service"
                        )
                        return False, "Ultralytics (YOLOv8) no está instalado"
                except ImportError:
                    logger.warning(
                        "❌ Failed to import importlib.util while checking Ultralytics dependency"
                    )
                    return False, "Ultralytics (YOLOv8) no está instalado"

                # Check OpenCV
                try:
                    import importlib.util

                    if importlib.util.find_spec("cv2") is None:
                        logger.warning(
                            "❌ OpenCV dependency missing for detection service"
                        )
                        return False, "OpenCV no está instalado"
                except ImportError:
                    logger.warning(
                        "❌ Failed to import importlib.util while checking OpenCV dependency"
                    )
                    return False, "OpenCV no está instalado"

            return True, ""

        except Exception as e:
            return False, f"Error verificando dependencias: {e}"

    def _verify_service_startup(
        self, service_name: str, process: subprocess.Popen
    ) -> tuple[bool, str]:
        """Verify that a service started successfully with progressive checks."""
        try:
            # Wait for initial startup
            time.sleep(3)

            # Check if process is still running
            if process.poll() is not None:
                return False, "Proceso terminó inmediatamente"

            # For services with ports, check if port is listening
            service_config = self.SERVICES[service_name]
            if service_config["port"]:
                # Wait a bit more for port to be ready
                time.sleep(2)

                # Check if port is now listening
                port_listening = False
                for _ in range(10):  # Try for up to 10 seconds
                    if self.is_port_in_use(service_config["port"]):
                        port_listening = True
                        break
                    time.sleep(1)

                if not port_listening:
                    return False, f"Puerto {service_config['port']} no está escuchando"

            # Final process check
            if process.poll() is not None:
                return False, "Proceso terminó durante la verificación"

            return True, "Startup verificado exitosamente"

        except Exception as e:
            return False, f"Error durante verificación: {e}"

    def _analyze_startup_failure(
        self, service_name: str, stdout: str, stderr: str
    ) -> str:
        """Analyze startup failure and provide detailed error information."""
        error_details = []

        # Analyze stderr for common errors
        if stderr:
            stderr_lower = stderr.lower()

            if "modulenotfounderror" in stderr_lower:
                error_details.append("Módulo Python faltante")
            elif "permission denied" in stderr_lower:
                error_details.append("Permisos insuficientes")
            elif "address already in use" in stderr_lower:
                error_details.append("Puerto ya en uso")
            elif "connection refused" in stderr_lower:
                error_details.append("Conexión rechazada")
            elif "no such file" in stderr_lower:
                error_details.append("Archivo no encontrado")
            elif "tensorflow" in stderr_lower and "error" in stderr_lower:
                error_details.append("Error de TensorFlow")
            elif "sumo" in stderr_lower and (
                "not found" in stderr_lower or "error" in stderr_lower
            ):
                error_details.append("Error de SUMO")
            else:
                error_details.append("Error desconocido en stderr")

        # Analyze stdout for additional info
        if stdout and "error" in stdout.lower():
            error_details.append("Error reportado en stdout")

        # Combine error details
        if error_details:
            result = "; ".join(error_details)
            if stderr:
                result += f"\nDetalles técnicos: {stderr[:500]}"  # Limit stderr length
            return result
        else:
            return f"Fallo sin detalles específicos. stderr: {stderr[:200] if stderr else 'vacío'}"

    def _create_enhanced_error_context(
        self, service_name: str, operation: str
    ) -> dict[str, Any]:
        """Create enhanced error context for debugging."""
        service_config = self.SERVICES.get(service_name, {})

        # Log warning if service config is empty or missing critical fields
        if not service_config:
            logger.warning(f"⚠️ Service config for '{service_name}' is empty or missing")
        elif "command" not in service_config:
            logger.warning(
                f"⚠️ Service config for '{service_name}' missing 'command' field"
            )
        elif "port" not in service_config:
            logger.warning(
                f"⚠️ Service config for '{service_name}' missing 'port' field"
            )

        context: dict[str, Any] = {
            "service_name": service_name,
            "operation": operation,
            "timestamp": datetime.now().isoformat(),
            "system_info": {
                "platform": os.name,
                "python_version": __import__("sys").version,
                "working_directory": os.getcwd(),
            },
            "service_config": service_config,
        }

        # Add running services info
        running_services_list: list[dict[str, Any]] = []
        for svc_name, status in self.get_all_services_status().items():
            if status.is_running:
                running_services_list.append(
                    {"name": svc_name, "pid": status.process_id, "port": status.port}
                )
        context["running_services"] = running_services_list

        return context

    def handle_service_timeout(
        self, service_name: str, operation: str, timeout_seconds: int
    ) -> tuple[bool, str]:
        """
        Handle service operation timeout with recovery options.

        Args:
            service_name: Name of the service
            operation: Operation that timed out
            timeout_seconds: Timeout duration

        Returns:
            Tuple of (recovery_success, message)
        """
        try:
            logger.error(
                f"⏰ Timeout en operación '{operation}' para {service_name} ({timeout_seconds}s)"
            )

            # Log timeout context
            context = self._create_enhanced_error_context(service_name, operation)
            logger.error(f"Contexto del timeout: {context}")

            # Attempt recovery based on operation type
            if operation == "start":
                # Try to find and kill any partially started process
                process = self._find_service_process(service_name)
                if process:
                    try:
                        logger.warning(
                            f"🔄 Terminando proceso parcialmente iniciado: PID {process.pid}"
                        )
                        process.terminate()
                        process.wait(timeout=5)
                        return (
                            True,
                            f"Proceso parcialmente iniciado terminado (PID: {process.pid})",
                        )
                    except Exception as e:
                        logger.error(f"❌ Error terminando proceso: {e}")
                        return False, f"No se pudo limpiar proceso parcial: {e}"

            elif operation == "stop":
                # Try force kill if graceful stop timed out
                process = self._find_service_process(service_name)
                if process:
                    try:
                        logger.warning(
                            f"💀 Forzando terminación del proceso: PID {process.pid}"
                        )
                        process.kill()
                        process.wait(timeout=5)
                        self.clear_cache()
                        return True, f"Proceso forzado a terminar (PID: {process.pid})"
                    except Exception as e:
                        logger.error(f"❌ Error en terminación forzada: {e}")
                        return False, f"No se pudo forzar terminación: {e}"

            return (
                False,
                f"Timeout en {operation} - no se pudo recuperar automáticamente",
            )

        except Exception as e:
            logger.error(f"❌ Error manejando timeout: {e}")
            return False, f"Error en manejo de timeout: {e}"

    def validate_service_environment(self, service_name: str) -> tuple[bool, list[str]]:
        """
        Validate the environment for a specific service.

        Args:
            service_name: Name of the service to validate

        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        issues = []

        try:
            # Check if service exists
            if service_name not in self.SERVICES:
                issues.append(f"Servicio '{service_name}' no está definido")
                return False, issues

            service_config = self.SERVICES[service_name]

            # Check script file exists
            script_path = Path(service_config["script"])
            if not script_path.exists():
                issues.append(f"Script no encontrado: {script_path}")

            # Check Poetry availability
            if not self._check_poetry_available():
                issues.append("Poetry no está disponible")

            # Check system resources
            if not self._check_system_resources():
                issues.append("Recursos del sistema insuficientes")

            # Check service dependencies
            deps_ok, deps_msg = self._check_service_dependencies(service_name)
            if not deps_ok:
                issues.append(f"Dependencias: {deps_msg}")

            # Check port availability (if service uses a port)
            if service_config["port"]:
                if self.is_port_in_use(service_config["port"]):
                    conflicting_process = self._get_process_using_port(
                        service_config["port"]
                    )
                    issues.append(
                        f"Puerto {service_config['port']} ocupado por: {conflicting_process}"
                    )

            # Check service dependencies are running
            deps_running, missing_deps = self.check_dependencies(service_name)
            if not deps_running:
                issues.append(
                    f"Servicios dependientes no activos: {', '.join(missing_deps)}"
                )

            return len(issues) == 0, issues

        except Exception as e:
            issues.append(f"Error validando entorno: {e}")
            return False, issues

    def get_service_recovery_suggestions(
        self, service_name: str, error_type: str
    ) -> list[str]:
        """
        Get recovery suggestions for a specific service error.

        Args:
            service_name: Name of the service
            error_type: Type of error that occurred

        Returns:
            List of recovery suggestions
        """
        suggestions = []

        try:
            # General suggestions based on error type
            if error_type == "startup_failed":
                suggestions.extend(
                    [
                        "Verifica que todas las dependencias estén instaladas: poetry install",
                        "Revisa los logs del servicio para errores específicos",
                        "Verifica la configuración en config.yaml",
                        "Asegúrate de que no hay conflictos de puertos",
                    ]
                )

            elif error_type == "timeout":
                suggestions.extend(
                    [
                        "Verifica la carga del sistema (CPU, memoria)",
                        "Cierra otras aplicaciones que consuman recursos",
                        "Reinicia el sistema si es necesario",
                        "Aumenta el tiempo de espera si es posible",
                    ]
                )

            elif error_type == "port_conflict":
                service_config = self.SERVICES.get(service_name, {})
                if service_config.get("port"):
                    suggestions.extend(
                        [
                            f"Detén otros procesos usando el puerto {service_config['port']}",
                            "Cambia el puerto en la configuración",
                            "Usa 'netstat -tulpn' para ver qué proceso usa el puerto",
                        ]
                    )

            # Service-specific suggestions
            if service_name == "simulation":
                suggestions.extend(
                    [
                        "Verifica que SUMO esté instalado: sumo --version",
                        "Revisa que los archivos de mapa estén en assets/sumo_maps/",
                        "Verifica la configuración de SUMO en config.yaml",
                    ]
                )

            elif service_name == "decision":
                suggestions.extend(
                    [
                        "Verifica TensorFlow: python -c 'import tensorflow as tf; print(tf.__version__)'",
                        "Revisa la configuración de GPU/CUDA si usas GPU",
                        "Verifica que el modelo DQN esté disponible",
                    ]
                )

            elif service_name == "detection":
                suggestions.extend(
                    [
                        "Verifica YOLOv8: python -c 'import ultralytics'",
                        "Revisa que OpenCV esté instalado: python -c 'import cv2'",
                        "Verifica que el modelo YOLO esté en assets/yolo_models/",
                    ]
                )

            elif service_name == "reporting":
                suggestions.extend(
                    [
                        "Verifica la configuración de la base de datos",
                        "Revisa los permisos de escritura en el directorio de reportes",
                    ]
                )

            return suggestions

        except Exception as e:
            logger.error(f"❌ Error obteniendo sugerencias de recuperación: {e}")
            return ["Error obteniendo sugerencias de recuperación"]

    def create_service_diagnostic_report(self, service_name: str) -> dict[str, Any]:
        """
        Create a comprehensive diagnostic report for a service.

        Args:
            service_name: Name of the service

        Returns:
            Diagnostic report dictionary
        """
        try:
            report = {
                "service_name": service_name,
                "timestamp": datetime.now().isoformat(),
                "status": {},
                "environment": {},
                "dependencies": {},
                "resources": {},
                "errors": {},
                "suggestions": [],
            }

            # Service status
            status = self.get_service_status(service_name)
            report["status"] = {
                "is_running": status.is_running,
                "process_id": status.process_id,
                "start_time": (
                    status.start_time.isoformat() if status.start_time else None
                ),
                "runtime_seconds": status.runtime_seconds,
                "port": status.port,
            }

            # Environment validation
            env_valid, env_issues = self.validate_service_environment(service_name)
            report["environment"] = {"is_valid": env_valid, "issues": env_issues}

            # Dependencies check
            deps_running, missing_deps = self.check_dependencies(service_name)
            report["dependencies"] = {
                "all_running": deps_running,
                "missing": missing_deps,
                "required": self.get_service_dependencies().get(service_name, []),
            }

            # Health check
            health = self.check_service_health(service_name)
            report["health"] = health

            # Error statistics
            error_stats = self.get_error_statistics()
            report["errors"] = {
                "total_errors": sum(error_stats.values()),
                "error_breakdown": error_stats,
            }

            # Recovery suggestions
            if not status.is_running or not env_valid or not health["healthy"]:
                report["suggestions"] = self.get_service_recovery_suggestions(
                    service_name, "general"
                )

            return report

        except Exception as e:
            logger.error(f"❌ Error creando reporte diagnóstico: {e}")
            return {
                "service_name": service_name,
                "error": f"Error creando reporte: {e}",
                "timestamp": datetime.now().isoformat(),
            }
