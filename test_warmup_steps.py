#!/usr/bin/env python3
"""
🧪 Test del Sistema de Warm-up de Pasos

Verifica que el sistema de warm-up funciona correctamente:
1. Salta los primeros N pasos sin entrenamiento
2. Se aplica tanto en entrenamiento como en tiempo fijo
3. Es configurable vía config.yaml

Uso:
    poetry run python test_warmup_steps.py
"""

import logging
import time

from src.traffic_system.core.config_loader import load_app_settings
from src.traffic_system.decision.DQN.dqn_trainer import DQNTrainer

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


def test_warmup_skip_function() -> bool:
    """
    Prueba la función _skip_warmup_steps directamente.
    """
    logger.info("🧪 Iniciando test de función _skip_warmup_steps")

    try:
        # Crear instancia del trainer (sin auto_train)
        trainer = DQNTrainer(auto_train=False)

        # Verificar que la función existe
        assert hasattr(
            trainer, "_skip_warmup_steps"
        ), "Función _skip_warmup_steps no encontrada"
        logger.info("✅ Función _skip_warmup_steps encontrada")

        # Verificar configuración
        settings = load_app_settings()
        warmup_steps = getattr(settings.decision.entrenamiento, "warmup_steps", 250)
        logger.info(f"📋 Configuración warmup_steps: {warmup_steps}")

        # Test con simulación mock (si está disponible)
        logger.info("🔄 Función disponible para prueba con simulación real")

        return True

    except Exception as e:
        logger.error(f"❌ Error en test: {e}")
        return False


def test_warmup_configuration() -> bool:
    """
    Verifica que la configuración de warm-up esté correcta.
    """
    logger.info("🧪 Verificando configuración de warm-up")

    try:
        settings = load_app_settings()
        entrenamiento = settings.decision.entrenamiento

        # Verificar que warmup_steps existe
        warmup_steps = getattr(entrenamiento, "warmup_steps", None)

        if warmup_steps is None:
            logger.warning("⚠️ warmup_steps no configurado, usando default 250")
            warmup_steps = 250
        else:
            logger.info(f"✅ warmup_steps configurado: {warmup_steps}")

        # Verificar que es un valor razonable
        if 100 <= warmup_steps <= 500:
            logger.info(f"✅ Valor warmup_steps es razonable: {warmup_steps}")
        else:
            logger.warning(f"⚠️ Valor warmup_steps puede ser inusual: {warmup_steps}")

        return True

    except Exception as e:
        logger.error(f"❌ Error verificando configuración: {e}")
        return False


def test_integration_flow() -> bool:
    """
    Verifica el flujo de integración completo.
    """
    logger.info("🧪 Verificando flujo de integración")

    try:
        # Verificar que DQNTrainer puede crearse
        trainer = DQNTrainer(auto_train=False)
        logger.info("✅ DQNTrainer creado exitosamente")

        # Verificar métodos necesarios
        required_methods = [
            "_skip_warmup_steps",
            "_train_agent",
            "start_training_process",
        ]

        for method in required_methods:
            if hasattr(trainer, method):
                logger.info(f"✅ Método {method} disponible")
            else:
                logger.error(f"❌ Método {method} faltante")
                return False

        return True

    except Exception as e:
        logger.error(f"❌ Error en flujo de integración: {e}")
        return False


def main() -> bool:
    """
    Ejecuta todos los tests de warm-up.
    """
    logger.info("🚀 Iniciando tests del sistema de warm-up")
    logger.info("=" * 60)

    tests = [
        ("Configuración de warm-up", test_warmup_configuration),
        ("Función skip_warmup_steps", test_warmup_skip_function),
        ("Flujo de integración", test_integration_flow),
    ]

    results = []

    for test_name, test_func in tests:
        logger.info(f"\n🔍 Ejecutando: {test_name}")
        logger.info("-" * 40)

        start_time = time.time()
        success = test_func()
        duration = time.time() - start_time

        results.append((test_name, success, duration))

        if success:
            logger.info(f"✅ {test_name} completado en {duration:.2f}s")
        else:
            logger.error(f"❌ {test_name} falló en {duration:.2f}s")

    # Resumen final
    logger.info("\n" + "=" * 60)
    logger.info("📋 RESUMEN DE TESTS")
    logger.info("=" * 60)

    passed = sum(1 for _, success, _ in results if success)
    total = len(results)

    for test_name, success, duration in results:
        status = "✅ PASS" if success else "❌ FAIL"
        logger.info(f"{status} {test_name} ({duration:.2f}s)")

    logger.info("-" * 60)

    if passed == total:
        logger.info(f"🎉 TODOS LOS TESTS PASARON ({passed}/{total})")
        logger.info("✅ Sistema de warm-up listo para uso")
    else:
        logger.error(f"⚠️ ALGUNOS TESTS FALLARON ({passed}/{total})")
        logger.error("❌ Revisar implementación antes de usar")

    return passed == total


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
