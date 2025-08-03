"""
Simplified DQN Trainer para Control de Semáforos - Configuración Base Segura

Este módulo implementa un entrenador DQN SIMPLIFICADO que elimina todas las
contradicciones y complejidad excesiva del entrenador original.

CONFIGURACIONES HARDCODED - BASE SEGURA

Objetivo: Tener un modelo base ESTABLE antes de añadir complejidad.
"""

import csv
import datetime
import importlib.util
import logging
import os
import random
import time
from collections import deque

import numpy as np
import tensorflow as tf
from numpy.typing import NDArray

from src.traffic_system.api_client.data_source_client import DecisionAPI
from src.traffic_system.core.api_models import (
    VehicleQuantitiesResponse,
    WaitTimesResponse,
)
from src.traffic_system.core.config_loader import load_app_settings

# GPU optimizations availability check
MIXED_PRECISION_AVAILABLE = (
    importlib.util.find_spec("tensorflow.keras.mixed_precision") is not None
)


class SimplifiedDQNConfig:
    """Configuraciones simplificadas hardcoded para entrenamiento estable."""

    # === HIPERPARÁMETROS BÁSICOS ===
    NUM_EPOCHS = 100  # Suficientes épocas para ver tendencias claras
    BATCH_SIZE = 256  # Tamaño de lote estándar
    STEPS = 10  # Pasos de simulación por acción
    MEMORY_SIZE = 50000  # Buffer de experiencias más grande para diversidad
    MIN_REPLAY_SIZE = 2000  # Mínimo para empezar entrenamiento (batch dinámico)

    # === OPTIMIZACIÓN Y LEARNING RATE ===
    LEARNING_RATE = 0.0001  # Punto de partida conservador y seguro
    # SIN learning_rate_decay - mantener LR fijo inicialmente
    # SIN adaptive_lr - una cosa a la vez

    # === EXPLORACIÓN - SOLO EPSILON GREEDY ===
    # USE_NOISY_NETWORKS = False  # ❌ DESACTIVADO: Evitar conflicto con epsilon
    EPSILON = 1.0  # 100% exploración inicial
    EPSILON_DECAY = 0.95  # Decay lento para explorar durante más tiempo
    EPSILON_MIN = 0.1  # exploración mínima, 0.1 = 10%

    # === DESCUENTO Y ARQUITECTURA ===
    GAMMA = 0.90  # Valor estándar que mira al futuro
    HIDDEN_LAYERS = [128, 64]  # Red simple pero más potente

    # === MEJORAS ALGORÍTMICAS DQN - SOLO LAS PROBADAS ===
    USE_DOUBLE_DQN = True  # ✅ Técnica probada y estable
    USE_DUELING_DQN = True  # ✅ Técnica probada y estable
    TARGET_UPDATE_FREQUENCY = 200  # Valor estándar y estable

    # === ESTABILIDAD DEL ENTRENAMIENTO ===
    WARMUP_STEPS = 1000  # Pasos de calentamiento para estabilizar la simulacion
    USE_GRADIENT_CLIPPING = True  # ✅ Previene gradient explosion
    GRADIENT_CLIP_NORM = 0.8  # Valor estándar
    USE_HUBER_LOSS = True  # ✅ Más robusto que MSE

    # === TÉCNICAS DESACTIVADAS TEMPORALMENTE ===
    # USE_PRIORITIZED_REPLAY = False  # ❌ Fuente de complejidad - activar después
    # USE_DROPOUT = False  # ❌ Red simple no necesita regularización
    # USE_BATCH_NORMALIZATION = False  # ❌ Innecesario para red pequeña
    USE_HE_INITIALIZATION = True  # ✅ Segura y estándar
    # USE_RESIDUAL_CONNECTIONS = False  # ❌ Innecesario para 2 capas
    # USE_LEAKY_RELU = False  # ❌ ReLU estándar es suficiente

    # === EVALUACIÓN ===
    ENABLE_EVALUATION = True  # ✅ Importante para monitoreo
    EVALUATION_EPISODES = 10  # Episodios de evaluación
    EVALUATION_FREQUENCY = 5  # Evaluar cada 5 épocas

    # === EARLY STOPPING ===
    PATIENCE = 10  # Épocas sin mejora antes de parar
    MIN_IMPROVEMENT = 0.01  # Mejora mínima requerida


