import inspect
import logging
import time

import numpy as np
import tensorflow as tf
from numpy import ndarray as NDArray

from src.traffic_system.api_client.data_source_client import ApiDecision
from src.traffic_system.core.config_loader import load_app_settings
from src.traffic_system.core.config_models import DecisionSettings


class DQN:
    def __init__(
        self, path_modelo: str, decision_settings: DecisionSettings | None = None
    ) -> None:
        logging.basicConfig(level=logging.DEBUG)
        # TODO: Eliminar el uso de load_app_settings, ya que deberia cargar desde la configuración global.
        self.settings = load_app_settings()
        self.decision_settings = load_app_settings().decision

        self.__service = ApiDecision(self.settings.base_url)

        # Cargar modelo con manejo de compatibilidad
        try:
            # Intentar cargar con custom_objects para manejar funciones obsoletas
            custom_objects = {"mse": tf.keras.metrics.MeanSquaredError()}
            self.model = tf.keras.models.load_model(
                path_modelo, custom_objects=custom_objects
            )
        except Exception as e:
            logging.error(f"Error cargando con custom_objects: {e}")
            # Intentar cargar normalmente
            self.model = tf.keras.models.load_model(path_modelo, compile=False)
            # Recompilar el modelo manualmente
            self.model.compile(
                optimizer="adam",
                loss=tf.keras.losses.MeanSquaredError(),
                metrics=[tf.keras.metrics.MeanSquaredError()],
            )

        self.state_size = 12
        self.__setEspacioAcciones()
        self.ponderaciones_zonas: list[float] = (
            self.decision_settings.ponderaciones_zonas
        )

    # TODO: Generalizar esto, archivo de config? otro lugar?
    def __setEspacioAcciones(self) -> None:
        """
        Devuelve el espacio de acciones está formado por una lista de tuplas, donde cada tupla representa el estado de los 4 semaforos.
        - Ej: [('GGGGGGrrrrr', 'GgGGrrrrGgGg', 'GgGgGgGGrrrr', 'GGGrrrrGGg'), ...]
        """
        semaforo_1 = ["GGGGGGrrrrr", "rrrrrrGGgGG"]
        semaforo_2 = ["GGGrrrrrGGg", "rrrGGGGGrrr"]
        semaforo_3 = ["GGgGGGrrrrr", "rrrrrrGGGGG"]
        semaforo_4 = ["GGGrrrrGGg", "rrrGGGGrrr"]

        self.__espacio_acciones = [
            f"{s1}-{s2}-{s3}-{s4}"
            for s1 in semaforo_1
            for s2 in semaforo_2
            for s3 in semaforo_3
            for s4 in semaforo_4
        ]

    def usar(self) -> None:
        """
        Utilizar el modelo entrenado.
        """
        logger = logging.getLogger(f" {self.__class__.__name__}.{inspect.currentframe().f_code.co_name}")  # type: ignore

        logger.info("🔄 Verificando que la simulación esté lista...")
        while not self.__service.isSimulationOk():
            logger.info("⌛ Esperando que la simulación esté lista...")
            time.sleep(1)
        logger.info("✅ La simulación está lista.")

        logger.info("🔄 Verificando que la simulación esté sincronizada...")
        while not self.__service.isSimulationSync():
            logger.info("⌛ Esperando que la simulación esté sincronizada...")
            time.sleep(1)
        logger.info("✅ La simulación está sincronizada.")

        # TODO: Agregar que avance hasta los X pasos iniciales de la simulación para que las calles estén cargadas.

        logger.info("🚦 Comenzando la toma de decisiones...")
        done = False
        while not done:
            state = self.__estado()
            action = self.model.predict(state, verbose=0)
            done = self.__avanzar(int(np.argmax(action)))

    def __estado(self) -> NDArray:
        """
        Define el estado:
        - El tiempo de espera de los vehículos en las intersecciones.
        - No incluye el color de los semáforos porque estaría duplicando datos con respecto a la accion.
        - Ej: [1,3,5,0,1,2,4,2,6,3,9,10]

        Returns:
            NDArray: Estado actual normalizado. Ej: [0.1, 0.3, 0.5, 0, 0.1, 0.2, 0.4, 0.2, 0.6, 0.3, 0.9, 1]
        """
        #! Tiempo
        estado = tuple(self.__service.getTiemposEspera()["tiempos_espera"])  # type: ignore

        #! Ponderar mas un semáforo que otro
        estado_ponderado = tuple(
            [
                round(estado[i] * self.ponderaciones_zonas[i], 2)
                for i in range(len(estado))
            ]
        )

        tiempo_maximo_espera = max(estado_ponderado)
        if tiempo_maximo_espera == 0:
            return np.reshape(estado_ponderado, [1, self.state_size])

        else:
            #! Normalizar los tiempos de espera
            estado_normalizado = tuple(
                [
                    round(tiempo_espera / tiempo_maximo_espera, 2)
                    for tiempo_espera in estado_ponderado
                ]
            )
            return np.reshape(estado_normalizado, [1, self.state_size])

    def __avanzar(self, action: int) -> bool:
        """
        Realiza las siguientes tareas:
        1. Ejecuta la acción en SUMO.
        2. Simula 15 pasos (para tener una recompensa mas realista).
        3. Devuelve el nuevo estado, la recompensa y si se ha terminado la epoca.
        """

        action2 = self.__espacio_acciones[action]

        #! Cambiar el estado de los semáforos en SUMO
        self.__service.putEstados(accion=action2.split("-"))

        #! Avanzar en SUMO con la acción seleccionada
        respuesta = self.__service.putAvanzar(steps=15)
        if respuesta is None:
            return False
        else:
            done: bool = respuesta["done"]
            return done
