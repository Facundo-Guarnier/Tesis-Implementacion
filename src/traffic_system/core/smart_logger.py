"""
🧠 Sistema de Logging Inteligente para Entrenamiento DQN

Reduce el spam de logs y proporciona información útil agregada.
Implementa throttling, agregación estadística y logging condicional.
"""

import logging
import time
from collections import defaultdict
from dataclasses import dataclass
from enum import Enum
from typing import Any


class LogLevel(Enum):
    """Niveles de logging con prioridad."""

    CRITICAL = "CRITICAL"
    ERROR = "ERROR"
    WARNING = "WARNING"
    PROGRESS = "PROGRESS"  # Progreso importante
    INFO = "INFO"  # Información general
    DEBUG = "DEBUG"  # Debug detallado


@dataclass
class LogStats:
    """Estadísticas para agregación de logs."""

    count: int = 0
    last_logged: float = 0
    min_value: float | None = None
    max_value: float | None = None
    sum_value: float = 0
    values: list = None

    def __post_init__(self):
        if self.values is None:
            self.values = []


class SmartLogger:
    """
    Logger inteligente que reduce spam y agrega información útil.

    Características:
    - Throttling por tipo de mensaje
    - Agregación estadística automática
    - Logging condicional basado en cambios significativos
    - Separación por niveles de prioridad
    """

    def __init__(self, logger_name: str, config: dict | None = None):
        self.logger = logging.getLogger(logger_name)
        self.config = self._get_default_config()
        if config:
            self.config.update(config)

        # Estado interno para throttling y agregación
        self._throttle_state: dict[str, float] = {}
        self._aggregate_stats: dict[str, LogStats] = defaultdict(LogStats)
        self._last_values: dict[str, Any] = {}

        # Contadores para resúmenes periódicos
        self._step_count = 0
        self._last_summary = time.time()

    def _get_default_config(self) -> dict[str, Any]:
        """Configuración por defecto del SmartLogger."""
        return {
            # Intervalos de throttling por nivel (segundos)
            "throttle_intervals": {
                LogLevel.CRITICAL: 0,  # Nunca throttle
                LogLevel.ERROR: 0,  # Nunca throttle
                LogLevel.WARNING: 5,  # Máximo cada 5 segundos
                LogLevel.PROGRESS: 2,  # Progreso cada 2 segundos
                LogLevel.INFO: 10,  # Info cada 10 segundos
                LogLevel.DEBUG: 30,  # Debug cada 30 segundos
            },
            # Umbrales para cambios significativos (porcentaje)
            "significant_change_threshold": 0.20,  # 20% change
            # Intervalo para resúmenes automáticos
            "summary_interval": 60,  # 60 segundos
            # Tamaño de ventana para estadísticas móviles
            "stats_window_size": 100,
        }

    def should_log(
        self, message_key: str, level: LogLevel, value: float | None = None
    ) -> bool:
        """
        Determina si un mensaje debe ser loggeado basado en throttling y cambios.

        Args:
            message_key: Identificador único del tipo de mensaje
            level: Nivel de logging
            value: Valor numérico asociado (para detectar cambios significativos)

        Returns:
            bool: True si el mensaje debe ser loggeado
        """
        current_time = time.time()

        # Los errores y críticos siempre se loggean
        if level in [LogLevel.CRITICAL, LogLevel.ERROR]:
            return True

        # Verificar throttling por tiempo
        throttle_key = f"{message_key}_{level.value}"
        last_logged = self._throttle_state.get(throttle_key, 0)
        interval = self.config["throttle_intervals"][level]

        if current_time - last_logged < interval:
            return False

        # Verificar cambios significativos si hay valor numérico
        if value is not None and message_key in self._last_values:
            last_value = self._last_values[message_key]
            if last_value != 0:
                change_percent = abs(value - last_value) / abs(last_value)
                if change_percent < self.config["significant_change_threshold"]:
                    return False  # Cambio no significativo

        # Actualizar estado
        self._throttle_state[throttle_key] = current_time
        if value is not None:
            self._last_values[message_key] = value

        return True

    def add_metric(self, key: str, value: float):
        """Agregar métrica para estadísticas agregadas."""
        stats = self._aggregate_stats[key]
        stats.count += 1
        stats.sum_value += value

        if stats.min_value is None or value < stats.min_value:
            stats.min_value = value
        if stats.max_value is None or value > stats.max_value:
            stats.max_value = value

        # Mantener ventana móvil de valores
        stats.values.append(value)
        window_size = self.config["stats_window_size"]
        if len(stats.values) > window_size:
            stats.values = stats.values[-window_size:]

    def log_if_needed(
        self,
        level: LogLevel,
        message_key: str,
        message: str,
        value: float | None = None,
        **kwargs,
    ):
        """
        Log inteligente que aplica throttling y agregación.

        Args:
            level: Nivel de logging
            message_key: Identificador único del tipo de mensaje
            message: Mensaje a loggear
            value: Valor numérico asociado (opcional)
            **kwargs: Argumentos adicionales para formateo
        """
        if not self.should_log(message_key, level, value):
            # Aunque no loggeemos, agregamos la métrica si existe
            if value is not None:
                self.add_metric(message_key, value)
            return

        # Agregar métrica y loggear
        if value is not None:
            self.add_metric(message_key, value)

        # Formatear mensaje con estadísticas si están disponibles
        if message_key in self._aggregate_stats and value is not None:
            stats = self._aggregate_stats[message_key]
            if stats.count > 1:
                avg = stats.sum_value / stats.count
                message += f" | Avg: {avg:.1f}, Min: {stats.min_value:.1f}, Max: {stats.max_value:.1f}"

        # Log según nivel
        log_func = {
            LogLevel.CRITICAL: self.logger.critical,
            LogLevel.ERROR: self.logger.error,
            LogLevel.WARNING: self.logger.warning,
            LogLevel.PROGRESS: self.logger.info,
            LogLevel.INFO: self.logger.info,
            LogLevel.DEBUG: self.logger.debug,
        }[level]

        log_func(message, **kwargs)

    def step(self):
        """Incrementar contador de pasos y generar resúmenes si es necesario."""
        self._step_count += 1
        current_time = time.time()

        # Generar resumen cada intervalo configurado
        if current_time - self._last_summary > self.config["summary_interval"]:
            self._generate_summary()
            self._last_summary = current_time

    def _generate_summary(self):
        """Generar resumen estadístico de métricas agregadas."""
        if not self._aggregate_stats:
            return

        self.logger.info("📊 RESUMEN ESTADÍSTICO:")
        for key, stats in self._aggregate_stats.items():
            if stats.count > 0:
                avg = stats.sum_value / stats.count
                self.logger.info(
                    f"   {key}: Promedio: {avg:.2f} | "
                    f"Min: {stats.min_value:.2f} | Max: {stats.max_value:.2f} | "
                    f"Samples: {stats.count}"
                )

    def force_summary(self):
        """Forzar generación de resumen estadístico."""
        self._generate_summary()

    def reset_stats(self):
        """Resetear todas las estadísticas agregadas."""
        self._aggregate_stats.clear()
        self._last_values.clear()
        self._throttle_state.clear()
        self._step_count = 0


