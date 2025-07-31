#!/usr/bin/env python3
"""
Script de prueba para el entrenador DQN simplificado.

Este script demuestra cómo usar el nuevo entrenador simplificado que elimina
todas las contradicciones y complejidad excesiva del entrenador original.
"""

import logging
import os
import sys

# Añadir el directorio src al path para imports
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from src.traffic_system.decision.DQN.dqn_trainer_simplified import SimplifiedDQNTrainer


def main() -> int:
    """Función principal de prueba."""

    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    logger = logging.getLogger(__name__)

    try:
        logger.info("🔥 === INICIANDO PRUEBA DQN SIMPLIFICADO ===")

        # Mostrar configuración que se usará
        logger.info("📋 Configuración simplificada:")
        logger.info("   • Solo epsilon-greedy (SIN noisy networks)")
        logger.info("   • Learning rate fijo: 0.0001")
        logger.info("   • Arquitectura: [256, 256]")
        logger.info("   • Double DQN + Dueling DQN")
        logger.info("   • SIN PER, SIN batch norm, SIN dropout")
        logger.info("   • Gamma: 0.99 (estándar)")

        # Crear y ejecutar entrenador
        trainer = SimplifiedDQNTrainer()

        logger.info("🚀 Iniciando entrenamiento...")
        trainer.start_training_process()

        logger.info("✅ Entrenamiento completado exitosamente")

    except KeyboardInterrupt:
        logger.info("⏹️ Entrenamiento interrumpido por el usuario")
    except Exception as e:
        logger.error(f"❌ Error durante entrenamiento: {e}")
        import traceback

        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
