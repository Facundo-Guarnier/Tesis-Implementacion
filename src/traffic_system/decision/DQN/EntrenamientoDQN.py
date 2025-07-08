import csv
import inspect
import logging
import os
import random
import time
from collections import deque

import numpy as np
import tensorflow as tf
from numpy import ndarray as NDArray

from src.traffic_system.api_client.data_source_client import ApiDecision
from src.traffic_system.core.config_loader import load_app_settings
from src.traffic_system.core.config_models import DecisionSettings


class EntrenamientoDQN:
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
        self.__configure_gpu()

        logging.basicConfig(level=logging.DEBUG)
        self.memory: deque = deque(
            maxlen=self.decision_settings.entrenamiento.memory
        )  #! Memoria de reproducción
        self.__api = ApiDecision(self.settings.base_url)

        self.__setEspacioAcciones()
        self.__setPath()
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

    def __configure_gpu(self) -> None:
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
                logger.info(" 🔧 Mixed precision deshabilitado temporalmente para compatibilidad")

                self.use_gpu = True
                self.device = "/GPU:0"

                # Información detallada de GPU
                gpu_details = tf.config.experimental.get_device_details(gpus[0])
                logger.info(f" 🚀 GPU configurada: {len(gpus)} dispositivo(s)")
                logger.info(f" 📊 GPU Info: {gpu_details.get('device_name', 'N/A')}")
                logger.info(" 💾 Crecimiento dinámico de memoria: Habilitado")
                logger.info(" 🔧 Mixed precision deshabilitado temporalmente para compatibilidad")
                
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
                    memory_info = tf.config.experimental.get_memory_info(gpus[0].name.replace("/physical_device:", ""))
                    if memory_info:
                        current_mb = memory_info["current"] / (1024**2)
                        logger = logging.getLogger(f" {self.__class__.__name__}.GPU_Monitor")
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
                    memory_info = tf.config.experimental.get_memory_info(gpus[0].name.replace("/physical_device:", ""))
                    if memory_info:
                        current_mb = memory_info["current"] / (1024**2)
                        peak_mb = memory_info["peak"] / (1024**2)
                        logger = logging.getLogger(f" {self.__class__.__name__}.GPU_Monitor")
                        logger.info(f" 📊 {context} - GPU: {current_mb:.1f} MB actual, {peak_mb:.1f} MB pico")
            except Exception as e:
                logger = logging.getLogger(f" {self.__class__.__name__}.GPU_Monitor")
                logger.debug(f" Error monitoreando GPU: {e}")

    def __setEspacioAcciones(self) -> None:
        """
        Establece el espacio de acciones está formado por una lista de tuplas, donde cada tupla representa el estado de los 4 semaforos.
        - Ej: [('GGGGGGrrrrr', 'GgGGrrrrGgGg', 'GgGgGgGGrrrr', 'GGGrrrrGGg'), (...), ...]
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

    def __setPath(self) -> None:
        """
        Establece la ruta donde se guardarán los archivos.
        """
        self.__path = os.path.join(
            self.decision_settings.entrenamiento.path_resultado,
            f'DQN_{time.strftime("%Y-%m-%d_%H-%M")}',
        )
        if not os.path.exists(self.__path):
            os.makedirs(self.__path)

    def __build_model(self) -> tf.keras.Model:
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
                tf.keras.layers.Dense(len(self.__espacio_acciones), activation="linear")
            )

            # Usar learning_rate en lugar de lr (deprecado)
            # Deshabilitar XLA compilation temporalmente para evitar problemas
            model.compile(
                loss="mse",
                optimizer=tf.keras.optimizers.Adam(learning_rate=self.learning_rate),
                jit_compile=False,  # Deshabilitar XLA temporalmente
            )

        logger.info(f" {model.summary()}")

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

    def __remember(
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

    def __politica(self, state: NDArray) -> int:
        """
        Elige una acción basada en el estado actual del agente, utilizando una política ε-greedy para el control de la exploración.
        Optimizado para el dispositivo configurado (GPU/CPU) con monitoreo.

        returns:
            int: Índice de la acción seleccionada.
        """
        # Usar TensorFlow para generación de números aleatorios en GPU si es posible
        if self.use_gpu:
            with tf.device(self.device):
                # Usar TensorFlow para la comparación aleatoria
                random_val = tf.random.uniform([], 0, 1, dtype=tf.float32)
                if random_val <= self.epsilon:
                    # Selección aleatoria usando TensorFlow
                    action = tf.random.uniform([], 0, len(self.__espacio_acciones), dtype=tf.int32)
                    return int(action.numpy())
                else:
                    # Predicción en GPU
                    state_tensor = tf.constant(state, dtype=tf.float32)
                    act_values = self.model.predict(state_tensor, verbose=0)
                    return int(tf.argmax(act_values[0]).numpy())
        else:
            # Fallback a NumPy para CPU
            if np.random.rand() <= self.epsilon:
                return np.random.choice(len(self.__espacio_acciones))
            else:
                act_values = self.model.predict(state, verbose=0)
                return int(np.argmax(act_values[0]))

    def __replay(self) -> None:
        """
        Realiza el proceso de repetición, donde la red neuronal se entrena utilizando muestras de experiencia de la memoria de reproducción.
        Optimizado para GPU/CPU con monitoreo detallado y procesamiento eficiente de datos.
        """
        minibatch = random.sample(self.memory, self.batch_size)

        # Preparar todos los datos como tensores de TensorFlow para máxima eficiencia
        if self.use_gpu:
            with tf.device(self.device):
                # Convertir datos a tensores de TensorFlow directamente
                # Corregir el acceso a los estados - s[0] ya tiene la forma correcta (1, 12)
                batch_states = tf.constant([s[0] for s, _, _, _, _ in minibatch], dtype=tf.float32)
                batch_states = tf.reshape(batch_states, [self.batch_size, self.state_size])
                
                batch_next_states = tf.constant([ns[0] for _, _, _, ns, _ in minibatch], dtype=tf.float32)
                batch_next_states = tf.reshape(batch_next_states, [self.batch_size, self.state_size])
                
                batch_rewards = tf.constant([r for _, _, r, _, _ in minibatch], dtype=tf.float32)
                batch_actions = tf.constant([a for _, a, _, _, _ in minibatch], dtype=tf.int32)
                batch_dones = tf.constant([d for _, _, _, _, d in minibatch], dtype=tf.bool)

                # Predicciones en lote usando TensorFlow
                current_q_values = self.model(batch_states, training=False)
                next_q_values = self.model(batch_next_states, training=False)
                
                # Calcular targets usando operaciones de TensorFlow
                max_next_q = tf.reduce_max(next_q_values, axis=1)
                targets = tf.where(
                    batch_dones,
                    batch_rewards,
                    batch_rewards + self.gamma * max_next_q
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
                    batch_size=self.batch_size
                )
        else:
            # Procesamiento optimizado para CPU
            batch_states = np.array([s[0] for s, _, _, _, _ in minibatch])
            all_predictions = self.model.predict(batch_states, verbose=0, batch_size=self.batch_size)
            all_predictions_copy = all_predictions.copy()

            states = []
            targets = []

            for i, (state, action, reward, next_state, done) in enumerate(minibatch):
                target = reward
                if not done:
                    target = reward + self.gamma * np.amax(all_predictions_copy[i])

                target_f = all_predictions_copy[i]
                target_f[action] = target
                states.append(state[0])
                targets.append(target_f)

            # Entrenar con los datos preparados
            states_array = np.array(states)
            targets_array = np.array(targets)
            
            self.model.fit(
                states_array, 
                targets_array,
                epochs=1,
                verbose=0,
                batch_size=self.batch_size
            )

        # Actualizar parámetros
        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay

        if self.learning_rate > self.learning_rate_min:
            self.learning_rate *= self.learning_rate_decay

    def __train(self) -> None:
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
            
            state = self.__estado()
            done = False
            total_reward = 0.0
            replay_count = 0

            t1 = time.time()
            while not done:
                id_action = self.__politica(state)
                next_state, reward, done = self.__avanzar(id_action)

                total_reward += reward
                self.__remember(state, id_action, reward, next_state, done)

                state = next_state
                if len(self.memory) > self.batch_size:
                    self.__replay()
                    replay_count += 1
                    
                    # Monitorear GPU cada 500 replays para evitar spam
                    if replay_count % 500 == 0:
                        self._log_gpu_usage(f"Época {e+1} - Replay {replay_count}")

            #! Guardar los datos de entrenamiento por epoca en formato Keras moderno
            self.model.save(self.__path + f"/epoca_{e+1}.h5")
            self.model.save(self.__path + f"/epoca_{e+1}.keras")

            #! Guardar métricas de entrenamiento en un archivo CSV
            duracion_epoca = time.time() - t1
            with open(
                self.__path + "/entrenamiento_data.csv", mode="a", newline=""
            ) as file:
                writer = csv.writer(file)
                writer.writerow(
                    [
                        e + 1,
                        f"{duracion_epoca:.2f}",
                        f"{total_reward:.2f}",
                        f"{self.epsilon:.5f}",
                        f"{self.learning_rate:.5f}",
                    ]
                )

            logger.info(
                f" Epoca: {e+1}/{self.num_epocas}: {total_reward:.2f} recompensa acumulada - Duración: {duracion_epoca:.2f}s - Replays: {replay_count}"
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

    def __estado(self) -> NDArray:
        """
        Define el estado (El tiempo de espera de los vehículos en las intersecciones) normalizado en un rango de 0 a 1.
        Optimizado para usar TensorFlow en GPU cuando sea posible.
        returns:
            NDArray: Estado normalizado. [1,3,5,0,1,2,4,2,6,3,9,10] -> [0.1, 0.3, 0.5, 0.0, 0.1, 0.2, 0.4, 0.2, 0.6, 0.3, 0.9, 1.0]
        """
        #! Tiempo
        estado = tuple(self.__api.getTiemposEspera()["tiempos_espera"])  # type: ignore
        
        # Usar TensorFlow para operaciones numéricas si tenemos GPU
        if self.use_gpu:
            with tf.device(self.device):
                # Convertir a tensor de TensorFlow
                estado_tensor = tf.constant(estado, dtype=tf.float32)
                tiempo_maximo_espera = tf.reduce_max(estado_tensor)

                if tiempo_maximo_espera == 0:
                    # Reshape y convertir de vuelta a numpy
                    result = tf.reshape(estado_tensor, [1, self.state_size])
                    return result.numpy()
                else:
                    # Normalizar usando TensorFlow
                    estado_normalizado = tf.round(estado_tensor / tiempo_maximo_espera, 2)
                    result = tf.reshape(estado_normalizado, [1, self.state_size])
                    return result.numpy()
        else:
            # Fallback a NumPy para CPU
            tiempo_maximo_espera = max(estado)
            if tiempo_maximo_espera == 0:
                return np.reshape(estado, [1, self.state_size])
            else:
                estado_normalizado = tuple(
                    [
                        round(tiempo_espera / tiempo_maximo_espera, 2)
                        for tiempo_espera in estado
                    ]
                )
                return np.reshape(estado_normalizado, [1, self.state_size])

    def __avanzar(self, id_action: int) -> tuple[NDArray, float, bool]:
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

        action = self.__espacio_acciones[id_action]

        #! Cambiar el estado de los semáforos en SUMO
        self.__api.putEstados(accion=action.split("-"))

        #! Avanzar en SUMO con la acción seleccionada
        respuesta = self.__api.putAvanzar(steps=self.steps)

        done: bool = respuesta["done"]  # type: ignore #! Si la simulación ha terminado

        return self.__estado(), self.__recompensa(), done

    def __recompensa(self) -> float:
        """
        Calcula la recompensa en función del estado actual.
        La inversa del tiempo de espera de los vehículos en las intersecciones controladas por los semáforos.
        - 100 / (tiempo_espera_total + 100)
        """
        tiempo = self.__api.getTiemposEspera()["tiempo_espera_total"]  # type: ignore
        return 100 / ((tiempo) + 100)

    def main(self) -> None:
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
        while not self.__api.isSimulationOk():
            logger.info(" Esperando a que la simulación esté lista...")
            time.sleep(1)
        logger.info(" La simulación está lista")

        #! Verificar si el archivo ya existe
        if not os.path.isfile(self.__path + "/entrenamiento_data.csv"):
            with open(
                self.__path + "/entrenamiento_data.csv", mode="w", newline=""
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
        with open(self.__path + "/hiperparametros.csv", mode="w", newline="") as file:
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
            layers += f"{len(self.__espacio_acciones)}"
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
        t_fijo_inicio = time.time()
        while not done:
            total_reward += self.__recompensa()
            done = self.__api.putAvanzar(steps=self.steps)["done"]  # type: ignore
        tiempo_fijo = time.time() - t_fijo_inicio

        #! Guardar los datos de los semaforos con tiempo fijo
        with open(
            self.__path + "/entrenamiento_data.csv", mode="a", newline=""
        ) as file:
            writer = csv.writer(file)
            writer.writerow(["-", f"{tiempo_fijo:.2f}", f"{total_reward:.2f}", "-", "-"])

        self.model = self.__build_model()

        self.__train()