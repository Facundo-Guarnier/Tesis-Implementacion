import logging
from typing import Any

from pydantic import ValidationError

from src.traffic_system.core.api_helper import APIRequestHelper
from src.traffic_system.core.api_models import ReportResponse, SimulationStatusResponse
from src.traffic_system.core.config_loader import load_app_settings
from src.traffic_system.core.config_models import AppSettings


class ReportAPI:
    def __init__(self, app_settings: AppSettings | None = None) -> None:
        # TODO: Eliminar el uso de load_app_settings, ya que deberia cargar desde la configuración global.
        self.app_settings = load_app_settings()
        self.__url = self.app_settings.base_url

    def _safe_request(
        self, endpoint: str, method: str = "GET", **kwargs: Any
    ) -> dict[str, Any] | None:
        """
        Delegated to APIRequestHelper.safe_request for DRY compliance.
        """
        return APIRequestHelper.safe_request(self.__url, endpoint, method, **kwargs)

    def get_report(self) -> ReportResponse | None:
        """
        Obtener el reporte de la simulación. Incluye:
        - Tiempos de espera de cada zona.
        - Estados de los semáforos.

        Returns:
            ReportResponse | None: Respuesta tipada con datos del reporte
        """
        response_data = self._safe_request("/reporte")
        if response_data is None:
            return None

        try:
            return ReportResponse.model_validate(response_data)
        except ValidationError as e:
            logger = logging.getLogger(f"{self.__class__.__name__}.get_report")
            logger.error(f"Error validando respuesta: {e}")
            return None

    def is_simulation_running(self) -> bool:
        """
        Verificar si la simulación está en ejecución.
        """
        response_data = self._safe_request("/simulacion")
        if response_data is None:
            return False

        try:
            simulation_status = SimulationStatusResponse.model_validate(response_data)
            return simulation_status.simulacion
        except ValidationError as e:
            logger = logging.getLogger(
                f"{self.__class__.__name__}.is_simulation_running"
            )
            logger.error(f"Error validando respuesta: {e}")
            return False
