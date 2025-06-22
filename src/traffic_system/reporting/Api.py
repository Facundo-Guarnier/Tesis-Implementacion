import requests  # type: ignore

from src.traffic_system.core.config_loader import app_settings


class ApiReporte:
    def __init__(self) -> None:
        self.__url = app_settings["base_url"]

    def getReporte(self) -> dict:
        """
        Obtener el reporte de la simulación. Incluye:
        - Tiempos de espera de cada zona.
        - Estados de los semáforos.

        Returns:
            dict: {
                "steps": int,
                "tiempos_espera": list[float],
                "estados_semaforos": list[str]
            }
        """

        endpoint = "/reporte"
        response = requests.get(self.__url + endpoint)
        if response.status_code == 200:
            return response.json()
        else:
            return {"steps": -1, "tiempos_espera": [], "estados_semaforos": []}

    def getSimulacionOK(self) -> bool:
        """
        Verificar si la simulación está en ejecución.
        """
        endpoint = "/simulacion"
        response = requests.get(self.__url + endpoint)
        if response.status_code == 200:
            return response.json()["simulacion"]
        else:
            return False
