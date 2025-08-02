import inspect
import logging
import time

import numpy as np
import tensorflow as tf
from numpy import ndarray as NDArray

from src.traffic_system.api_client.data_source_client import DecisionAPI
from src.traffic_system.core.api_models import (
    VehicleQuantitiesResponse,
    WaitTimesResponse,
)
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
            # Primero intentar cargar normalmente
            self.model = tf.keras.models.load_model(path_modelo)
        except Exception as e:
            logging.warning(f"Error cargando modelo normalmente: {e}")
            try:
                # Intentar cargar con custom_objects para manejar funciones obsoletas
                custom_objects = {"mse": tf.keras.metrics.MeanSquaredError()}
                self.model = tf.keras.models.load_model(
                    path_modelo, custom_objects=custom_objects
                )
            except Exception as e2:
                logging.warning(f"Error cargando con custom_objects: {e2}")
                # Como último recurso, cargar sin compilar y recompilar
                self.model = tf.keras.models.load_model(path_modelo, compile=False)

        # Siempre recompilar para asegurar compatibilidad
        self.model.compile(
            optimizer="adam",
            loss=tf.keras.losses.MeanSquaredError(),
            metrics=[tf.keras.metrics.MeanSquaredError()],
        )

        # Detectar automáticamente el tamaño del estado basado en el modelo cargado
        model_input_shape = self.model.input_shape
        if model_input_shape is not None and len(model_input_shape) > 1:
            detected_state_size = model_input_shape[1]
            logging.info(f"🔍 Detectado state_size del modelo: {detected_state_size}")
            self.state_size = detected_state_size
        else:
            # Fallback al valor por defecto
            logging.warning("⚠️ No se pudo detectar state_size, usando 48 por defecto")
            self.state_size = 48

        self._set_action_space()
        self.zone_weights: list[float] = self.decision_settings.ponderaciones_zonas

        # Variables para historial temporal (solo si state_size es 48)
        if self.state_size == 48:
            self.state_history: list = []
            self.max_history_length = 2
            self.use_temporal_history = True
            logging.info("✅ Usando estado con historial temporal (48 características)")
        else:
            self.use_temporal_history = False
            logging.info(f"✅ Usando estado simple ({self.state_size} características)")

        # Cache de datos API
        self._cached_wait_times_response: WaitTimesResponse | None = None
        self._cached_quantities_response: VehicleQuantitiesResponse | None = (
            None  # TODO: Generalizar esto, archivo de config? otro lugar?
        )

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
        Obtiene el estado actual del entorno de forma compatible.

        - Si state_size = 12: Estado simple (solo tiempos de espera)
        - Si state_size = 48: Estado completo con historial temporal
        """
        if self.state_size == 12:
            return self._get_simple_state()
        elif self.state_size == 48:
            return self._get_temporal_state()
        else:
            raise RuntimeError(f"state_size no soportado: {self.state_size}")

    def _get_simple_state(self) -> NDArray:
        """
        Estado simple original de 12 características (solo tiempos de espera).
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

    def _get_temporal_state(self) -> NDArray:
        """
        Estado de 48 características con historial temporal:
        - 12 tiempos de espera actuales
        - 12 cantidades de vehículos actuales
        - 12 tiempos de espera previos
        - 12 cantidades de vehículos previos
        """
        # Actualizar datos de simulación
        self._update_simulation_data()

        # Obtener datos con reintentos
        wait_times_response = self._cached_wait_times_response
        quantities_response = self._cached_quantities_response

        if wait_times_response is None:
            raise RuntimeError("No se pudo obtener tiempos de espera")

        if quantities_response is None:
            raise RuntimeError("No se pudo obtener cantidades de vehículos")

        # Preparar observación actual
        wait_times = wait_times_response.tiempos_espera
        quantities = list(quantities_response.cantidades.values())

        # Validar datos
        if len(wait_times) != 12 or len(quantities) != 12:
            raise RuntimeError(
                f"Datos inválidos: {len(wait_times)} tiempos, {len(quantities)} cantidades"
            )

        # Combinar observación actual
        current_observation = wait_times + quantities

        # Gestionar historial temporal
        if hasattr(self, "state_history"):
            self.state_history.append(current_observation)
            if len(self.state_history) > self.max_history_length:
                self.state_history.pop(0)

            # Construir estado completo
            if len(self.state_history) >= 2:
                previous_observation = self.state_history[-2]
                complete_state = current_observation + previous_observation
            else:
                # Si no hay historial, duplicar observación actual
                complete_state = current_observation + current_observation
        else:
            # Fallback si no hay historial inicializado
            complete_state = current_observation + current_observation

        normalized_state = self._normalize_state(complete_state)
        return np.reshape(normalized_state, [1, self.state_size])

    def _normalize_state(self, state: list) -> NDArray:
        """Normaliza el estado de manera robusta."""
        state_array = np.array(state, dtype=np.float32)

        # Normalización por componentes
        mid_point = len(state_array) // 2

        # Normalizar tiempos de espera
        wait_times_part = state_array[:mid_point]
        wait_max = np.max(wait_times_part) if np.max(wait_times_part) > 0 else 1.0
        normalized_waits = wait_times_part / wait_max

        # Normalizar cantidades
        quantities_part = state_array[mid_point:]
        qty_max = np.max(quantities_part) if np.max(quantities_part) > 0 else 1.0
        normalized_quantities = quantities_part / qty_max

        # Combinar y verificar
        normalized_state = np.concatenate([normalized_waits, normalized_quantities])
        normalized_state = np.nan_to_num(
            normalized_state, nan=0.0, posinf=1.0, neginf=0.0
        )

        return normalized_state.astype(np.float32)

    def _update_simulation_data(self) -> None:
        """Actualiza los datos de simulación con reintentos (solo para estado temporal)."""
        if not self.use_temporal_history:
            return

        max_retries = 3
        retry_delay = 0.01

        # Intentar obtener tiempos de espera
        for attempt in range(max_retries):
            self._cached_wait_times_response = self._service.get_wait_times()
            if self._cached_wait_times_response is not None:
                break
            if attempt < max_retries - 1:
                time.sleep(retry_delay)

        # Intentar obtener cantidades
        for attempt in range(max_retries):
            self._cached_quantities_response = self._service.get_quantities()
            if self._cached_quantities_response is not None:
                break
            if attempt < max_retries - 1:
                time.sleep(retry_delay)

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
