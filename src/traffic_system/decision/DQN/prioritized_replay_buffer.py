"""
Prioritized Replay Buffer para Deep Q-Learning.

Este módulo implementa el Prioritized Experience Replay (PER) que mejora
el aprendizaje al muestrear experiencias importantes más frecuentemente.
"""

import numpy as np
from numpy import ndarray as NDArray


class PrioritizedReplayBuffer:
    """
    Buffer de experiencia con priorización para Prioritized Experience Replay (PER).

    Implementa muestreo basado en TD-error con importance sampling para corregir bias.
    El algoritmo PER mejora significativamente la eficiencia del aprendizaje al
    priorizar experiencias que generan mayor error de predicción.

    Attributes:
        capacity: Capacidad máxima del buffer
        alpha: Grado de priorización (0=uniforme, 1=completamente priorizado)
        buffer: Lista circular de experiencias
        priorities: Prioridades correspondientes a cada experiencia
        position: Posición actual en el buffer circular
    """

    def __init__(self, capacity: int, alpha: float = 0.6) -> None:
        """
        Inicializa el buffer de experiencias priorizadas.

        Args:
            capacity: Número máximo de experiencias a almacenar
            alpha: Exponente de priorización. 0=muestreo uniforme, 1=completamente priorizado
        """
        if capacity <= 0:
            raise ValueError("La capacidad debe ser mayor que 0")
        if not 0 <= alpha <= 1:
            raise ValueError("Alpha debe estar en el rango [0, 1]")

        self.capacity = capacity
        self.alpha = alpha
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
        """
        Añade nueva experiencia con prioridad basada en TD-error.

        Args:
            state: Estado actual
            action: Acción tomada
            reward: Recompensa recibida
            next_state: Siguiente estado
            done: Si el episodio terminó
            td_error: Error de diferencia temporal para calcular prioridad
        """
        # Evitar prioridad 0 añadiendo pequeña constante
        priority = (abs(td_error) + 1e-6) ** self.alpha

        experience = (state, action, reward, next_state, done)

        if len(self.buffer) < self.capacity:
            self.buffer.append(experience)
            self.priorities.append(priority)
        else:
            # Sobrescribir experiencia más antigua
            self.buffer[self.position] = experience
            self.priorities[self.position] = priority

        self.position = (self.position + 1) % self.capacity

    def sample(
        self, batch_size: int, beta: float = 0.4
    ) -> tuple[list, list[int], NDArray]:
        """
        Muestrea experiencias basadas en prioridades con importance sampling.

        Args:
            batch_size: Número de experiencias a muestrear
            beta: Parámetro de importance sampling (0=sin corrección, 1=corrección completa)

        Returns:
            Tupla con (experiencias_muestreadas, índices, pesos_importance_sampling)
        """
        if len(self.buffer) < batch_size:
            return [], [], np.array([])

        # Calcular probabilidades de muestreo
        priorities = np.array(self.priorities[: len(self.buffer)])
        probabilities = priorities / priorities.sum()

        # Muestrear índices basados en probabilidades
        indices = np.random.choice(len(self.buffer), batch_size, p=probabilities)

        # Calcular importance sampling weights para corregir bias
        total = len(self.buffer)
        weights = (total * probabilities[indices]) ** (-beta)
        weights /= weights.max()  # Normalizar

        # Extraer experiencias muestreadas
        samples = [self.buffer[idx] for idx in indices]

        return samples, indices.tolist(), weights

    def update_priorities(self, indices: list[int], td_errors: list[float]) -> None:
        """
        Actualiza las prioridades basadas en nuevos TD-errors.

        Args:
            indices: Índices de las experiencias a actualizar
            td_errors: Nuevos errores de diferencia temporal
        """
        for idx, td_error in zip(indices, td_errors, strict=True):
            if 0 <= idx < len(self.priorities):
                self.priorities[idx] = (abs(td_error) + 1e-6) ** self.alpha

    def __len__(self) -> int:
        """Retorna el número actual de experiencias almacenadas."""
        return len(self.buffer)

    @property
    def is_full(self) -> bool:
        """Indica si el buffer ha alcanzado su capacidad máxima."""
        return len(self.buffer) == self.capacity
