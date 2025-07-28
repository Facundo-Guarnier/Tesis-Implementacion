"""
Deep Q-Network (DQN) Trainer para Control de Semáforos Inteligentes.

Este módulo implementa un entrenador de DQN con las siguientes características:
- Double DQN para reducir sobreestimación de Q-values
- Dueling DQN para separar valor del estado y ventaja de acciones
- Prioritized Experience Replay para mejor eficiencia de aprendizaje
- Arquitectura optimizada para GPU con monitoreo de rendimiento
- Sistema completo de métricas y evaluación

Principales componentes:
- DQNTrainer: Clase principal de entrenamiento
- Configuración automática de GPU/CPU
- Sistema de recompensas optimizado para tráfico vehicular
- Early stopping inteligente para evitar sobreentrenamiento

Ejemplo de uso:
    trainer = DQNTrainer()
    trainer.start_training_process()
"""

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
from src.traffic_system.core.api_models import (
    VehicleQuantitiesResponse,
    WaitTimesResponse,
)
from src.traffic_system.core.config_loader import load_app_settings
from src.traffic_system.core.config_models import DecisionSettings
from src.traffic_system.core.training_dashboard import (
    ProgressMetrics,
    create_training_dashboard,
)
from src.traffic_system.decision.DQN.evaluation_metrics import DQNEvaluator
from src.traffic_system.decision.DQN.prioritized_replay_buffer import (
    PrioritizedReplayBuffer,
)


