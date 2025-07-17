import inspect
import logging
from typing import cast

import requests

from src.traffic_system.core.api_models import (
    SimulationStatusResponse,
    SimulationStepResponse,
    SuccessResponse,
    SynchronizationResponse,
    TrafficLightStateResponse,
    TrafficLightStatesResponse,
    VehicleQuantitiesResponse,
    WaitTimesResponse,
)


class DecisionAPI:
    def __init__(self, base_url: str) -> None:
        logging.basicConfig(level=logging.DEBUG)
        self.base_url = base_url

    def get_quantities(self) -> VehicleQuantitiesResponse | None:
        """
        Obtener la cantidad de vehículos en cada una de las zonas.

        Returns:
            VehicleQuantitiesResponse | None: Respuesta tipada con cantidades por zona
        """
        endpoint = "/cantidad"
        response = requests.get(self.base_url + endpoint)
        if response.status_code == 200:
            # TODO: No implementar cast
            return cast(
                VehicleQuantitiesResponse,
                VehicleQuantitiesResponse.model_validate(response.json()),
            )
        return None

    def get_zone_quantity(self, zona_name: str) -> VehicleQuantitiesResponse | None:
        """
        Obtener la cantidad de vehículos en una zona específica.
        """
        endpoint = f"/cantidad/{zona_name}"
        response = requests.get(self.base_url + endpoint)
        if response.status_code == 200:
            return VehicleQuantitiesResponse.model_validate(response.json())
        return None

    def get_all_traffic_light_states(self) -> TrafficLightStatesResponse | None:
        """
        Obtener el estado de todos los semáforos.

        Returns:
            TrafficLightStatesResponse | None: Respuesta tipada con estados de semáforos
        """
        endpoint = "/semaforo"
        response = requests.get(self.base_url + endpoint)
        if response.status_code == 200:
            return TrafficLightStatesResponse.model_validate(response.json())
        return None

    def get_traffic_light_state(
        self, light_id: int
    ) -> TrafficLightStateResponse | None:
        """
        Obtener el estado de un semáforo.
        """
        endpoint = f"/semaforo/{light_id}"
        response = requests.get(self.base_url + endpoint)
        if response.status_code == 200:
            return TrafficLightStateResponse.model_validate(response.json())
        return None

    def get_zone_wait_time(self, zone_id: str) -> WaitTimesResponse | None:
        """
        Obtener el tiempo total de espera de una zona en la simulación.
        """
        endpoint = f"/espera/{zone_id}"
        response = requests.get(self.base_url + endpoint)
        if response.status_code == 200:
            return WaitTimesResponse.model_validate(response.json())
        return None

    def get_wait_times(self) -> WaitTimesResponse | None:
        """
        Obtener el tiempo total de espera de todas las zonas en la simulación.

        Returns:
            WaitTimesResponse | None: Respuesta tipada con tiempos de espera
        """
        endpoint = "/espera"
        response = requests.get(self.base_url + endpoint)
        if response.status_code == 200:
            return WaitTimesResponse.model_validate(response.json())
        return None

    def advance_simulation(self, steps: int) -> SimulationStepResponse | None:
        """
        Avanzar la simulación un número de pasos.

        Args:
            steps: Número de pasos a avanzar

        Returns:
            SimulationStepResponse | None: Respuesta tipada con resultado del avance
        """
        endpoint = "/avanzar"
        response = requests.put(self.base_url + endpoint, params={"steps": steps})
        if response.status_code == 200:
            return SimulationStepResponse.model_validate(response.json())
        return None

    def set_traffic_light_states(self, states: list[str]) -> SuccessResponse | None:
        """
        Cambiar el estado de un semáforo.
        """
        endpoint = "/semaforo"

        data_payload = []
        for light_id in range(len(states)):
            data_payload.append({"id": str(light_id + 1), "estado": states[light_id]})

        response = requests.put(self.base_url + endpoint, json={"data": data_payload})

        if response.status_code == 200:
            return SuccessResponse.model_validate(response.json())
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
            simulation_status = SimulationStatusResponse.model_validate(response.json())
            return simulation_status.simulacion
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
                sync_response = SynchronizationResponse.model_validate(response.json())
                logger.info(
                    f"📊 Sincronización actual: S1={sync_response.s1_time:.1f}s, S2={sync_response.s2_time or 0:.1f}s"
                )
                return sync_response.sincronizado
            else:
                logger.warning("⚠️ No hay simulación de comparación activa")
                return False
        except Exception as e:
            logger.error(f"❌ Error verificando sincronización: {e}")
            return False
