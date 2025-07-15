import requests

from src.traffic_system.core.api_models import ReportResponse, SimulationStatusResponse
from src.traffic_system.core.config_loader import load_app_settings
from src.traffic_system.core.config_models import AppSettings


class ReportAPI:
    def __init__(self, app_settings: AppSettings | None = None) -> None:
        # TODO: Eliminar el uso de load_app_settings, ya que deberia cargar desde la configuración global.
        self.app_settings = load_app_settings()
        self.__url = self.app_settings.base_url

    def get_report(self) -> ReportResponse | None:
        """
        Obtener el reporte de la simulación. Incluye:
        - Tiempos de espera de cada zona.
        - Estados de los semáforos.

        Returns:
            ReportResponse | None: Respuesta tipada con datos del reporte
        """
        endpoint = "/reporte"
        response = requests.get(self.__url + endpoint)
        if response.status_code == 200:
            return ReportResponse.model_validate(response.json())
        else:
            return None

    def is_simulation_running(self) -> bool:
        """
        Verificar si la simulación está en ejecución.
        """
        endpoint = "/simulacion"
        response = requests.get(self.__url + endpoint)
        if response.status_code == 200:
            simulation_status = SimulationStatusResponse.model_validate(response.json())
            return simulation_status.simulacion
        else:
            return False
