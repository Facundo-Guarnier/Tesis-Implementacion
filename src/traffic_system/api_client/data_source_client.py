import inspect
import logging

import requests
from pydantic import ValidationError

from src.traffic_system.core.api_helper import APIRequestHelper
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
    def __init__(self, base_url: str, infinite_retry: bool = False) -> None:
        logging.basicConfig(level=logging.DEBUG)
        self.base_url = base_url
        self.infinite_retry = infinite_retry

    def get_quantities(self) -> VehicleQuantitiesResponse | None:
        """
        Obtener la cantidad de vehículos en cada una de las zonas.

        Returns:
            VehicleQuantitiesResponse | None: Respuesta tipada con cantidades por zona
        """
        return APIRequestHelper.safe_request_with_validation(
            self.base_url,
            "/cantidad",
            VehicleQuantitiesResponse,
            infinite_retry=self.infinite_retry,
        )

    def get_zone_quantity(self, zona_name: str) -> VehicleQuantitiesResponse | None:
        """
        Obtener la cantidad de vehículos en una zona específica.
        """
        return APIRequestHelper.safe_request_with_validation(
            self.base_url,
            f"/cantidad/{zona_name}",
            VehicleQuantitiesResponse,
            infinite_retry=self.infinite_retry,
        )

    def get_all_traffic_light_states(self) -> TrafficLightStatesResponse | None:
        """
        Obtener el estado de todos los semáforos.

        Returns:
            TrafficLightStatesResponse | None: Respuesta tipada con estados de semáforos
        """
        return APIRequestHelper.safe_request_with_validation(
            self.base_url,
            "/semaforo",
            TrafficLightStatesResponse,
            infinite_retry=self.infinite_retry,
        )

    def get_traffic_light_state(
        self, light_id: int
    ) -> TrafficLightStateResponse | None:
        """
        Obtener el estado de un semáforo.
        """
        return APIRequestHelper.safe_request_with_validation(
            self.base_url,
            f"/semaforo/{light_id}",
            TrafficLightStateResponse,
            infinite_retry=self.infinite_retry,
        )

    def get_zone_wait_time(self, zone_id: str) -> WaitTimesResponse | None:
        """
        Obtener el tiempo total de espera de una zona en la simulación.
        """
        return APIRequestHelper.safe_request_with_validation(
            self.base_url,
            f"/espera/{zone_id}",
            WaitTimesResponse,
            infinite_retry=self.infinite_retry,
        )

    def get_wait_times(self) -> WaitTimesResponse | None:
        """
        Obtener el tiempo total de espera de todas las zonas en la simulación.

        Returns:
            WaitTimesResponse | None: Respuesta tipada con tiempos de espera
        """
        return APIRequestHelper.safe_request_with_validation(
            self.base_url,
            "/espera",
            WaitTimesResponse,
            infinite_retry=self.infinite_retry,
        )

    def advance_simulation(self, steps: int) -> SimulationStepResponse | None:
        """
        Avanzar la simulación un número de pasos.

        Args:
            steps: Número de pasos a avanzar

        Returns:
            SimulationStepResponse | None: Respuesta tipada con resultado del avance
        """
        return APIRequestHelper.safe_request_with_validation(
            self.base_url,
            "/avanzar",
            SimulationStepResponse,
            method="PUT",
            params={"steps": steps},
            infinite_retry=self.infinite_retry,
        )

    def set_traffic_light_states(self, states: list[str]) -> SuccessResponse | None:
        """
        Cambiar el estado de un semáforo.
        """
        data_payload = []
        for light_id in range(len(states)):
            data_payload.append({"id": str(light_id + 1), "estado": states[light_id]})

        return APIRequestHelper.safe_request_with_validation(
            self.base_url,
            "/semaforo",
            SuccessResponse,
            method="PUT",
            json={"data": data_payload},
            infinite_retry=self.infinite_retry,
        )

    def is_simulation_running(self) -> bool:
        """
        Verificar si la simulación está en ejecución.
        """
        logger = logging.getLogger(
            f" {self.__class__.__name__}.{inspect.currentframe().f_code.co_name}"  # type: ignore
        )

        logger.info(f"🔍 Verificando estado de la simulación {self.base_url}...")

        try:
            # Usamos APIRequestHelper.safe_request para consistencia
            response_data = APIRequestHelper.safe_request(
                self.base_url, "/simulacion", infinite_retry=self.infinite_retry
            )
            if response_data is None:
                logger.error("❌ La API no está disponible")
                return False

            simulation_status = SimulationStatusResponse.model_validate(response_data)
            return simulation_status.simulacion
        except requests.ConnectionError:
            logger.error(
                "❌ No se puede conectar a la API. ¿Está ejecutándose el servidor?"
            )
            return False
        except ValidationError as e:
            logger.error(f"❌ Error validando respuesta: {e}")
            return False

    def is_simulation_synchronized(self) -> bool:
        """
        Verificar si la simulación está sincronizada.
        """
        logger = logging.getLogger(
            f" {self.__class__.__name__}.{inspect.currentframe().f_code.co_name}"  # type: ignore
        )
        try:
            response_data = APIRequestHelper.safe_request(
                self.base_url, "/sincronizacion", infinite_retry=self.infinite_retry
            )
            if response_data is not None:
                sync_response = SynchronizationResponse.model_validate(response_data)
                logger.info(
                    f"📊 Sincronización actual: S1={sync_response.s1_time:.1f}s, S2={sync_response.s2_time or 0:.1f}s"
                )
                return sync_response.sincronizado
            else:
                logger.warning("⚠️ No hay simulación de comparación activa")
                return False
        except ValidationError as e:
            logger.error(f"❌ Error validando respuesta de sincronización: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Error verificando sincronización: {e}")
            return False
