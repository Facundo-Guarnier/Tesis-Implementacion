import csv
import inspect
import io
import logging
import os
import random
import time
from collections import deque
from contextlib import redirect_stdout

import numpy as np
import tensorflow as tf
from numpy import ndarray as NDArray

from src.traffic_system.api_client.data_source_client import DecisionAPI
from src.traffic_system.core.config_loader import load_app_settings
from src.traffic_system.core.config_models import DecisionSettings


class DQNTrainer:
    """
    Entrenamiento de un agente utilizando el algoritmo DQN (Deep Q-Learning).

    - La red neuronal se entrena utilizando la experiencia almacenada en la memoria de reproducción.
    - La política ε-greedy se utiliza para la exploración.
    - La recompensa se calcula en función del tiempo de espera de los vehículos en las intersecciones.
    - La red neuronal se guarda en un archivo .h5 por cada epoca.
    - Las métricas de entrenamiento se guardan en un archivo CSV.
    - Los hiperparámetros se guardan en un archivo CSV.

    Attributes:
        base_path (str): Ruta donde se guardarán los archivos.
        steps (int): Pasos que se avanzará en la simulación por cada acción.
        learning_rate (float): Tasa de aprendizaje.
        learning_rate_decay (float): Decaimiento de la tasa de aprendizaje.
        learning_rate_min (float): Minima tasa de aprendizaje.
        epsilon (float): Exploración/explotación inicial.
        epsilon_decay (float): Decaimiento de la exploración/explotación.
        epsilon_min (float): Exploración/explotación mínima.
        num_epocas (int): Cantidad de épocas.
        batch_size (int): Tamaño del lote de datos que se utilizará en cada paso de entrenamiento.
        gamma (float): Factor de descuento, que determina la importancia de las recompensas futuras.
    """

    def __init__(self, decision_settings: DecisionSettings | None = None) -> None:
        # TODO: Eliminar el uso de load_app_settings, ya que deberia cargar desde la configuración global.
        self.settings = load_app_settings()
        self.decision_settings = load_app_settings().decision

        # Configurar GPU para entrenamiento óptimo
        self._configure_gpu()

        logging.basicConfig(level=logging.DEBUG)
        self.memory: deque = deque(
            maxlen=self.decision_settings.entrenamiento.memory
        )  #! Memoria de reproducción
        self._api = DecisionAPI(self.settings.base_url)

        self._set_action_space()
        self._set_save_path()
        self.state_size = 12

        #! Hiperparámetros
        self.num_epocas = self.decision_settings.entrenamiento.num_epocas
        self.batch_size = self.decision_settings.entrenamiento.batch_size
        self.steps = self.decision_settings.entrenamiento.steps

        self.learning_rate = self.decision_settings.entrenamiento.learning_rate
        self.learning_rate_decay = (
            self.decision_settings.entrenamiento.learning_rate_decay
        )
        self.learning_rate_min = self.decision_settings.entrenamiento.learning_rate_min

        self.epsilon = self.decision_settings.entrenamiento.epsilon
        self.epsilon_decay = self.decision_settings.entrenamiento.epsilon_decay
        self.epsilon_min = self.decision_settings.entrenamiento.epsilon_min

        self.gamma = self.decision_settings.entrenamiento.gamma
        self.hidden_layers = self.decision_settings.entrenamiento.hidden_layers

        # Configuración para testing con modelo más grande
        self.test_large_model = False  # Cambiar a True para probar modelo grande

        if self.test_large_model:
            logger = logging.getLogger(f" {self.__class__.__name__}.__init__")
            logger.info(" 🧪 MODO TESTING: Usando modelo DQN más grande")
            # Modelo mucho más grande para testing de GPU
            self.hidden_layers = [512, 512, 256, 256, 128, 128, 64]

    def _configure_gpu(self) -> None:
        """
        Configura la GPU para entrenamiento óptimo, o CPU como fallback.
        Incluye monitoreo detallado de GPU.
        """
        logger = logging.getLogger(f" {self.__class__.__name__}.{inspect.currentframe().f_code.co_name}")  # type: ignore

        # Verificar GPUs disponibles
        gpus = tf.config.experimental.list_physical_devices("GPU")
        self.use_gpu = False

        if gpus:
            try:
                # Configurar crecimiento dinámico de memoria
                for gpu in gpus:
                    tf.config.experimental.set_memory_growth(gpu, True)

                # Deshabilitar mixed precision temporalmente para evitar problemas de compatibilidad
                # policy = tf.keras.mixed_precision.Policy("mixed_float16")
                # tf.keras.mixed_precision.set_global_policy(policy)
                logger.info(
                    " 🔧 Mixed precision deshabilitado temporalmente para compatibilidad"
                )

                self.use_gpu = True
                self.device = "/GPU:0"

                # Información detallada de GPU
                gpu_details = tf.config.experimental.get_device_details(gpus[0])
                logger.info(f" 🚀 GPU configurada: {len(gpus)} dispositivo(s)")
                logger.info(f" 📊 GPU Info: {gpu_details.get('device_name', 'N/A')}")
                logger.info(" 💾 Crecimiento dinámico de memoria: Habilitado")
                logger.info(
                    " 🔧 Mixed precision deshabilitado temporalmente para compatibilidad"
                )

                # Inicializar monitoreo de GPU
                self._init_gpu_monitoring()

            except RuntimeError as e:
                logger.warning(f" ⚠️ Error configurando GPU: {e}")
                logger.info(" 🔄 Cambiando a CPU...")
                self.use_gpu = False
                self.device = "/CPU:0"
        else:
            logger.warning(" ⚠️ No se encontraron GPUs")
            logger.info(" 🖥️ Usando CPU para entrenamiento")
            self.use_gpu = False
            self.device = "/CPU:0"

        logger.info(f" 🎯 Dispositivo seleccionado: {self.device}")

    def _init_gpu_monitoring(self) -> None:
        """
        Inicializa el monitoreo de GPU.
        """
        if self.use_gpu:
            try:
                # Crear un tensor dummy para inicializar el contexto de GPU
                with tf.device(self.device):
                    dummy = tf.constant([1.0])
                    _ = tf.square(dummy)

                # Obtener información inicial de memoria
                gpus = tf.config.experimental.list_physical_devices("GPU")
                if gpus:
                    memory_info = tf.config.experimental.get_memory_info(
                        gpus[0].name.replace("/physical_device:", "")
                    )
                    if memory_info:
                        current_mb = memory_info["current"] / (1024**2)
                        logger = logging.getLogger(
                            f" {self.__class__.__name__}.GPU_Monitor"
                        )
                        logger.info(f" 🔍 Memoria GPU inicial: {current_mb:.1f} MB")
            except Exception as e:
                logger = logging.getLogger(f" {self.__class__.__name__}.GPU_Monitor")
                logger.warning(f" ⚠️ Error inicializando monitoreo GPU: {e}")

    def _log_gpu_usage(self, context: str = "") -> None:
        """
        Registra el uso actual de GPU.
        """
        if self.use_gpu:
            try:
                gpus = tf.config.experimental.list_physical_devices("GPU")
                if gpus:
                    memory_info = tf.config.experimental.get_memory_info(
                        gpus[0].name.replace("/physical_device:", "")
                    )
                    if memory_info:
                        current_mb = memory_info["current"] / (1024**2)
                        peak_mb = memory_info["peak"] / (1024**2)
                        logger = logging.getLogger(
                            f" {self.__class__.__name__}.GPU_Monitor"
                        )
                        logger.info(
                            f" 📊 {context} - GPU: {current_mb:.1f} MB actual, {peak_mb:.1f} MB pico"
                        )
            except Exception as e:
                logger = logging.getLogger(f" {self.__class__.__name__}.GPU_Monitor")
                logger.debug(f" Error monitoreando GPU: {e}")

    def _set_action_space(self) -> None:
        """
        Establece el espacio de acciones está formado por una lista de tuplas, donde cada tupla representa el estado de los 4 semaforos.
        - Ej: [('GGGGGGrrrrr', 'GgGGrrrrGgGg', 'GgGgGgGGrrrr', 'GGGrrrrGGg'), (...), ...]
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

    def _set_save_path(self) -> None:
        """
        Establece la ruta donde se guardarán los archivos.
        """
        self._save_path = os.path.join(
            self.decision_settings.entrenamiento.path_resultado,
            f'DQN_{time.strftime("%Y-%m-%d_%H-%M")}',
        )
        if not os.path.exists(self._save_path):
            os.makedirs(self._save_path)

    def _build_model(self) -> tf.keras.Model:
        """
        Define la arquitectura de la red neuronal utilizando TensorFlow.

        Returns:
            tf.keras.Model: Modelo de la red neuronal.
        """
        logger = logging.getLogger(f" {self.__class__.__name__}.{inspect.currentframe().f_code.co_name}")  # type: ignore

        # Usar el dispositivo detectado (GPU o CPU)
        with tf.device(self.device):
            #! Construir el modelo en base a self.hidden_layers
            model = tf.keras.Sequential()
            model.add(
                tf.keras.layers.Dense(
                    self.hidden_layers[0], input_dim=self.state_size, activation="relu"
                )
            )

            for i in range(1, len(self.hidden_layers)):
                model.add(
                    tf.keras.layers.Dense(self.hidden_layers[i], activation="relu")
                )

            model.add(
                tf.keras.layers.Dense(len(self._action_space), activation="linear")
            )

            # Usar learning_rate en lugar de lr (deprecado)
            # Deshabilitar XLA compilation temporalmente para evitar problemas
            model.compile(
                loss="mse",
                optimizer=tf.keras.optimizers.Adam(learning_rate=self.learning_rate),
                jit_compile=False,  # Deshabilitar XLA temporalmente
            )

        stream = io.StringIO()
        with redirect_stdout(stream):
            model.summary()
        logger.info(stream.getvalue())

        # Mostrar información del dispositivo usado
        try:
            device_info = (
                model.layers[0].weights[0].device
                if model.layers[0].weights
                else self.device
            )
            logger.info(f" 🎯 Modelo creado en: {device_info}")
        except Exception:
            logger.info(f" 🎯 Modelo configurado para: {self.device}")

        return model

    def _remember(
        self,
        state: NDArray,
        action: int,
        reward: float,
        next_state: NDArray,
        done: bool,
    ) -> None:
        """
        Almacena la experiencia del agente en la memoria de reproducción.
        """
        self.memory.append((state, action, reward, next_state, done))

    def _select_action(self, state: NDArray) -> int:
        """
        Elige una acción basada en el estado actual del agente, utilizando una política ε-greedy para el control de la exploración.
        Optimizado para el dispositivo configurado (GPU/CPU) con monitoreo.

        returns:
            int: Índice de la acción seleccionada.
        """
        if np.random.rand() <= self.epsilon:
            return np.random.choice(len(self._action_space))
        else:
            # Reshape para predicción en lote (más eficiente)
            state_batch = np.expand_dims(state, axis=0)  # (12,) -> (1, 12)
            act_values = self.model.predict(state_batch, verbose=0)
            return int(np.argmax(act_values[0]))

    def _replay(self) -> None:
        """
        Realiza el proceso de repetición, donde la red neuronal se entrena utilizando muestras de experiencia de la memoria de reproducción.
        Optimizado para reducir conversiones y cálculos redundantes.
        """
        minibatch = random.sample(self.memory, self.batch_size)

        # Preparar datos de manera más eficiente
        if self.use_gpu:
            with tf.device(self.device):
                # Extraer datos directamente como arrays numpy y convertir una sola vez
                states = np.array([s for s, _, _, _, _ in minibatch], dtype=np.float32)
                next_states = np.array(
                    [ns for _, _, _, ns, _ in minibatch], dtype=np.float32
                )
                rewards = np.array([r for _, _, r, _, _ in minibatch], dtype=np.float32)
                actions = np.array([a for _, a, _, _, _ in minibatch], dtype=np.int32)
                dones = np.array([d for _, _, _, _, d in minibatch], dtype=bool)

                # Convertir a tensores una sola vez
                batch_states = tf.constant(states)
                batch_next_states = tf.constant(next_states)
                batch_rewards = tf.constant(rewards)
                batch_actions = tf.constant(actions)
                batch_dones = tf.constant(dones)

                # Predicciones en lote
                current_q_values = self.model(batch_states, training=False)
                next_q_values = self.model(batch_next_states, training=False)

                # Calcular targets
                max_next_q = tf.reduce_max(next_q_values, axis=1)
                targets = tf.where(
                    batch_dones, batch_rewards, batch_rewards + self.gamma * max_next_q
                )

                # Actualizar Q-values
                target_q_values = tf.identity(current_q_values)
                batch_indices = tf.range(self.batch_size)
                action_indices = tf.stack([batch_indices, batch_actions], axis=1)

                updated_q_values = tf.tensor_scatter_nd_update(
                    target_q_values, action_indices, targets
                )

                # Entrenar el modelo
                self.model.fit(
                    batch_states,
                    updated_q_values,
                    epochs=1,
                    verbose=0,
                    batch_size=self.batch_size,
                )
        else:
            # Versión CPU optimizada - sin copias innecesarias
            states = np.array([s for s, _, _, _, _ in minibatch], dtype=np.float32)
            next_states = np.array(
                [ns for _, _, _, ns, _ in minibatch], dtype=np.float32
            )

            # Predicciones en lote
            current_q_values = self.model.predict(
                states, verbose=0, batch_size=self.batch_size
            )
            next_q_values = self.model.predict(
                next_states, verbose=0, batch_size=self.batch_size
            )

            # Preparar targets directamente
            targets = current_q_values.copy()
            for i, (_, action, reward, _, done) in enumerate(minibatch):
                if done:
                    targets[i][action] = reward
                else:
                    targets[i][action] = reward + self.gamma * np.max(next_q_values[i])

            # Entrenar
            self.model.fit(
                states, targets, epochs=1, verbose=0, batch_size=self.batch_size
            )

        # Actualizar parámetros - solo epsilon (learning_rate se maneja en el optimizador)
        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay

    def _train_agent(self) -> None:
        """
        Entrena el agente utilizando el algoritmo DQN.
        Por cada epoca, el agente realiza una serie de acciones en el entorno, almacenando la
        experiencia en la memoria de reproducción.
        Cuando el tamaño de la memoria de reproducción alcanza el tamaño del lote, el agente
        realiza el proceso de repetición.
        Incluye monitoreo detallado de GPU.
        - 19500 segundos / 15 steps  = 1300 repeticiones por epoca
        """
        logger = logging.getLogger(f" {self.__class__.__name__}.{inspect.currentframe().f_code.co_name}")  # type: ignore

        self._log_gpu_usage("Inicio entrenamiento")

        for e in range(self.num_epocas):
            logger.info(f" 🏁 Iniciando época {e+1}/{self.num_epocas}")

            state = self._get_current_state()
            done = False
            total_reward = 0.0
            replay_count = 0

            t1 = time.time()
            while not done:
                action_index = self._select_action(state)
                next_state, reward, done = self._execute_action_and_advance(
                    action_index
                )

                total_reward += reward
                self._remember(state, action_index, reward, next_state, done)

                state = next_state
                if len(self.memory) > self.batch_size:
                    self._replay()
                    replay_count += 1

                    # Monitorear GPU cada 500 replays para evitar spam
                    if replay_count % 500 == 0:
                        self._log_gpu_usage(f"Época {e+1} - Replay {replay_count}")

            #! Guardar los datos de entrenamiento por epoca en formato Keras moderno
            self.model.save(self._save_path + f"/epoca_{e+1}.h5")
            self.model.save(self._save_path + f"/epoca_{e+1}.keras")

            #! Guardar métricas de entrenamiento en un archivo CSV
            epoch_duration = time.time() - t1
            with open(
                self._save_path + "/entrenamiento_data.csv", mode="a", newline=""
            ) as file:
                writer = csv.writer(file)
                writer.writerow(
                    [
                        e + 1,
                        f"{epoch_duration:.2f}",
                        f"{total_reward:.2f}",
                        f"{self.epsilon:.5f}",
                        "-",  # Ya no actualizamos learning_rate en cada replay
                    ]
                )

            logger.info(
                f" Epoca: {e+1}/{self.num_epocas}: {total_reward:.2f} recompensa acumulada - Duración: {epoch_duration:.2f}s - Replays: {replay_count}"
            )

        logger.info(" Entrenamiento finalizado.")

        # Mostrar información final del dispositivo usado
        if self.use_gpu:
            try:
                gpus = tf.config.experimental.list_physical_devices("GPU")
                if gpus:
                    memory_info = tf.config.experimental.get_memory_info(
                        gpus[0].name.replace("/physical_device:", "")
                    )
                    if memory_info:
                        peak_mb = memory_info["peak"] / (1024**2)
                        logger.info(f" 💾 Memoria GPU máxima usada: {peak_mb:.1f} MB")
            except Exception as e:
                logger.debug(f" No se pudo obtener info de memoria GPU: {e}")
        else:
            logger.info(" 🖥️ Entrenamiento completado usando CPU")
            # Opcional: Mostrar información de memoria RAM usada
            try:
                import psutil

                memory_info = psutil.virtual_memory()
                used_gb = (memory_info.total - memory_info.available) / (1024**3)
                logger.info(f" 💾 Memoria RAM en uso: {used_gb:.1f} GB")
            except ImportError:
                logger.debug(" psutil no disponible para mostrar uso de RAM")

    def _get_current_state(self) -> NDArray:
        """
        Define el estado (El tiempo de espera de los vehículos en las intersecciones) normalizado en un rango de 0 a 1.
        Optimizado para reducir conversiones innecesarias.
        returns:
            NDArray: Estado normalizado como (12,) en lugar de (1,12)
        """
        #! Tiempo
        state_raw = self._api.get_wait_times()["tiempos_espera"]  # type: ignore
        state_raw = np.array(state_raw, dtype=np.float32)

        # Optimizar normalización
        max_wait_time = np.max(state_raw)
        if max_wait_time == 0:
            return state_raw
        else:
            # Normalización simple sin conversiones innecesarias
            return state_raw / max_wait_time

    def _execute_action_and_advance(
        self, id_action: int
    ) -> tuple[NDArray, float, bool]:
        """
        Realiza las siguientes tareas:
        1. Ejecuta la acción en SUMO.
        2. Simula x pasos.
        3. Devuelve el nuevo estado, la recompensa y si se ha terminado la epoca.

        returns:
            NDArray: Nuevo estado.
            float: Recompensa.
            bool: Si la simulación ha terminado.
        """

        action_phases_str = self._action_space[id_action]
        action_phases_list = action_phases_str.split("-")

        #! Cambiar el estado de los semáforos en SUMO
        self._api.set_traffic_light_states(states=action_phases_list)

        #! Avanzar en SUMO con la acción seleccionada
        response = self._api.advance_simulation(steps=self.steps)

        done: bool = response["done"]  # type: ignore #! Si la simulación ha terminado

        return self._get_current_state(), self._calculate_reward(), done

    def _calculate_reward(self) -> float:
        """
        Calcula la recompensa en función del estado actual.
        La inversa del tiempo de espera de los vehículos en las intersecciones controladas por los semáforos.
        - 100 / (tiempo_espera_total + 100)
        """
        wait_time = self._api.get_wait_times()["tiempo_espera_total"]  # type: ignore
        return 100 / ((wait_time) + 100)

    def start_training_process(self) -> None:
        """
        Inicia el proceso de entrenamiento del agente.
        1. Espera a que la simulación esté lista.
        2. Guarda los hiperparámetros en un archivo CSV.
        3. Calcula la recompensa con semaforos con tiempo fijo.
        4. Guarda los datos de los semaforos con tiempo fijo en un archivo CSV.
        5. Inicializa la red neuronal.
        6. Inicia el entrenamiento del agente.
        """
        logger = logging.getLogger(f" {self.__class__.__name__}.{inspect.currentframe().f_code.co_name}")  # type: ignore

        #! Esperar a que la simulación esté lista
        while not self._api.is_simulation_running():
            logger.info(" Esperando a que la simulación esté lista...")
            time.sleep(1)
        logger.info(" La simulación está lista")

        #! Verificar si el archivo ya existe
        if not os.path.isfile(self._save_path + "/entrenamiento_data.csv"):
            with open(
                self._save_path + "/entrenamiento_data.csv", mode="w", newline=""
            ) as file:
                writer = csv.writer(file)
                writer.writerow(
                    [
                        "Epoca",
                        "Duración (segundos)",
                        "Recompensa Acumulada",
                        "Epsilon",
                        "Tasa de Aprendizaje",
                    ]
                )

        #! Guardar hiperparámetros
        with open(
            self._save_path + "/hiperparametros.csv", mode="w", newline=""
        ) as file:
            writer = csv.writer(file)
            writer.writerow(
                [
                    "Num Epocas",
                    "Batch size",
                    "Steps",
                    "Learning rate",
                    "Learning rate decay",
                    "Learning rate min",
                    "Epsilon",
                    "Epsilon decay",
                    "Epsilon min",
                    "Gamma",
                    "Memoria de reproducción",
                    "Red neuronal",
                ]
            )
            layers = f"{self.state_size} | "
            for i in range(len(self.hidden_layers)):
                layers += f"{self.hidden_layers[i]} | "
            layers += f"{len(self._action_space)}"
            writer.writerow(
                [
                    self.num_epocas,
                    self.batch_size,
                    str(self.steps) + "+3",
                    str(self.learning_rate),
                    self.learning_rate_decay,
                    self.learning_rate_min,
                    self.epsilon,
                    self.epsilon_decay,
                    self.epsilon_min,
                    self.gamma,
                    self.memory.maxlen,
                    layers,
                ]
            )

        #! Calcular la recompensa con semaforos con tiempo fijo
        total_reward = 0.0
        done = False
        logger.info(" Calculando recompensa con semaforos con tiempo fijo.")
        fixed_time_start = time.time()
        while not done:
            total_reward += self._calculate_reward()
            done = self._api.advance_simulation(steps=self.steps)["done"]  # type: ignore
        fixed_time_duration = time.time() - fixed_time_start

        #! Guardar los datos de los semaforos con tiempo fijo
        with open(
            self._save_path + "/entrenamiento_data.csv", mode="a", newline=""
        ) as file:
            writer = csv.writer(file)
            writer.writerow(
                ["-", f"{fixed_time_duration:.2f}", f"{total_reward:.2f}", "-", "-"]
            )

        self.model = self._build_model()

        self._train_agent()
