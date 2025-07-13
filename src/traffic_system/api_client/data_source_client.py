import inspect
import logging

import requests  # type: ignore


class DecisionAPI:
    def __init__(self, base_url):
        logging.basicConfig(level=logging.DEBUG)
        self.base_url = base_url

    def get_quantities(self) -> dict[str, int] | None:
        """
        Obtener la cantidad de vehículos en cada una de las zonas.

        Returns:
            dict[str, int]: {zona_nombre: cantidad_detecciones}
        """
        endpoint = "/cantidad"
        response = requests.get(self.base_url + endpoint)
        if response.status_code == 200:
            return response.json()

        else:
            return None

    def get_zone_quantity(self, zona_name: str) -> dict | None:
        """
        Obtener la cantidad de vehículos en una zona específica.
        """
        endpoint = f"/cantidad/{zona_name}"
        response = requests.get(self.base_url + endpoint)
        if response.status_code == 200:
            return response.json()
        else:
            return None

    def get_all_traffic_light_states(self) -> dict | None:
        """
        Obtener el estado de todos los semáforos.

        Returns:
            dict: {"estado": list[str]}
                list[str]: [estado_semaforo_1, estado_semaforo_2, ...]
        """
        endpoint = "/semaforo"
        response = requests.get(self.base_url + endpoint)
        if response.status_code == 200:
            return response.json()
        else:
            return None

    def get_traffic_light_state(self, light_id: int) -> dict | None:
        """
        Obtener el estado de un semáforo.
        """
        endpoint = f"/semaforo/{light_id}"
        response = requests.get(self.base_url + endpoint)
        if response.status_code == 200:
            return response.json()
        else:
            return None

    def get_zone_wait_time(self, zone_id) -> dict | None:
        """
        Obtener el tiempo total de espera de una zona en la simulación.
        """
        endpoint = f"/espera/{zone_id}"
        response = requests.get(self.base_url + endpoint)
        if response.status_code == 200:
            return response.json()
        else:
            return None

    def get_wait_times(self) -> dict | None:
        """
        Obtener el tiempo total de espera de todas las zonas en la simulación.

        Returns:
            dict: {"tiempo_espera_total": int, "tiempos_espera": list[float]}
        """
        endpoint = "/espera"
        response = requests.get(self.base_url + endpoint)
        if response.status_code == 200:
            return response.json()
        else:
            return None

    def advance_simulation(self, steps: int) -> dict | None:
        """
        Avanzar la simulación un número de pasos.
        """

        endpoint = "/avanzar"
        response = requests.put(self.base_url + endpoint, params={"steps": steps})
        if response.status_code == 200:
            return response.json()
        else:
            return None

    def set_traffic_light_states(self, states: list[str]) -> dict | None:
        """
        Cambiar el estado de un semáforo.
        """
        endpoint = "/semaforo"

        data_payload = []
        for light_id in range(len(states)):
            data_payload.append({"id": str(light_id + 1), "estado": states[light_id]})

        response = requests.put(self.base_url + endpoint, json={"data": data_payload})

        if response.status_code == 200:
            return response.json()
        else:
            return None

    def is_simulation_running(self) -> bool:
        """
        Verificar si la simulación está en ejecución.
        """
        logger = logging.getLogger(
            f" {self.__class__.__name__}.{inspect.currentframe().f_code.co_name}"  # type: ignore
        )

        try:
            response = requests.get(f"{self.base_url}/simulacion")
            if response.status_code != 200:
                logger.error("❌ La API no está disponible")
                return False
            return response.json().get("simulacion", False)
        except requests.ConnectionError:
            logger.error(
                "❌ No se puede conectar a la API. ¿Está ejecutándose el servidor?"
            )
            return False

    def is_simulation_synchronized(self) -> bool:
        """
        Verificar si la simulación está sincronizada.
        """
        logger = logging.getLogger(
            f" {self.__class__.__name__}.{inspect.currentframe().f_code.co_name}"  # type: ignore
        )
        try:
            response = requests.get(f"{self.base_url}/sincronizacion")
            if response.status_code == 200:
                sync_data = response.json()
                logger.info(f"📊 Sincronización actual: {sync_data}")
                return sync_data.get("sincronizacion", False)
            else:
                logger.warning("⚠️ No hay simulación de comparación activa")
                return False
        except Exception as e:
            logger.error(f"❌ Error verificando sincronización: {e}")
            return False