# Factory function para crear loggers configurados
def create_smart_logger(name: str, config: dict | None = None) -> SmartLogger:
    """Crear un SmartLogger con configuración específica."""
    return SmartLogger(name, config)


# Configuraciones predefinidas
DQN_LOGGER_CONFIG = {
    "throttle_intervals": {
        LogLevel.CRITICAL: 0,
        LogLevel.ERROR: 0,
        LogLevel.WARNING: 10,
        LogLevel.PROGRESS: 5,  # Progreso DQN cada 5 segundos
        LogLevel.INFO: 30,  # Info general cada 30 segundos
        LogLevel.DEBUG: 60,  # Debug cada minuto
    },
    "significant_change_threshold": 0.15,  # 15% para DQN
    "summary_interval": 120,  # Resumen cada 2 minutos
}

SIMULATION_LOGGER_CONFIG = {
    "throttle_intervals": {
        LogLevel.CRITICAL: 0,
        LogLevel.ERROR: 0,
        LogLevel.WARNING: 15,  # Warnings de simulación cada 15 segundos
        LogLevel.PROGRESS: 10,  # Progreso cada 10 segundos
        LogLevel.INFO: 60,  # Info cada minuto
        LogLevel.DEBUG: 120,  # Debug cada 2 minutos
    },
    "significant_change_threshold": 0.25,  # 25% para simulación
    "summary_interval": 180,  # Resumen cada 3 minutos
}
