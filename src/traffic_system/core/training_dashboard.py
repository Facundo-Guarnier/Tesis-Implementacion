"""
📊 Dashboard de Progreso para Entrenamiento DQN

Proporciona métricas en tiempo real, detección de problemas y alertas automáticas.
Facilita el diagnóstico de problemas de aprendizaje como catastrophic forgetting.
"""

import logging
import time
from collections import deque
from dataclasses import dataclass, field
from enum import Enum

import numpy as np


class TrainingHealth(Enum):
    """Estados de salud del entrenamiento."""

    EXCELLENT = "🟢 EXCELENTE"
    GOOD = "🟡 BUENO"
    WARNING = "🟠 ADVERTENCIA"
    CRITICAL = "🔴 CRÍTICO"
    CATASTROPHIC = "💀 CATASTRÓFICO"


@dataclass
class ProgressMetrics:
    """Métricas de progreso del entrenamiento."""

    epoch: int
    total_steps: int
    avg_reward: float
    cumulative_reward: float
    epsilon: float
    learning_rate: float
    avg_q_value: float
    max_q_value: float
    replay_count: int
    epoch_duration: float

    # Métricas derivadas
    steps_per_second: float = 0.0
    reward_trend: float = 0.0  # Tendencia de recompensa (positiva = mejorando)
    vs_baseline_percent: float = 0.0  # Porcentaje vs baseline

    # Estado de salud
    health_status: TrainingHealth = TrainingHealth.GOOD


