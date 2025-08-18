"""
🧪 Fase 4: Sistema de Evaluación y Métricas DQN

Este módulo implementa un sistema robusto para evaluar el rendimiento del agente DQN,
incluyendo métricas estadísticas, comparaciones con baseline y análisis de progreso.
"""

import json
import logging
import os
import time
from collections import deque
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

from src.traffic_system.core.config_models import DecisionSettings

logger = logging.getLogger(__name__)


class DQNEvaluator:
    """Sistema de evaluación para el agente DQN."""

    def __init__(
        self,
        config: DecisionSettings,
        results_dir: str = "results/evaluation",
        model_name: str = "DQN",
    ):
        """
        Inicializar el evaluador.

        Args:
            config: Configuración del sistema
            results_dir: Directorio para guardar resultados
            model_name: Nombre del modelo para identificación
        """
        self.config = config
        self.results_dir = results_dir
        self.model_name = model_name
        self.timestamp = time.strftime("%Y-%m-%d_%H-%M")

        # Crear directorios
        os.makedirs(results_dir, exist_ok=True)
        self.session_dir = os.path.join(results_dir, f"{model_name}_{self.timestamp}")
        os.makedirs(self.session_dir, exist_ok=True)

        # Métricas de entrenamiento
        self.training_metrics: dict[str, list[float]] = {
            "episodes": [],
            "rewards": [],
            "losses": [],
            "epsilons": [],
            "learning_rates": [],
            "avg_q_values": [],
            "episode_lengths": [],
            "waiting_times": [],
            "throughput": [],
        }

        # Métricas de evaluación
        self.evaluation_metrics: dict[str, list[float]] = {
            "evaluation_episodes": [],
            "evaluation_rewards": [],
            "evaluation_waiting_times": [],
            "evaluation_throughput": [],
            "statistical_significance": [],
        }

        # Ventanas deslizantes para suavizado
        self.window_size = getattr(config.entrenamiento, "metrics_window_size", 100)
        self.reward_window: deque[float] = deque(maxlen=self.window_size)
        self.loss_window: deque[float] = deque(maxlen=self.window_size)

        # Baseline para comparación
        self.baseline_metrics: dict | None = None

        logger.info(f"🧪 DQNEvaluator inicializado para {model_name}")
        logger.info(f"📁 Directorio de sesión: {self.session_dir}")

    def record_training_step(
        self,
        episode: int,
        reward: float,
        loss: float,
        epsilon: float,
        learning_rate: float,
        avg_q_value: float,
        episode_length: int,
        waiting_time: float,
        throughput: float,
    ) -> None:
        """Registrar métricas de un paso de entrenamiento."""
        self.training_metrics["episodes"].append(episode)
        self.training_metrics["rewards"].append(reward)
        self.training_metrics["losses"].append(loss)
        self.training_metrics["epsilons"].append(epsilon)
        self.training_metrics["learning_rates"].append(learning_rate)
        self.training_metrics["avg_q_values"].append(avg_q_value)
        self.training_metrics["episode_lengths"].append(episode_length)
        self.training_metrics["waiting_times"].append(waiting_time)
        self.training_metrics["throughput"].append(throughput)

        # Actualizar ventanas deslizantes
        self.reward_window.append(reward)
        self.loss_window.append(loss)

    def evaluate_agent(
        self, agent: Any, env: Any, num_episodes: int | None = None
    ) -> dict[str, float]:
        """
        Evaluar el agente en un conjunto de episodios sin exploración.

        Args:
            agent: Agente DQN a evaluar
            env: Entorno de evaluación
            num_episodes: Número de episodios de evaluación

        Returns:
            Diccionario con métricas de evaluación
        """
        if num_episodes is None:
            num_episodes = getattr(self.config.entrenamiento, "evaluation_episodes", 10)

        logger.info(f"🧪 Iniciando evaluación con {num_episodes} episodios")

        evaluation_rewards = []
        evaluation_waiting_times = []
        evaluation_throughput = []
        evaluation_episode_lengths = []

        # Guardar epsilon original y desactivar exploración
        original_epsilon = agent.epsilon
        agent.epsilon = 0.0

        try:
            for episode in range(num_episodes):
                state = env.reset()
                total_reward = 0
                episode_length = 0
                episode_waiting_time = 0
                episode_throughput = 0

                done = False
                while not done:
                    action = agent.act(state, training=False)
                    next_state, reward, done, info = env.step(action)

                    total_reward += reward
                    episode_length += 1

                    # Extraer métricas del entorno
                    if "waiting_time" in info:
                        episode_waiting_time += info["waiting_time"]
                    if "throughput" in info:
                        episode_throughput += info["throughput"]

                    state = next_state

                evaluation_rewards.append(total_reward)
                evaluation_waiting_times.append(episode_waiting_time)
                evaluation_throughput.append(episode_throughput)
                evaluation_episode_lengths.append(episode_length)

                logger.debug(
                    f"🧪 Episodio eval {episode + 1}: Reward={total_reward:.2f}, "
                    f"Length={episode_length}"
                )

        finally:
            # Restaurar epsilon original
            agent.epsilon = original_epsilon

        # Calcular estadísticas
        metrics = {
            "mean_reward": float(np.mean(evaluation_rewards)),
            "std_reward": float(np.std(evaluation_rewards)),
            "mean_waiting_time": float(np.mean(evaluation_waiting_times)),
            "std_waiting_time": float(np.std(evaluation_waiting_times)),
            "mean_throughput": float(np.mean(evaluation_throughput)),
            "std_throughput": float(np.std(evaluation_throughput)),
            "mean_episode_length": float(np.mean(evaluation_episode_lengths)),
            "total_episodes": num_episodes,
        }

        # Registrar métricas de evaluación
        current_episode = (
            len(self.training_metrics["episodes"])
            if self.training_metrics["episodes"]
            else 0
        )
        self.evaluation_metrics["evaluation_episodes"].append(current_episode)
        self.evaluation_metrics["evaluation_rewards"].append(
            float(metrics["mean_reward"])
        )
        self.evaluation_metrics["evaluation_waiting_times"].append(
            float(metrics["mean_waiting_time"])
        )
        self.evaluation_metrics["evaluation_throughput"].append(
            float(metrics["mean_throughput"])
        )

        logger.info("✅ Evaluación completada:")
        logger.info(
            f"   📊 Reward promedio: {metrics['mean_reward']:.2f} ± {metrics['std_reward']:.2f}"
        )
        logger.info(
            f"   ⏱️  Tiempo espera: {metrics['mean_waiting_time']:.2f} ± {metrics['std_waiting_time']:.2f}"
        )
        logger.info(
            f"   🚗 Throughput: {metrics['mean_throughput']:.2f} ± {metrics['std_throughput']:.2f}"
        )

        return metrics

    def compare_with_baseline(
        self, current_metrics: dict[str, float]
    ) -> dict[str, Any]:
        """
        Comparar métricas actuales con baseline.

        Args:
            current_metrics: Métricas actuales del modelo

        Returns:
            Diccionario con resultados de la comparación
        """
        if self.baseline_metrics is None:
            logger.warning("⚠️ No hay métricas baseline para comparar")
            return {"has_baseline": False}

        comparison = {"has_baseline": True}

        # Comparar reward
        reward_improvement = (
            (current_metrics["mean_reward"] - self.baseline_metrics["mean_reward"])
            / abs(self.baseline_metrics["mean_reward"])
            * 100
        )

        # Comparar tiempo de espera (menor es mejor)
        waiting_improvement = (
            (
                self.baseline_metrics["mean_waiting_time"]
                - current_metrics["mean_waiting_time"]
            )
            / self.baseline_metrics["mean_waiting_time"]
            * 100
        )

        # Comparar throughput (mayor es mejor)
        throughput_improvement = (
            (
                current_metrics["mean_throughput"]
                - self.baseline_metrics["mean_throughput"]
            )
            / self.baseline_metrics["mean_throughput"]
            * 100
        )

        comparison.update(
            {
                "reward_improvement_pct": reward_improvement,
                "waiting_improvement_pct": waiting_improvement,
                "throughput_improvement_pct": throughput_improvement,
                "is_better_reward": reward_improvement > 0,
                "is_better_waiting": waiting_improvement > 0,
                "is_better_throughput": throughput_improvement > 0,
            }
        )

        logger.info("📈 Comparación con baseline:")
        logger.info(f"   🎯 Reward: {reward_improvement:+.1f}%")
        logger.info(f"   ⏱️  Espera: {waiting_improvement:+.1f}%")
        logger.info(f"   🚗 Throughput: {throughput_improvement:+.1f}%")

        return comparison

    def statistical_significance_test(
        self, current_rewards: list[float], baseline_rewards: list[float]
    ) -> dict[str, Any]:
        """
        Realizar test de significancia estadística.

        Args:
            current_rewards: Rewards del modelo actual
            baseline_rewards: Rewards del modelo baseline

        Returns:
            Resultados del test estadístico
        """
        if not getattr(self.config.entrenamiento, "statistical_tests", True):
            return {"tests_enabled": False}

        # Test t de Student para muestras independientes
        t_stat, t_p_value = stats.ttest_ind(current_rewards, baseline_rewards)

        # Test de Mann-Whitney U (no paramétrico)
        u_stat, u_p_value = stats.mannwhitneyu(
            current_rewards, baseline_rewards, alternative="two-sided"
        )

        # Efecto size (Cohen's d)
        pooled_std = np.sqrt(
            (
                (len(current_rewards) - 1) * np.var(current_rewards, ddof=1)
                + (len(baseline_rewards) - 1) * np.var(baseline_rewards, ddof=1)
            )
            / (len(current_rewards) + len(baseline_rewards) - 2)
        )
        cohens_d = (np.mean(current_rewards) - np.mean(baseline_rewards)) / pooled_std

        results = {
            "tests_enabled": True,
            "t_test": {"statistic": t_stat, "p_value": t_p_value},
            "mann_whitney": {"statistic": u_stat, "p_value": u_p_value},
            "cohens_d": cohens_d,
            "is_significant_t": t_p_value < 0.05,
            "is_significant_mw": u_p_value < 0.05,
            "effect_size": self._interpret_cohens_d(cohens_d),
        }

        # Registrar significancia
        self.evaluation_metrics["statistical_significance"].append(
            results["is_significant_t"]
        )

        logger.info("📊 Tests estadísticos:")
        logger.info(
            f"   📈 t-test: p={t_p_value:.4f} ({'significativo' if results['is_significant_t'] else 'no significativo'})"
        )
        logger.info(
            f"   📈 Mann-Whitney: p={u_p_value:.4f} ({'significativo' if results['is_significant_mw'] else 'no significativo'})"
        )
        logger.info(f"   📏 Effect size: {results['effect_size']} (d={cohens_d:.3f})")

        return results

    def _interpret_cohens_d(self, d: float) -> str:
        """Interpretar el tamaño del efecto Cohen's d."""
        abs_d = abs(d)
        if abs_d < 0.2:
            return "pequeño"
        elif abs_d < 0.5:
            return "mediano"
        elif abs_d < 0.8:
            return "grande"
        else:
            return "muy grande"

    def generate_plots(self) -> None:
        """Generar gráficos de progreso y evaluación."""
        if not getattr(self.config.entrenamiento, "generate_plots", True):
            return

        logger.info("📊 Generando gráficos de evaluación...")

        # Configurar estilo de matplotlib
        plt.style.use("ggplot")
        fig, axes = plt.subplots(2, 3, figsize=(18, 12))
        fig.suptitle(f"Evaluación DQN - {self.model_name}", fontsize=16)

        # 1. Rewards de entrenamiento
        if self.training_metrics["rewards"]:
            axes[0, 0].plot(
                self.training_metrics["episodes"],
                self.training_metrics["rewards"],
                alpha=0.6,
            )
            if len(self.training_metrics["rewards"]) > self.window_size:
                smoothed_rewards = self._moving_average(
                    self.training_metrics["rewards"], self.window_size
                )
                axes[0, 0].plot(
                    self.training_metrics["episodes"][-len(smoothed_rewards) :],
                    smoothed_rewards,
                    linewidth=2,
                    color="red",
                )
            axes[0, 0].set_title("Rewards de Entrenamiento")
            axes[0, 0].set_xlabel("Episodio")
            axes[0, 0].set_ylabel("Reward")
            axes[0, 0].grid(True)

        # 2. Pérdidas de entrenamiento
        if self.training_metrics["losses"]:
            axes[0, 1].plot(
                self.training_metrics["episodes"],
                self.training_metrics["losses"],
                alpha=0.6,
            )
            if len(self.training_metrics["losses"]) > self.window_size:
                smoothed_losses = self._moving_average(
                    self.training_metrics["losses"], self.window_size
                )
                axes[0, 1].plot(
                    self.training_metrics["episodes"][-len(smoothed_losses) :],
                    smoothed_losses,
                    linewidth=2,
                    color="red",
                )
            axes[0, 1].set_title("Pérdidas de Entrenamiento")
            axes[0, 1].set_xlabel("Episodio")
            axes[0, 1].set_ylabel("Loss")
            axes[0, 1].grid(True)

        # 3. Epsilon decay
        if self.training_metrics["epsilons"]:
            axes[0, 2].plot(
                self.training_metrics["episodes"], self.training_metrics["epsilons"]
            )
            axes[0, 2].set_title("Decay de Epsilon")
            axes[0, 2].set_xlabel("Episodio")
            axes[0, 2].set_ylabel("Epsilon")
            axes[0, 2].grid(True)

        # 4. Rewards de evaluación
        if self.evaluation_metrics["evaluation_rewards"]:
            axes[1, 0].plot(
                self.evaluation_metrics["evaluation_episodes"],
                self.evaluation_metrics["evaluation_rewards"],
                marker="o",
                linewidth=2,
            )
            axes[1, 0].set_title("Rewards de Evaluación")
            axes[1, 0].set_xlabel("Episodio de Entrenamiento")
            axes[1, 0].set_ylabel("Reward Promedio")
            axes[1, 0].grid(True)

        # 5. Tiempos de espera
        if self.training_metrics["waiting_times"]:
            axes[1, 1].plot(
                self.training_metrics["episodes"],
                self.training_metrics["waiting_times"],
                alpha=0.6,
            )
            if len(self.training_metrics["waiting_times"]) > self.window_size:
                smoothed_waiting = self._moving_average(
                    self.training_metrics["waiting_times"], self.window_size
                )
                axes[1, 1].plot(
                    self.training_metrics["episodes"][-len(smoothed_waiting) :],
                    smoothed_waiting,
                    linewidth=2,
                    color="red",
                )
            axes[1, 1].set_title("Tiempos de Espera")
            axes[1, 1].set_xlabel("Episodio")
            axes[1, 1].set_ylabel("Tiempo (s)")
            axes[1, 1].grid(True)

        # 6. Throughput
        if self.training_metrics["throughput"]:
            axes[1, 2].plot(
                self.training_metrics["episodes"],
                self.training_metrics["throughput"],
                alpha=0.6,
            )
            if len(self.training_metrics["throughput"]) > self.window_size:
                smoothed_throughput = self._moving_average(
                    self.training_metrics["throughput"], self.window_size
                )
                axes[1, 2].plot(
                    self.training_metrics["episodes"][-len(smoothed_throughput) :],
                    smoothed_throughput,
                    linewidth=2,
                    color="red",
                )
            axes[1, 2].set_title("Throughput")
            axes[1, 2].set_xlabel("Episodio")
            axes[1, 2].set_ylabel("Vehículos/min")
            axes[1, 2].grid(True)

        plt.tight_layout()
        plot_path = os.path.join(self.session_dir, "training_evaluation_plots.png")
        plt.savefig(plot_path, dpi=300, bbox_inches="tight")
        plt.close()

        logger.info(f"📊 Gráficos guardados en: {plot_path}")

    def _moving_average(self, data: list[float], window: int) -> list[float]:
        """Calcular promedio móvil."""
        return [
            float(np.mean(data[i : i + window])) for i in range(len(data) - window + 1)
        ]

    def save_metrics(self) -> str:
        """
        Guardar todas las métricas en archivos.

        Returns:
            Ruta del archivo principal de métricas
        """
        if not getattr(self.config.entrenamiento, "save_evaluation_data", True):
            return ""

        # Crear resumen completo
        summary = {
            "model_name": self.model_name,
            "timestamp": self.timestamp,
            "config": {
                "window_size": self.window_size,
                "evaluation_episodes": getattr(
                    self.config.entrenamiento, "evaluation_episodes", 10
                ),
                "evaluation_frequency": getattr(
                    self.config.entrenamiento, "evaluation_frequency", 5
                ),
            },
            "training_metrics": self._convert_to_serializable(self.training_metrics),
            "evaluation_metrics": self._convert_to_serializable(
                self.evaluation_metrics
            ),
            "baseline_metrics": (
                self._convert_to_serializable(self.baseline_metrics)
                if self.baseline_metrics
                else None
            ),
        }

        # Guardar como JSON
        json_path = os.path.join(self.session_dir, "metrics_summary.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)

        # Guardar como CSV para análisis
        if self.training_metrics["episodes"]:
            df_training = pd.DataFrame(self.training_metrics)
            csv_path = os.path.join(self.session_dir, "training_metrics.csv")
            df_training.to_csv(csv_path, index=False)

        if self.evaluation_metrics["evaluation_episodes"]:
            df_evaluation = pd.DataFrame(self.evaluation_metrics)
            eval_csv_path = os.path.join(self.session_dir, "evaluation_metrics.csv")
            df_evaluation.to_csv(eval_csv_path, index=False)

        logger.info(f"💾 Métricas guardadas en: {self.session_dir}")
        return json_path

    def load_baseline(self, baseline_path: str) -> bool:
        """
        Cargar métricas baseline desde archivo.

        Args:
            baseline_path: Ruta al archivo de métricas baseline

        Returns:
            True si se cargó exitosamente
        """
        try:
            with open(baseline_path, encoding="utf-8") as f:
                baseline_data = json.load(f)

            self.baseline_metrics = baseline_data.get("baseline_metrics", baseline_data)
            logger.info(f"📂 Baseline cargado desde: {baseline_path}")
            return True
        except Exception as e:
            logger.error(f"❌ Error cargando baseline: {e}")
            return False

    def set_baseline_from_current(self) -> None:
        """Establecer las métricas actuales como baseline."""
        if self.evaluation_metrics["evaluation_rewards"]:
            self.baseline_metrics = {
                "mean_reward": np.mean(self.evaluation_metrics["evaluation_rewards"]),
                "mean_waiting_time": np.mean(
                    self.evaluation_metrics["evaluation_waiting_times"]
                ),
                "mean_throughput": np.mean(
                    self.evaluation_metrics["evaluation_throughput"]
                ),
            }
            logger.info("📊 Métricas actuales establecidas como baseline")
        else:
            logger.warning("⚠️ No hay métricas de evaluación para establecer baseline")

    def get_summary_stats(self) -> dict[str, Any]:
        """Obtener estadísticas resumen."""
        summary: dict[str, Any] = {
            "total_training_episodes": len(self.training_metrics["episodes"]),
            "total_evaluations": len(self.evaluation_metrics["evaluation_episodes"]),
            "current_performance": {},
        }

        if self.training_metrics["rewards"]:
            recent_rewards = self.training_metrics["rewards"][-self.window_size :]
            summary["current_performance"]["recent_mean_reward"] = float(
                np.mean(recent_rewards)
            )
            summary["current_performance"]["recent_std_reward"] = float(
                np.std(recent_rewards)
            )

        if self.evaluation_metrics["evaluation_rewards"]:
            summary["current_performance"]["last_eval_reward"] = float(
                self.evaluation_metrics["evaluation_rewards"][-1]
            )

        return summary

    def _convert_to_serializable(self, obj: Any) -> Any:
        """Convierte objetos numpy a tipos serializables en JSON."""
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.bool_):
            return bool(obj)
        elif isinstance(obj, dict):
            return {
                key: self._convert_to_serializable(value) for key, value in obj.items()
            }
        elif isinstance(obj, list):
            return [self._convert_to_serializable(item) for item in obj]
        else:
            return obj
