#!/usr/bin/env python3
"""
Test para verificar las mejoras de la Fase 1 del modelo DQN.

Este script verifica que:
1. La nueva función de recompensa funciona correctamente
2. El estado enriquecido incluye cantidades de vehículos e historial
3. La normalización robusta maneja casos extremos

Ejecutar: poetry run python test_dqn_mejoras_fase1.py
"""

import logging
import sys
from unittest.mock import Mock

import numpy as np

# Configurar logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def test_new_reward_function() -> bool:
    """
    Test de la nueva función de recompensa mejorada.
    """
    logger.info("🧪 Probando nueva función de recompensa...")

    try:
        # Importar y configurar la clase
        from src.traffic_system.decision.DQN.dqn_trainer import DQNTrainer

        # Crear instancia con configuración mínima
        trainer = DQNTrainer()

        # Mockear las respuestas de API
        mock_wait_response = Mock()
        mock_wait_response.tiempos_espera = [
            10.0,
            20.0,
            15.0,
            5.0,
            30.0,
            25.0,
            8.0,
            12.0,
            18.0,
            22.0,
            7.0,
            13.0,
        ]

        mock_quantities_response = Mock()
        mock_quantities_response.cantidades = {
            "Zona A": 5,
            "Zona B": 8,
            "Zona C": 3,
            "Zona D": 12,
            "Zona E": 7,
            "Zona F": 15,
            "Zona G": 2,
            "Zona H": 9,
            "Zona I": 6,
            "Zona J": 11,
            "Zona K": 4,
            "Zona L": 10,
        }

        # Mockear la API
        trainer._api.get_wait_times = Mock(return_value=mock_wait_response)  # type: ignore
        trainer._api.get_quantities = Mock(return_value=mock_quantities_response)  # type: ignore

        # Calcular recompensa
        reward = trainer._calculate_reward()

        logger.info(f"✅ Nueva recompensa calculada: {reward:.4f}")

        # Verificar que la recompensa es negativa (penalización)
        assert reward < 0, f"La recompensa debería ser negativa, obtenido: {reward}"

        # Verificar que considera múltiples factores
        assert trainer._api.get_wait_times.called, "Debería consultar tiempos de espera"
        assert (
            trainer._api.get_quantities.called
        ), "Debería consultar cantidades de vehículos"

        logger.info("✅ Test de función de recompensa: EXITOSO")
        return True

    except Exception as e:
        logger.error(f"❌ Error en test de recompensa: {e}")
        return False


def test_enriched_state() -> bool:
    """
    Test del estado enriquecido con historial temporal.
    """
    logger.info("🧪 Probando estado enriquecido...")

    try:
        from src.traffic_system.decision.DQN.dqn_trainer import DQNTrainer

        # Crear instancia
        trainer = DQNTrainer()

        # Verificar que el state_size se actualizó
        assert (
            trainer.state_size == 48
        ), f"State size debería ser 48, obtenido: {trainer.state_size}"

        # Mockear respuestas de API
        mock_wait_response = Mock()
        mock_wait_response.tiempos_espera = [10.0] * 12  # 12 valores

        mock_quantities_response = Mock()
        mock_quantities_response.cantidades = {
            f"Zona {chr(65+i)}": i + 1 for i in range(12)
        }  # 12 valores

        trainer._api.get_wait_times = Mock(return_value=mock_wait_response)  # type: ignore
        trainer._api.get_quantities = Mock(return_value=mock_quantities_response)  # type: ignore

        # Obtener primer estado (sin historial)
        state1 = trainer._get_current_state()
        logger.info(f"✅ Primer estado shape: {state1.shape}")
        assert state1.shape == (
            48,
        ), f"Estado debería tener shape (48,), obtenido: {state1.shape}"

        # Cambiar valores para segunda observación
        mock_wait_response.tiempos_espera = [15.0] * 12
        mock_quantities_response.cantidades = {
            f"Zona {chr(65+i)}": (i + 1) * 2 for i in range(12)
        }

        # Obtener segundo estado (con historial)
        state2 = trainer._get_current_state()
        logger.info(f"✅ Segundo estado shape: {state2.shape}")
        assert state2.shape == (
            48,
        ), f"Estado debería tener shape (48,), obtenido: {state2.shape}"

        # Verificar que los estados son diferentes (incluye historial)
        state_diff = np.sum(np.abs(state1 - state2))
        assert (
            state_diff > 0
        ), "Los estados deberían ser diferentes cuando incluyen historial"

        # Verificar que el historial se mantiene
        assert (
            len(trainer.state_history) == 2
        ), f"Debería tener 2 observaciones en historial, tiene: {len(trainer.state_history)}"

        logger.info("✅ Test de estado enriquecido: EXITOSO")
        return True

    except Exception as e:
        logger.error(f"❌ Error en test de estado enriquecido: {e}")
        return False


def test_robust_normalization() -> bool:
    """
    Test de la normalización robusta.
    """
    logger.info("🧪 Probando normalización robusta...")

    try:
        from src.traffic_system.decision.DQN.dqn_trainer import DQNTrainer

        trainer = DQNTrainer()

        # Test con valores normales
        normal_state = [10.0] * 24 + [5.0] * 24  # 48 valores
        normalized = trainer._normalize_state_robust(normal_state)

        assert normalized.shape == (48,), f"Shape incorrecto: {normalized.shape}"
        assert np.all(normalized >= 0) and np.all(
            normalized <= 1
        ), "Valores deberían estar entre 0 y 1"

        # Test con valores extremos (ceros, infinitos, NaN)
        extreme_state = [0.0, np.inf, np.nan, 1000.0] * 12  # 48 valores
        normalized_extreme = trainer._normalize_state_robust(extreme_state)

        assert np.all(
            np.isfinite(normalized_extreme)
        ), "No debería haber valores infinitos o NaN"
        assert normalized_extreme.shape == (
            48,
        ), f"Shape incorrecto: {normalized_extreme.shape}"

        logger.info("✅ Test de normalización robusta: EXITOSO")
        return True

    except Exception as e:
        logger.error(f"❌ Error en test de normalización: {e}")
        return False


def main() -> int:
    """
    Ejecutar todos los tests de las mejoras de Fase 1.
    """
    logger.info("🚀 Iniciando tests de mejoras DQN - Fase 1")

    tests = [test_new_reward_function, test_enriched_state, test_robust_normalization]

    results = []
    for test_func in tests:
        try:
            result = test_func()
            results.append(result)
        except Exception as e:
            logger.error(f"❌ Error ejecutando {test_func.__name__}: {e}")
            results.append(False)

    # Resumen
    successful = sum(results)
    total = len(results)

    logger.info("=" * 60)
    logger.info(f"📊 RESULTADOS: {successful}/{total} tests exitosos")

    if successful == total:
        logger.info("🎉 ¡Todas las mejoras de Fase 1 funcionan correctamente!")
        return 0
    else:
        logger.error("❌ Algunos tests fallaron. Revisar implementación.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
