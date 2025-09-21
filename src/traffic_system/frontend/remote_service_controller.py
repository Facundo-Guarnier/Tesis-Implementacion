"""
Controlador de servicios remotos para health checks via HTTP.

Maneja verificación de estado de servicios remotos usando endpoints /health.
"""

import time
from typing import Any, Literal

import requests

from src.traffic_system.core.config_loader import load_app_settings
from src.traffic_system.frontend.utils import (
    log_error,
    log_info,
    log_warning,
)

ServiceStatus = Literal["running", "stopped", "timeout", "error", "connection_error"]


class RemoteServiceController:
    """Controlador para servicios remotos usando health checks HTTP."""

    # Servicios remotos soportados
    REMOTE_SERVICES = ["decision", "reporting"]

    # Nombres amigables para mostrar en UI
    SERVICE_NAMES = {
        "decision": "Decisión",
        "reporting": "Reportes",
    }

    def __init__(self) -> None:
        """Inicializar el controlador de servicios remotos."""
        self._status_cache: dict[str, dict[str, Any]] = {}
        self._last_check_time: float = 0
        self._cache_duration = 3  # Cache por x segundos

        # Configuración de requests
        self.timeout = 2  # segundos timeout (aumentado para evitar timeouts prematuros)
        self.max_retries = 2  # reducido para respuesta más rápida

    def _get_service_url(self, service_name: str) -> str | None:
        """
        Obtener URL del health check para un servicio.

        Args:
            service_name: Nombre del servicio ('decision' o 'reporting')

        Returns:
            URL completa del endpoint /health o None si no está configurado
        """
        try:
            settings = load_app_settings()

            if service_name == "decision":
                ip = settings.services.remote.decision.ip
                port = settings.services.remote.decision.port
            elif service_name == "reporting":
                ip = settings.services.remote.reporting.ip
                port = settings.services.remote.reporting.port
            else:
                log_error(f"Servicio desconocido: {service_name}")
                return None

            return f"http://{ip}:{port}/health"

        except Exception as e:
            log_error(f"Error obteniendo URL para {service_name}: {e}")
            return None

    def _check_service_health(self, service_name: str) -> ServiceStatus:
        """
        Verificar el estado de un servicio remoto.

        Args:
            service_name: Nombre del servicio

        Returns:
            Estado del servicio
        """
        url = self._get_service_url(service_name)
        if not url:
            return "error"

        for attempt in range(self.max_retries):
            try:
                response = requests.get(url, timeout=self.timeout)

                if response.status_code == 200:
                    data = response.json()
                    if data.get("status") == "ok":
                        return "running"
                    else:
                        log_warning(f"{service_name}: respuesta inesperada: {data}")
                        return "error"
                else:
                    log_warning(f"{service_name}: HTTP {response.status_code}")
                    return "error"

            except requests.exceptions.ConnectionError:
                if attempt == self.max_retries - 1:
                    log_warning(
                        f"{service_name}: sin conexión después de {self.max_retries} intentos"
                    )
                    return "connection_error"

            except requests.exceptions.Timeout:
                if attempt == self.max_retries - 1:
                    log_warning(
                        f"{service_name}: timeout después de {self.max_retries} intentos"
                    )
                    return "timeout"

            except requests.exceptions.RequestException as e:
                if attempt == self.max_retries - 1:
                    log_error(f"{service_name}: error de request: {e}")
                    return "error"

            except Exception as e:
                if attempt == self.max_retries - 1:
                    log_error(f"{service_name}: error inesperado: {e}")
                    return "error"

            # Esperar antes del siguiente intento
            if attempt < self.max_retries - 1:
                time.sleep(0.5)

        return "error"

    def get_service_status(self, service_name: str) -> ServiceStatus:
        """
        Obtener el estado actual de un servicio remoto.

        Args:
            service_name: Nombre del servicio

        Returns:
            Estado actual del servicio
        """
        if service_name not in self.REMOTE_SERVICES:
            log_error(f"Servicio remoto no soportado: {service_name}")
            return "error"

        # Usar cache si está disponible y no ha expirado
        current_time = time.time()
        if (
            service_name in self._status_cache
            and current_time - self._last_check_time < self._cache_duration
        ):
            cached_status: ServiceStatus = self._status_cache[service_name]["status"]
            # Asegurar que el valor cached es del tipo correcto
            if cached_status in [
                "running",
                "stopped",
                "timeout",
                "error",
                "connection_error",
            ]:
                return cached_status

        # Verificar estado
        status = self._check_service_health(service_name)

        # Actualizar cache
        self._status_cache[service_name] = {
            "status": status,
            "last_check": current_time,
        }
        self._last_check_time = current_time

        return status

    def get_all_services_status(self) -> dict[str, ServiceStatus]:
        """
        Obtener el estado de todos los servicios remotos.

        Returns:
            Diccionario con el estado de cada servicio
        """
        status_dict = {}

        for service_name in self.REMOTE_SERVICES:
            status_dict[service_name] = self.get_service_status(service_name)

        return status_dict

    def get_service_friendly_name(self, service_name: str) -> str:
        """
        Obtener el nombre amigable de un servicio.

        Args:
            service_name: Nombre interno del servicio

        Returns:
            Nombre amigable para mostrar en UI
        """
        return self.SERVICE_NAMES.get(service_name, service_name.title())

    def is_service_running(self, service_name: str) -> bool:
        """
        Verificar si un servicio está ejecutándose.

        Args:
            service_name: Nombre del servicio

        Returns:
            True si el servicio está ejecutándose
        """
        return self.get_service_status(service_name) == "running"

    def get_status_emoji(self, status: ServiceStatus) -> str:
        """
        Obtener emoji para el estado de un servicio.

        Args:
            status: Estado del servicio

        Returns:
            Emoji correspondiente al estado
        """
        status_emojis = {
            "running": "🟢",
            "stopped": "🔴",
            "timeout": "🔴",
            "error": "🔴",
            "connection_error": "🔴",
        }
        return status_emojis.get(status, "⚪")

    def get_status_text(self, status: ServiceStatus) -> str:
        """
        Obtener texto descriptivo para el estado de un servicio.

        Args:
            status: Estado del servicio

        Returns:
            Texto descriptivo del estado
        """
        status_texts = {
            "running": "Ejecutándose",
            "stopped": "Detenido",
            "timeout": "Timeout",
            "error": "Error",
            "connection_error": "Sin conexión",
        }
        return status_texts.get(status, "Desconocido")

    def clear_cache(self) -> None:
        """Limpiar el cache de estados."""
        self._status_cache.clear()
        self._last_check_time = 0
        log_info("Cache de servicios remotos limpiado")

    def get_cache_info(self) -> dict[str, Any]:
        """
        Obtener información del cache.

        Returns:
            Información del estado del cache
        """
        current_time = time.time()
        cache_age = current_time - self._last_check_time

        return {
            "cache_size": len(self._status_cache),
            "cache_age_seconds": cache_age,
            "cache_valid": cache_age < self._cache_duration,
            "last_check": self._last_check_time,
        }

    def force_refresh(self) -> dict[str, ServiceStatus]:
        """
        Forzar actualización de todos los servicios remotos.

        Returns:
            Estados actualizados de todos los servicios
        """
        self.clear_cache()
        return self.get_all_services_status()
