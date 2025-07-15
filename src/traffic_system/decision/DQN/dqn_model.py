import inspect
import logging
import time

import numpy as np
import tensorflow as tf
from numpy import ndarray as NDArray

from src.traffic_system.api_client.data_source_client import DecisionAPI
from src.traffic_system.core.config_loader import load_app_settings
from src.traffic_system.core.config_models import DecisionSettings


class DQNModel:
    def __init__(
        self, path_modelo: str, decision_settings: DecisionSettings | None = None
    ) -> None:
        logging.basicConfig(level=logging.DEBUG)
        # TODO: Eliminar el uso de load_app_settings, ya que deberia cargar desde la configuración global.
        self.settings = load_app_settings()
        self.decision_settings = load_app_settings().decision

        self._service = DecisionAPI(self.settings.base_url)

        # Cargar modelo con manejo de compatibilidad
        try:
            # Intentar cargar con custom_objects para manejar funciones obsoletas
            custom_objects = {"mse": tf.keras.metrics.MeanSquaredError()}
            self.model = tf.keras.models.load_model(
                path_modelo, custom_objects=custom_objects
            )
        except Exception as e:
            logging.error(f"Error cargando con custom_objects: {e}")
            self.model = tf.keras.models.load_model(path_modelo, compile=False)
            self.model.compile(
                optimizer="adam",
                loss=tf.keras.losses.MeanSquaredError(),
                metrics=[tf.keras.metrics.MeanSquaredError()],
            )

        self.state_size = 12
        self._set_action_space()
        self.zone_weights: list[float] = self.decision_settings.ponderaciones_zonas

    # TODO: Generalizar esto, archivo de config? otro lugar?
    def _set_action_space(self) -> None:
        """
        Devuelve el espacio de acciones está formado por una lista de tuplas, donde cada tupla representa el estado de los 4 semaforos.
        - Ej: [('GGGGGGrrrrr', 'GgGGrrrrGgGg', 'GgGgGgGGrrrr', 'GGGrrrrGGg'), ...]
        """
        traffic_light_1_phases = ["GGGGGGrrrrr", "rrrrrrGGgGG"]
        traffic_light_2_phases = ["GGGrrrrrGGg", "rrrGGGGGrrr"]
        traffic_light_3_phases = ["GGgGGGrrrrr", "rrrrrrGGGGG"]
        traffic_light_4_phases = ["GGGrrrrGGg", "rrrGGGGrrr"]

        self._action_space = [
            f"{s1}-{s2}-{s3}-{s4}"
            for s1 in traffic_light_1_phases
            for s2 in traffic_light_2_phases
            for s3 in traffic_light_3_phases
            for s4 in traffic_light_4_phases
        ]

    def run_inference(self) -> None:
        """
        Utilizar el modelo entrenado.
        """
        logger = logging.getLogger(
            f" {self.__class__.__name__}.{inspect.currentframe().f_code.co_name}"  # type: ignore
        )

        logger.info("🔄 Verificando que la simulación esté lista...")
        while not self._service.is_simulation_running():
            logger.info("⌛ Esperando que la simulación esté lista...")
            time.sleep(1)
        logger.info("✅ La simulación está lista.")

        logger.info("🔄 Verificando que la simulación esté sincronizada...")
        while not self._service.is_simulation_synchronized():
            logger.info("⌛ Esperando que la simulación esté sincronizada...")
            time.sleep(1)
        logger.info("✅ La simulación está sincronizada.")

        # TODO: Agregar que avance hasta los X pasos iniciales de la simulación para que las calles estén cargadas.

        logger.info("🚦 Comenzando la toma de decisiones...")
        done = False
        while not done:
            state = self._get_current_state()
            action_prediction = self.model.predict(state, verbose=0)
            done = self._execute_action_and_advance(int(np.argmax(action_prediction)))

    def _get_current_state(self) -> NDArray:
        """
        Define el estado:
        - El tiempo de espera de los vehículos en las intersecciones.
        - No incluye el color de los semáforos porque estaría duplicando datos con respecto a la accion.
        - Ej: [1,3,5,0,1,2,4,2,6,3,9,10]

        Returns:
            NDArray: Estado actual normalizado. Ej: [0.1, 0.3, 0.5, 0, 0.1, 0.2, 0.4, 0.2, 0.6, 0.3, 0.9, 1]
        """
        #! Tiempo
        wait_times_response = self._service.get_wait_times()
        if wait_times_response is None:
            raise RuntimeError("No se pudo obtener los tiempos de espera del servicio")

        state_raw = tuple(wait_times_response.tiempos_espera)

        #! Ponderar mas un semáforo que otro
        weighted_state = tuple(
            [
                round(state_raw[i] * self.zone_weights[i], 2)
                for i in range(len(state_raw))
            ]
        )

        max_wait_time = max(weighted_state)
        if max_wait_time == 0:
            return np.reshape(weighted_state, [1, self.state_size])

        else:
            #! Normalizar los tiempos de espera
            normalized_state = tuple(
                [round(wait_time / max_wait_time, 2) for wait_time in weighted_state]
            )
            return np.reshape(normalized_state, [1, self.state_size])

    def _execute_action_and_advance(self, action_index: int) -> bool:
        """
        Realiza las siguientes tareas:
        1. Ejecuta la acción en SUMO.
        2. Simula 15 pasos (para tener una recompensa mas realista).
        3. Devuelve el nuevo estado, la recompensa y si se ha terminado la epoca.
        """

        action_phases_str = self._action_space[action_index]
        action_phases_list = action_phases_str.split("-")

        #! Cambiar el estado de los semáforos en SUMO
        self._service.set_traffic_light_states(states=action_phases_list)

        #! Avanzar en SUMO con la acción seleccionada
        response = self._service.advance_simulation(steps=15)
        if response is None:
            return False
        else:
            done: bool = response.done
            return done