class SimplifiedDQNTrainer:
    """
    Entrenador DQN Simplificado - Configuración Base Segura.

    Elimina todas las contradicciones y complejidad excesiva del entrenador original.
    Objetivo: modelo base ESTABLE antes de añadir optimizaciones.
    """

    def __init__(self) -> None:
        """Inicializa el entrenador con configuración simplificada."""
        # Configurar logging PRIMERO
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

        # Configuración base
        self.config = SimplifiedDQNConfig()
        self.settings = load_app_settings()

        # API y estado
        self._api = DecisionAPI(self.settings.base_url)
        self._setup_action_space()
        self.state_size = (
            48  # 12 tiempos + 12 cantidades + 12 tiempos_prev + 12 cantidades_prev
        )

        # Memoria de experiencias (solo deque estándar)
        self.memory: deque[tuple[NDArray, int, float, NDArray, bool]] = deque(
            maxlen=self.config.MEMORY_SIZE
        )

        # Variables de entrenamiento
        self.epsilon = self.config.EPSILON
        self.learning_rate = self.config.LEARNING_RATE
        self.target_update_counter = 0

        # Early stopping
        self.best_avg_reward = float("-inf")
        self.epochs_without_improvement = 0

        # Historial de estado para dinámica temporal
        self.state_history: list[NDArray] = []
        self.max_history_length = 2

        # Cache de datos API
        self._cached_wait_times_response: WaitTimesResponse | None = None
        self._cached_quantities_response: VehicleQuantitiesResponse | None = None

        # Variables para métricas avanzadas por época
        self.epoch_losses: list[float] = []
        self.epoch_gradient_norms: list[float] = []
        self.epoch_q_values: list[float] = []
        self.epoch_entropies: list[float] = []
        self.epoch_wait_penalties: list[float] = []
        self.epoch_congestion_penalties: list[float] = []
        self.epoch_efficiency_bonuses: list[float] = []
        self.initial_state_q_value = 0.0
        self.step_count = 0
        self.last_seed_info: dict | None = (
            None  # Información de semilla del último reset
        )
        self.initial_seed_config: dict | None = (
            None  # Configuración SUMO obtenida al inicio
        )

        # Configurar GPU/CPU
        self._configure_device()

        # Configurar rutas de guardado
        self._setup_save_path()

        # Crear modelos inmediatamente - no hay razón para esperar
        self.logger.info("🏗️ Construyendo modelos...")

        # Declarar tipos
        self.target_model: tf.keras.Model | None

        try:
            self.model: tf.keras.Model = self._build_model()
            self.logger.info("✅ Modelo principal creado exitosamente")

            if self.config.USE_DOUBLE_DQN:
                self.target_model = self._build_model()
                self.target_model.set_weights(self.model.get_weights())
                self.logger.info("🎯 Target model inicializado para Double DQN")
            else:
                self.target_model = None
                self.logger.info("📝 Double DQN desactivado - sin target model")

        except Exception as e:
            self.logger.error(f"❌ Error crítico creando modelos: {e}")
            self.logger.error("💡 Verifica:")
            self.logger.error("   • Configuración de GPU/CPU")
            self.logger.error("   • Memoria disponible")
            self.logger.error("   • Versión de TensorFlow")
            raise RuntimeError(f"No se pudieron crear los modelos DQN: {e}") from e

    def _configure_device(self) -> None:
        """Configura GPU o CPU para entrenamiento con optimizaciones básicas."""
        gpus = tf.config.experimental.list_physical_devices("GPU")

        if gpus:
            try:
                # Configurar crecimiento dinámico de memoria
                for gpu in gpus:
                    tf.config.experimental.set_memory_growth(gpu, True)

                self.device = "/GPU:0"
                self.use_gpu = True

                # Optimizaciones básicas para cualquier GPU
                self.use_mixed_precision = False
                self.use_xla = False

                # Intentar activar Mixed Precision solo si es explícitamente requerido
                # Desactivado por defecto para evitar problemas de compatibilidad
                if MIXED_PRECISION_AVAILABLE and False:  # Cambiar a True para activar
                    try:
                        policy = tf.keras.mixed_precision.Policy("mixed_float16")
                        tf.keras.mixed_precision.set_global_policy(policy)
                        self.use_mixed_precision = True
                        self.logger.info("✅ Mixed Precision activado")
                    except Exception as e:
                        # Revertir a política float32 si Mixed Precision falla
                        tf.keras.mixed_precision.set_global_policy("float32")
                        self.use_mixed_precision = False
                        self.logger.warning(
                            f"⚠️ Mixed Precision falló, revirtiendo a float32: {e}"
                        )
                else:
                    self.use_mixed_precision = False
                    self.logger.info("🎯 Mixed Precision desactivado por defecto")

                # Intentar activar XLA (universal para GPUs modernas)
                try:
                    tf.config.optimizer.set_jit(True)
                    self.use_xla = True
                    self.logger.info("✅ XLA Compilation activado")
                except Exception as e:
                    self.logger.warning(f"⚠️ XLA no disponible: {e}")

                self.logger.info(f"🚀 GPU configurada: {len(gpus)} dispositivo(s)")

            except RuntimeError as e:
                self.logger.warning(f"⚠️ Error configurando GPU: {e}")
                self.device = "/CPU:0"
                self.use_gpu = False
                self.use_mixed_precision = False
                self.use_xla = False
        else:
            self.device = "/CPU:0"
            self.use_gpu = False
            self.use_mixed_precision = False
            self.use_xla = False
            self.logger.info("🖥️ Usando CPU para entrenamiento")

    def _setup_action_space(self) -> None:
        """Establece el espacio de acciones de los semáforos."""
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

        self.logger.info(
            f"🎯 Espacio de acciones configurado: {len(self._action_space)} acciones"
        )

    def _setup_save_path(self) -> None:
        """Configura la ruta donde se guardarán los resultados."""
        timestamp = time.strftime("%Y-%m-%d_%H-%M")
        self._save_path = os.path.join(
            "results/training/", f"SimplifiedDQN_{timestamp}"
        )
        os.makedirs(self._save_path, exist_ok=True)
        self.logger.info(f"💾 Ruta de guardado: {self._save_path}")

    def _build_model(self) -> tf.keras.Model:
        """
        Construye el modelo DQN simplificado con optimizaciones GPU.

        Solo usa técnicas probadas:
        - Double DQN
        - Dueling DQN
        - He initialization
        - Gradient clipping
        - Huber loss
        + Optimizaciones GPU: Mixed Precision, XLA compilation
        """
        with tf.device(self.device):
            if self.config.USE_DUELING_DQN:
                model = self._build_dueling_model()
                self.logger.info("🔀 Usando arquitectura Dueling DQN")
            else:
                model = self._build_standard_model()
                self.logger.info("📊 Usando arquitectura DQN estándar")

            # Optimizador configurado para GPU estándar (sin Mixed Precision por defecto)
            optimizer_kwargs = {
                "learning_rate": self.config.LEARNING_RATE,
                "beta_1": 0.9,
                "beta_2": 0.999,
                "epsilon": 1e-7,
            }

            # Gradient clipping
            if self.config.USE_GRADIENT_CLIPPING:
                optimizer_kwargs["clipnorm"] = self.config.GRADIENT_CLIP_NORM

            optimizer = tf.keras.optimizers.Adam(**optimizer_kwargs)

            # Solo envolver con LossScaleOptimizer si Mixed Precision está realmente activo
            if self.use_mixed_precision:
                optimizer = tf.keras.mixed_precision.LossScaleOptimizer(optimizer)
                self.logger.info("🎯 Optimizador configurado para Mixed Precision")

            # Loss function con compatibilidad Mixed Precision
            if self.config.USE_HUBER_LOSS:
                loss_function = tf.keras.losses.Huber(delta=1.0)
            else:
                loss_function = "mse"

            model.compile(
                loss=loss_function,
                optimizer=optimizer,
                metrics=["mae"],
                # Nota: XLA ya está configurado globalmente, no necesario aquí
            )

        self.logger.info(f"🎯 Modelo creado en: {self.device}")
        return model

    def _build_standard_model(self) -> tf.keras.Model:
        """Construye modelo DQN estándar simplificado."""
        model = tf.keras.Sequential()

        # Inicialización He para ReLU
        initializer = (
            "he_normal" if self.config.USE_HE_INITIALIZATION else "random_normal"
        )

        # Primera capa
        model.add(
            tf.keras.layers.Dense(
                self.config.HIDDEN_LAYERS[0],
                input_dim=self.state_size,
                activation="relu",
                kernel_initializer=initializer,
            )
        )

        # Capas ocultas
        for units in self.config.HIDDEN_LAYERS[1:]:
            model.add(
                tf.keras.layers.Dense(
                    units, activation="relu", kernel_initializer=initializer
                )
            )

        # Capa de salida
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
        Construye modelo Dueling DQN simplificado.
        ```
                                        +--> [Dense 256] --> [Dense 1 (V)] --+
                                        |                                    |
            Input --> [Dense 256] --(bifurcación)                      [Combinación] --> Q-Values
                                        |                                    |
                                        +--> [Dense 256] --> [Dense 16 (A)]--+
        ```
        """
        # Input layer
        inputs = tf.keras.layers.Input(shape=(self.state_size,))

        # Inicialización He
        initializer = (
            "he_normal" if self.config.USE_HE_INITIALIZATION else "random_normal"
        )

        # Capas compartidas
        shared = inputs
        for units in self.config.HIDDEN_LAYERS[:-1]:  # Todas menos la última
            shared = tf.keras.layers.Dense(
                units, activation="relu", kernel_initializer=initializer
            )(shared)

        # Value stream V(s)
        value_stream = tf.keras.layers.Dense(
            self.config.HIDDEN_LAYERS[-1],
            activation="relu",
            kernel_initializer=initializer,
            name="value_hidden",
        )(shared)
        value = tf.keras.layers.Dense(1, name="value")(value_stream)

        # Advantage stream A(s,a)
        advantage_stream = tf.keras.layers.Dense(
            self.config.HIDDEN_LAYERS[-1],
            activation="relu",
            kernel_initializer=initializer,
            name="advantage_hidden",
        )(shared)
        advantage = tf.keras.layers.Dense(len(self._action_space), name="advantage")(
            advantage_stream
        )

        # Combinar: Q(s,a) = V(s) + A(s,a) - mean(A(s,a))
        advantage_reshaped = tf.keras.layers.Reshape((-1, 1), name="advantage_reshape")(
            advantage
        )
        advantage_mean = tf.keras.layers.GlobalAveragePooling1D(name="advantage_mean")(
            advantage_reshaped
        )

        q_values = tf.keras.layers.Add(name="q_values")(
            [
                value,
                tf.keras.layers.Subtract(name="advantage_centered")(
                    [advantage, advantage_mean]
                ),
            ]
        )

        model = tf.keras.Model(
            inputs=inputs, outputs=q_values, name="Dueling_DQN_Simplified"
        )
        return model

    def _select_action(self, state: NDArray) -> tuple[int, float]:
        """
        Selecciona acción usando SOLO epsilon-greedy.

        SIN noisy networks - evita conflicto de exploración.
        """
        if np.random.rand() <= self.epsilon:
            # Exploración
            action = random.randrange(len(self._action_space))
            max_q_value = 0.0
        else:
            # Explotación
            state_batch = np.expand_dims(state, axis=0)
            q_values = self.model.predict(state_batch, verbose=0)
            action = int(np.argmax(q_values[0]))
            max_q_value = float(np.max(q_values[0]))

        return action, max_q_value

    def _calculate_action_entropy(self, q_values: NDArray) -> float:
        """
        Calcula la entropía de la política basada en Q-values.

        Una entropía alta indica más exploración/incertidumbre.
        Una entropía baja indica una política más determinista.
        """
        try:
            # Convertir Q-values a probabilidades usando softmax
            q_values_stable = q_values - np.max(q_values)  # Para estabilidad numérica
            exp_q = np.exp(q_values_stable)
            probabilities = exp_q / np.sum(exp_q)

            # Calcular entropía de Shannon: H = -Σ(p * log(p))
            # Agregar pequeño epsilon para evitar log(0)
            epsilon = 1e-8
            probabilities = np.clip(probabilities, epsilon, 1.0)
            entropy = -np.sum(probabilities * np.log(probabilities))

            return float(entropy)
        except Exception as e:
            self.logger.warning(f"⚠️ Error calculando entropía: {e}")
            return 0.0

    def _get_initial_state_q_value(self, state: NDArray) -> float:
        """
        Obtiene el Q-value máximo para el estado inicial de la época.

        Útil para comparar las expectativas del agente con el rendimiento real.
        """
        try:
            state_batch = np.expand_dims(state, axis=0)
            q_values = self.model.predict(state_batch, verbose=0)
            return float(np.max(q_values[0]))
        except Exception as e:
            self.logger.warning(f"⚠️ Error obteniendo Q-value inicial: {e}")
            return 0.0

    def _remember(
        self,
        state: NDArray,
        action: int,
        reward: float,
        next_state: NDArray,
        done: bool,
    ) -> None:
        """Almacena experiencia en memoria estándar (sin PER)."""
        self.memory.append((state, action, reward, next_state, done))

    # def _replay(self):
    #     """
    #     Entrenamiento con memoria estándar (sin PER).

    #     Usa batch dinámico: empieza entrenando temprano con lotes pequeños.
    #     Captura métricas adicionales: loss y gradient norm.
    #     """
    #     if len(self.memory) < self.config.MIN_REPLAY_SIZE:
    #         return

    #     # Batch size dinámico
    #     batch_size = min(self.config.BATCH_SIZE, len(self.memory))
    #     minibatch = random.sample(self.memory, batch_size)

    #     # Preparar datos
    #     states = np.array([experience[0] for experience in minibatch])
    #     actions = np.array([experience[1] for experience in minibatch])
    #     rewards = np.array([experience[2] for experience in minibatch])
    #     next_states = np.array([experience[3] for experience in minibatch])
    #     dones = np.array([experience[4] for experience in minibatch])

    #     # Predicciones actuales
    #     current_q_values = self.model.predict(states, verbose=0)

    #     if self.config.USE_DOUBLE_DQN and self.target_model is not None:
    #         # Double DQN: usar online network para seleccionar, target para evaluar
    #         next_q_values_online = self.model.predict(next_states, verbose=0)
    #         next_q_values_target = self.target_model.predict(next_states, verbose=0)

    #         # Seleccionar mejores acciones con online network
    #         best_actions = np.argmax(next_q_values_online, axis=1)

    #         # Evaluar con target network
    #         max_next_q = next_q_values_target[np.arange(batch_size), best_actions]
    #     else:
    #         # DQN estándar
    #         next_q_values = self.model.predict(next_states, verbose=0)
    #         max_next_q = np.max(next_q_values, axis=1)

    #     # Calcular targets
    #     targets = current_q_values.copy()
    #     for i in range(batch_size):
    #         if dones[i]:
    #             targets[i][actions[i]] = rewards[i]
    #         else:
    #             targets[i][actions[i]] = rewards[i] + self.config.GAMMA * max_next_q[i]

    #     # Entrenar y capturar métricas
    #     with tf.GradientTape() as tape:
    #         # Forward pass
    #         predicted_q_values = self.model(states, training=True)

    #         # Calcular loss
    #         if self.config.USE_HUBER_LOSS:
    #             loss_fn = tf.keras.losses.Huber(delta=1.0)
    #         else:
    #             loss_fn = tf.keras.losses.MeanSquaredError()

    #         loss = loss_fn(targets, predicted_q_values)

    #     # Calcular gradientes
    #     gradients = tape.gradient(loss, self.model.trainable_variables)

    #     # Calcular norma del gradiente
    #     gradient_norm = self._calculate_gradient_norm(gradients)

    #     # Aplicar gradientes
    #     self.model.optimizer.apply_gradients(
    #         zip(gradients, self.model.trainable_variables, strict=True)
    #     )

    #     # Almacenar métricas
    #     self.epoch_losses.append(float(loss))
    #     self.epoch_gradient_norms.append(gradient_norm)

    #     # Almacenar Q-values promedio del batch
    #     avg_q_value = float(np.mean(predicted_q_values))
    #     self.epoch_q_values.append(avg_q_value)

    #     # Actualizar target model si es necesario
    #     if self.config.USE_DOUBLE_DQN and self.target_model is not None:
    #         self.target_update_counter += 1
    #         if self.target_update_counter >= self.config.TARGET_UPDATE_FREQUENCY:
    #             self._update_target_model()
    #             self.target_update_counter = 0

    # def _replay(self):
    #     if len(self.memory) < self.config.MIN_REPLAY_SIZE:
    #         return

    #     batch_size = min(self.config.BATCH_SIZE, len(self.memory))
    #     minibatch = random.sample(self.memory, batch_size)

    #     states = np.array([experience[0] for experience in minibatch])
    #     actions = np.array([experience[1] for experience in minibatch])
    #     rewards = np.array([experience[2] for experience in minibatch])
    #     next_states = np.array([experience[3] for experience in minibatch])
    #     dones = np.array([experience[4] for experience in minibatch])

    #     # Predicción de Q-values futuros (usando Double DQN)
    #     next_q_values_online = self.model.predict(next_states, verbose=0)
    #     next_q_values_target = self.target_model.predict(next_states, verbose=0)
    #     best_actions = np.argmax(next_q_values_online, axis=1)
    #     max_next_q = next_q_values_target[np.arange(batch_size), best_actions]

    #     # Calcular los targets
    #     targets = self.model.predict(
    #         states, verbose=0
    #     )  # Usamos las predicciones actuales como base
    #     for i in range(batch_size):
    #         if dones[i]:
    #             targets[i][actions[i]] = rewards[i]
    #         else:
    #             targets[i][actions[i]] = rewards[i] + self.config.GAMMA * max_next_q[i]

    #     # *** LA LÍNEA CLAVE ***
    #     # Keras se encarga de todo: forward, loss, backward, apply gradients
    #     history = self.model.train_on_batch(states, targets, return_dict=True)

    #     # Almacenar métricas desde el historial devuelto
    #     self.epoch_losses.append(history["loss"])
    #     # Nota: para obtener Gradient Norm, tendrías que quedarte con GradientTape,
    #     # pero primero asegúrate de que el aprendizaje funciona. La loss es más importante.
    #     # Puedes añadir un cálculo de gradientes opcional si lo necesitas.
    #     avg_q_value = float(np.mean(targets))  # O de las predicciones
    #     self.epoch_q_values.append(avg_q_value)

    #     # Actualizar target model
    #     self.target_update_counter += 1
    #     if self.target_update_counter >= self.config.TARGET_UPDATE_FREQUENCY:
    #         self._update_target_model()
    #         self.target_update_counter = 0

    def _replay(self) -> None:
        """Entrenamiento simplificado con optimizaciones básicas GPU/CPU."""
        if len(self.memory) < self.config.MIN_REPLAY_SIZE:
            return

        batch_size = min(self.config.BATCH_SIZE, len(self.memory))
        minibatch = random.sample(self.memory, batch_size)

        # Convertir a tensores TensorFlow para eficiencia
        # Asegurar dtype consistente para Mixed Precision
        dtype = tf.float16 if self.use_mixed_precision else tf.float32

        states = tf.convert_to_tensor(
            np.array([exp[0] for exp in minibatch]), dtype=dtype
        )
        actions = tf.convert_to_tensor(
            np.array([exp[1] for exp in minibatch]), dtype=tf.int32
        )
        rewards = tf.convert_to_tensor(
            np.array([exp[2] for exp in minibatch]), dtype=dtype
        )
        next_states = tf.convert_to_tensor(
            np.array([exp[3] for exp in minibatch]), dtype=dtype
        )
        dones = tf.convert_to_tensor(
            np.array([exp[4] for exp in minibatch]), dtype=dtype
        )

        # Calcular targets con Double DQN
        batch_indices = tf.range(batch_size, dtype=tf.int32)

        if self.config.USE_DOUBLE_DQN and self.target_model is not None:
            next_q_values_online = self.model(next_states, training=False)
            next_q_values_target = self.target_model(next_states, training=False)
            best_actions = tf.argmax(next_q_values_online, axis=1, output_type=tf.int32)

            action_indices = tf.stack([batch_indices, best_actions], axis=1)
            max_next_q = tf.gather_nd(next_q_values_target, action_indices)
        else:
            # Fallback a DQN estándar si no hay target model
            next_q_values = self.model(next_states, training=False)
            max_next_q = tf.reduce_max(next_q_values, axis=1)

        targets_q = rewards + tf.cast(self.config.GAMMA, dtype) * max_next_q * (
            tf.cast(1.0, dtype) - dones
        )

        # Entrenamiento con GradientTape
        with tf.GradientTape() as tape:
            all_current_q_values = self.model(states, training=True)
            action_indices_taken = tf.stack([batch_indices, actions], axis=1)
            predicted_q_values = tf.gather_nd(
                all_current_q_values, action_indices_taken
            )

            # Asegurar que todos los tensores estén en el mismo dtype
            targets_q = tf.cast(targets_q, predicted_q_values.dtype)

            # Loss con compatibilidad de tipos
            loss_fn = tf.keras.losses.Huber(delta=1.0)
            loss = loss_fn(targets_q, predicted_q_values)

            # Escalar loss solo si Mixed Precision está activo y optimizer lo soporta
            if (
                self.use_mixed_precision
                and self.model.optimizer is not None
                and hasattr(self.model.optimizer, "get_scaled_loss")
            ):
                scaled_loss = self.model.optimizer.get_scaled_loss(loss)
            else:
                scaled_loss = loss

        # Calcular gradientes
        if (
            self.use_mixed_precision
            and self.model.optimizer is not None
            and hasattr(self.model.optimizer, "get_unscaled_gradients")
        ):
            scaled_gradients = tape.gradient(
                scaled_loss, self.model.trainable_variables
            )
            gradients = self.model.optimizer.get_unscaled_gradients(scaled_gradients)
        else:
            gradients = tape.gradient(scaled_loss, self.model.trainable_variables)

        # Gradient clipping
        if self.config.USE_GRADIENT_CLIPPING:
            gradients, _ = tf.clip_by_global_norm(
                gradients, self.config.GRADIENT_CLIP_NORM
            )

        # Aplicar gradientes
        if self.model.optimizer is not None:
            self.model.optimizer.apply_gradients(
                zip(gradients, self.model.trainable_variables, strict=True)
            )
        else:
            self.logger.warning("⚠️ Optimizer es None, no se pueden aplicar gradientes")

        # Almacenar métricas
        gradient_norm = tf.linalg.global_norm(gradients)
        self.epoch_losses.append(float(loss))
        self.epoch_gradient_norms.append(float(gradient_norm))
        self.epoch_q_values.append(float(tf.reduce_mean(predicted_q_values)))

        # Actualizar target model
        self.target_update_counter += 1
        if self.target_update_counter >= self.config.TARGET_UPDATE_FREQUENCY:
            self._update_target_model()
            self.target_update_counter = 0

    def _calculate_gradient_norm(self, gradients: list) -> float:
        """
        Calcula la norma L2 de los gradientes.

        Métrica crítica para detectar gradient explosion o vanishing.
        """
        try:
            total_norm = 0.0
            for grad in gradients:
                if grad is not None:
                    grad_norm = tf.norm(grad)
                    total_norm += grad_norm**2

            total_norm = tf.sqrt(total_norm)
            return float(total_norm)
        except Exception as e:
            self.logger.warning(f"⚠️ Error calculando norma del gradiente: {e}")
            return 0.0

    def _update_target_model(self) -> None:
        """Actualiza la red target copiando pesos de la red principal."""
        if self.target_model is not None:
            self.target_model.set_weights(self.model.get_weights())
            self.logger.info("🎯 Red target actualizada")

    def _update_epsilon(self) -> None:
        """Actualiza epsilon para exploración decreciente."""
        if self.epsilon > self.config.EPSILON_MIN:
            self.epsilon *= self.config.EPSILON_DECAY

    def _get_current_state(self) -> NDArray:
        """
        Obtiene el estado actual del entorno.

        Estado de 48 características:
        - 12 tiempos de espera actuales
        - 12 cantidades de vehículos actuales
        - 12 tiempos de espera previos
        - 12 cantidades de vehículos previos
        """
        # Obtener datos con reintentos
        wait_times_response = self._cached_wait_times_response
        quantities_response = self._cached_quantities_response

        if wait_times_response is None:
            wait_times_response = self._api.get_wait_times()
            if wait_times_response is None:
                raise RuntimeError("No se pudo obtener tiempos de espera")

        if quantities_response is None:
            quantities_response = self._api.get_quantities()
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

        return self._normalize_state(complete_state)

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
        """Actualiza los datos de simulación con reintentos."""
        max_retries = 3
        retry_delay = 0.01

        # Intentar obtener tiempos de espera
        for attempt in range(max_retries):
            self._cached_wait_times_response = self._api.get_wait_times()
            if self._cached_wait_times_response is not None:
                break
            if attempt < max_retries - 1:
                time.sleep(retry_delay)

        # Intentar obtener cantidades
        for attempt in range(max_retries):
            self._cached_quantities_response = self._api.get_quantities()
            if self._cached_quantities_response is not None:
                break
            if attempt < max_retries - 1:
                time.sleep(retry_delay)

    def _execute_action_and_advance(
        self, action_index: int
    ) -> tuple[NDArray, float, bool, float, float, float, dict | None]:
        """Ejecuta acción y avanza simulación."""
        # Ejecutar acción
        action_phases_str = self._action_space[action_index]
        action_phases_list = action_phases_str.split("-")
        self._api.set_traffic_light_states(states=action_phases_list)

        # Avanzar simulación
        response = self._api.advance_simulation(steps=self.config.STEPS)
        if response is None:
            raise RuntimeError("No se pudo avanzar la simulación")

        done = response.done
        seed_info = response.info if hasattr(response, "info") else None

        # Actualizar datos
        self._update_simulation_data()

        next_state = self._get_current_state()

        reward, wait_penalty, congestion_penalty, efficiency_bonus = (
            self._calculate_reward_components()
        )

        return (
            next_state,
            reward,
            done,
            wait_penalty,
            congestion_penalty,
            efficiency_bonus,
            seed_info,
        )

    def _calculate_reward(self) -> float:
        """
        Calcula recompensa simplificada y estable.

        Fórmula simplificada:
        reward = -(avg_wait_time + congestion_penalty) + efficiency_bonus
        """
        reward_total, wait_penalty, congestion_penalty, efficiency_bonus = (
            self._calculate_reward_components()
        )
        return reward_total

    def _calculate_reward_components(self) -> tuple[float, float, float, float]:
        """
        Calcula recompensa y sus componentes separados.

        Returns:
            Tupla con (reward_total, wait_penalty, congestion_penalty, efficiency_bonus)
        """
        try:
            # Usar datos cacheados
            wait_times_response = self._cached_wait_times_response
            quantities_response = self._cached_quantities_response

            if wait_times_response is None:
                wait_times_response = self._api.get_wait_times()
            if quantities_response is None:
                quantities_response = self._api.get_quantities()

            if wait_times_response is None or quantities_response is None:
                self.logger.error(
                    "⚠️ No se pudieron obtener datos de espera o cantidades"
                )
                return -10.0, -10.0, 0.0, 0.0

            # Obtener datos
            wait_times = wait_times_response.tiempos_espera
            quantities = list(quantities_response.cantidades.values())

            if not wait_times or not quantities:
                self.logger.error("⚠️ Datos de espera o cantidades vacíos")
                return -10.0, -10.0, 0.0, 0.0

            # Validación de datos anómalos
            max_wait_time = max(wait_times)
            total_vehicles = sum(quantities)

            if max_wait_time > 5000 or total_vehicles > 150:
                self.logger.warning(
                    f"⚠️ Datos anómalos detectados: max_wait_time={max_wait_time}, total_vehicles={total_vehicles}"
                )
                self.logger.warning(f"⚠️ Tiempos de espera: {wait_times}")
                self.logger.warning(f"⚠️ Cantidad de vehículos: {quantities}")

                # Limpiar caché para forzar nuevos datos en la próxima consulta
                self._cached_wait_times_response = None
                self._cached_quantities_response = None

                return -100.0, -100.0, 0.0, 0.0  # Penalización por datos anómalos

            # Calcular componentes separados
            avg_wait_time = sum(wait_times) / len(wait_times)
            wait_penalty = -(avg_wait_time * 0.2)

            # Penalización por congestión total
            congestion_penalty = (
                -max(0, (total_vehicles - 20) * 0.5) if total_vehicles > 20 else 0.0
            )

            # Bonificación por eficiencia
            efficiency_bonus = (
                min(5.0, total_vehicles * 0.1)
                if total_vehicles > 0 and avg_wait_time < 50
                else 0.0
            )

            # Recompensa total
            reward_total = wait_penalty + congestion_penalty + efficiency_bonus

            # Clipping para estabilidad
            reward_total = float(np.clip(reward_total, -120.0, 10.0))

            return reward_total, wait_penalty, congestion_penalty, efficiency_bonus

        except Exception as e:
            self.logger.error(f"Error calculando recompensa: {e}")
            return -1.0, -1.0, 0.0, 0.0

    def _check_early_stopping(self, current_avg_reward: float, epoch: int) -> bool:
        """Verifica early stopping."""
        improved = current_avg_reward > (
            self.best_avg_reward + self.config.MIN_IMPROVEMENT
        )

        if improved:
            self.best_avg_reward = current_avg_reward
            self.epochs_without_improvement = 0
            return False
        else:
            self.epochs_without_improvement += 1

        if self.epochs_without_improvement >= self.config.PATIENCE:
            self.logger.info(f"🛑 Early stopping activado en época {epoch}")
            return True

        return False

    def _skip_warmup_steps(self, warmup_steps: int) -> int:
        """Avanza simulación durante warmup."""
        self.logger.info(f"🔄 Iniciando warm-up: {warmup_steps} pasos")
        response = self._api.advance_simulation(steps=warmup_steps)
        if response is None:
            self.logger.warning("⚠️ No se pudo avanzar simulación durante warm-up")
            return 0
        self.logger.info(f"✅ Warm-up completado: {warmup_steps} pasos")
        return warmup_steps

    def _reset_epoch_metrics(self) -> None:
        """Resetea las métricas de época al inicio de cada nueva época."""
        self.epoch_losses.clear()
        self.epoch_gradient_norms.clear()
        self.epoch_q_values.clear()
        self.epoch_entropies.clear()
        self.epoch_wait_penalties.clear()
        self.epoch_congestion_penalties.clear()
        self.epoch_efficiency_bonuses.clear()
        self.initial_state_q_value = 0.0
        self.step_count = 0

    def _train_agent(self) -> None:
        """Loop principal de entrenamiento."""
        self.logger.info("🚀 Iniciando entrenamiento del agente")

        for epoch in range(self.config.NUM_EPOCHS):
            self.logger.info(f"🏁 Época {epoch + 1}/{self.config.NUM_EPOCHS}")

            # Resetear métricas de época
            self._reset_epoch_metrics()

            # Warm-up inicial
            if epoch == 0:
                self._skip_warmup_steps(self.config.WARMUP_STEPS)

            # Variables de época
            epoch_rewards = []
            state = self._get_current_state()
            done = False
            total_reward = 0.0
            replay_count = 0

            # Capturar Q-value del primer estado
            self.initial_state_q_value = self._get_initial_state_q_value(state)

            start_time = time.time()

            # Loop de pasos en la época
            while not done:
                # Seleccionar y ejecutar acción
                action, max_q_value = self._select_action(state)

                # Calcular entropía de la acción
                state_batch = np.expand_dims(state, axis=0)
                q_values = self.model.predict(state_batch, verbose=0)
                entropy = self._calculate_action_entropy(q_values[0])
                self.epoch_entropies.append(entropy)

                (
                    next_state,
                    reward,
                    done,
                    wait_penalty,
                    congestion_penalty,
                    efficiency_bonus,
                    seed_info,
                ) = self._execute_action_and_advance(action)

                self.epoch_wait_penalties.append(wait_penalty)
                self.epoch_congestion_penalties.append(congestion_penalty)
                self.epoch_efficiency_bonuses.append(efficiency_bonus)

                # Capturar información de semilla cuando done=True
                if done and seed_info:
                    self.last_seed_info = seed_info

                # Almacenar experiencia
                self._remember(state, action, reward, next_state, done)

                # Acumular métricas
                epoch_rewards.append(reward)
                total_reward += reward
                state = next_state
                self.step_count += 1

                # Entrenar si hay suficiente memoria
                if len(self.memory) >= self.config.MIN_REPLAY_SIZE:
                    self._replay()
                    replay_count += 1

            # Finalizar época
            epoch_duration = time.time() - start_time
            avg_reward = np.mean(epoch_rewards) if epoch_rewards else 0.0

            # Calcular métricas promedio de la época
            avg_loss = np.mean(self.epoch_losses) if self.epoch_losses else 0.0
            avg_gradient_norm = (
                np.mean(self.epoch_gradient_norms) if self.epoch_gradient_norms else 0.0
            )
            avg_q_value = np.mean(self.epoch_q_values) if self.epoch_q_values else 0.0
            avg_entropy = np.mean(self.epoch_entropies) if self.epoch_entropies else 0.0
            avg_wait_penalty = (
                np.mean(self.epoch_wait_penalties) if self.epoch_wait_penalties else 0.0
            )
            avg_congestion_penalty = (
                np.mean(self.epoch_congestion_penalties)
                if self.epoch_congestion_penalties
                else 0.0
            )
            avg_efficiency_bonus = (
                np.mean(self.epoch_efficiency_bonuses)
                if self.epoch_efficiency_bonuses
                else 0.0
            )

            # Actualizar epsilon
            self._update_epsilon()

            # Guardar modelo
            self.model.save(os.path.join(self._save_path, f"epoch_{epoch + 1}.h5"))
            self.model.save(os.path.join(self._save_path, f"epoch_{epoch + 1}.keras"))

            # Log de progreso
            self.logger.info(
                f"📊 Época {epoch + 1}: "
                f"Recompensa total: {total_reward:.2f}, "
                f"Promedio: {avg_reward:.2f}, "
                f"Loss: {avg_loss:.4f}, "
                f"Q-value: {avg_q_value:.2f}, "
                f"Epsilon: {self.epsilon:.4f}, "
                f"Pasos: {self.step_count}, "
                f"Duración: {epoch_duration:.1f}s"
            )

            # Guardar métricas en CSV
            self._save_epoch_metrics(
                epoch + 1,
                total_reward,
                avg_reward,
                epoch_duration,
                replay_count,
                self.step_count,
                avg_loss,
                avg_q_value,
                self.initial_state_q_value,
                avg_gradient_norm,
                avg_entropy,
                avg_wait_penalty,
                avg_congestion_penalty,
                avg_efficiency_bonus,
            )

            # Early stopping
            if epoch > 5:  # Permitir al menos 5 épocas
                if self._check_early_stopping(avg_reward, epoch):
                    break

        self.logger.info("✅ Entrenamiento completado")

    def _save_epoch_metrics(
        self,
        epoch: int,
        total_reward: float,
        avg_reward: float,
        duration: float,
        replay_count: int,
        step_count: int,
        avg_loss: float,
        avg_q_value: float,
        initial_q_value: float,
        avg_gradient_norm: float,
        avg_entropy: float,
        avg_wait_penalty: float,
        avg_congestion_penalty: float,
        avg_efficiency_bonus: float,
    ) -> None:
        """Guarda métricas avanzadas de la época en CSV."""
        csv_path = os.path.join(self._save_path, "training_metrics.csv")

        # Crear archivo con headers si no existe
        if not os.path.exists(csv_path):
            with open(csv_path, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(
                    [
                        "Epoca",
                        "Duracion_seg",
                        "Recompensa_Acumulada",
                        "Recompensa_Promedio",
                        "Num_Pasos",
                        "Loss_Promedio",
                        "Q_Value_Promedio",
                        "Q_Value_Inicial",
                        "Gradiente_Norma_Prom",
                        "Entropia_Prom",
                        "Epsilon_Final",
                        "LR_Final",
                        "Recompensa_Penalidad_Espera",
                        "Recompensa_Penalidad_Congestion",
                        "Recompensa_Bonus_Eficiencia",
                        "Replay_Count",
                        "Memory_Size",
                        "SUMO_Current_Real_Seed",
                    ]
                )

        # Añadir métricas de la época
        with open(csv_path, "a", newline="") as f:
            writer = csv.writer(f)

            # Obtener semilla de la información capturada
            current_seed = None
            if self.last_seed_info:
                # Priorizar current_seed (semilla real) sobre current_persistent_seed
                if "current_seed" in self.last_seed_info:
                    current_seed = self.last_seed_info["current_seed"]
                elif "current_persistent_seed" in self.last_seed_info:
                    current_seed = self.last_seed_info["current_persistent_seed"]

            writer.writerow(
                [
                    epoch,
                    f"{duration:.2f}",
                    f"{total_reward:.2f}",
                    f"{avg_reward:.2f}",
                    step_count,
                    f"{avg_loss:.6f}",
                    f"{avg_q_value:.2f}",
                    f"{initial_q_value:.2f}",
                    f"{avg_gradient_norm:.6f}",
                    f"{avg_entropy:.6f}",
                    f"{self.epsilon:.4f}",
                    f"{self.learning_rate:.6f}",
                    f"{avg_wait_penalty:.2f}",
                    f"{avg_congestion_penalty:.2f}",
                    f"{avg_efficiency_bonus:.2f}",
                    replay_count,
                    len(self.memory),
                    current_seed,
                ]
            )

    def start_training_process(self) -> None:
        """Inicia el proceso completo de entrenamiento simplificado con optimizaciones GPU."""
        self.logger.info("🔥 Iniciando DQN Trainer Simplificado")

        while not self._api.is_simulation_running():
            self.logger.info("⏳ Esperando simulador...")
            time.sleep(1)

        self.logger.info("✅ Simulador listo")

        # Obtener configuración SUMO al inicio y guardar hiperparámetros
        self._get_sumo_config_and_save_hyperparameters()

        self._calculate_baseline_performance()

        self._train_agent()

        self.logger.info("🎉 Proceso completo terminado")

    def _get_sumo_config_and_save_hyperparameters(self) -> None:
        """
        Obtiene la configuración SUMO por API al inicio del entrenamiento
        y guarda todos los hiperparámetros incluyendo la configuración SUMO.
        """
        # Obtener configuración SUMO por API
        try:
            # Hacer una llamada con 1 step para obtener la configuración SUMO via info
            response = self._api.advance_simulation(steps=1)
            if response and hasattr(response, "info") and response.info:
                self.initial_seed_config = response.info
                self.logger.info(
                    f"✅ Configuración SUMO obtenida: {self.initial_seed_config}"
                )
            else:
                self.logger.warning("⚠️ No se pudo obtener configuración SUMO inicial")
                self.initial_seed_config = None
        except Exception as e:
            self.logger.warning(f"⚠️ Error obteniendo configuración SUMO: {e}")
            self.initial_seed_config = None

        # Guardar hiperparámetros incluyendo configuración SUMO
        self._save_hyperparameters()

    def _save_hyperparameters(self) -> None:
        """Guarda TODOS los hiperparámetros de SimplifiedDQNConfig."""
        config_path = os.path.join(self._save_path, "hyperparameters.csv")

        with open(config_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(
                ["Parameter", "Value", "Type", "Category", "Description", "Status"]
            )

            # === HIPERPARÁMETROS BÁSICOS ===
            writer.writerow(
                [
                    "NUM_EPOCHS",
                    self.config.NUM_EPOCHS,
                    "int",
                    "Basic",
                    "Suficientes épocas para ver tendencias claras",
                    "Active",
                ]
            )
            writer.writerow(
                [
                    "BATCH_SIZE",
                    self.config.BATCH_SIZE,
                    "int",
                    "Basic",
                    "Tamaño de lote estándar",
                    "Active",
                ]
            )
            writer.writerow(
                [
                    "STEPS",
                    self.config.STEPS,
                    "int",
                    "Basic",
                    "Pasos de simulación por acción",
                    "Active",
                ]
            )
            writer.writerow(
                [
                    "MEMORY_SIZE",
                    self.config.MEMORY_SIZE,
                    "int",
                    "Basic",
                    "Buffer de experiencias más grande para diversidad",
                    "Active",
                ]
            )
            writer.writerow(
                [
                    "MIN_REPLAY_SIZE",
                    self.config.MIN_REPLAY_SIZE,
                    "int",
                    "Basic",
                    "Mínimo para empezar entrenamiento (batch dinámico)",
                    "Active",
                ]
            )

            # === OPTIMIZACIÓN Y LEARNING RATE ===
            writer.writerow(
                [
                    "LEARNING_RATE",
                    self.config.LEARNING_RATE,
                    "float",
                    "Optimization",
                    "Punto de partida conservador y seguro",
                    "Active",
                ]
            )

            # === EXPLORACIÓN - SOLO EPSILON GREEDY ===
            writer.writerow(
                [
                    "EPSILON",
                    self.config.EPSILON,
                    "float",
                    "Exploration",
                    "100% exploración inicial",
                    "Active",
                ]
            )
            writer.writerow(
                [
                    "EPSILON_DECAY",
                    self.config.EPSILON_DECAY,
                    "float",
                    "Exploration",
                    "Decay lento para explorar durante más tiempo",
                    "Active",
                ]
            )
            writer.writerow(
                [
                    "EPSILON_MIN",
                    self.config.EPSILON_MIN,
                    "float",
                    "Exploration",
                    "20% exploración mínima",
                    "Active",
                ]
            )

            # === DESCUENTO Y ARQUITECTURA ===
            writer.writerow(
                [
                    "GAMMA",
                    self.config.GAMMA,
                    "float",
                    "Architecture",
                    "Valor estándar que mira al futuro",
                    "Active",
                ]
            )
            writer.writerow(
                [
                    "HIDDEN_LAYERS",
                    str(self.config.HIDDEN_LAYERS),
                    "list",
                    "Architecture",
                    "Red simple pero más potente",
                    "Active",
                ]
            )

            # === MEJORAS ALGORÍTMICAS DQN - SOLO LAS PROBADAS ===
            writer.writerow(
                [
                    "USE_DOUBLE_DQN",
                    self.config.USE_DOUBLE_DQN,
                    "bool",
                    "Algorithmic",
                    "Técnica probada y estable",
                    "Active",
                ]
            )
            writer.writerow(
                [
                    "USE_DUELING_DQN",
                    self.config.USE_DUELING_DQN,
                    "bool",
                    "Algorithmic",
                    "Técnica probada y estable",
                    "Active",
                ]
            )
            writer.writerow(
                [
                    "TARGET_UPDATE_FREQUENCY",
                    self.config.TARGET_UPDATE_FREQUENCY,
                    "int",
                    "Algorithmic",
                    "Valor estándar y estable",
                    "Active",
                ]
            )

            # === ESTABILIDAD DEL ENTRENAMIENTO ===
            writer.writerow(
                [
                    "WARMUP_STEPS",
                    self.config.WARMUP_STEPS,
                    "int",
                    "Stability",
                    "Pasos de calentamiento para estabilizar la simulacion",
                    "Active",
                ]
            )
            writer.writerow(
                [
                    "USE_GRADIENT_CLIPPING",
                    self.config.USE_GRADIENT_CLIPPING,
                    "bool",
                    "Stability",
                    "Previene gradient explosion",
                    "Active",
                ]
            )
            writer.writerow(
                [
                    "GRADIENT_CLIP_NORM",
                    self.config.GRADIENT_CLIP_NORM,
                    "float",
                    "Stability",
                    "Valor estándar",
                    "Active",
                ]
            )
            writer.writerow(
                [
                    "USE_HUBER_LOSS",
                    self.config.USE_HUBER_LOSS,
                    "bool",
                    "Stability",
                    "Más robusto que MSE",
                    "Active",
                ]
            )

            # === TÉCNICAS ACTIVADAS ===
            writer.writerow(
                [
                    "USE_HE_INITIALIZATION",
                    self.config.USE_HE_INITIALIZATION,
                    "bool",
                    "Techniques",
                    "Segura y estándar",
                    "Active",
                ]
            )

            # === EVALUACIÓN ===
            writer.writerow(
                [
                    "ENABLE_EVALUATION",
                    self.config.ENABLE_EVALUATION,
                    "bool",
                    "Evaluation",
                    "Importante para monitoreo",
                    "Active",
                ]
            )
            writer.writerow(
                [
                    "EVALUATION_EPISODES",
                    self.config.EVALUATION_EPISODES,
                    "int",
                    "Evaluation",
                    "Episodios de evaluación",
                    "Active",
                ]
            )
            writer.writerow(
                [
                    "EVALUATION_FREQUENCY",
                    self.config.EVALUATION_FREQUENCY,
                    "int",
                    "Evaluation",
                    "Evaluar cada 5 épocas",
                    "Active",
                ]
            )

            # === EARLY STOPPING ===
            writer.writerow(
                [
                    "PATIENCE",
                    self.config.PATIENCE,
                    "int",
                    "Early_Stopping",
                    "Épocas sin mejora antes de parar",
                    "Active",
                ]
            )
            writer.writerow(
                [
                    "MIN_IMPROVEMENT",
                    self.config.MIN_IMPROVEMENT,
                    "float",
                    "Early_Stopping",
                    "Mejora mínima requerida",
                    "Active",
                ]
            )

            # === TÉCNICAS DESACTIVADAS TEMPORALMENTE ===
            writer.writerow(
                [
                    "USE_NOISY_NETWORKS",
                    False,
                    "bool",
                    "Exploration",
                    "Evitar conflicto con epsilon",
                    "Disabled",
                ]
            )
            writer.writerow(
                [
                    "learning_rate_decay",
                    False,
                    "bool",
                    "Optimization",
                    "Mantener LR fijo inicialmente",
                    "Disabled",
                ]
            )
            writer.writerow(
                [
                    "adaptive_lr",
                    False,
                    "bool",
                    "Optimization",
                    "Una cosa a la vez",
                    "Disabled",
                ]
            )
            writer.writerow(
                [
                    "USE_PRIORITIZED_REPLAY",
                    False,
                    "bool",
                    "Algorithmic",
                    "Fuente de complejidad - activar después",
                    "Disabled",
                ]
            )
            writer.writerow(
                [
                    "USE_DROPOUT",
                    False,
                    "bool",
                    "Regularization",
                    "Red simple no necesita regularización",
                    "Disabled",
                ]
            )
            writer.writerow(
                [
                    "USE_BATCH_NORMALIZATION",
                    False,
                    "bool",
                    "Regularization",
                    "Innecesario para red pequeña",
                    "Disabled",
                ]
            )
            writer.writerow(
                [
                    "USE_RESIDUAL_CONNECTIONS",
                    False,
                    "bool",
                    "Architecture",
                    "Innecesario para 2 capas",
                    "Disabled",
                ]
            )
            writer.writerow(
                [
                    "USE_LEAKY_RELU",
                    False,
                    "bool",
                    "Architecture",
                    "ReLU estándar es suficiente",
                    "Disabled",
                ]
            )

            # === INFORMACIÓN DEL ENTORNO DE EJECUCIÓN ===
            writer.writerow(
                [
                    "DEVICE",
                    self.device,
                    "str",
                    "Runtime",
                    "Dispositivo de ejecución",
                    "Info",
                ]
            )
            writer.writerow(
                ["USE_GPU", self.use_gpu, "bool", "Runtime", "Uso de GPU", "Info"]
            )
            writer.writerow(
                [
                    "MIXED_PRECISION",
                    self.use_mixed_precision,
                    "bool",
                    "Runtime",
                    "Precisión mixta",
                    "Info",
                ]
            )
            writer.writerow(
                [
                    "XLA_COMPILATION",
                    self.use_xla,
                    "bool",
                    "Runtime",
                    "Compilación XLA",
                    "Info",
                ]
            )

            # === TIMESTAMP ===
            writer.writerow(
                [
                    "TIMESTAMP",
                    datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "str",
                    "Metadata",
                    "Fecha y hora de ejecución",
                    "Info",
                ]
            )

            # === CONFIGURACIÓN SUMO (obtenida por API) ===
            if hasattr(self, "initial_seed_config") and self.initial_seed_config:
                writer.writerow(
                    [
                        "SUMO_USE_RANDOM_SEED",
                        self.initial_seed_config.get("use_random_seed", "Unknown"),
                        "bool",
                        "SUMO_Config",
                        "Usar semilla aleatoria vs determinística",
                        "Active",
                    ]
                )
                writer.writerow(
                    [
                        "SUMO_FIXED_SEED",
                        self.initial_seed_config.get("fixed_seed", "Unknown"),
                        "int|null",
                        "SUMO_Config",
                        "Semilla específica para reproducibilidad",
                        "Active",
                    ]
                )
                writer.writerow(
                    [
                        "SUMO_PERSIST_RANDOM_SEED",
                        self.initial_seed_config.get("persist_random_seed", "Unknown"),
                        "bool",
                        "SUMO_Config",
                        "Reutilizar semilla entre reinicios",
                        "Active",
                    ]
                )

    def _calculate_baseline_performance(self) -> None:
        """Calcula rendimiento baseline con semáforos de tiempo fijo."""
        self.logger.info("📏 Calculando baseline con tiempo fijo...")

        # Warm-up para tiempo fijo
        self._skip_warmup_steps(self.config.WARMUP_STEPS)

        total_reward = 0.0
        done = False
        step_count = 0
        start_time = time.time()
        baseline_seed_info = None

        while not done:
            reward = self._calculate_reward()
            total_reward += reward

            response = self._api.advance_simulation(steps=self.config.STEPS)
            if response is None:
                break
            done = response.done

            if done and hasattr(response, "info") and response.info:
                baseline_seed_info = response.info

            step_count += 1

            # Límite de seguridad
            if step_count > 2000:  # Aprox 5 horas de simulación
                break

        duration = time.time() - start_time

        # Extraer la seed para el CSV
        current_seed = None
        if baseline_seed_info:
            # Priorizar current_seed (semilla real) sobre current_persistent_seed
            if "current_seed" in baseline_seed_info:
                current_seed = baseline_seed_info["current_seed"]
            elif "current_persistent_seed" in baseline_seed_info:
                current_seed = baseline_seed_info["current_persistent_seed"]

        self.logger.info(
            f"📏 Baseline - Recompensa total: {total_reward:.2f}, Duración: {duration:.1f}s, Seed: {current_seed}"
        )

        # Guardar baseline con información de seed
        baseline_path = os.path.join(self._save_path, "baseline.csv")
        with open(baseline_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(
                [
                    "Type",
                    "Total_Reward",
                    "Duration_s",
                    "Steps",
                    "SUMO_Current_Real_Seed",
                ]
            )
            writer.writerow(
                [
                    "Fixed_Time",
                    f"{total_reward:.2f}",
                    f"{duration:.2f}",
                    step_count,
                    current_seed,
                ]
            )
