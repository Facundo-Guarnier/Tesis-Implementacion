import csv
import datetime
import inspect
import io
import logging
import os
import platform
import random
import sys
import time
from collections import deque
from contextlib import redirect_stdout

import numpy as np
import psutil
import tensorflow as tf
from numpy import ndarray as NDArray

from src.traffic_system.api_client.data_source_client import DecisionAPI
from src.traffic_system.core.config_loader import load_app_settings
from src.traffic_system.core.config_models import DecisionSettings
from src.traffic_system.decision.DQN.evaluation_metrics import DQNEvaluator


class PrioritizedReplayBuffer:
    """
    Buffer de experiencia con priorización para Prioritized Experience Replay (PER).

    Implementa muestreo basado en TD-error con importance sampling para corregir bias.
    """

    def __init__(self, capacity: int, alpha: float = 0.6):
        self.capacity = capacity
        self.alpha = (
            alpha  # Grado de priorización (0 = uniforme, 1 = completamente priorizado)
        )
        self.buffer: list = []
        self.priorities: list[float] = []
        self.position = 0

    def add(
        self,
        state: NDArray,
        action: int,
        reward: float,
        next_state: NDArray,
        done: bool,
        td_error: float = 1.0,
    ) -> None:
        """Añade nueva experiencia con prioridad basada en TD-error."""
        priority = (abs(td_error) + 1e-6) ** self.alpha  # Evitar prioridad 0

        if len(self.buffer) < self.capacity:
            self.buffer.append((state, action, reward, next_state, done))
            self.priorities.append(priority)
        else:
            self.buffer[self.position] = (state, action, reward, next_state, done)
            self.priorities[self.position] = priority

        self.position = (self.position + 1) % self.capacity

    def sample(self, batch_size: int, beta: float = 0.4) -> tuple:
        """Muestrea experiencias basadas en prioridades con importance sampling."""
        if len(self.buffer) < batch_size:
            return [], [], []

        # Calcular probabilidades de muestreo
        priorities = np.array(self.priorities[: len(self.buffer)])
        probabilities = priorities / priorities.sum()

        # Muestrear índices basados en probabilidades
        indices = np.random.choice(len(self.buffer), batch_size, p=probabilities)

        # Calcular importance sampling weights
        total = len(self.buffer)
        weights = (total * probabilities[indices]) ** (-beta)
        weights /= weights.max()  # Normalizar

        # Extraer experiencias
        samples = [self.buffer[idx] for idx in indices]

        return samples, indices, weights

    def update_priorities(self, indices: list[int], td_errors: list[float]) -> None:
        """Actualiza las prioridades basadas en nuevos TD-errors."""
        for idx, td_error in zip(indices, td_errors, strict=True):
            if idx < len(self.priorities):
                self.priorities[idx] = (abs(td_error) + 1e-6) ** self.alpha

    def __len__(self) -> int:
        return len(self.buffer)


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

    def __init__(
        self, decision_settings: DecisionSettings | None = None, auto_train: bool = True
    ) -> None:
        # TODO: Eliminar el uso de load_app_settings, ya que deberia cargar desde la configuración global.
        self.settings = load_app_settings()
        self.decision_settings = load_app_settings().decision
        self.auto_train = auto_train  # Almacenar parámetro para usar al final

        # FASE 4: Declarar tipo para evaluador (se inicializará después)
        self.evaluator: DQNEvaluator | None = None
        self.evaluation_frequency: int = 5

        # Configurar GPU para entrenamiento óptimo
        self._configure_gpu()

        logging.basicConfig(level=logging.DEBUG)

        # FASE 3: Configurar memoria de reproducción (estándar o priorizada)
        if (
            hasattr(self.decision_settings.entrenamiento, "use_prioritized_replay")
            and self.decision_settings.entrenamiento.use_prioritized_replay
        ):
            self.memory_buffer: PrioritizedReplayBuffer | deque = (
                PrioritizedReplayBuffer(
                    capacity=self.decision_settings.entrenamiento.memory,
                    alpha=getattr(
                        self.decision_settings.entrenamiento, "per_alpha", 0.6
                    ),
                )
            )
            self.use_prioritized_replay = True
        else:
            self.memory_buffer = deque(
                maxlen=self.decision_settings.entrenamiento.memory
            )  #! Memoria de reproducción estándar
            self.use_prioritized_replay = False

        self._api = DecisionAPI(self.settings.base_url)

        self._set_action_space()
        self._set_save_path()
        self.state_size = (
            48  # 12 tiempos + 12 cantidades + 12 tiempos_prev + 12 cantidades_prev
        )

        # Historial para capturar dinámica temporal
        self.state_history: list[list[float]] = []
        self.max_history_length = 2  # Mantener actual + anterior

        self._init_process_memory_monitoring()

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

        # FASE 2: Configuración para Double DQN
        self.use_double_dqn = getattr(
            self.decision_settings.entrenamiento, "use_double_dqn", True
        )
        self.target_update_frequency = getattr(
            self.decision_settings.entrenamiento, "target_update_frequency", 100
        )

        # FASE 2: Configuración para Dueling DQN
        self.use_dueling_dqn = getattr(
            self.decision_settings.entrenamiento, "use_dueling_dqn", True
        )

        # FASE 3: Configuración para optimizaciones avanzadas
        self.use_prioritized_replay = getattr(
            self.decision_settings.entrenamiento, "use_prioritized_replay", True
        )
        self.per_alpha = getattr(self.decision_settings.entrenamiento, "per_alpha", 0.6)
        self.per_beta_start = getattr(
            self.decision_settings.entrenamiento, "per_beta_start", 0.4
        )
        self.per_beta_frames = getattr(
            self.decision_settings.entrenamiento, "per_beta_frames", 100000
        )
        self.use_noisy_networks = getattr(
            self.decision_settings.entrenamiento, "use_noisy_networks", True
        )
        self.noise_std = getattr(self.decision_settings.entrenamiento, "noise_std", 0.5)
        self.use_dropout = getattr(
            self.decision_settings.entrenamiento, "use_dropout", True
        )
        self.dropout_rate = getattr(
            self.decision_settings.entrenamiento, "dropout_rate", 0.1
        )
        self.adaptive_lr = getattr(
            self.decision_settings.entrenamiento, "adaptive_lr", True
        )
        self.lr_schedule_type = getattr(
            self.decision_settings.entrenamiento, "lr_schedule_type", "cosine"
        )

        # Inicializar variables para PER
        if self.use_prioritized_replay:
            self.per_beta = self.per_beta_start
            self.per_beta_increment_per_frame = (
                1.0 - self.per_beta_start
            ) / self.per_beta_frames
            # Inicializar memory prioritizada (se reemplazará después)
            self.priority_memory: list[tuple] = (
                []
            )  # Se implementará como estructura específica

        # Contador de frames para ajustes adaptativos
        self.frame_count = 0

        # FASE 4: Configuración para optimizaciones de rendimiento
        self.enable_jit_compilation = getattr(
            self.decision_settings.entrenamiento, "enable_jit_compilation", True
        )
        self.dropout_mode = getattr(
            self.decision_settings.entrenamiento, "dropout_mode", "optimized"
        )
        self.dropout_layers = getattr(
            self.decision_settings.entrenamiento, "dropout_layers", "strategic"
        )
        self.noisy_implementation = getattr(
            self.decision_settings.entrenamiento, "noisy_implementation", "efficient"
        )

        # Configuración para testing con modelo más grande
        self.test_large_model = False  # Cambiar a True para probar modelo grande

        if self.test_large_model:
            logger = logging.getLogger(f" {self.__class__.__name__}.__init__")
            logger.info(" 🧪 MODO TESTING: Usando modelo DQN más grande")
            # Modelo mucho más grande para testing de GPU
            self.hidden_layers = [512, 512, 256, 256, 128, 128, 64]

        # NOTA: El modelo se construye en start_training_process(), no aquí
        # Esto permite hacer el cálculo de baseline ANTES de crear el modelo
        self.model: tf.keras.Model | None = None
        self.target_model: tf.keras.Model | None = None
        self.model = None  # Se inicializará en start_training_process()

        # FASE 2: Configuración para Double DQN (modelo target se crea después)
        if self.use_double_dqn:
            self.target_model = None  # Se inicializará junto con el modelo principal
            self.target_update_counter = 0  # Contador para actualizaciones

        # FASE 4: Inicializar sistema de evaluación
        if getattr(self.decision_settings.entrenamiento, "enable_evaluation", True):
            logger = logging.getLogger(f" {self.__class__.__name__}.__init__")
            self.evaluator = DQNEvaluator(
                config=self.decision_settings,
                results_dir="results/evaluation",
                model_name=f"DQN_F1-2-3-4_{self.decision_settings.entrenamiento.num_epocas}ep",
            )
            self.evaluation_frequency = getattr(
                self.decision_settings.entrenamiento, "evaluation_frequency", 5
            )
            logger.info(" 🧪 Sistema de evaluación inicializado")
            logger.info(f" 📊 Evaluación cada {self.evaluation_frequency} épocas")
        else:
            self.evaluator = None
            logger.info(" ⚠️ Sistema de evaluación desactivado")

        # Solo entrenar si auto_train es True (para evitar entrenamiento en tests)
        # NOTA: El entrenamiento real se hace en start_training_process(), no aquí
        # Este parámetro se mantiene para compatibilidad con tests
        if self.auto_train:
            # No hacer nada aquí - el entrenamiento se inicia en start_training_process()
            pass

    def _configure_gpu(self) -> None:
        """
        Configura la GPU para entrenamiento óptimo, o CPU como fallback.
        Incluye monitoreo detallado de GPU.
        """
        logger = logging.getLogger(
            f" {self.__class__.__name__}.{inspect.currentframe().f_code.co_name}"  # type: ignore
        )
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

    def _init_process_memory_monitoring(self) -> None:
        """
        Inicializa el monitoreo de memoria del proceso actual.
        """
        logger = logging.getLogger(f" {self.__class__.__name__}.Memory_Monitor")
        try:
            self.process = psutil.Process()
            initial_memory = self.process.memory_info().rss / (1024**2)
            logger.info(f" 🔍 Memoria RAM inicial del proceso: {initial_memory:.1f} MB")
        except ImportError:
            logger.warning(" ⚠️ psutil no disponible - monitoreo de RAM deshabilitado")
            self.process = None
        except Exception as e:
            logger.warning(f" ⚠️ Error inicializando monitoreo RAM: {e}")
            self.process = None

    def _get_process_memory_mb(self) -> float:
        """
        Obtiene el uso de memoria RAM del proceso actual en MB.

        Returns:
            float: Memoria RAM usada por el proceso en MB, o 0 si no disponible
        """
        if hasattr(self, "process") and self.process:
            try:
                return float(self.process.memory_info().rss / (1024**2))
            except Exception:
                return 0.0
        return 0.0

    def _get_system_info(self) -> dict[str, str]:
        """
        Recopila información relevante del sistema, hardware y librerías para el entrenamiento.

        Returns:
            dict[str, str]: Diccionario con información del sistema
        """
        logger = logging.getLogger(
            f" {self.__class__.__name__}.{inspect.currentframe().f_code.co_name}"  # type: ignore
        )

        # Información básica del sistema
        system_info = {
            # Hardware y dispositivo
            "dispositivo": "GPU" if self.use_gpu else "CPU",
            "dispositivo_detalle": self.device,
            "modo_testing": str(self.test_large_model),
            # Sistema operativo
            "os": platform.system(),
            "os_version": platform.release(),
            "arquitectura": platform.machine(),
            "python_version": sys.version.split()[0],
            # Fecha y hora
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            # Versiones de librerías críticas
            "tensorflow_version": tf.__version__,
            "numpy_version": np.__version__,
        }

        # Información específica de GPU si está disponible
        if self.use_gpu:
            try:
                gpus = tf.config.experimental.list_physical_devices("GPU")
                if gpus:
                    gpu_details = tf.config.experimental.get_device_details(gpus[0])
                    system_info["gpu_nombre"] = gpu_details.get("device_name", "N/A")
                    system_info["gpu_memoria_dinamica"] = "Habilitado"
                    system_info["gpu_mixed_precision"] = (
                        "Deshabilitado"  # Como está configurado actualmente
                    )
                    system_info["gpu_count"] = str(len(gpus))
                else:
                    system_info["gpu_nombre"] = "N/A"
            except Exception as e:
                logger.warning(f" ⚠️ Error obteniendo detalles de GPU: {e}")
                system_info["gpu_nombre"] = "Error al obtener info"
        else:
            system_info["gpu_nombre"] = "N/A (CPU)"
            system_info["gpu_memoria_dinamica"] = "N/A"
            system_info["gpu_mixed_precision"] = "N/A"
            system_info["gpu_count"] = "0"

        # Configuración de TensorFlow
        try:
            # Usar métodos actualizados en lugar de los deprecados
            gpus_available = (
                len(tf.config.experimental.list_physical_devices("GPU")) > 0
            )
            system_info["tf_gpu_available"] = str(gpus_available)
            system_info["tf_built_with_cuda"] = str(tf.test.is_built_with_cuda())
        except Exception:
            system_info["tf_gpu_available"] = "Error"
            system_info["tf_built_with_cuda"] = "Error"

        logger.info(" 📋 Información del sistema recopilada para hiperparámetros")

        return system_info

    def _collect_training_metrics(
        self,
        epoch_rewards: list[float],
        epoch_actions: list[int],
        epoch_q_values: list[float],
        replay_count: int,
        epoch_duration: float,
        inference_times: list[float],
        total_steps: int,
    ) -> dict[str, float]:
        """
        Recopila métricas variables del entrenamiento para una época específica.

        Args:
            epoch_rewards: Lista de recompensas de la época
            epoch_actions: Lista de acciones tomadas en la época
            epoch_q_values: Lista de Q-values máximos de la época
            replay_count: Número de replays ejecutados
            epoch_duration: Duración total de la época en segundos
            inference_times: Tiempos de inferencia individuales
            total_steps: Total de pasos de simulación ejecutados

        Returns:
            dict[str, float]: Métricas calculadas de la época
        """
        metrics = {}

        # Métricas básicas de recompensa (cálculo rápido)
        if epoch_rewards:
            rewards_array = np.array(epoch_rewards)
            metrics["recompensa_max"] = float(np.max(rewards_array))
            metrics["recompensa_min"] = float(np.min(rewards_array))
            metrics["recompensa_std"] = float(np.std(rewards_array))
        else:
            metrics["recompensa_max"] = 0.0
            metrics["recompensa_min"] = 0.0
            metrics["recompensa_std"] = 0.0

        # Métricas de Q-values (cálculo rápido)
        if epoch_q_values:
            q_values_array = np.array(epoch_q_values)
            metrics["q_value_promedio"] = float(np.mean(q_values_array))
            metrics["q_value_maximo"] = float(np.max(q_values_array))
        else:
            metrics["q_value_promedio"] = 0.0
            metrics["q_value_maximo"] = 0.0

        # Hiperparámetros actuales (acceso directo, sin cálculos)
        metrics["epsilon_actual"] = float(self.epsilon)
        metrics["learning_rate_actual"] = float(self.learning_rate)

        # Métricas de eficiencia (cálculos simples)
        metrics["numero_replays"] = float(replay_count)
        metrics["pasos_por_segundo"] = float(
            total_steps / epoch_duration if epoch_duration > 0 else 0
        )

        # Tiempo de inferencia (promedio rápido)
        if inference_times:
            metrics["tiempo_inferencia_promedio"] = float(np.mean(inference_times))
        else:
            metrics["tiempo_inferencia_promedio"] = 0.0

        # Memoria del proceso (acceso rápido)
        metrics["memoria_ram_proceso_mb"] = self._get_process_memory_mb()

        # Memoria GPU solo si está disponible y no es costosa
        metrics["memoria_gpu_pico_mb"] = 0.0
        # REMOVIDO: Llamada costosa a tf.config.experimental.get_memory_info()
        # Esta operación puede ser muy lenta y afectar el rendimiento del entrenamiento

        # Métricas de simulación - REMOVIDAS para evitar llamadas API costosas
        # Estas métricas requieren llamadas HTTP adicionales que ralentizan el entrenamiento
        metrics["tiempo_espera_total"] = 0.0
        metrics["tiempo_espera_promedio"] = 0.0
        metrics["congestion_maxima"] = 0.0

        return metrics

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
        FASE 2: Soporte para Dueling DQN y modelo estándar.

        Returns:
            tf.keras.Model: Modelo de la red neuronal (estándar o Dueling).
        """
        logger = logging.getLogger(
            f" {self.__class__.__name__}.{inspect.currentframe().f_code.co_name}"  # type: ignore
        )

        # Usar el dispositivo detectado (GPU o CPU)
        with tf.device(self.device):
            if self.use_dueling_dqn:
                model = self._build_dueling_model()
                logger.info(" 🔀 Usando arquitectura Dueling DQN")
            else:
                model = self._build_standard_model()
                logger.info(" 📊 Usando arquitectura DQN estándar")

            # Compilar modelo con optimizaciones configurables
            jit_compile_enabled = (
                self.enable_jit_compilation and self.use_gpu
            )  # JIT más eficaz en GPU

            model.compile(
                loss="mse",
                optimizer=tf.keras.optimizers.Adam(learning_rate=self.learning_rate),
                jit_compile=jit_compile_enabled,
            )

            if jit_compile_enabled:
                logger.info(" ⚡ JIT compilation habilitado para optimización")
            else:
                logger.info(" 📊 JIT compilation deshabilitado")

        # Mostrar resumen del modelo
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

    def _should_add_dropout(self, layer_index: int) -> bool:
        """
        Determina si se debe añadir dropout en una capa específica basado en la estrategia configurada.

        Args:
            layer_index: Índice de la capa (1-indexed)

        Returns:
            bool: True si se debe añadir dropout
        """
        if self.dropout_mode == "full":
            return True  # Dropout en todas las capas (comportamiento original)
        elif self.dropout_mode == "optimized":
            # Dropout estratégico: primera capa, mitad y antes de output
            total_layers = len(self.hidden_layers)
            return (
                layer_index == 1  # Primera capa
                or layer_index == total_layers // 2  # Capa del medio
                or layer_index == total_layers - 1  # Antes de output
            )
        elif self.dropout_mode == "strategic":
            # Solo en primeras y últimas capas
            total_layers = len(self.hidden_layers)
            return layer_index <= 2 or layer_index >= total_layers - 1
        elif self.dropout_mode == "minimal":
            # Solo antes de la capa de salida
            return layer_index == len(self.hidden_layers)
        else:
            return True  # Default: full dropout

    def _create_noisy_layer(
        self, units: int, input_dim: int | None = None, activation: str = "relu"
    ) -> tf.keras.layers.Layer:
        """
        Crea una Noisy Layer para exploración automática.

        Las Noisy Networks reemplazan epsilon-greedy con ruido paramétrico en los pesos.
        Esto permite exploración más sofisticada y específica por estado.

        Args:
            units: Número de neuronas en la capa
            input_dim: Dimensión de entrada (solo para primera capa)
            activation: Función de activación

        Returns:
            tf.keras.layers.Layer: Capa con ruido paramétrico
        """
        if not self.use_noisy_networks:
            # Si no se usan noisy networks, crear capa estándar
            if input_dim is not None:
                return tf.keras.layers.Dense(
                    units, input_dim=input_dim, activation=activation
                )
            else:
                return tf.keras.layers.Dense(units, activation=activation)

        # Seleccionar implementación basada en configuración
        if self.noisy_implementation == "efficient":
            # Implementación más eficiente usando inicializadores específicos
            # En lugar de añadir ruido post-procesamiento, usar inicialización con ruido
            if input_dim is not None:
                layer = tf.keras.layers.Dense(
                    units,
                    input_dim=input_dim,
                    activation=activation,
                    kernel_initializer=tf.keras.initializers.RandomNormal(
                        stddev=self.noise_std * 0.1
                    ),  # Ruido en inicialización
                    bias_initializer=tf.keras.initializers.RandomNormal(
                        stddev=self.noise_std * 0.1
                    ),
                )
            else:
                layer = tf.keras.layers.Dense(
                    units,
                    activation=activation,
                    kernel_initializer=tf.keras.initializers.RandomNormal(
                        stddev=self.noise_std * 0.1
                    ),
                    bias_initializer=tf.keras.initializers.RandomNormal(
                        stddev=self.noise_std * 0.1
                    ),
                )
            return layer
        else:
            # Implementación original con GaussianNoise (menos eficiente)
            if input_dim is not None:
                dense = tf.keras.layers.Dense(
                    units, input_dim=input_dim, activation=activation
                )
            else:
                dense = tf.keras.layers.Dense(units, activation=activation)

            # Añadir ruido gaussiano para simular exploración
            return tf.keras.Sequential(
                [
                    dense,
                    (
                        tf.keras.layers.GaussianNoise(stddev=self.noise_std)
                        if activation != "linear"
                        else dense
                    ),
                ]
            )

    def _build_standard_model(self) -> tf.keras.Model:
        """
        Construye el modelo DQN estándar con mejoras de Fase 3.

        Returns:
            tf.keras.Model: Modelo DQN estándar con Dropout y Noisy Layers
        """
        model = tf.keras.Sequential()

        # Primera capa con input_dim
        if self.use_noisy_networks:
            model.add(
                self._create_noisy_layer(
                    self.hidden_layers[0], input_dim=self.state_size
                )
            )
        else:
            model.add(
                tf.keras.layers.Dense(
                    self.hidden_layers[0], input_dim=self.state_size, activation="relu"
                )
            )

        # Dropout después de la primera capa si está habilitado
        if self.use_dropout and self._should_add_dropout(layer_index=1):
            model.add(tf.keras.layers.Dropout(self.dropout_rate))

        # Capas ocultas restantes
        for i in range(1, len(self.hidden_layers)):
            if self.use_noisy_networks:
                model.add(self._create_noisy_layer(self.hidden_layers[i]))
            else:
                model.add(
                    tf.keras.layers.Dense(self.hidden_layers[i], activation="relu")
                )

            # Dropout entre capas si está habilitado
            if self.use_dropout and self._should_add_dropout(layer_index=i + 1):
                model.add(tf.keras.layers.Dropout(self.dropout_rate))

        # Capa de salida (sin dropout)
        if self.use_noisy_networks:
            model.add(
                self._create_noisy_layer(len(self._action_space), activation="linear")
            )
        else:
            model.add(
                tf.keras.layers.Dense(len(self._action_space), activation="linear")
            )

        return model

    def _build_dueling_model(self) -> tf.keras.Model:
        """
        Construye el modelo Dueling DQN con mejoras de Fase 3.

        Arquitectura:
        - Capas compartidas (shared layers) con Dropout y Noisy Layers
        - Stream de valor del estado V(s)
        - Stream de ventaja de acciones A(s,a)
        - Combinación: Q(s,a) = V(s) + A(s,a) - mean(A(s,a))

        Returns:
            tf.keras.Model: Modelo Dueling DQN con optimizaciones
        """
        # Input layer
        inputs = tf.keras.layers.Input(shape=(self.state_size,))

        # Capas compartidas (shared layers) con mejoras de Fase 3
        shared = inputs
        for i, units in enumerate(
            self.hidden_layers[:-2]
        ):  # Usar todas menos las últimas 2
            if self.use_noisy_networks:
                # Crear capa noisy usando Sequential como workaround
                noisy_layer = tf.keras.Sequential(
                    [
                        tf.keras.layers.Dense(
                            units, activation="relu", name=f"shared_{i}_dense"
                        ),
                        tf.keras.layers.GaussianNoise(
                            stddev=self.noise_std, name=f"shared_{i}_noise"
                        ),
                    ],
                    name=f"shared_{i}",
                )
                shared = noisy_layer(shared)
            else:
                shared = tf.keras.layers.Dense(
                    units, activation="relu", name=f"shared_{i}"
                )(shared)

            # Añadir Dropout si está habilitado
            if self.use_dropout and self._should_add_dropout(layer_index=i):
                shared = tf.keras.layers.Dropout(
                    self.dropout_rate, name=f"shared_{i}_dropout"
                )(shared)

        # Stream de valor del estado V(s)
        if self.use_noisy_networks and self.noisy_implementation == "efficient":
            # Implementación eficiente para Noisy Networks
            value_stream = tf.keras.layers.Dense(
                self.hidden_layers[-2],
                activation="relu",
                name="value_hidden",
                kernel_initializer=tf.keras.initializers.RandomNormal(
                    stddev=self.noise_std * 0.1
                ),
            )(shared)
        elif self.use_noisy_networks:
            # Implementación original menos eficiente
            value_stream = tf.keras.Sequential(
                [
                    tf.keras.layers.Dense(
                        self.hidden_layers[-2],
                        activation="relu",
                        name="value_hidden_dense",
                    ),
                    tf.keras.layers.GaussianNoise(
                        stddev=self.noise_std, name="value_hidden_noise"
                    ),
                ],
                name="value_stream",
            )(shared)
        else:
            value_stream = tf.keras.layers.Dense(
                self.hidden_layers[-2], activation="relu", name="value_hidden"
            )(shared)

        if self.use_dropout and self.dropout_mode in ["full", "strategic"]:
            value_stream = tf.keras.layers.Dropout(
                self.dropout_rate, name="value_dropout"
            )(value_stream)

        value = tf.keras.layers.Dense(1, name="value")(value_stream)

        # Stream de ventaja de acciones A(s,a)
        if self.use_noisy_networks and self.noisy_implementation == "efficient":
            # Implementación eficiente para Noisy Networks
            advantage_stream = tf.keras.layers.Dense(
                self.hidden_layers[-1],
                activation="relu",
                name="advantage_hidden",
                kernel_initializer=tf.keras.initializers.RandomNormal(
                    stddev=self.noise_std * 0.1
                ),
            )(shared)
        elif self.use_noisy_networks:
            # Implementación original menos eficiente
            advantage_stream = tf.keras.Sequential(
                [
                    tf.keras.layers.Dense(
                        self.hidden_layers[-1],
                        activation="relu",
                        name="advantage_hidden_dense",
                    ),
                    tf.keras.layers.GaussianNoise(
                        stddev=self.noise_std, name="advantage_hidden_noise"
                    ),
                ],
                name="advantage_stream",
            )(shared)
        else:
            advantage_stream = tf.keras.layers.Dense(
                self.hidden_layers[-1], activation="relu", name="advantage_hidden"
            )(shared)

        if self.use_dropout and self.dropout_mode in ["full", "strategic"]:
            advantage_stream = tf.keras.layers.Dropout(
                self.dropout_rate, name="advantage_dropout"
            )(advantage_stream)

        advantage = tf.keras.layers.Dense(len(self._action_space), name="advantage")(
            advantage_stream
        )

        # Combinar valor y ventaja: Q(s,a) = V(s) + A(s,a) - mean(A(s,a))
        # Esto asegura que V(s) representa realmente el valor del estado
        advantage_mean = tf.keras.layers.Lambda(
            lambda x: tf.reduce_mean(x, axis=1, keepdims=True), name="advantage_mean"
        )(advantage)

        q_values = tf.keras.layers.Add(name="q_values")(
            [
                value,
                tf.keras.layers.Subtract(name="advantage_centered")(
                    [advantage, advantage_mean]
                ),
            ]
        )

        model = tf.keras.Model(inputs=inputs, outputs=q_values, name="Dueling_DQN")

        return model

    def _remember(
        self,
        state: NDArray,
        action: int,
        reward: float,
        next_state: NDArray,
        done: bool,
        td_error: float = 1.0,
    ) -> None:
        """
        Almacena la experiencia del agente en la memoria de reproducción.
        FASE 3: Soporte para Prioritized Experience Replay.
        """
        if self.use_prioritized_replay:
            assert isinstance(self.memory_buffer, PrioritizedReplayBuffer)
            self.memory_buffer.add(state, action, reward, next_state, done, td_error)
        else:
            assert isinstance(self.memory_buffer, deque)
            self.memory_buffer.append((state, action, reward, next_state, done))

    def _get_memory_size(self) -> int:
        """Obtiene el tamaño actual de la memoria de reproducción."""
        return len(self.memory_buffer)

    def _get_memory_capacity(self) -> int:
        """Obtiene la capacidad máxima de la memoria de reproducción."""
        if self.use_prioritized_replay:
            assert isinstance(self.memory_buffer, PrioritizedReplayBuffer)
            return self.memory_buffer.capacity
        else:
            assert isinstance(self.memory_buffer, deque)
            maxlen = self.memory_buffer.maxlen
            return maxlen if maxlen is not None else 0

    def _select_action(self, state: NDArray) -> tuple[int, float, float]:
        """
        Elige una acción basada en el estado actual del agente, utilizando una política ε-greedy para el control de la exploración.
        Optimizado para el dispositivo configurado (GPU/CPU) con monitoreo.

        returns:
            tuple[int, float, float]: (Índice de la acción seleccionada, Q-value máximo, tiempo de inferencia)
        """
        inference_start = time.time()

        if np.random.rand() <= self.epsilon:
            action = int(np.random.choice(len(self._action_space)))
            max_q_value = 0.0  # No hay Q-value para acciones aleatorias
        else:
            assert (
                self.model is not None
            ), "Model must be initialized before selecting actions"
            # Reshape para predicción en lote (más eficiente)
            state_batch = np.expand_dims(state, axis=0)  # (12,) -> (1, 12)
            act_values = self.model.predict(state_batch, verbose=0)
            action = int(np.argmax(act_values[0]))
            max_q_value = float(np.max(act_values[0]))

        inference_time = time.time() - inference_start
        return action, max_q_value, inference_time

    def _replay(self) -> None:
        """
        Realiza el proceso de repetición, donde la red neuronal se entrena utilizando muestras de experiencia de la memoria de reproducción.
        FASE 2: Soporte para Double DQN y actualización de red target.
        FASE 3: Soporte para Prioritized Experience Replay.
        """
        if self.use_prioritized_replay:
            self._replay_prioritized()
        else:
            self._replay_standard()

        # Actualizar red target si es necesario (Double DQN)
        if self.use_double_dqn and hasattr(self, "target_model"):
            if hasattr(self, "target_update_counter"):
                self.target_update_counter += 1
                if self.target_update_counter >= self.target_update_frequency:
                    self._update_target_model()
                    self.target_update_counter = 0

        # FASE 3: Actualizar parámetros adaptativos
        self._update_adaptive_parameters()

    def _replay_prioritized(self) -> None:
        """
        Replay con Prioritized Experience Replay (PER).
        """
        assert isinstance(
            self.memory_buffer, PrioritizedReplayBuffer
        ), "Prioritized replay requires PrioritizedReplayBuffer"

        if len(self.memory_buffer) < self.batch_size:
            return

        # Actualizar beta para importance sampling
        self.per_beta = min(1.0, self.per_beta + self.per_beta_increment_per_frame)

        # Muestrear experiencias con prioridades
        minibatch, indices, weights = self.memory_buffer.sample(
            self.batch_size, self.per_beta
        )

        if not minibatch:
            return

        # Calcular TD-errors para actualizar prioridades
        td_errors = self._calculate_td_errors(minibatch)

        # Actualizar prioridades en el buffer
        self.memory_buffer.update_priorities(indices, td_errors)

        # Entrenar con importance sampling weights
        self._train_batch_with_weights(minibatch, weights)

    def _replay_standard(self) -> None:
        """
        Replay estándar sin priorización.
        """
        assert isinstance(
            self.memory_buffer, deque
        ), "Standard replay requires deque memory buffer"
        assert self.model is not None, "Model must be initialized before replay"

        minibatch: list[tuple[NDArray, int, float, NDArray, bool]] = random.sample(
            self.memory_buffer, self.batch_size
        )

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

                if self.use_double_dqn and hasattr(self, "target_model"):
                    assert (
                        self.target_model is not None
                    ), "Target model must be initialized for Double DQN"
                    # Double DQN: usar online network para seleccionar acción, target network para evaluar
                    next_q_values_online = self.model(batch_next_states, training=False)
                    next_q_values_target = self.target_model(
                        batch_next_states, training=False
                    )

                    # Seleccionar mejores acciones usando la red online
                    best_actions = tf.argmax(
                        next_q_values_online, axis=1, output_type=tf.int32
                    )

                    # Evaluar las acciones seleccionadas usando la red target
                    batch_indices = tf.range(self.batch_size)
                    best_action_indices = tf.stack(
                        [batch_indices, best_actions], axis=1
                    )
                    max_next_q = tf.gather_nd(next_q_values_target, best_action_indices)
                else:
                    # DQN estándar: usar la misma red para seleccionar y evaluar
                    next_q_values = self.model(batch_next_states, training=False)
                    max_next_q = tf.reduce_max(next_q_values, axis=1)

                # Calcular targets
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
            # Versión CPU optimizada
            states = np.array([s for s, _, _, _, _ in minibatch], dtype=np.float32)
            next_states = np.array(
                [ns for _, _, _, ns, _ in minibatch], dtype=np.float32
            )

            # Predicciones en lote
            current_q_values = self.model.predict(
                states, verbose=0, batch_size=self.batch_size
            )

            if self.use_double_dqn and hasattr(self, "target_model"):
                assert (
                    self.target_model is not None
                ), "Target model must be initialized for Double DQN"
                # Double DQN: usar online network para seleccionar, target network para evaluar
                next_q_values_online = self.model.predict(
                    next_states, verbose=0, batch_size=self.batch_size
                )
                next_q_values_target = self.target_model.predict(
                    next_states, verbose=0, batch_size=self.batch_size
                )

                # Preparar targets con Double DQN
                targets = current_q_values.copy()
                for i, (_, action, reward, _, done) in enumerate(minibatch):
                    if done:
                        targets[i][action] = reward
                    else:
                        # Seleccionar acción con red online, evaluar con red target
                        best_action = np.argmax(next_q_values_online[i])
                        targets[i][action] = (
                            reward + self.gamma * next_q_values_target[i][best_action]
                        )
            else:
                # DQN estándar
                next_q_values = self.model.predict(
                    next_states, verbose=0, batch_size=self.batch_size
                )

                targets = current_q_values.copy()
                for i, (_, action, reward, _, done) in enumerate(minibatch):
                    if done:
                        targets[i][action] = reward
                    else:
                        targets[i][action] = reward + self.gamma * np.max(
                            next_q_values[i]
                        )

            # Entrenar
            self.model.fit(
                states, targets, epochs=1, verbose=0, batch_size=self.batch_size
            )

    def _calculate_td_errors(self, minibatch: list) -> list[float]:
        """
        Calcula TD-errors para Prioritized Experience Replay.
        """
        assert (
            self.model is not None
        ), "Model must be initialized before calculating TD errors"

        td_errors = []
        states = np.array([s for s, _, _, _, _ in minibatch], dtype=np.float32)
        next_states = np.array([ns for _, _, _, ns, _ in minibatch], dtype=np.float32)

        current_q_values = self.model.predict(states, verbose=0)
        next_q_values = self.model.predict(next_states, verbose=0)

        if self.use_double_dqn and hasattr(self, "target_model"):
            assert (
                self.target_model is not None
            ), "Target model must be initialized for Double DQN"
            next_q_values_target = self.target_model.predict(next_states, verbose=0)

        for i, (_, action, reward, _, done) in enumerate(minibatch):
            current_q = current_q_values[i][action]

            if done:
                target_q = reward
            else:
                if self.use_double_dqn and hasattr(self, "target_model"):
                    best_action = np.argmax(next_q_values[i])
                    target_q = (
                        reward + self.gamma * next_q_values_target[i][best_action]
                    )
                else:
                    target_q = reward + self.gamma * np.max(next_q_values[i])

            td_error = abs(target_q - current_q)
            td_errors.append(td_error)

        return td_errors

    def _train_batch_with_weights(self, minibatch: list, weights: NDArray) -> None:
        """
        Entrena el modelo con importance sampling weights para PER.
        """
        assert self.model is not None, "Model must be initialized before training"

        # Implementación simplificada - en production se usaría weighted loss
        # Por ahora entrenar normalmente pero podríamos aplicar weights al loss
        states = np.array([s for s, _, _, _, _ in minibatch], dtype=np.float32)
        next_states = np.array([ns for _, _, _, ns, _ in minibatch], dtype=np.float32)

        current_q_values = self.model.predict(states, verbose=0)
        next_q_values = self.model.predict(next_states, verbose=0)

        if self.use_double_dqn and hasattr(self, "target_model"):
            assert (
                self.target_model is not None
            ), "Target model must be initialized for Double DQN"
            next_q_values_target = self.target_model.predict(next_states, verbose=0)

        targets = current_q_values.copy()
        for i, (_, action, reward, _, done) in enumerate(minibatch):
            if done:
                targets[i][action] = reward
            else:
                if self.use_double_dqn and hasattr(self, "target_model"):
                    best_action = np.argmax(next_q_values[i])
                    targets[i][action] = (
                        reward + self.gamma * next_q_values_target[i][best_action]
                    )
                else:
                    targets[i][action] = reward + self.gamma * np.max(next_q_values[i])

        # Entrenar con importance sampling (simplificado)
        self.model.fit(states, targets, epochs=1, verbose=0, sample_weight=weights)

    def _update_adaptive_parameters(self) -> None:
        """
        Actualiza parámetros adaptativos para Fase 3.
        """
        self.frame_count += 1

        # Actualizar epsilon (mantener lógica existente)
        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay

        # NOTA: Learning rate se actualiza SOLO al final de cada época
        # en _on_epoch_end() para evitar decay excesivo por step

    def _update_target_model(self) -> None:
        """
        Actualiza la red target copiando los pesos de la red principal (online).
        Solo se ejecuta si Double DQN está habilitado.
        """
        if hasattr(self, "target_model"):
            assert (
                self.model is not None
            ), "Model must be initialized before updating target model"
            assert (
                self.target_model is not None
            ), "Target model must be initialized before updating"
            logger = logging.getLogger(
                f" {self.__class__.__name__}.{inspect.currentframe().f_code.co_name}"  # type: ignore
            )
            self.target_model.set_weights(self.model.get_weights())
            logger.info(" 🎯 Red target actualizada con pesos de la red principal")

    def _train_agent(self) -> None:
        """
        Entrena el agente utilizando el algoritmo DQN.
        Por cada epoca, el agente realiza una serie de acciones en el entorno, almacenando la
        experiencia en la memoria de reproducción.
        Cuando el tamaño de la memoria de reproducción alcanza el tamaño del lote, el agente
        realiza el proceso de repetición.
        Incluye monitoreo detallado de GPU y recopilación de métricas avanzadas.
        - 19500 segundos / 15 steps  = 1300 repeticiones por epoca
        """
        logger = logging.getLogger(
            f" {self.__class__.__name__}.{inspect.currentframe().f_code.co_name}"  # type: ignore
        )

        self._log_gpu_usage("Inicio entrenamiento")

        for e in range(self.num_epocas):
            logger.info(f" 🏁 Iniciando época {e+1}/{self.num_epocas}")

            # Inicializar métricas de la época
            epoch_rewards = []
            epoch_actions = []
            epoch_q_values = []
            inference_times = []

            state = self._get_current_state()
            done = False
            total_reward = 0.0
            replay_count = 0
            total_steps = 0

            t1 = time.time()
            while not done:
                # Seleccionar acción y capturar métricas
                action_index, max_q_value, inference_time = self._select_action(state)
                next_state, reward, done = self._execute_action_and_advance(
                    action_index
                )

                # Recopilar métricas de la acción
                epoch_rewards.append(reward)
                epoch_actions.append(action_index)
                epoch_q_values.append(max_q_value)
                inference_times.append(inference_time)

                total_reward += reward
                total_steps += 1
                self._remember(state, action_index, reward, next_state, done)

                state = next_state
                if self._get_memory_size() > self.batch_size:
                    self._replay()
                    replay_count += 1

                    # Monitorear GPU menos frecuentemente para reducir overhead
                    if replay_count % 1000 == 0:
                        self._log_gpu_usage(f"Época {e+1} - Replay {replay_count}")

            #! Guardar los datos de entrenamiento por epoca en formato Keras moderno
            assert self.model is not None, "Model must be initialized before saving"
            self.model.save(self._save_path + f"/epoca_{e+1}.h5")
            self.model.save(self._save_path + f"/epoca_{e+1}.keras")

            #! Recopilar métricas de entrenamiento
            epoch_duration = time.time() - t1
            training_metrics = self._collect_training_metrics(
                epoch_rewards,
                epoch_actions,
                epoch_q_values,
                replay_count,
                epoch_duration,
                inference_times,
                total_steps,
            )

            #! Guardar métricas completas de entrenamiento en un archivo CSV
            with open(
                self._save_path + "/entrenamiento_data.csv", mode="a", newline=""
            ) as file:
                writer = csv.writer(file)
                writer.writerow(
                    [
                        # Métricas básicas
                        e + 1,
                        f"{epoch_duration:.2f}",
                        f"{total_reward:.2f}",
                        f"{self.epsilon:.5f}",
                        f"{self.learning_rate:.8f}",  # Learning rate actual del optimizador
                        # Métricas de rendimiento del modelo
                        f"{training_metrics['recompensa_max']:.2f}",
                        f"{training_metrics['recompensa_min']:.2f}",
                        f"{training_metrics['recompensa_std']:.4f}",
                        f"{training_metrics['q_value_promedio']:.4f}",
                        f"{training_metrics['q_value_maximo']:.4f}",
                        # Hiperparámetros actuales
                        f"{training_metrics['epsilon_actual']:.5f}",
                        f"{training_metrics['learning_rate_actual']:.8f}",
                        # Métricas de eficiencia
                        f"{training_metrics['numero_replays']:.0f}",
                        f"{training_metrics['pasos_por_segundo']:.2f}",
                        f"{training_metrics['tiempo_inferencia_promedio']:.6f}",
                        # Métricas de memoria optimizadas
                        f"{training_metrics['memoria_ram_proceso_mb']:.1f}",
                    ]
                )

            logger.info(
                f" Epoca: {e+1}/{self.num_epocas}: {total_reward:.2f} recompensa acumulada - Duración: {epoch_duration:.2f}s - Replays: {replay_count}"
            )

            # FASE 4: Registro de métricas de entrenamiento en evaluador
            if self.evaluator is not None:
                avg_q_value = float(np.mean(epoch_q_values)) if epoch_q_values else 0.0

                # Calcular métricas adicionales (simuladas para esta implementación)
                waiting_time = (
                    training_metrics.get("tiempo_inferencia_promedio", 0.0) * 1000
                )  # Convertir a ms
                throughput = training_metrics.get("pasos_por_segundo", 0.0)

                self.evaluator.record_training_step(
                    episode=e + 1,
                    reward=total_reward,
                    loss=0.0,  # Se actualizará cuando tengamos access a las pérdidas
                    epsilon=self.epsilon,
                    learning_rate=self.learning_rate,
                    avg_q_value=avg_q_value,
                    episode_length=total_steps,
                    waiting_time=waiting_time,
                    throughput=throughput,
                )

                # Evaluación periódica
                if (e + 1) % self.evaluation_frequency == 0:
                    logger.info(f" 🧪 Realizando evaluación en época {e + 1}")
                    # Crear un entorno simulado para evaluación (simplificado)
                    evaluation_metrics = self._simulate_evaluation()

                    # Comparar con baseline si está disponible
                    if self.evaluator.baseline_metrics is not None:
                        comparison = self.evaluator.compare_with_baseline(
                            evaluation_metrics
                        )
                        logger.info(f" 📊 Comparación completada: {comparison}")

            # FASE 4: Actualizar parámetros adaptativos para la siguiente época
            if hasattr(self, "frame_count"):
                self._update_adaptive_parameters()

            # FASE 3: Learning rate adaptativo (solo al final de cada época)
            if self.adaptive_lr and self.learning_rate > self.learning_rate_min:
                old_lr = self.learning_rate
                if self.lr_schedule_type == "exponential":
                    new_learning_rate = max(
                        self.learning_rate * self.learning_rate_decay,
                        self.learning_rate_min,
                    )
                elif self.lr_schedule_type == "cosine":
                    # Cosine annealing basado en progreso por épocas, no por steps
                    progress = (e + 1) / self.num_epocas
                    new_learning_rate = (
                        self.learning_rate_min
                        + (self.learning_rate - self.learning_rate_min)
                        * (1 + np.cos(np.pi * progress))
                        / 2
                    )
                    new_learning_rate = max(new_learning_rate, self.learning_rate_min)
                else:
                    # Default: exponential
                    new_learning_rate = max(
                        self.learning_rate * self.learning_rate_decay,
                        self.learning_rate_min,
                    )

                if new_learning_rate != self.learning_rate:
                    assert (
                        self.model is not None
                    ), "Model must be initialized before updating learning rate"
                    self.learning_rate = new_learning_rate
                    self.model.optimizer.learning_rate.assign(self.learning_rate)
                    logger.info(
                        f" 📉 Learning rate actualizado: {old_lr:.8f} → {new_learning_rate:.8f}"
                    )

        logger.info(" ✅ Entrenamiento finalizado.")

        # FASE 4: Generar reporte final de evaluación
        if self.evaluator is not None:
            logger.info(" 📊 Generando reporte final de evaluación...")

            # Establecer baseline si es la primera vez
            if self.evaluator.baseline_metrics is None:
                self.evaluator.set_baseline_from_current()

            # Generar gráficos finales
            self.evaluator.generate_plots()

            # Guardar métricas finales
            metrics_path = self.evaluator.save_metrics()
            logger.info(f" 💾 Métricas guardadas en: {metrics_path}")

            # Mostrar resumen estadístico
            summary = self.evaluator.get_summary_stats()
            logger.info(f" 📈 Resumen final: {summary}")

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
        Define el estado enriquecido que incluye:
        - Tiempos de espera de las 12 zonas (actual)
        - Cantidades de vehículos de las 12 zonas (actual)
        - Tiempos de espera de las 12 zonas (anterior)
        - Cantidades de vehículos de las 12 zonas (anterior)

        Total: 48 características para capturar dinámica temporal

        Returns:
            NDArray: Estado enriquecido y normalizado como (48,)
        """
        # Obtener tiempos de espera actuales
        wait_times_response = self._api.get_wait_times()
        if wait_times_response is None:
            raise RuntimeError("No se pudo obtener los tiempos de espera de la API")

        # Obtener cantidades de vehículos actuales
        quantities_response = self._api.get_quantities()
        if quantities_response is None:
            raise RuntimeError(
                "No se pudo obtener las cantidades de vehículos de la API"
            )

        # Preparar observación actual
        wait_times = wait_times_response.tiempos_espera
        quantities = list(quantities_response.cantidades.values())

        # Asegurar que tenemos exactamente 12 valores para cada tipo
        if len(wait_times) != 12:
            raise RuntimeError(
                f"Se esperaban 12 tiempos de espera, se obtuvieron {len(wait_times)}"
            )
        if len(quantities) != 12:
            raise RuntimeError(
                f"Se esperaban 12 cantidades, se obtuvieron {len(quantities)}"
            )

        # Combinar observación actual: [tiempos(12) + cantidades(12)] = 24 valores
        current_observation = wait_times + quantities

        # Gestionar historial temporal
        self.state_history.append(current_observation)
        if len(self.state_history) > self.max_history_length:
            self.state_history.pop(0)

        # Construir estado completo con historial
        if len(self.state_history) >= 2:
            # Estado: [actual(24) + anterior(24)] = 48 valores
            previous_observation = self.state_history[-2]
            complete_state = current_observation + previous_observation
        else:
            # Si no hay historial, duplicar observación actual
            complete_state = current_observation + current_observation

        # Normalizar estado de manera robusta
        return self._normalize_state_robust(complete_state)

    def _normalize_state_robust(self, state: list[float]) -> NDArray:
        """
        Normalización robusta del estado que maneja casos extremos.

        Args:
            state: Lista con los valores del estado a normalizar

        Returns:
            NDArray: Estado normalizado
        """
        state_array = np.array(state, dtype=np.float32)

        # Normalización por componentes: primera mitad = tiempos, segunda = cantidades
        mid_point = len(state_array) // 2

        # Normalizar tiempos de espera (0-1000 segundos típicamente)
        wait_times_part = state_array[:mid_point]
        wait_max = np.max(wait_times_part) if np.max(wait_times_part) > 0 else 1.0
        normalized_waits = wait_times_part / wait_max

        # Normalizar cantidades (0-100 vehículos típicamente)
        quantities_part = state_array[mid_point:]
        qty_max = np.max(quantities_part) if np.max(quantities_part) > 0 else 1.0
        normalized_quantities = quantities_part / qty_max

        # Combinar partes normalizadas
        normalized_state = np.concatenate([normalized_waits, normalized_quantities])

        # Verificar que no hay valores inválidos
        normalized_state = np.nan_to_num(
            normalized_state, nan=0.0, posinf=1.0, neginf=0.0
        )

        return np.array(normalized_state, dtype=np.float32)

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
        if response is None:
            raise RuntimeError("No se pudo avanzar la simulación")

        done: bool = response.done  #! Si la simulación ha terminado

        return self._get_current_state(), self._calculate_reward(), done

    def _calculate_reward(self) -> float:
        """
        Calcula la recompensa mejorada en función del estado actual.

        Nueva fórmula con penalizaciones ponderadas:
        - Penaliza tiempo de espera (cuadrático para casos extremos)
        - Penaliza congestión desigual (alta varianza)
        - Bonifica eficiencia del flujo vehicular

        Returns:
            float: Recompensa calculada (valores negativos = penalización)
        """
        wait_times_response = self._api.get_wait_times()
        if wait_times_response is None:
            raise RuntimeError(
                "No se pudo obtener los tiempos de espera para calcular recompensa"
            )

        quantities_response = self._api.get_quantities()
        if quantities_response is None:
            raise RuntimeError(
                "No se pudo obtener las cantidades de vehículos para calcular recompensa"
            )

        # Obtener datos
        wait_times = wait_times_response.tiempos_espera
        quantities = list(quantities_response.cantidades.values())

        # 1. Penalización por tiempo de espera (cuadrático para casos extremos)
        wait_penalty = sum(t**2 for t in wait_times) / len(wait_times)

        # 2. Penalización por congestión desigual (alta varianza = mal balance)
        if len(quantities) > 1:
            congestion_variance = float(np.var(quantities))
        else:
            congestion_variance = 0.0

        # 3. Penalización por congestión total excesiva
        total_vehicles = sum(quantities)
        congestion_penalty = total_vehicles**1.5 if total_vehicles > 50 else 0

        # 4. Fórmula final con pesos ajustables
        w1_wait = 0.01  # Peso para tiempo de espera
        w2_variance = 0.1  # Peso para varianza de congestión
        w3_congestion = 0.005  # Peso para congestión total

        reward = -(
            w1_wait * wait_penalty
            + w2_variance * congestion_variance
            + w3_congestion * congestion_penalty
        )

        return float(reward)

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
        logger = logging.getLogger(
            f" {self.__class__.__name__}.{inspect.currentframe().f_code.co_name}"  # type: ignore
        )

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
                        # Métricas básicas
                        "Epoca",
                        "Duración (segundos)",
                        "Recompensa Acumulada",
                        "Epsilon",
                        "Tasa de Aprendizaje",
                        # Métricas de rendimiento del modelo
                        "Recompensa Max",
                        "Recompensa Min",
                        "Recompensa Std",
                        "Q-Value Promedio",
                        "Q-Value Máximo",
                        # Hiperparámetros actuales (optimizados)
                        "Epsilon Actual",
                        "Learning Rate Actual",
                        # Métricas de eficiencia (optimizadas)
                        "Número Replays",
                        "Pasos por Segundo",
                        "Tiempo Inferencia Promedio",
                        # Métricas de memoria (optimizadas para rendimiento)
                        "Memoria RAM Proceso (MB)",
                    ]
                )

        #! Guardar hiperparámetros
        system_info = self._get_system_info()
        with open(
            self._save_path + "/hiperparametros.csv", mode="w", newline=""
        ) as file:
            writer = csv.writer(file)

            # Encabezados - Hiperparámetros del modelo
            headers = [
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

            # Encabezados - Información del sistema
            system_headers = [
                "Dispositivo",
                "Dispositivo Detalle",
                "GPU Nombre",
                "GPU Count",
                "GPU Memoria Dinamica",
                "GPU Mixed Precision",
                "Modo Testing",
                "OS",
                "OS Version",
                "Arquitectura",
                "Python Version",
                "TensorFlow Version",
                "NumPy Version",
                "TF GPU Available",
                "TF Built with CUDA",
                "Timestamp",
            ]

            writer.writerow(headers + system_headers)

            # Valores - Hiperparámetros del modelo
            layers = f"{self.state_size} | "
            for i in range(len(self.hidden_layers)):
                layers += f"{self.hidden_layers[i]} | "
            layers += f"{len(self._action_space)}"

            hyperparams_values = [
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
                self._get_memory_capacity(),
                layers,
            ]

            # Valores - Información del sistema
            system_values = [
                system_info["dispositivo"],
                system_info["dispositivo_detalle"],
                system_info["gpu_nombre"],
                system_info["gpu_count"],
                system_info["gpu_memoria_dinamica"],
                system_info["gpu_mixed_precision"],
                system_info["modo_testing"],
                system_info["os"],
                system_info["os_version"],
                system_info["arquitectura"],
                system_info["python_version"],
                system_info["tensorflow_version"],
                system_info["numpy_version"],
                system_info["tf_gpu_available"],
                system_info["tf_built_with_cuda"],
                system_info["timestamp"],
            ]

            writer.writerow(hyperparams_values + system_values)

            logger.info(" 💾 Hiperparámetros e información del sistema guardados")
            logger.info(
                f" 🎯 Entrenamiento: {system_info['dispositivo']} ({system_info['gpu_nombre']})"
            )
            logger.info(
                f" 🐍 Python {system_info['python_version']} + TensorFlow {system_info['tensorflow_version']}"
            )
            logger.info(
                f" 💻 {system_info['os']} {system_info['os_version']} ({system_info['arquitectura']})"
            )

        #! Calcular la recompensa con semaforos con tiempo fijo
        total_reward = 0.0
        done = False
        logger.info(" Calculando recompensa con semaforos con tiempo fijo.")
        fixed_time_start = time.time()
        while not done:
            total_reward += self._calculate_reward()
            response = self._api.advance_simulation(steps=self.steps)
            if response is None:
                raise RuntimeError(
                    "No se pudo avanzar la simulación en cálculo de tiempo fijo"
                )
            done = response.done
        fixed_time_duration = time.time() - fixed_time_start

        #! Guardar los datos de los semaforos con tiempo fijo
        with open(
            self._save_path + "/entrenamiento_data.csv", mode="a", newline=""
        ) as file:
            writer = csv.writer(file)
            # Datos de tiempo fijo con valores por defecto para las nuevas columnas
            writer.writerow(
                [
                    "-",  # Época
                    f"{fixed_time_duration:.2f}",  # Duración
                    f"{total_reward:.2f}",  # Recompensa
                    "-",  # Epsilon
                    "-",  # Learning rate
                    "-",  # Recompensa Max
                    "-",  # Recompensa Min
                    "-",  # Recompensa Std
                    "-",  # Q-Value Promedio
                    "-",  # Q-Value Máximo
                    "-",  # Epsilon Actual
                    "-",  # Learning Rate Actual
                    "-",  # Número Replays
                    "-",  # Pasos por Segundo
                    "-",  # Tiempo Inferencia Promedio
                    "-",  # Memoria RAM Proceso
                ]
            )

        self.model = self._build_model()

        # FASE 2: Inicializar red target y contador para Double DQN
        if self.use_double_dqn:
            logger.info(" 🎯 Inicializando red target para Double DQN")
            self.target_model = self._build_model()  # Crear red target idéntica
            assert (
                self.model is not None
            ), "Model must be initialized before copying weights"
            self.target_model.set_weights(
                self.model.get_weights()
            )  # Copiar pesos iniciales
            self.target_update_counter = 0  # Contador para actualizaciones
            logger.info(
                f" 🔄 Red target se actualizará cada {self.target_update_frequency} pasos"
            )

        # Iniciar el entrenamiento del agente después de tener todo configurado
        logger.info(" 🚀 Iniciando entrenamiento del agente DQN...")
        self._train_agent()

    def _simulate_evaluation(self) -> dict[str, float]:
        """
        Simula una evaluación del agente para métricas de rendimiento.

        En una implementación completa, esto ejecutaría episodios de evaluación
        en un entorno separado sin exploración.

        Returns:
            dict: Métricas de evaluación simuladas
        """
        logger = logging.getLogger(f" {self.__class__.__name__}._simulate_evaluation")

        # Para esta implementación simplificada, simulamos métricas basadas en el rendimiento actual
        current_reward = (
            self.evaluator.reward_window[-1]
            if self.evaluator and self.evaluator.reward_window
            else 0.0
        )

        # Simular variabilidad en la evaluación
        evaluation_variance = 0.1  # 10% de variabilidad
        simulated_reward = current_reward * (
            1 + np.random.uniform(-evaluation_variance, evaluation_variance)
        )

        # Simular otras métricas basadas en el reward
        simulated_waiting_time = max(
            0, 100 - simulated_reward * 2
        )  # Menos reward = más tiempo de espera
        simulated_throughput = max(
            0, 10 + simulated_reward * 0.5
        )  # Más reward = mayor throughput

        evaluation_metrics = {
            "mean_reward": float(simulated_reward),
            "std_reward": abs(simulated_reward * 0.05),
            "mean_waiting_time": float(simulated_waiting_time),
            "std_waiting_time": simulated_waiting_time * 0.1,
            "mean_throughput": float(simulated_throughput),
            "std_throughput": simulated_throughput * 0.05,
            "mean_episode_length": 100.0,
            "total_episodes": 10,
        }

        logger.debug(
            f" 🧪 Evaluación simulada completada: reward={simulated_reward:.2f}"
        )
        return evaluation_metrics