@dataclass
class TrainingDashboard:
    """
    Dashboard de progreso en tiempo real para entrenamiento DQN.

    Proporciona:
    - Métricas en tiempo real
    - Detección automática de problemas
    - Alertas de degradación de performance
    - Comparación vs baseline
    - Recomendaciones automáticas
    """

    baseline_performance: float = -48285.77  # Del CSV proporcionado

    # Historial de métricas
    metrics_history: deque = field(default_factory=lambda: deque(maxlen=100))

    # Configuración de alertas
    alert_config: dict = field(
        default_factory=lambda: {
            "catastrophic_threshold": 0.5,  # 50% peor que baseline
            "warning_threshold": 0.2,  # 20% peor que baseline
            "stagnation_epochs": 5,  # Épocas sin mejora para alerta
            "q_value_min_threshold": 0.001,  # Q-values mínimos esperados
            "reward_explosion_threshold": 200,  # Recompensa por paso muy negativa
        }
    )

    # Estado interno
    last_alert_time: float = field(default_factory=time.time)
    consecutive_bad_epochs: int = 0
    best_performance: float = float("-inf")
    start_time: float = field(default_factory=time.time)

    logger: logging.Logger = field(
        default_factory=lambda: logging.getLogger("TrainingDashboard")
    )

    def update_metrics(self, metrics: ProgressMetrics) -> TrainingHealth:
        """
        Actualizar métricas y evaluar estado de salud del entrenamiento.

        Args:
            metrics: Nuevas métricas del entrenamiento

        Returns:
            TrainingHealth: Estado de salud actualizado
        """
        # Calcular métricas derivadas
        metrics.vs_baseline_percent = (
            (metrics.cumulative_reward - self.baseline_performance)
            / abs(self.baseline_performance)
        ) * 100

        # Calcular tendencia de recompensa
        if len(self.metrics_history) >= 3:
            recent_rewards = [
                m.cumulative_reward for m in list(self.metrics_history)[-3:]
            ]
            metrics.reward_trend = (recent_rewards[-1] - recent_rewards[0]) / len(
                recent_rewards
            )

        # Evaluar estado de salud
        metrics.health_status = self._evaluate_health(metrics)

        # Agregar al historial
        self.metrics_history.append(metrics)

        # Generar alertas si es necesario
        self._check_alerts(metrics)

        # Log de progreso inteligente
        self._log_progress(metrics)

        return metrics.health_status

    def _evaluate_health(self, metrics: ProgressMetrics) -> TrainingHealth:
        """Evaluar estado de salud basado en múltiples indicadores."""

        # Indicador 1: Performance vs baseline
        if metrics.vs_baseline_percent < -100:  # Más del 100% peor
            return TrainingHealth.CATASTROPHIC
        elif metrics.vs_baseline_percent < -50:  # 50% peor
            return TrainingHealth.CRITICAL
        elif metrics.vs_baseline_percent < -20:  # 20% peor
            return TrainingHealth.WARNING

        # Indicador 2: Q-values cerca de cero (red no está aprendiendo)
        if metrics.max_q_value < self.alert_config["q_value_min_threshold"]:
            return TrainingHealth.CRITICAL

        # Indicador 3: Recompensas extremadamente negativas
        if abs(metrics.avg_reward) > self.alert_config["reward_explosion_threshold"]:
            return TrainingHealth.WARNING

        # Indicador 4: Tendencia de mejora
        if metrics.reward_trend > 0:
            return TrainingHealth.GOOD
        elif metrics.reward_trend < -1000:  # Empeorando rápidamente
            return TrainingHealth.CRITICAL

        return TrainingHealth.GOOD

    def _check_alerts(self, metrics: ProgressMetrics) -> None:
        """Verificar y generar alertas según configuración."""
        current_time = time.time()

        # Throttling de alertas (máximo cada 30 segundos)
        if current_time - self.last_alert_time < 30:
            return

        alerts = []

        # Alert 1: Performance catastrófica
        if metrics.health_status == TrainingHealth.CATASTROPHIC:
            alerts.append(
                "🚨 CATASTROPHIC FORGETTING DETECTED! El modelo está desaprendiendo severamente."
            )
            alerts.append(
                f"   Performance: {metrics.vs_baseline_percent:.1f}% vs baseline"
            )
            alerts.append(
                "   RECOMENDACIÓN: Resetear entrenamiento con hiperparámetros ajustados"
            )

        # Alert 2: Q-values en cero
        if metrics.max_q_value < self.alert_config["q_value_min_threshold"]:
            alerts.append(f"🚨 Q-VALUES NEAR ZERO! Max Q: {metrics.max_q_value:.6f}")
            alerts.append("   La red neuronal no está generando valores útiles")
            alerts.append(
                "   RECOMENDACIÓN: Aumentar learning rate o revisar arquitectura"
            )

        # Alert 3: Estancamiento prolongado
        if len(self.metrics_history) >= self.alert_config["stagnation_epochs"]:
            recent_performance = [
                m.cumulative_reward
                for m in list(self.metrics_history)[
                    -self.alert_config["stagnation_epochs"] :
                ]
            ]
            if all(perf < self.best_performance for perf in recent_performance):
                alerts.append(
                    f"⚠️ STAGNATION ALERT: Sin mejora por {self.alert_config['stagnation_epochs']} épocas"
                )
                alerts.append(
                    "   RECOMENDACIÓN: Aumentar exploración (epsilon) o ajustar learning rate"
                )

        # Alert 4: Exploración insuficiente
        if metrics.epsilon < 0.1 and metrics.health_status in [
            TrainingHealth.CRITICAL,
            TrainingHealth.WARNING,
        ]:
            alerts.append(f"⚠️ LOW EXPLORATION: Epsilon = {metrics.epsilon:.3f}")
            alerts.append("   El agente podría estar atrapado en local minimum")
            alerts.append("   RECOMENDACIÓN: Aumentar epsilon temporalmente")

        # Loggear alertas si las hay
        if alerts:
            self.logger.error("🚨 ALERTAS DE ENTRENAMIENTO:")
            for alert in alerts:
                self.logger.error(f"   {alert}")
            self.last_alert_time = current_time

    def _log_progress(self, metrics: ProgressMetrics) -> None:
        """Log inteligente de progreso."""
        # Solo log de progreso cada 5 épocas o si hay cambios significativos
        should_log = (
            metrics.epoch % 5 == 0
            or metrics.health_status
            in [TrainingHealth.CRITICAL, TrainingHealth.CATASTROPHIC]
            or abs(metrics.reward_trend) > 500  # Cambio significativo
        )

        if not should_log:
            return

        # Progress log con información clave
        self.logger.info(f"📊 PROGRESO ÉPOCA {metrics.epoch}:")
        self.logger.info(f"   Estado: {metrics.health_status.value}")
        self.logger.info(
            f"   Performance vs Baseline: {metrics.vs_baseline_percent:+.1f}%"
        )
        self.logger.info(f"   Recompensa Acumulada: {metrics.cumulative_reward:.0f}")
        self.logger.info(f"   Tendencia: {metrics.reward_trend:+.0f} por época")
        self.logger.info(f"   Q-Value Max: {metrics.max_q_value:.6f}")
        self.logger.info(
            f"   Epsilon: {metrics.epsilon:.3f} | LR: {metrics.learning_rate:.6f}"
        )

        # Tiempo estimado para completar
        if len(self.metrics_history) > 1:
            avg_epoch_time = np.mean([m.epoch_duration for m in self.metrics_history])
            remaining_epochs = 50 - metrics.epoch  # Asumiendo 50 épocas totales
            eta_minutes = (remaining_epochs * avg_epoch_time) / 60
            self.logger.info(f"   ETA: {eta_minutes:.0f} minutos restantes")

    def get_recommendations(self) -> list[str]:
        """Obtener recomendaciones basadas en estado actual."""
        if not self.metrics_history:
            return ["No hay suficientes datos para recomendaciones"]

        current_metrics = self.metrics_history[-1]
        recommendations = []

        # Recomendaciones basadas en estado de salud
        if current_metrics.health_status == TrainingHealth.CATASTROPHIC:
            recommendations.extend(
                [
                    "🔄 RESTART TRAINING: El modelo está en catastrophic forgetting",
                    "📈 INCREASE Learning Rate: De 0.0003 a 0.001-0.002",
                    "🎲 INCREASE Exploration: Epsilon de 0.2 a 0.5-0.7",
                    "🎯 REVIEW Target Network: Actualizar cada 50-100 pasos en lugar de actual",
                    "🧠 SIMPLIFY Architecture: Reducir capas ocultas temporalmente",
                ]
            )

        elif current_metrics.health_status == TrainingHealth.CRITICAL:
            recommendations.extend(
                [
                    "⚡ INCREASE Learning Rate: Multiplicar por 2-3x",
                    "🎲 BOOST Exploration: Aumentar epsilon en 0.2-0.3",
                    "🔄 RESET Target Network: Forzar actualización de target",
                    "📊 CHECK Reward Function: Verificar señales de aprendizaje",
                ]
            )

        elif current_metrics.health_status == TrainingHealth.WARNING:
            recommendations.extend(
                [
                    "🎯 FINE-TUNE Hyperparameters: Ajustes menores",
                    "📈 MONITOR Closely: Estar atento a degradación",
                    "🎲 CONSIDER Exploration Boost: Si estancamiento continúa",
                ]
            )

        # Recomendaciones específicas por indicadores
        if current_metrics.max_q_value < 0.001:
            recommendations.append(
                "🧠 NEURAL NETWORK ISSUE: Red no genera Q-values útiles"
            )

        if (
            current_metrics.epsilon < 0.15
            and current_metrics.health_status != TrainingHealth.GOOD
        ):
            recommendations.append(
                "🎲 EXPLORATION TOO LOW: Aumentar epsilon inmediatamente"
            )

        return (
            recommendations
            if recommendations
            else ["✅ Entrenamiento progresando normalmente"]
        )

    def generate_summary_report(self) -> str:
        """Generar reporte de resumen del entrenamiento."""
        if not self.metrics_history:
            return "No hay datos disponibles para reporte"

        current = self.metrics_history[-1]
        total_time = time.time() - self.start_time

        report = f"""
🎯 REPORTE DE ENTRENAMIENTO - ÉPOCA {current.epoch}
{'=' * 60}

📊 PERFORMANCE GENERAL:
   Estado Actual: {current.health_status.value}
   vs Baseline: {current.vs_baseline_percent:+.1f}%
   Recompensa Acumulada: {current.cumulative_reward:.0f}
   Tendencia: {current.reward_trend:+.0f} por época

🧠 ESTADO DE LA RED:
   Q-Value Máximo: {current.max_q_value:.6f}
   Epsilon: {current.epsilon:.3f}
   Learning Rate: {current.learning_rate:.6f}

⏱️ TIEMPO Y EFICIENCIA:
   Tiempo Total: {total_time/60:.1f} minutos
   Pasos por Segundo: {current.steps_per_second:.2f}
   Duración Época: {current.epoch_duration:.1f}s

🎯 RECOMENDACIONES:
"""

        for rec in self.get_recommendations():
            report += f"   • {rec}\n"

        return report

    def should_stop_training(self) -> tuple[bool, str]:
        """Determinar si se debe detener el entrenamiento y por qué."""
        if not self.metrics_history:
            return False, ""

        current = self.metrics_history[-1]

        # Criterio 1: Catastrophic forgetting persistente
        if (
            current.health_status == TrainingHealth.CATASTROPHIC
            and len(self.metrics_history) >= 3
            and all(
                m.health_status == TrainingHealth.CATASTROPHIC
                for m in list(self.metrics_history)[-3:]
            )
        ):
            return True, "Catastrophic forgetting persistente - modelo irrecuperable"

        # Criterio 2: Q-values colapsados
        if (
            current.max_q_value < 0.0001
            and len(self.metrics_history) >= 5
            and all(m.max_q_value < 0.0001 for m in list(self.metrics_history)[-5:])
        ):
            return True, "Colapso de Q-values - red neuronal no funcional"

        # Criterio 3: Degradación severa prolongada
        if len(self.metrics_history) >= 10:
            recent_trend = np.mean(
                [m.reward_trend for m in list(self.metrics_history)[-10:]]
            )
            if recent_trend < -2000:  # Empeorando consistentemente
                return True, "Degradación severa prolongada"

        return False, ""


def create_training_dashboard(
    baseline_performance: float = -48285.77,
) -> TrainingDashboard:
    """Factory function para crear dashboard configurado."""
    return TrainingDashboard(baseline_performance=baseline_performance)