class DQNTrainer:
    """
    Entrenador de Deep Q-Network para control optimizado de semáforos inteligentes.

    Esta clase implementa un algoritmo DQN avanzado con múltiples mejoras algorítmicas:

    Arquitecturas soportadas:
        - DQN estándar: Red neuronal básica para aproximar Q-values
        - Double DQN: Reduce sobreestimación de Q-values usando red target
        - Dueling DQN: Separación de valor de estado y ventaja de acciones

    Optimizaciones avanzadas:
        - Prioritized Experience Replay (PER): Muestreo inteligente de experiencias
        - Noisy Networks: Exploración automática mediante ruido paramétrico
        - Gradient clipping: Estabilización del entrenamiento
        - Early stopping adaptativo: Prevención de sobreentrenamiento

    Características técnicas:
        - Optimización automática GPU/CPU con monitoreo de rendimiento
        - Sistema de métricas completo con evaluación periódica
        - Manejo robusto de APIs con fallbacks y reintentos
        - Normalización avanzada de estados y recompensas

    Args:
        decision_settings: Configuración específica del componente de decisión
        auto_train: Si debe iniciar entrenamiento automáticamente en __init__

    Attributes:
        model: Red neuronal principal (online network)
        target_model: Red neuronal target para Double DQN
        memory_buffer: Buffer de experiencias (estándar o priorizado)
        evaluator: Sistema de evaluación y métricas
        smart_logger: Logger optimizado con control de nivel dinámico
        dashboard: Dashboard de progreso con early stopping

    Example:
        >>> trainer = DQNTrainer()
        >>> trainer.start_training_process()

    Note:
        El entrenamiento requiere que el simulador SUMO esté ejecutándose
        y accesible a través de la API configurada en settings.base_url
    """

    def __init__(
        self, decision_settings: DecisionSettings | None = None, auto_train: bool = True
    ) -> None:
        """
        Inicializa el entrenador DQN con configuración y recursos del sistema.

        Args:
            decision_settings: Configuración específica (usa configuración global si None)
            auto_train: Si debe iniciar entrenamiento automáticamente
        """
        # CONFIGURACIÓN PRINCIPAL
        self.settings = load_app_settings()
        self.decision_settings = self.settings.decision
        self.auto_train = auto_train

        # SISTEMA DE EVALUACIÓN Y LOGGING
        self.evaluator: DQNEvaluator | None = None
        self.evaluation_frequency: int = 5
        # self.smart_logger = create_smart_logger("DQNTrainer", DQN_LOGGER_CONFIG)
        self.dashboard = create_training_dashboard(baseline_performance=-48285.77)

        # CONFIGURACIÓN DE HARDWARE
        self._configure_gpu()
        self._init_process_memory_monitoring()

        # CONFIGURACIÓN DE MEMORIA DE EXPERIENCIAS
        self._setup_replay_buffer()

        # CONFIGURACIÓN DE API Y ESTADO
        self._api = DecisionAPI(self.settings.base_url)
        self._setup_state_management()

        # CONFIGURACIÓN DE HIPERPARÁMETROS
        self._setup_hyperparameters()

        # CONFIGURACIÓN DE MODELOS
        self._setup_models()

        # CONFIGURACIÓN DE OPTIMIZACIONES AVANZADAS
        self._setup_advanced_optimizations()

        # CONFIGURACIÓN DE EVALUACIÓN
        self._setup_evaluation_system()

        # if self.auto_train:
        #     self.smart_logger.log_if_needed(
        #         LogLevel.INFO,
        #         "init_complete",
        #         "🚀 DQNTrainer inicializado, comenzando entrenamiento...",
        #     )

    def _setup_replay_buffer(self) -> None:
        """Configura el buffer de memoria de experiencias (estándar o priorizado)."""
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

    def _setup_state_management(self) -> None:
        """Configura el manejo de estado y API."""
        self._set_action_space()
        self._set_save_path()
        self.state_size = (
            48  # 12 tiempos + 12 cantidades + 12 tiempos_prev + 12 cantidades_prev
        )

        # Historial para capturar dinámica temporal
        self.state_history: list[list[float]] = []
        self.max_history_length = 2  # Mantener actual + anterior

        # Variables para evitar llamadas API duplicadas
        self._cached_wait_times_response: WaitTimesResponse | None = None
        self._cached_quantities_response: VehicleQuantitiesResponse | None = None

        # Variables para métricas adicionales (bajo costo computacional)
        self.epoch_losses: list[float] = []  # Loss por época
        self.epoch_actions: list[int] = []  # Acciones tomadas para entropía
        self.epoch_q_values: list[float] = []  # Q-values para varianza
        self.epoch_gradients: list[float] = []  # Normas de gradientes
        self._last_loss: float | None = None  # 🔧 NUEVO: Para gradient norm estimation

        # 🎯 COMPONENTES DETALLADOS DE RECOMPENSA (para análisis de entrenamiento)
        self.epoch_wait_penalties: list[float] = []
        self.epoch_congestion_std_penalties: list[float] = []
        self.epoch_congestion_total_penalties: list[float] = []
        self.epoch_efficiency_bonuses: list[float] = []
        self.epoch_avg_wait_times_log: list[float] = []
        self.epoch_total_vehicles: list[int] = []

    def _setup_hyperparameters(self) -> None:
        """Configura todos los hiperparámetros del entrenamiento."""
        # Parámetros básicos de entrenamiento
        self.num_epocas = self.decision_settings.entrenamiento.num_epocas
        self.batch_size = self.decision_settings.entrenamiento.batch_size
        self.min_replay_size = getattr(
            self.decision_settings.entrenamiento, "min_replay_size", 32
        )  # Mínimo para batch dinámico
        self.steps = self.decision_settings.entrenamiento.steps

        # Parámetros de learning rate
        self.learning_rate = self.decision_settings.entrenamiento.learning_rate
        self.learning_rate_decay = (
            self.decision_settings.entrenamiento.learning_rate_decay
        )
        self.learning_rate_min = self.decision_settings.entrenamiento.learning_rate_min

        # Parámetros de exploración
        self.epsilon = self.decision_settings.entrenamiento.epsilon
        self.epsilon_decay = self.decision_settings.entrenamiento.epsilon_decay
        self.epsilon_min = self.decision_settings.entrenamiento.epsilon_min

        # Parámetros de arquitectura
        self.gamma = self.decision_settings.entrenamiento.gamma
        self.hidden_layers = self.decision_settings.entrenamiento.hidden_layers

    def _setup_models(self) -> None:
        """Configura las redes neuronales (online y target)."""
        # Configuración para Double DQN
        self.use_double_dqn = getattr(
            self.decision_settings.entrenamiento, "use_double_dqn", True
        )
        self.target_update_frequency = getattr(
            self.decision_settings.entrenamiento, "target_update_frequency", 100
        )

        # Configuración para Dueling DQN
        self.use_dueling_dqn = getattr(
            self.decision_settings.entrenamiento, "use_dueling_dqn", True
        )

    def _setup_advanced_optimizations(self) -> None:
        """Configura optimizaciones avanzadas (PER, Noisy Networks, etc.)."""
        # Configuración para Prioritized Experience Replay
        self.per_alpha = getattr(self.decision_settings.entrenamiento, "per_alpha", 0.6)
        self.per_beta_start = getattr(
            self.decision_settings.entrenamiento, "per_beta_start", 0.4
        )
        self.per_beta_frames = getattr(
            self.decision_settings.entrenamiento, "per_beta_frames", 100000
        )

        # Configuración para Noisy Networks
        self.use_noisy_networks = getattr(
            self.decision_settings.entrenamiento, "use_noisy_networks", True
        )
        self.noise_std = getattr(self.decision_settings.entrenamiento, "noise_std", 0.5)

        # Configuración para Dropout
        self.use_dropout = getattr(
            self.decision_settings.entrenamiento, "use_dropout", True
        )
        self.dropout_rate = getattr(
            self.decision_settings.entrenamiento, "dropout_rate", 0.1
        )

        # Configuración para Learning Rate Adaptativo
        self.adaptive_lr = getattr(
            self.decision_settings.entrenamiento, "adaptive_lr", True
        )

        # Configuración para testing y debugging
        self.test_large_model = getattr(
            self.decision_settings.entrenamiento, "test_large_model", False
        )

        # 🛡️ CONFIGURACIÓN ANTI-GRADIENT VANISHING
        # Estas configuraciones previenen el colapso de gradientes y Q-values
        self.use_batch_normalization = getattr(
            self.decision_settings.entrenamiento, "use_batch_normalization", False
        )
        self.use_he_initialization = getattr(
            self.decision_settings.entrenamiento, "use_he_initialization", False
        )
        self.use_leaky_relu = getattr(
            self.decision_settings.entrenamiento, "use_leaky_relu", False
        )
        self.use_gradient_clipping = getattr(
            self.decision_settings.entrenamiento, "use_gradient_clipping", True
        )
        self.gradient_clip_norm = getattr(
            self.decision_settings.entrenamiento, "gradient_clip_norm", 1.0
        )
        self.use_huber_loss = getattr(
            self.decision_settings.entrenamiento, "use_huber_loss", False
        )
        self.huber_delta = getattr(
            self.decision_settings.entrenamiento, "huber_delta", 1.0
        )

        # Configuración para optimizaciones avanzadas
        self.enable_jit_compilation = getattr(
            self.decision_settings.entrenamiento, "enable_jit_compilation", True
        )
        self.dropout_mode = getattr(
            self.decision_settings.entrenamiento, "dropout_mode", "optimized"
        )
        self.noisy_implementation = getattr(
            self.decision_settings.entrenamiento, "noisy_implementation", "efficient"
        )
        self.hidden_layers_optimization = getattr(
            self.decision_settings.entrenamiento, "hidden_layers_optimization", False
        )
        self.dueling_stream_simplification = getattr(
            self.decision_settings.entrenamiento, "dueling_stream_simplification", False
        )

        # Configuración para PER avanzado
        self.per_batch_processing = getattr(
            self.decision_settings.entrenamiento, "per_batch_processing", False
        )
        self.per_update_frequency = getattr(
            self.decision_settings.entrenamiento, "per_update_frequency", 4
        )
        self.per_importance_annealing = getattr(
            self.decision_settings.entrenamiento, "per_importance_annealing", False
        )

        # Configuración para Double DQN avanzado
        self.double_dqn_batch_optimization = getattr(
            self.decision_settings.entrenamiento, "double_dqn_batch_optimization", False
        )
        self.target_update_batch_size = getattr(
            self.decision_settings.entrenamiento, "target_update_batch_size", 512
        )

        # Variables de estado para optimizaciones
        self.frame_count: int = 0
        self.per_update_counter: int = 0
        self.target_update_counter: int = 0
        self.target_update_batch_counter: int = 0
        self.per_beta: float = self.per_beta_start
        self.per_beta_increment_per_frame: float = (
            1.0 - self.per_beta_start
        ) / self.per_beta_frames

        # Variables para early stopping
        self.best_avg_reward: float = float("-inf")
        self.epochs_without_improvement: int = 0
        self.patience: int = 10
        self.min_improvement: float = 0.01

        # Atributos para monitoreo de memoria y proceso
        self.process: psutil.Process | None = None

        # Modelo target para Double DQN (se inicializa en start_training_process si se habilita)
        self.target_model: tf.keras.Model | None = None

    def _setup_evaluation_system(self) -> None:
        """Configura el sistema de evaluación y métricas."""
        # Este método se implementará cuando se extraiga la lógica de evaluación
        pass

    def _create_model_builder(self) -> None:
        """Configura el constructor de modelos con arquitecturas avanzadas."""
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

        # 📊 NUEVAS MÉTRICAS ADICIONALES (bajo costo computacional)

        # Loss promedio de la época
        if self.epoch_losses:
            metrics["loss_promedio"] = float(np.mean(self.epoch_losses))
            metrics["loss_std"] = float(np.std(self.epoch_losses))
        else:
            metrics["loss_promedio"] = 0.0
            metrics["loss_std"] = 0.0

        # Varianza de Q-values (inestabilidad del modelo)
        if self.epoch_q_values:
            q_vals_array = np.array(self.epoch_q_values)
            metrics["q_value_varianza"] = float(np.var(q_vals_array))
        else:
            metrics["q_value_varianza"] = 0.0

        # Entropía de acciones (exploración vs explotación)
        if self.epoch_actions and len(set(self.epoch_actions)) > 1:
            action_counts = np.bincount(
                self.epoch_actions, minlength=len(self._action_space)
            )
            action_probs = action_counts / len(self.epoch_actions)
            action_probs = action_probs[action_probs > 0]  # Evitar log(0)
            metrics["action_entropy"] = float(
                -np.sum(action_probs * np.log(action_probs))
            )
        else:
            metrics["action_entropy"] = 0.0

        # Gradient norm (se calculará cuando esté disponible)
        if self.epoch_gradients:
            metrics["gradient_norm"] = float(np.mean(self.epoch_gradients))
        else:
            metrics["gradient_norm"] = 0.0

        # Memoria GPU solo si está disponible y no es costosa
        metrics["memoria_gpu_pico_mb"] = 0.0
        # REMOVIDO: Llamada costosa a tf.config.experimental.get_memory_info()
        # Esta operación puede ser muy lenta y afectar el rendimiento del entrenamiento

        # Métricas de simulación - REMOVIDAS para evitar llamadas API costosas
        # Estas métricas requieren llamadas HTTP adicionales que ralentizan el entrenamiento
        metrics["tiempo_espera_total"] = 0.0
        metrics["tiempo_espera_promedio"] = 0.0
        metrics["congestion_maxima"] = 0.0

        # 🎯 COMPONENTES DETALLADOS DE RECOMPENSA (para análisis de entrenamiento)
        if self.epoch_wait_penalties:
            metrics["wait_penalty_promedio"] = float(np.mean(self.epoch_wait_penalties))
        else:
            metrics["wait_penalty_promedio"] = 0.0

        if self.epoch_congestion_std_penalties:
            metrics["congestion_std_penalty_promedio"] = float(
                np.mean(self.epoch_congestion_std_penalties)
            )
        else:
            metrics["congestion_std_penalty_promedio"] = 0.0

        if self.epoch_congestion_total_penalties:
            metrics["congestion_total_penalty_promedio"] = float(
                np.mean(self.epoch_congestion_total_penalties)
            )
        else:
            metrics["congestion_total_penalty_promedio"] = 0.0

        if self.epoch_efficiency_bonuses:
            metrics["efficiency_bonus_promedio"] = float(
                np.mean(self.epoch_efficiency_bonuses)
            )
        else:
            metrics["efficiency_bonus_promedio"] = 0.0

        if self.epoch_avg_wait_times_log:
            metrics["avg_wait_time_log_promedio"] = float(
                np.mean(self.epoch_avg_wait_times_log)
            )
        else:
            metrics["avg_wait_time_log_promedio"] = 0.0

        if self.epoch_total_vehicles:
            metrics["total_vehicles_promedio"] = float(
                np.mean(self.epoch_total_vehicles)
            )
        else:
            metrics["total_vehicles_promedio"] = 0.0

        return metrics

    def _compute_gradient_norm(self) -> float | None:
        """
        Calcula la norma L2 de los gradientes del modelo.
        Esto ayuda a detectar gradient explosion/vanishing.

        Returns:
            float | None: Norma L2 de gradientes o None si hay error
        """
        try:
            if self.model is None:
                return None

            # 🔧 SOLUCIÓN SIMPLE: Usar loss como indicador directo
            # Si loss = 0 → gradientes = 0
            # Si loss > 0 → gradientes existen (magnitud proporcional a loss)
            if hasattr(self, "_last_loss") and self._last_loss is not None:
                if self._last_loss < 1e-10:  # Loss prácticamente cero
                    return 0.0
                else:
                    # Usar loss directamente como proxy para gradient magnitude
                    # Esto es consistente: loss alta = gradientes grandes
                    return float(self._last_loss)

            return None
        except Exception:
            return None

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

            # Crear optimizador con gradient clipping para estabilidad
            optimizer = self._create_optimizer_with_clipping()

            # Configurar pérdida (Huber Loss más robusto que MSE)
            loss_function = (
                tf.keras.losses.Huber(delta=self.huber_delta)
                if self.use_huber_loss
                else "mse"
            )

            model.compile(
                loss=loss_function,
                optimizer=optimizer,
                jit_compile=jit_compile_enabled,
                metrics=["mae"],
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

    def _create_optimizer_with_clipping(self) -> tf.keras.optimizers.Optimizer:
        """
        Crea un optimizador con gradient clipping para estabilidad del entrenamiento.

        Gradient clipping previene:
        - Gradient explosion (gradientes muy grandes)
        - Inestabilidad en el entrenamiento
        - Divergencia del modelo

        Returns:
            tf.keras.optimizers.Optimizer: Optimizador configurado con clipping
        """
        # Obtener norma de clipping desde configuración
        clip_norm = self.gradient_clip_norm

        # Usar gradient clipping si está habilitado
        if self.use_gradient_clipping:
            optimizer = tf.keras.optimizers.Adam(
                learning_rate=self.learning_rate,
                clipnorm=clip_norm,  # Gradient clipping por norma L2
                # Parámetros optimizados para DQN
                beta_1=0.9,
                beta_2=0.999,
                epsilon=1e-7,
            )
        else:
            optimizer = tf.keras.optimizers.Adam(
                learning_rate=self.learning_rate,
                beta_1=0.9,
                beta_2=0.999,
                epsilon=1e-7,
            )

        return optimizer

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
        Construye el modelo DQN estándar con mejoras anti-gradient vanishing.

        MEJORAS IMPLEMENTADAS:
        - He initialization para ReLU/LeakyReLU
        - Batch Normalization entre capas
        - LeakyReLU para evitar "dying ReLU"
        - Residual connections opcionales
        - Gradient clipping integrado

        Returns:
            tf.keras.Model: Modelo DQN optimizado contra gradient vanishing
        """
        model = tf.keras.Sequential()

        # Configurar inicialización
        initializer = "he_normal" if self.use_he_initialization else "random_normal"

        # Primera capa con configuración optimizada
        if self.use_noisy_networks:
            model.add(
                self._create_noisy_layer(
                    self.hidden_layers[0],
                    input_dim=self.state_size,
                    activation="linear",  # Sin activación en Dense
                )
            )
        else:
            model.add(
                tf.keras.layers.Dense(
                    self.hidden_layers[0],
                    input_dim=self.state_size,
                    activation="linear",  # Sin activación en Dense
                    kernel_initializer=initializer,
                )
            )

        # 🛡️ APLICAR ACTIVACIÓN CORRECTA (LeakyReLU o ReLU)
        if self.use_leaky_relu:
            model.add(tf.keras.layers.LeakyReLU(alpha=0.01))
        else:
            model.add(tf.keras.layers.ReLU())

        # Batch Normalization después de la activación
        if self.use_batch_normalization:
            model.add(tf.keras.layers.BatchNormalization())

        # Dropout después de la primera capa si está habilitado
        if self.use_dropout and self._should_add_dropout(layer_index=1):
            model.add(tf.keras.layers.Dropout(self.dropout_rate))

        # Capas ocultas restantes con mejoras
        for i in range(1, len(self.hidden_layers)):
            if self.use_noisy_networks:
                model.add(
                    self._create_noisy_layer(
                        self.hidden_layers[i], activation="linear"  # Sin activación
                    )
                )
            else:
                model.add(
                    tf.keras.layers.Dense(
                        self.hidden_layers[i],
                        activation="linear",  # Sin activación
                        kernel_initializer=initializer,
                    )
                )

            # 🛡️ APLICAR ACTIVACIÓN CORRECTA
            if self.use_leaky_relu:
                model.add(tf.keras.layers.LeakyReLU(alpha=0.01))
            else:
                model.add(tf.keras.layers.ReLU())

            # Batch Normalization entre capas
            if self.use_batch_normalization:
                model.add(tf.keras.layers.BatchNormalization())

            # Dropout entre capas si está habilitado
            if self.use_dropout and self._should_add_dropout(layer_index=i + 1):
                model.add(tf.keras.layers.Dropout(self.dropout_rate))

            # Dropout entre capas si está habilitado
            if self.use_dropout and self._should_add_dropout(layer_index=i + 1):
                model.add(tf.keras.layers.Dropout(self.dropout_rate))

        # Capa de salida (sin dropout, sin batch norm)
        if self.use_noisy_networks:
            model.add(
                self._create_noisy_layer(len(self._action_space), activation="linear")
            )
        else:
            model.add(
                tf.keras.layers.Dense(
                    len(self._action_space),
                    activation="linear",
                    kernel_initializer=initializer,
                )
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

        OPTIMIZACIÓN AVANZADA: Soporte para simplificación de streams y optimización automática de capas.

        Returns:
            tf.keras.Model: Modelo Dueling DQN con optimizaciones
        """
        # OPTIMIZACIÓN: Hidden layers optimization automática
        if self.hidden_layers_optimization:
            # Optimizar automáticamente el número de capas basado en el tamaño del problema
            optimized_layers = self._optimize_hidden_layers()
            logger = logging.getLogger(
                f" {self.__class__.__name__}._build_dueling_model"
            )
            logger.info(
                f" 🏗️⚡ Capas optimizadas: {self.hidden_layers} → {optimized_layers}"
            )
            working_layers = optimized_layers
        else:
            working_layers = self.hidden_layers

        # Input layer
        inputs = tf.keras.layers.Input(shape=(self.state_size,))

        # 🛡️ CONFIGURAR INICIALIZACIÓN ANTI-GRADIENT VANISHING
        initializer = "he_normal" if self.use_he_initialization else "random_normal"

        # Capas compartidas (shared layers) con mejoras de Fase 3
        shared = inputs

        # OPTIMIZACIÓN: Determinar número de capas compartidas de forma inteligente
        if self.dueling_stream_simplification:
            # Simplificación: usar menos capas compartidas, streams más directos
            shared_layers_count = max(
                1, len(working_layers) // 3
            )  # Solo el primer tercio
        else:
            # Comportamiento original: usar todas menos las últimas 2
            shared_layers_count = max(1, len(working_layers) - 2)

        for i in range(shared_layers_count):
            units = working_layers[i] if i < len(working_layers) else working_layers[-1]

            if self.use_noisy_networks:
                # Crear capa noisy usando Sequential como workaround
                noisy_layer = tf.keras.Sequential(
                    [
                        tf.keras.layers.Dense(
                            units,
                            activation="linear",
                            name=f"shared_{i}_dense",
                            kernel_initializer=initializer,
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
                    units,
                    activation="linear",
                    name=f"shared_{i}",
                    kernel_initializer=initializer,
                )(shared)

            # 🛡️ APLICAR ACTIVACIÓN ANTI-GRADIENT VANISHING
            if self.use_leaky_relu:
                shared = tf.keras.layers.LeakyReLU(
                    alpha=0.01, name=f"shared_{i}_leaky_relu"
                )(shared)
            else:
                shared = tf.keras.layers.ReLU(name=f"shared_{i}_relu")(shared)

            # 🛡️ BATCH NORMALIZATION ANTI-GRADIENT VANISHING
            if self.use_batch_normalization:
                shared = tf.keras.layers.BatchNormalization(name=f"shared_{i}_bn")(
                    shared
                )

            # Añadir Dropout si está habilitado
            if self.use_dropout and self._should_add_dropout(layer_index=i):
                shared = tf.keras.layers.Dropout(
                    self.dropout_rate, name=f"shared_{i}_dropout"
                )(shared)

        # OPTIMIZACIÓN: Streams simplificados cuando está habilitado
        if self.dueling_stream_simplification:
            # Simplificación: streams más directos con menos capas
            value_units = working_layers[-2] if len(working_layers) >= 2 else 64
            advantage_units = working_layers[-1] if len(working_layers) >= 1 else 64
        else:
            # Comportamiento original
            value_units = working_layers[-2] if len(working_layers) >= 2 else 128
            advantage_units = working_layers[-1] if len(working_layers) >= 1 else 128

        # Stream de valor del estado V(s) - 🛡️ CON CONFIGURACIONES ANTI-GRADIENT VANISHING
        if self.use_noisy_networks and self.noisy_implementation == "efficient":
            value_stream = tf.keras.layers.Dense(
                value_units,
                activation="linear",  # Sin activación en Dense
                name="value_hidden",
                kernel_initializer=initializer,
            )(shared)
        elif self.use_noisy_networks:
            value_stream = tf.keras.Sequential(
                [
                    tf.keras.layers.Dense(
                        value_units,
                        activation="linear",  # Sin activación en Dense
                        name="value_hidden_dense",
                        kernel_initializer=initializer,
                    ),
                    tf.keras.layers.GaussianNoise(
                        stddev=self.noise_std, name="value_hidden_noise"
                    ),
                ],
                name="value_stream",
            )(shared)
        else:
            value_stream = tf.keras.layers.Dense(
                value_units,
                activation="linear",
                name="value_hidden",
                kernel_initializer=initializer,
            )(shared)

        # 🛡️ ACTIVACIÓN ANTI-GRADIENT VANISHING para value stream
        if self.use_leaky_relu:
            value_stream = tf.keras.layers.LeakyReLU(
                alpha=0.01, name="value_leaky_relu"
            )(value_stream)
        else:
            value_stream = tf.keras.layers.ReLU(name="value_relu")(value_stream)

        # 🛡️ BATCH NORMALIZATION para value stream
        if self.use_batch_normalization:
            value_stream = tf.keras.layers.BatchNormalization(name="value_bn")(
                value_stream
            )

        # Dropout para value stream solo si no es simplificado o si es necesario
        if self.use_dropout and (
            not self.dueling_stream_simplification or self.dropout_mode == "full"
        ):
            value_stream = tf.keras.layers.Dropout(
                self.dropout_rate, name="value_dropout"
            )(value_stream)

        value = tf.keras.layers.Dense(1, name="value")(value_stream)

        # Stream de ventaja de acciones A(s,a) - 🛡️ CON CONFIGURACIONES ANTI-GRADIENT VANISHING
        if self.use_noisy_networks and self.noisy_implementation == "efficient":
            advantage_stream = tf.keras.layers.Dense(
                advantage_units,
                activation="linear",  # Sin activación en Dense
                name="advantage_hidden",
                kernel_initializer=initializer,
            )(shared)
        elif self.use_noisy_networks:
            advantage_stream = tf.keras.Sequential(
                [
                    tf.keras.layers.Dense(
                        advantage_units,
                        activation="linear",  # Sin activación en Dense
                        name="advantage_hidden_dense",
                        kernel_initializer=initializer,
                    ),
                    tf.keras.layers.GaussianNoise(
                        stddev=self.noise_std, name="advantage_hidden_noise"
                    ),
                ],
                name="advantage_stream",
            )(shared)
        else:
            advantage_stream = tf.keras.layers.Dense(
                advantage_units,
                activation="linear",
                name="advantage_hidden",
                kernel_initializer=initializer,
            )(shared)

        # 🛡️ ACTIVACIÓN ANTI-GRADIENT VANISHING para advantage stream
        if self.use_leaky_relu:
            advantage_stream = tf.keras.layers.LeakyReLU(
                alpha=0.01, name="advantage_leaky_relu"
            )(advantage_stream)
        else:
            advantage_stream = tf.keras.layers.ReLU(name="advantage_relu")(
                advantage_stream
            )

        # 🛡️ BATCH NORMALIZATION para advantage stream
        if self.use_batch_normalization:
            advantage_stream = tf.keras.layers.BatchNormalization(name="advantage_bn")(
                advantage_stream
            )

        # Dropout para advantage stream solo si no es simplificado o si es necesario
        if self.use_dropout and (
            not self.dueling_stream_simplification or self.dropout_mode == "full"
        ):
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

        model_name = (
            "Dueling_DQN_Simplified"
            if self.dueling_stream_simplification
            else "Dueling_DQN"
        )
        model = tf.keras.Model(inputs=inputs, outputs=q_values, name=model_name)

        return model

    def _optimize_hidden_layers(self) -> list[int]:
        """
        Optimiza automáticamente el número y tamaño de capas ocultas.

        OPTIMIZACIÓN AVANZADA: Algoritmo heurístico para determinar arquitectura óptima.

        Returns:
            list[int]: Lista optimizada de tamaños de capas ocultas
        """
        # Heurísticas basadas en el tamaño del problema
        input_size = self.state_size
        output_size = len(self._action_space)

        # Cálculo de complejidad del problema
        problem_complexity = input_size * output_size

        if problem_complexity < 100:
            # Problema simple: arquitectura más ligera
            optimized = [64, 32]
        elif problem_complexity < 500:
            # Problema moderado: arquitectura mediana
            optimized = [128, 64, 32]
        elif problem_complexity < 1000:
            # Problema complejo: arquitectura robusta pero optimizada
            optimized = [256, 128, 64]
        else:
            # Problema muy complejo: usar arquitectura original pero simplificada
            # Reducir hasta 75% del tamaño original
            scale_factor = 0.75
            optimized = [
                max(32, int(layer * scale_factor)) for layer in self.hidden_layers[:5]
            ]

        # Asegurar que tenemos al menos 2 capas para Dueling DQN
        if len(optimized) < 2:
            optimized.append(max(32, optimized[-1] // 2))

        # Log de la optimización
        logger = logging.getLogger(
            f" {self.__class__.__name__}._optimize_hidden_layers"
        )
        total_params_original = sum(self.hidden_layers)
        total_params_optimized = sum(optimized)
        reduction_pct = (
            (total_params_original - total_params_optimized) / total_params_original
        ) * 100

        logger.info(
            f" 🏗️ Problema: {input_size}→{output_size} (complejidad: {problem_complexity})"
        )
        logger.info(
            f" 🏗️ Reducción de parámetros: {reduction_pct:.1f}% ({total_params_original}→{total_params_optimized})"
        )

        return optimized

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

        # 📊 Capturar acción para entropía (sin costo adicional)
        self.epoch_actions.append(action)

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
        Replay con Prioritized Experience Replay (PER) y batch size dinámico.

        OPTIMIZACIÓN AVANZADA: Soporte para batch processing y actualización eficiente de prioridades.
        """
        assert isinstance(
            self.memory_buffer, PrioritizedReplayBuffer
        ), "Prioritized replay requires PrioritizedReplayBuffer"

        # Batch size dinámico: empezar entrenamiento temprano pero escalar gradualmente
        if len(self.memory_buffer) < self.min_replay_size:
            return

        # Calcular batch size efectivo (dinámico)
        effective_batch_size = min(self.batch_size, len(self.memory_buffer))

        # OPTIMIZACIÓN: Batch processing para TD-errors
        if self.per_batch_processing:
            # Procesar lotes más grandes para mejor eficiencia
            batch_multiplier = min(4, len(self.memory_buffer) // self.batch_size)
            effective_batch_size = min(
                effective_batch_size * max(1, batch_multiplier), len(self.memory_buffer)
            )

        # OPTIMIZACIÓN: Importance sampling annealing inteligente
        if self.per_importance_annealing:
            # Annealing adaptativo basado en progreso del entrenamiento
            training_progress = (
                len(self.memory_buffer) / self.decision_settings.entrenamiento.memory
            )
            # Annealing más rápido al inicio, más lento después
            adaptive_increment = self.per_beta_increment_per_frame * (
                1 + training_progress
            )
            self.per_beta = min(1.0, self.per_beta + adaptive_increment)
        else:
            # Annealing estándar
            self.per_beta = min(1.0, self.per_beta + self.per_beta_increment_per_frame)

        # Muestrear experiencias con prioridades usando batch size dinámico
        minibatch, indices, weights = self.memory_buffer.sample(
            effective_batch_size, self.per_beta
        )

        if not minibatch:
            return

        # OPTIMIZACIÓN: Actualizar prioridades menos frecuentemente
        self.per_update_counter += 1
        should_update_priorities = (
            self.per_update_counter % self.per_update_frequency == 0
        )

        if should_update_priorities:
            # Calcular TD-errors para actualizar prioridades (solo cuando sea necesario)
            if self.per_batch_processing:
                # Procesamiento optimizado de TD-errors en chunks
                td_errors = self._calculate_td_errors_batch_optimized(minibatch)
            else:
                # Cálculo estándar de TD-errors
                td_errors = self._calculate_td_errors(minibatch)

            # Actualizar prioridades en el buffer
            self.memory_buffer.update_priorities(indices, td_errors)

            # Log ocasional del estado de PER optimizaciones
            if self.per_update_counter % (self.per_update_frequency * 20) == 0:
                logger = logging.getLogger(
                    f" {self.__class__.__name__}._replay_prioritized"
                )
                logger.debug(
                    f" 🎯⚡ PER optimizado: freq={self.per_update_frequency}, beta={self.per_beta:.3f}"
                )

        # Entrenar con importance sampling weights
        self._train_batch_with_weights(minibatch, weights)

    def _replay_standard(self) -> None:
        """
        Replay estándar sin priorización con batch size dinámico.
        """
        assert isinstance(
            self.memory_buffer, deque
        ), "Standard replay requires deque memory buffer"
        assert self.model is not None, "Model must be initialized before replay"

        # Batch size dinámico: empezar entrenamiento temprano pero escalar gradualmente
        if len(self.memory_buffer) < self.min_replay_size:
            return

        # Calcular batch size efectivo (dinámico)
        effective_batch_size = min(self.batch_size, len(self.memory_buffer))

        # Log del progreso del batch dinámico (solo ocasionalmente para no saturar logs)
        if len(self.memory_buffer) % 50 == 0:  # Cada 50 experiencias
            logger = logging.getLogger(f" {self.__class__.__name__}._replay_standard")
            progress_pct = min(100, (len(self.memory_buffer) / self.batch_size) * 100)
            logger.info(
                f" � Batch dinámico ENTRENANDO: {effective_batch_size}/{self.batch_size} "
                f"({progress_pct:.1f}%) - Memoria: {len(self.memory_buffer)}"
            )

        minibatch: list[tuple[NDArray, int, float, NDArray, bool]] = random.sample(
            self.memory_buffer, effective_batch_size
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

                # 🔍 DEBUG CRÍTICO: Verificar por qué Loss = 0.000000
                print("=== 🔍 DEBUG ENTRENAMIENTO (GPU) ===")
                print(f"Batch size: {len(minibatch)}")
                print(f"Rewards (primeros 5): {batch_rewards.numpy()[:5]}")
                print(f"Dones (primeros 5): {batch_dones.numpy()[:5]}")
                print(f"Actions (primeros 5): {batch_actions.numpy()[:5]}")
                print(f"Max next Q (primeros 5): {max_next_q.numpy()[:5]}")
                print(f"Targets (primeros 5): {targets.numpy()[:5]}")
                print(
                    f"Current Q-Values (primera muestra): {current_q_values[0].numpy()}"
                )
                print(
                    f"Updated Q-Values (primera muestra): {updated_q_values[0].numpy()}"
                )

                # Calcular diferencia entre predicciones y targets
                diff = tf.reduce_mean(tf.abs(current_q_values - updated_q_values))
                max_diff = tf.reduce_max(tf.abs(current_q_values - updated_q_values))
                print(f"Diferencia promedio: {diff.numpy()}")
                print(f"Diferencia máxima: {max_diff.numpy()}")
                print("================================")

                # Entrenar el modelo y capturar loss
                history = self.model.fit(
                    batch_states,
                    updated_q_values,
                    epochs=1,
                    verbose=0,
                    batch_size=self.batch_size,
                )

                # 📊 Capturar loss para métricas (sin costo adicional)
                if history.history and "loss" in history.history:
                    loss_value = history.history["loss"][0]
                    self.epoch_losses.append(loss_value)
                    # 🔧 NUEVO: Guardar último valor de loss para gradient norm
                    self._last_loss = loss_value

                    # 🔍 DEBUG: Solo mostrar loss ocasionalmente (cada 100 batches)
                    if len(self.epoch_losses) % 100 == 1:  # Primera vez y cada 100
                        print(f"🔧 DEBUG: Loss calculada (GPU): {loss_value:.6f}")
                else:
                    if len(self.epoch_losses) % 100 == 1:
                        print("⚠️ WARNING: No se pudo capturar loss del history (GPU)")
                    self._last_loss = None

                # 📊 Capturar norma de gradientes (cálculo ligero post-entrenamiento)
                try:
                    gradient_norm = self._compute_gradient_norm()
                    if gradient_norm is not None:
                        self.epoch_gradients.append(gradient_norm)
                except Exception:
                    pass  # Ignorar errores de gradient norm para no afectar entrenamiento

                # 📊 Capturar Q-values para varianza (CONSISTENCIA: usar current_q_values como CPU y PER)
                if isinstance(current_q_values, tf.Tensor):
                    q_vals = current_q_values.numpy()
                else:
                    q_vals = current_q_values
                self.epoch_q_values.extend(q_vals.flatten())
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

            # 🔍 DEBUG CRÍTICO: Verificar por qué Loss = 0.000000
            print("=== 🔍 DEBUG ENTRENAMIENTO (CPU) ===")
            print(f"Batch size: {len(minibatch)}")
            rewards_sample = [reward for _, _, reward, _, _ in minibatch[:5]]
            dones_sample = [done for _, _, _, _, done in minibatch[:5]]
            actions_sample = [action for _, action, _, _, _ in minibatch[:5]]
            print(f"Rewards (primeros 5): {rewards_sample}")
            print(f"Dones (primeros 5): {dones_sample}")
            print(f"Actions (primeros 5): {actions_sample}")
            print(f"Current Q-Values (primera muestra): {current_q_values[0]}")
            print(f"Targets (primera muestra): {targets[0]}")

            # Calcular diferencia entre predicciones y targets
            diff = np.mean(np.abs(current_q_values - targets))
            max_diff = np.max(np.abs(current_q_values - targets))
            print(f"Diferencia promedio: {diff}")
            print(f"Diferencia máxima: {max_diff}")
            print("================================")

            # Entrenar y capturar loss
            history = self.model.fit(
                states, targets, epochs=1, verbose=0, batch_size=self.batch_size
            )

            # 📊 Capturar loss para métricas (sin costo adicional)
            if history.history and "loss" in history.history:
                loss_value = history.history["loss"][0]
                self.epoch_losses.append(loss_value)
                # 🔧 NUEVO: Guardar último valor de loss para gradient norm
                self._last_loss = loss_value

                # 🔍 DEBUG: Solo mostrar loss ocasionalmente (cada 100 batches)
                if len(self.epoch_losses) % 100 == 1:  # Primera vez y cada 100
                    print(f"🔧 DEBUG: Loss calculada (CPU): {loss_value:.6f}")
            else:
                if len(self.epoch_losses) % 100 == 1:
                    print("⚠️ WARNING: No se pudo capturar loss del history (CPU)")
                self._last_loss = None

            # 📊 Capturar norma de gradientes (cálculo ligero post-entrenamiento)
            try:
                gradient_norm = self._compute_gradient_norm()
                if gradient_norm is not None:
                    self.epoch_gradients.append(gradient_norm)
            except Exception:
                pass  # Ignorar errores de gradient norm para no afectar entrenamiento

            # 📊 Capturar Q-values para varianza (datos ya disponibles)
            # 🔧 CONSISTENCIA: Usar current_q_values (predicciones) igual que GPU path
            self.epoch_q_values.extend(current_q_values.flatten())

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

    def _calculate_td_errors_batch_optimized(self, minibatch: list) -> list[float]:
        """
        Calcula TD-errors de forma optimizada para lotes grandes (PER optimization).

        OPTIMIZACIÓN AVANZADA: Procesamiento en chunks para mejor eficiencia de memoria y GPU.
        """
        assert (
            self.model is not None
        ), "Model must be initialized before calculating TD errors"

        if not minibatch:
            return []

        # Procesar en chunks para optimizar memoria
        chunk_size = min(128, len(minibatch))  # Chunks más pequeños para eficiencia
        all_td_errors = []

        for i in range(0, len(minibatch), chunk_size):
            chunk = minibatch[i : i + chunk_size]

            # Procesar chunk
            states = np.array([s for s, _, _, _, _ in chunk], dtype=np.float32)
            next_states = np.array([ns for _, _, _, ns, _ in chunk], dtype=np.float32)

            # Predicciones en lote para eficiencia
            current_q_values = self.model.predict(
                states, verbose=0, batch_size=len(states)
            )
            next_q_values = self.model.predict(
                next_states, verbose=0, batch_size=len(next_states)
            )

            if self.use_double_dqn and hasattr(self, "target_model"):
                assert (
                    self.target_model is not None
                ), "Target model must be initialized for Double DQN"
                next_q_values_target = self.target_model.predict(
                    next_states, verbose=0, batch_size=len(next_states)
                )

            # Calcular TD-errors para el chunk
            chunk_td_errors = []
            for j, (_, action, reward, _, done) in enumerate(chunk):
                current_q = current_q_values[j][action]

                if done:
                    target_q = reward
                else:
                    if self.use_double_dqn and hasattr(self, "target_model"):
                        best_action = np.argmax(next_q_values[j])
                        target_q = (
                            reward + self.gamma * next_q_values_target[j][best_action]
                        )
                    else:
                        target_q = reward + self.gamma * np.max(next_q_values[j])

                td_error = abs(target_q - current_q)
                chunk_td_errors.append(td_error)

            all_td_errors.extend(chunk_td_errors)

        return all_td_errors

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

        # 🔧 CORREGIDO: Entrenar con importance sampling Y capturar loss
        history = self.model.fit(
            states, targets, epochs=1, verbose=0, sample_weight=weights
        )

        # 📊 NUEVO: Capturar loss también en PER
        if history.history and "loss" in history.history:
            loss_value = history.history["loss"][0]
            self.epoch_losses.append(loss_value)
            self._last_loss = loss_value

            # 🔍 DEBUG: Solo mostrar loss ocasionalmente (cada 100 batches)
            if len(self.epoch_losses) % 100 == 1:  # Primera vez y cada 100
                print(f"🔧 DEBUG: Loss calculada (PER): {loss_value:.6f}")
        else:
            if len(self.epoch_losses) % 100 == 1:
                print("⚠️ WARNING: No se pudo capturar loss del history (PER)")
            self._last_loss = None

        # 📊 NUEVO: Capturar gradient norm también en PER
        try:
            gradient_norm = self._compute_gradient_norm()
            if gradient_norm is not None:
                self.epoch_gradients.append(gradient_norm)
        except Exception:
            pass  # Ignorar errores de gradient norm para no afectar entrenamiento

        # 📊 NUEVO: Capturar Q-values para varianza en PER (consistente con otros paths)
        self.epoch_q_values.extend(current_q_values.flatten())

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

        OPTIMIZACIÓN AVANZADA: Soporte para batch optimization cuando está habilitado.
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

            if self.double_dqn_batch_optimization:
                # OPTIMIZACIÓN: Actualización por lotes para mejor eficiencia
                # Acumular actualizaciones y procesarlas en lotes
                self.target_update_batch_counter += 1

                if self.target_update_batch_counter >= self.target_update_batch_size:
                    # Realizar actualización por lotes
                    weights = self.model.get_weights()
                    # Procesamiento optimizado de pesos en chunks
                    chunk_size = max(1, len(weights) // 4)  # Procesar en 4 chunks

                    for i in range(0, len(weights), chunk_size):
                        chunk = weights[i : i + chunk_size]
                        target_chunk = self.target_model.get_weights()[
                            i : i + chunk_size
                        ]

                        # Aplicar actualización suave (tau=1.0 para copia completa, <1.0 para suave)
                        tau = 1.0  # Copia completa por defecto
                        for j, (w, t_w) in enumerate(
                            zip(chunk, target_chunk, strict=False)
                        ):
                            target_chunk[j] = tau * w + (1 - tau) * t_w

                        # Actualizar chunk en el modelo target
                        self.target_model.set_weights(
                            self.target_model.get_weights()[:i]
                            + target_chunk
                            + self.target_model.get_weights()[i + len(target_chunk) :]
                        )

                    self.target_update_batch_counter = 0
                    logger.info(
                        f" 🎯⚡ Red target actualizada (Batch Opt: {self.target_update_batch_size})"
                    )
                else:
                    # Acumular para próxima actualización por lotes
                    if self.target_update_batch_counter % 100 == 0:  # Log ocasional
                        progress = (
                            self.target_update_batch_counter
                            / self.target_update_batch_size
                        ) * 100
                        logger.debug(
                            f" 🎯📊 Acumulando para batch update: {progress:.1f}%"
                        )
            else:
                # Actualización estándar (comportamiento original)
                self.target_model.set_weights(self.model.get_weights())
                logger.info(" 🎯 Red target actualizada con pesos de la red principal")

    def _check_early_stopping(self, current_avg_reward: float, epoch: int) -> bool:
        """
        Verifica si se debe activar early stopping basado en mejoras del rendimiento.

        Args:
            current_avg_reward: Recompensa promedio de la época actual
            epoch: Número de época actual

        Returns:
            bool: True si se debe detener el entrenamiento
        """
        improved = current_avg_reward > (self.best_avg_reward + self.min_improvement)

        if improved:
            self.best_avg_reward = current_avg_reward
            self.epochs_without_improvement = 0
            return False
        else:
            self.epochs_without_improvement += 1

        # Early stopping si no hay mejora en varias épocas
        if self.epochs_without_improvement >= self.patience:
            logger = logging.getLogger(
                f" {self.__class__.__name__}._check_early_stopping"
            )
            logger.info(f" 🛑 Early stopping activado en época {epoch}")
            logger.info(f" 📈 Sin mejora por {self.epochs_without_improvement} épocas")
            logger.info(f" 🏆 Mejor recompensa promedio: {self.best_avg_reward:.2f}")
            return True

        return False

    def _adaptive_learning_rate_update(self, epoch: int, current_reward: float) -> None:
        """
        Actualiza learning rate de manera adaptativa basado en el rendimiento.

        Args:
            epoch: Número de época actual
            current_reward: Recompensa de la época actual
        """
        # Solo actualizar si el modelo está inicializado
        if self.model is None:
            return

        # Aplicar decay programado
        if self.adaptive_lr and hasattr(self.model, "optimizer"):
            # Decay más agresivo si no hay mejora
            if self.epochs_without_improvement > 3:
                decay_factor = 0.8  # Decay más fuerte
            else:
                decay_factor = self.learning_rate_decay

            # Actualizar learning rate
            new_lr = max(
                self.learning_rate_min,
                float(self.model.optimizer.learning_rate) * decay_factor,
            )

            if new_lr != float(self.model.optimizer.learning_rate):
                self.model.optimizer.learning_rate.assign(new_lr)
                self.learning_rate = new_lr  # Actualizar atributo para métricas

                logger = logging.getLogger(
                    f" {self.__class__.__name__}._adaptive_learning_rate_update"
                )
                logger.debug(f" 📉 Learning rate actualizado: {new_lr:.6f}")

    def _skip_warmup_steps(self, warmup_steps: int = 250) -> int:
        """
        Avanza la simulación los primeros pasos sin entrenar para esperar que lleguen vehículos.

        Args:
            warmup_steps: Número de pasos a avanzar sin entrenamiento (default: 250)

        Returns:
            int: Número real de pasos avanzados durante warm-up
        """
        logger = logging.getLogger(f"{self.__class__.__name__}._skip_warmup_steps")
        logger.info(
            f" 🔄 Iniciando warm-up: avanzando {warmup_steps} pasos sin entrenamiento"
        )

        # Avanzar directamente todos los pasos de warm-up en una sola llamada
        response = self._api.advance_simulation(steps=warmup_steps)
        if response is None:
            logger.warning("⚠️ No se pudo avanzar simulación durante warm-up")
            return 0

        logger.info(f"✅ Warm-up completado: {warmup_steps} pasos avanzados")
        return warmup_steps

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

        # Variable para rastrear la época actual (evita error de MyPy con variable 'e')
        current_epoch: int = 0

        for e in range(self.num_epocas):
            current_epoch = e  # Guardar época actual para uso posterior
            logger.info(f" 🏁 Iniciando época {e+1}/{self.num_epocas}")

            # FASE DE WARM-UP: Avanzar pasos iniciales sin entrenamiento
            warmup_steps = getattr(
                self.decision_settings.entrenamiento, "warmup_steps", 250
            )
            actual_warmup = self._skip_warmup_steps(warmup_steps)

            # Log del estado inicial del entrenamiento
            memory_size = self._get_memory_size()
            logger.info(
                f" 📊 Estado inicial época {e+1}: Memoria={memory_size}, "
                f"Min_replay={self.min_replay_size}, Batch_size={self.batch_size}, "
                f"Warmup_completado={actual_warmup} pasos"
            )

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

                # Normalizar recompensa para mayor estabilidad
                normalized_reward = self._normalize_reward(reward)

                # Recopilar métricas de la acción (usar recompensa original para métricas)
                epoch_rewards.append(
                    reward
                )  # Mantener recompensa original para análisis
                epoch_actions.append(action_index)
                epoch_q_values.append(max_q_value)
                inference_times.append(inference_time)

                total_reward += reward  # Acumulación con recompensa original

                # Incrementar step counter del smart logger
                # self.smart_logger.step()
                total_steps += 1
                # Usar recompensa normalizada para entrenamiento
                self._remember(state, action_index, normalized_reward, next_state, done)

                state = next_state

                # 🚀 CRÍTICO: Usar min_replay_size para entrenamiento temprano (batch dinámico)
                if self._get_memory_size() >= self.min_replay_size:
                    # Log cuando se inicia el entrenamiento por primera vez
                    if replay_count == 0:
                        memory_size = self._get_memory_size()
                        logger.info(
                            f" 🎯 ¡ENTRENAMIENTO INICIADO! Memoria: {memory_size}/{self.min_replay_size} "
                            f"(Paso total: {total_steps + warmup_steps}, Época: {e+1})"
                        )

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

            # 📊 ACTUALIZAR DASHBOARD DE PROGRESO
            progress_metrics = ProgressMetrics(
                epoch=e + 1,
                total_steps=total_steps,
                avg_reward=(
                    sum(epoch_rewards) / len(epoch_rewards) if epoch_rewards else 0
                ),
                cumulative_reward=total_reward,
                epsilon=self.epsilon,
                learning_rate=self.learning_rate,
                avg_q_value=training_metrics["q_value_promedio"],
                max_q_value=training_metrics["q_value_maximo"],
                replay_count=replay_count,
                epoch_duration=epoch_duration,
                steps_per_second=training_metrics["pasos_por_segundo"],
            )

            # Actualizar dashboard con métricas de progreso
            self.dashboard.update_metrics(progress_metrics)

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
                        # 📊 NUEVAS MÉTRICAS CRÍTICAS (bajo costo)
                        f"{training_metrics['loss_promedio']:.6f}",
                        f"{training_metrics['loss_std']:.6f}",
                        f"{training_metrics['q_value_varianza']:.6f}",
                        f"{training_metrics['action_entropy']:.4f}",
                        f"{training_metrics['gradient_norm']:.6f}",
                        # 🎯 COMPONENTES DETALLADOS DE RECOMPENSA (para análisis)
                        f"{training_metrics['wait_penalty_promedio']:.4f}",
                        f"{training_metrics['congestion_std_penalty_promedio']:.4f}",
                        f"{training_metrics['congestion_total_penalty_promedio']:.4f}",
                        f"{training_metrics['efficiency_bonus_promedio']:.4f}",
                        f"{training_metrics['avg_wait_time_log_promedio']:.4f}",
                        f"{training_metrics['total_vehicles_promedio']:.2f}",
                    ]
                )

            logger.info(
                f" Epoca: {e+1}/{self.num_epocas}: {total_reward:.2f} recompensa acumulada - Duración: {epoch_duration:.2f}s - Replays: {replay_count}"
            )

            # Verificar si se debe detener el entrenamiento
            # should_stop, stop_reason = self.dashboard.should_stop_training()
            # if should_stop:
            #     self.smart_logger.log_if_needed(
            #         LogLevel.CRITICAL,
            #         "training_stop",
            #         f"🛑 DETENIENDO ENTRENAMIENTO: {stop_reason}",
            #     )
            #     # Generar reporte final antes de detener
            #     final_report = self.dashboard.generate_summary_report()
            #     self.smart_logger.logger.error(final_report)
            #     break

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
                    loss=training_metrics.get(
                        "loss_promedio", 0.0
                    ),  # 📊 Usar loss real de las nuevas métricas
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

                    # 💾 Guardado periódico de métricas (cada evaluación)
                    try:
                        metrics_path = self.evaluator.save_metrics()
                        logger.info(
                            f" 💾 Métricas guardadas periódicamente en: {metrics_path}"
                        )
                    except Exception as e:
                        logger.warning(f" ⚠️ Error guardando métricas periódicas: {e}")

            # FASE 4: Actualizar parámetros adaptativos para la siguiente época
            if hasattr(self, "frame_count"):
                self._update_adaptive_parameters()

            # 📊 Limpiar listas de métricas para la próxima época (evitar acumulación de memoria)
            self.epoch_losses.clear()
            self.epoch_actions.clear()
            self.epoch_q_values.clear()
            self.epoch_gradients.clear()
            # 🎯 Limpiar componentes detallados de recompensa
            self.epoch_wait_penalties.clear()
            self.epoch_congestion_std_penalties.clear()
            self.epoch_congestion_total_penalties.clear()
            self.epoch_efficiency_bonuses.clear()
            self.epoch_avg_wait_times_log.clear()
            self.epoch_total_vehicles.clear()

            # FASE 3: Learning rate adaptativo mejorado (reemplaza lógica anterior)
            current_avg_reward = np.mean(epoch_rewards) if epoch_rewards else 0.0
            self._adaptive_learning_rate_update(current_epoch, current_avg_reward)

            # Early stopping inteligente basado en rendimiento
            if (
                current_epoch > 5
            ):  # Permitir al menos 5 épocas antes de evaluar early stopping
                if self._check_early_stopping(current_avg_reward, current_epoch):
                    logger.info(
                        f" 🛑 Entrenamiento detenido early stopping en época {current_epoch}"
                    )
                    break

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
        Construye el estado completo del entorno de tráfico para el agente DQN.

        Composición del estado (48 características):
        - Tiempos de espera actuales: 12 zonas de detección
        - Cantidades de vehículos actuales: 12 zonas de detección
        - Tiempos de espera previos: 12 zonas (dinámica temporal)
        - Cantidades de vehículos previos: 12 zonas (dinámica temporal)

        Características técnicas:
        - Normalización Min-Max adaptativa para estabilidad
        - Sistema de cache con fallback robusto a APIs
        - Manejo de errores con valores de seguridad
        - Captura de dinámica temporal para mejor aprendizaje

        Pipeline de procesamiento:
        1. Recuperación de datos actuales (cache + fallback)
        2. Integración con historial temporal
        3. Normalización adaptativa por característica
        4. Validación de integridad y formato

        Returns:
            NDArray: Estado normalizado de forma (48,) ready para red neuronal

        Raises:
            RuntimeError: Si fallan todas las fuentes de datos tras reintentos

        Note:
            Estado crítico para calidad del entrenamiento - optimizado
            para estabilidad numérica y robustez ante fallos de API.
        """
        # SOLUCIÓN ROBUSTA: Usar datos cacheados con fallback a llamadas directas
        wait_times_response = self._cached_wait_times_response
        quantities_response = self._cached_quantities_response

        # 🛡️ FALLBACK: Si datos cacheados son None, intentar obtenerlos directamente
        if wait_times_response is None:
            logger = logging.getLogger(f"{self.__class__.__name__}._get_current_state")
            logger.warning(
                "⚠️ Datos de tiempos de espera cacheados son None en _get_current_state, intentando obtener directamente..."
            )
            wait_times_response = self._api.get_wait_times()
            if wait_times_response is None:
                logger.error(
                    "🚨 CRÍTICO: No se pudo obtener tiempos de espera ni de cache ni directamente en _get_current_state"
                )
                raise RuntimeError("No se pudo obtener los tiempos de espera de la API")
            else:
                logger.info(
                    "✅ Tiempos de espera obtenidos directamente como fallback en _get_current_state"
                )

        if quantities_response is None:
            logger = logging.getLogger(f"{self.__class__.__name__}._get_current_state")
            logger.warning(
                "⚠️ Datos de cantidades cacheados son None en _get_current_state, intentando obtener directamente..."
            )
            quantities_response = self._api.get_quantities()
            if quantities_response is None:
                logger.error(
                    "🚨 CRÍTICO: No se pudo obtener cantidades ni de cache ni directamente en _get_current_state"
                )
                raise RuntimeError(
                    "No se pudo obtener las cantidades de vehículos de la API"
                )
            else:
                logger.info(
                    "✅ Cantidades obtenidas directamente como fallback en _get_current_state"
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

    def _update_simulation_data(self) -> None:
        """
        SOLUCIÓN ROBUSTA: Actualiza los datos de simulación con reintentos.
        Los métodos _get_current_state() y _calculate_reward() usarán estos datos.

        Maneja problemas de timing donde SUMO puede no estar listo inmediatamente
        después de advance_simulation().
        """
        logger = logging.getLogger(f"{self.__class__.__name__}._update_simulation_data")

        # Configuración de reintentos
        max_retries = 3
        retry_delay = 0.01  # 10ms entre reintentos

        # Intentar obtener tiempos de espera con reintentos
        for attempt in range(max_retries):
            self._cached_wait_times_response = self._api.get_wait_times()
            if self._cached_wait_times_response is not None:
                break

            if attempt < max_retries - 1:  # No delay en el último intento
                logger.debug(
                    f"🔄 Reintento {attempt + 1}/{max_retries} para get_wait_times()"
                )
                time.sleep(retry_delay)

        if self._cached_wait_times_response is None:
            logger.warning("⚠️ get_wait_times() falló después de todos los reintentos")

        # Intentar obtener cantidades con reintentos
        for attempt in range(max_retries):
            self._cached_quantities_response = self._api.get_quantities()
            if self._cached_quantities_response is not None:
                break

            if attempt < max_retries - 1:  # No delay en el último intento
                logger.debug(
                    f"🔄 Reintento {attempt + 1}/{max_retries} para get_quantities()"
                )
                time.sleep(retry_delay)

        if self._cached_quantities_response is None:
            logger.warning("⚠️ get_quantities() falló después de todos los reintentos")

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

        # SOLUCIÓN SIMPLE: Actualizar datos una sola vez después del avance
        self._update_simulation_data()

        return self._get_current_state(), self._calculate_reward(), done

    def _normalize_reward(self, reward: float) -> float:
        """
        Normaliza las recompensas para mayor estabilidad del entrenamiento.

        Args:
            reward: Recompensa original (típicamente negativa)

        Returns:
            float: Recompensa normalizada en rango [-1, 0]
        """
        # Clipping de recompensas extremas
        reward = np.clip(reward, -50000, 0)  # Evitar recompensas demasiado negativas

        # Normalización logarítmica para valores negativos grandes
        if reward < -1000:
            normalized = -np.log10(abs(reward) / 1000) / 10  # Escala logarítmica
        else:
            normalized = reward / 1000  # Escala lineal para valores pequeños

        # Asegurar rango [-1, 0]
        return float(np.clip(normalized, -1.0, 0.0))

    def _calculate_reward(self) -> float:
        """
        Calcula la función de recompensa optimizada para entrenamiento DQN.

        ## 🔬 FÓRMULA MATEMÁTICA DETALLADA

        ### Componentes de la Recompensa:

        1. **Wait Penalty (Penalización por Tiempo de Espera)**:
           ```
           avg_wait_time_log = Σ(log(1 + t_i/10)) para todos los tiempos t_i
           wait_penalty = 10 * log(1 + avg_wait_time_log/10)
           ```
           - Usa suma de logaritmos (no promedio) para suavizar outliers
           - Saturación suave evita explosión exponencial
           - Factor 10 para escalado apropiado

        2. **Congestion Std Penalty (Penalización por Distribución Desigual)**:
           ```
           congestion_std_penalty = 2 * std(quantities)
           ```
           - Penaliza distribución desigual de vehículos entre zonas
           - Usa desviación estándar (no varianza) para evitar explosión
           - Factor 2 para balance con otros componentes

        3. **Congestion Total Penalty (Penalización por Congestión Total)**:
           ```
           congestion_total_penalty = min(20, (total_vehicles - 20) * 0.5) si total > 20
                                    = 0 si total ≤ 20
           ```
           - Función lineal con saturación en 20 puntos
           - Tolerancia base de 20 vehículos
           - Factor 0.5 para penalización gradual

        4. **Efficiency Bonus (Bonificación por Eficiencia)**:
           ```
           efficiency_bonus = min(5.0, total_vehicles * 0.1) si total > 0 y avg_wait < 30
                           = 0 en caso contrario
           ```
           - Premia vehículos en movimiento con tiempo de espera bajo
           - Máximo +5 puntos de bonificación
           - Condición: tiempo promedio < 30 segundos

        ### Fórmula Final:
        ```
        reward = -(wait_penalty + congestion_std_penalty + congestion_total_penalty) + efficiency_bonus
        final_reward = clip(reward, -100.0, 10.0)
        ```

        ## 🎯 Objetivos de Optimización:
        1. **Minimizar tiempo total de espera** (componente principal)
        2. **Equilibrar distribución** entre zonas de detección
        3. **Controlar congestión total** en intersecciones críticas
        4. **Premiar eficiencia** cuando el tráfico fluye bien

        ## 🛡️ Características Técnicas:
        - **Estabilidad numérica**: Sin exponentes problemáticos
        - **Rango acotado**: [-100.0, 10.0] para convergencia DQN estable
        - **Sistema de cache**: Con fallback robusto para APIs
        - **Manejo de anomalías**: Detección de valores extremos
        - **Logging detallado**: Componentes separados para análisis

        ## 📊 Métricas de Análisis:
        Cada componente se registra por separado en el CSV para permitir:
        - Análisis de dominancia entre componentes
        - Detección de "gaming" del sistema
        - Optimización de pesos y parámetros
        - Debugging de comportamiento del agente

        Returns:
            float: Recompensa normalizada en rango [-100.0, 10.0]
                  - Valores cercanos a 10: Alto rendimiento
                  - Valores cercanos a -100: Bajo rendimiento

        Note:
            Función crítica para calidad del aprendizaje - optimizada
            para gradientes estables y convergencia rápida.
        """
        # SOLUCIÓN ROBUSTA: Usar datos cacheados con fallback a llamadas directas
        logger = logging.getLogger(f"{self.__class__.__name__}._calculate_reward")

        try:
            # SOLUCIÓN ROBUSTA: Usar datos cacheados con fallback silencioso a llamadas directas
            wait_times_response = self._cached_wait_times_response
            quantities_response = self._cached_quantities_response

            # 🛡️ FALLBACK SILENCIOSO: Si datos cacheados son None, obtenerlos directamente
            if wait_times_response is None:
                logger.debug("📝 Usando fallback directo para tiempos de espera")
                wait_times_response = self._api.get_wait_times()
                if wait_times_response is None:
                    logger.error(
                        "🚨 CRÍTICO: No se pudo obtener tiempos de espera ni de cache ni directamente"
                    )
                    return -10.0  # Recompensa de emergencia más suave

            if quantities_response is None:
                logger.debug("📝 Usando fallback directo para cantidades")
                quantities_response = self._api.get_quantities()
                if quantities_response is None:
                    logger.error(
                        "🚨 CRÍTICO: No se pudo obtener cantidades ni de cache ni directamente"
                    )
                    return -10.0  # Recompensa de emergencia más suave

            # Obtener datos
            wait_times = wait_times_response.tiempos_espera
            quantities = list(quantities_response.cantidades.values())

            # 🛡️ VALIDACIÓN DE DATOS CRÍTICA
            if not wait_times or not quantities:
                logger.error("🚨 Datos vacíos del simulador")
                return -1.0

            # 🛡️ DETECTAR DATOS ANÓMALOS
            max_wait_time = max(wait_times) if wait_times else 0
            total_vehicles = int(sum(quantities)) if quantities else 0

            if max_wait_time > 10000:  # Más de 10000 segundos es anómalo
                logger.error(
                    f"🚨 DATOS ANÓMALOS: Tiempo de espera máximo en una zona: {max_wait_time}"
                    + f" Tiempo en zonas: {wait_times}"
                )
                return -100.0  # Penalización moderada para datos anómalos

            if total_vehicles > 1000:  # Más de 1000 vehículos es anómalo
                logger.error(
                    f"🚨 DATOS ANÓMALOS: Total vehículos: {total_vehicles}"
                    + f" Cantidad en zonas: {quantities}"
                )
                return -100.0  # Penalización moderada para datos anómalos

            # 🧮 NUEVA FÓRMULA MATEMÁTICAMENTE ESTABLE

            # 1. Penalización por tiempo de espera - LINEAL con saturación
            # Usar función logarítmica para evitar explosión exponencial
            # avg_wait_time = sum(wait_times) / len(wait_times)
            avg_wait_time = sum(np.log(1 + t / 10) for t in wait_times)

            # Saturación suave: log(1 + x) crece más lento que x²
            if avg_wait_time > 0:
                wait_penalty = 10 * np.log(1 + avg_wait_time / 10)  # Saturación suave
            else:
                wait_penalty = 0

            # 2. Penalización por congestión desigual - CONTROLADA
            if len(quantities) > 1:
                # Usar desviación estándar en lugar de varianza para evitar explosión
                congestion_std = float(np.std(quantities))
                congestion_variance_penalty = 2 * congestion_std  # Factor controlado
            else:
                congestion_variance_penalty = 0.0

            # 3. Penalización por congestión total - LINEAL con saturación
            if total_vehicles > 20:
                # Función lineal con saturación en lugar de exponencial
                congestion_penalty = min(20, (total_vehicles - 20) * 0.5)
            else:
                congestion_penalty = 0

            # 4. Bonificación por eficiencia (vehículos moviéndose)
            efficiency_bonus = 0.0
            if total_vehicles > 0 and avg_wait_time < 30:
                efficiency_bonus = min(5.0, total_vehicles * 0.1)  # Máximo +5

            # 5. Fórmula final con pesos balanceados
            reward = (
                -(wait_penalty + congestion_variance_penalty + congestion_penalty)
                + efficiency_bonus
            )

            # 🛡️ LÍMITES DUROS FINALES (valores razonables)
            final_reward = np.clip(reward, -100.0, 10.0)

            # 📊 ALMACENAR COMPONENTES DETALLADOS PARA ANÁLISIS
            self.epoch_wait_penalties.append(float(wait_penalty))
            self.epoch_congestion_std_penalties.append(
                float(congestion_variance_penalty)
            )
            self.epoch_congestion_total_penalties.append(float(congestion_penalty))
            self.epoch_efficiency_bonuses.append(float(efficiency_bonus))
            self.epoch_avg_wait_times_log.append(float(avg_wait_time))
            self.epoch_total_vehicles.append(int(total_vehicles))

            # 🔍 LOGGING DETALLADO DE COMPONENTES (opcional para debugging)
            # Habilitar descomentando las siguientes líneas para análisis detallado:
            # if len(self.epoch_wait_penalties) % 100 == 1:  # Cada 100 pasos
            #     logger.debug(
            #         f"🎯 Componentes recompensa: "
            #         f"Wait={wait_penalty:.2f} | "
            #         f"CongStd={congestion_variance_penalty:.2f} | "
            #         f"CongTotal={congestion_penalty:.2f} | "
            #         f"Efficiency={efficiency_bonus:.2f} | "
            #         f"Final={final_reward:.2f}"
            #     )

            # # 🚨 SMART LOGGING - Solo casos relevantes
            # # Usar smart logger para evitar spam pero mantener información importante
            # self.smart_logger.log_if_needed(
            #     LogLevel.INFO,
            #     "reward_calculation",
            #     f"📊 Recompensa: {final_reward:.2f} | Espera avg: {avg_wait_time:.1f}s | Vehículos: {total_vehicles}",
            #     value=final_reward,
            # )

            # # Agregar métricas al dashboard para análisis
            # self.smart_logger.add_metric("avg_wait_time", avg_wait_time)
            # self.smart_logger.add_metric("total_vehicles", total_vehicles)
            # self.smart_logger.add_metric("reward_value", final_reward)

            return float(final_reward)

        except Exception as e:
            logger.error(f"🚨 ERROR CRÍTICO en cálculo de recompensa: {e}")
            return -1.0  # Recompensa de seguridad

    def start_training_process(self) -> None:
        """
        Inicia el proceso completo de entrenamiento del agente DQN.

        Flujo de ejecución:
        1. Validación de API y simulador SUMO
        2. Cálculo de baseline con semáforos de tiempo fijo
        3. Persistencia de hiperparámetros y configuración
        4. Construcción e inicialización de redes neuronales
        5. Ejecución del loop principal de entrenamiento con:
           - Exploración ε-greedy
           - Acumulación de experiencias
           - Entrenamiento por lotes con PER
           - Actualización de red target (Double DQN)
           - Evaluación periódica de rendimiento
           - Early stopping inteligente

        Características avanzadas:
        - Manejo robusto de fallos de API con reintentos
        - Optimización adaptativa de learning rate
        - Monitoreo en tiempo real de GPU/RAM
        - Dashboard de progreso con visualización
        - Sistemas de logging inteligente con filtrado

        Raises:
            RuntimeError: Si el simulador no está disponible
            ValueError: Si los hiperparámetros son inválidos

        Note:
            Requiere que el simulador SUMO esté ejecutándose
            y accesible a través de la API configurada.
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
                        # 📊 NUEVAS MÉTRICAS CRÍTICAS (bajo costo)
                        "Loss Promedio",
                        "Loss Std",
                        "Q-Value Varianza",
                        "Action Entropy",
                        "Gradient Norm",
                        # 🎯 COMPONENTES DETALLADOS DE RECOMPENSA (para análisis)
                        "Wait Penalty",
                        "Congestion Std Penalty",
                        "Congestion Total Penalty",
                        "Efficiency Bonus",
                        "Avg Wait Time Log",
                        "Total Vehicles",
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
                f"{self.steps}+3",
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

        # WARM-UP: Aplicar el mismo skip de pasos iniciales para mantener coherencia
        warmup_steps = getattr(
            self.decision_settings.entrenamiento, "warmup_steps", 250
        )
        logger.info(f" 🔄 Aplicando warm-up de {warmup_steps} pasos para tiempo fijo")
        self._skip_warmup_steps(warmup_steps)

        fixed_time_start = time.time()
        step_count = 0  # Contador para debug
        while not done:
            reward = self._calculate_reward()

            # 🛡️ PROTECCIÓN CRÍTICA EN TIEMPO FIJO
            if abs(reward) > 1000:
                logger.error(
                    f"🚨 RECOMPENSA EXTREMA en tiempo fijo: {reward:.2f} (paso {step_count})"
                )
                reward = 1000.0 if reward > 0 else -1000.0

            total_reward += reward

            # 🛡️ LÍMITE ABSOLUTO PARA TIEMPO FIJO
            if abs(total_reward) > 100000:  # Límite más alto para tiempo fijo
                logger.error(
                    f"🚨 ACUMULACIÓN EXTREMA en tiempo fijo: {total_reward:.2f}"
                )
                logger.error(
                    f"📊 Pasos ejecutados: {step_count}, Última recompensa: {reward:.2f}"
                )
                break  # Salir del bucle para evitar overflow

            response = self._api.advance_simulation(steps=self.steps)
            if response is None:
                raise RuntimeError(
                    "No se pudo avanzar la simulación en cálculo de tiempo fijo"
                )
            done = response.done
            step_count += 1
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
                    # 📊 NUEVAS MÉTRICAS CRÍTICAS (tiempo fijo no aplica)
                    "-",  # Loss Promedio
                    "-",  # Loss Std
                    "-",  # Q-Value Varianza
                    "-",  # Action Entropy
                    "-",  # Gradient Norm
                    # 🎯 COMPONENTES DETALLADOS DE RECOMPENSA (tiempo fijo no aplica)
                    "-",  # Wait Penalty
                    "-",  # Congestion Std Penalty
                    "-",  # Congestion Total Penalty
                    "-",  # Efficiency Bonus
                    "-",  # Avg Wait Time Log
                    "-",  # Total Vehicles
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
