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
from typing import Any

import psutil

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
    cpu_percent: float = 0.0
    memory_mb: float = 0.0
    runtime_seconds: int = 0


class ServiceManager:
    """Manages traffic system microservices."""

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

    def __init__(self) -> None:
        """Initialize the service manager."""
        self._process_cache: dict[str, psutil.Process] = {}
        self._last_update = 0
        self._cache_duration = 2  # Cache duration in seconds

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

                try:
                    cpu_percent = process.cpu_percent()
                    memory_info = process.memory_info()
                    memory_mb = memory_info.rss / 1024 / 1024  # Convert to MB
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    cpu_percent = 0.0
                    memory_mb = 0.0

                return ServiceStatus(
                    name=service_name,
                    is_running=True,
                    process_id=process.pid,
                    start_time=create_time,
                    command=" ".join(service_config["command"]),
                    port=service_config["port"],
                    cpu_percent=cpu_percent,
                    memory_mb=memory_mb,
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
            and current_time - self._last_update < self._cache_duration
        ):
            try:
                process = self._process_cache[service_name]
                if process.is_running():
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
                            self._last_update = int(current_time)
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

    def get_system_resources(self) -> dict[str, float]:
        """
        Get current system resource usage.

        Returns:
            Dictionary with system resource information
        """
        try:
            return {
                "cpu_percent": psutil.cpu_percent(interval=1),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_percent": psutil.disk_usage("/").percent,
                "load_average": (
                    os.getloadavg()[0] if hasattr(os, "getloadavg") else 0.0
                ),
            }
        except Exception as e:
            logger.error(f"❌ Error getting system resources: {e}")
            return {
                "cpu_percent": 0.0,
                "memory_percent": 0.0,
                "disk_percent": 0.0,
                "load_average": 0.0,
            }

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

            # Check resource usage
            if status.cpu_percent > 80:
                health_info["issues"].append(
                    f"Alto uso de CPU: {status.cpu_percent:.1f}%"
                )
                health_info["recommendations"].append("Revisar carga del sistema")

            if status.memory_mb > 1000:  # More than 1GB
                health_info["issues"].append(
                    f"Alto uso de memoria: {status.memory_mb:.1f}MB"
                )
                health_info["recommendations"].append("Revisar uso de memoria")

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
        self._last_update = 0
        logger.info("🔄 Cache de procesos limpiado")

    def start_service(self, service_name: str) -> tuple[bool, str]:
        """
        Start a service using poetry run.

        Args:
            service_name: Name of the service to start

        Returns:
            Tuple of (success, message)
        """
        if service_name not in self.SERVICES:
            error_msg = f"Servicio desconocido: {service_name}"
            logger.error(f"❌ {error_msg}")
            return False, error_msg

        try:
            # Check if service is already running
            status = self.get_service_status(service_name)
            if status.is_running:
                msg = f"El servicio {service_name} ya está ejecutándose (PID: {status.process_id})"
                logger.info(f"ℹ️ {msg}")
                return True, msg

            # Check for port conflicts
            service_config = self.SERVICES[service_name]
            if service_config["port"] and self.is_port_in_use(service_config["port"]):
                error_msg = f"Puerto {service_config['port']} ya está en uso"
                logger.error(f"❌ {error_msg}")
                return False, error_msg

            # Start the service
            command: list[str] = service_config["command"]
            logger.info(f"🚀 Iniciando servicio {service_name}: {' '.join(command)}")

            # Start process in background
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=os.getcwd(),
                creationflags=(
                    subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0
                ),
            )

            # Give the process a moment to start
            time.sleep(2)

            # Check if process is still running
            if process.poll() is None:
                # Clear cache to force fresh lookup
                self.clear_cache()

                success_msg = f"Servicio {service_name} iniciado correctamente (PID: {process.pid})"
                logger.info(f"✅ {success_msg}")
                return True, success_msg
            else:
                # Process died immediately
                stdout, stderr = process.communicate()
                error_msg = f"El servicio {service_name} falló al iniciar"
                if stderr:
                    error_msg += f": {stderr.decode()[:200]}"
                logger.error(f"❌ {error_msg}")
                return False, error_msg

        except FileNotFoundError:
            error_msg = "Poetry no encontrado. Asegúrate de que Poetry esté instalado y en el PATH"
            logger.error(f"❌ {error_msg}")
            return False, error_msg
        except Exception as e:
            error_msg = f"Error iniciando servicio {service_name}: {str(e)}"
            logger.error(f"❌ {error_msg}")
            return False, error_msg

    def stop_service(self, service_name: str) -> tuple[bool, str]:
        """
        Stop a running service gracefully.

        Args:
            service_name: Name of the service to stop

        Returns:
            Tuple of (success, message)
        """
        if service_name not in self.SERVICES:
            error_msg = f"Servicio desconocido: {service_name}"
            logger.error(f"❌ {error_msg}")
            return False, error_msg

        try:
            # Find the service process
            process = self._find_service_process(service_name)

            if not process:
                msg = f"El servicio {service_name} no está ejecutándose"
                logger.info(f"ℹ️ {msg}")
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

        except Exception as e:
            error_msg = f"Error deteniendo servicio {service_name}: {str(e)}"
            logger.error(f"❌ {error_msg}")
            return False, error_msg

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
