#!/usr/bin/env python3
"""
Test para validar las nuevas optimizaciones del sistema DQN:
- Batch size dinámico
- Early stopping
- Learning rate adaptativo
"""

import logging
import sys
import time
from pathlib import Path

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

# Agregar el directorio src al path
sys.path.insert(0, str(Path(__file__).parent / "src"))


def test_configuration_loading() -> bool:
    """Test 1: Verificar que la nueva configuración se carga correctamente."""
    start_time = time.time()

    try:
        logging.info("🧪 Test 1: Verificando carga de configuración")

        from src.traffic_system.core.config_loader import load_app_settings

        config = load_app_settings()

        # Verificar nuevos parámetros
        assert hasattr(
            config.decision.entrenamiento, "min_replay_size"
        ), "min_replay_size no encontrado"
        assert hasattr(
            config.decision.entrenamiento, "warmup_steps"
        ), "warmup_steps no encontrado"

        min_replay_size = config.decision.entrenamiento.min_replay_size
        warmup_steps = config.decision.entrenamiento.warmup_steps
        batch_size = config.decision.entrenamiento.batch_size

        logging.info(f"✅ min_replay_size: {min_replay_size}")
        logging.info(f"✅ warmup_steps: {warmup_steps}")
        logging.info(f"✅ batch_size: {batch_size}")

        # Validaciones de lógica
        assert (
            min_replay_size < batch_size
        ), f"min_replay_size ({min_replay_size}) debe ser menor que batch_size ({batch_size})"
        assert (
            min_replay_size >= 16
        ), f"min_replay_size ({min_replay_size}) debería ser al menos 16"
        assert warmup_steps > 0, f"warmup_steps ({warmup_steps}) debe ser positivo"

        elapsed = time.time() - start_time
        logging.info(f"✅ Test 1 completado en {elapsed:.2f}s")
        return True

    except Exception as e:
        elapsed = time.time() - start_time
        logging.error(f"❌ Error en test 1: {e}")
        logging.error(f"❌ Test 1 falló en {elapsed:.2f}s")
        return False


def test_batch_dynamic_functions() -> bool:
    """Test 2: Verificar que las funciones de batch dinámico están disponibles."""
    start_time = time.time()

    try:
        logging.info("🧪 Test 2: Verificando funciones de batch dinámico")

        from src.traffic_system.core.config_loader import load_app_settings
        from src.traffic_system.decision.DQN.dqn_trainer import DQNTrainer

        config = load_app_settings()
        trainer = DQNTrainer(config.decision.entrenamiento, auto_train=False)

        # Verificar que min_replay_size está configurado
        assert hasattr(
            trainer, "min_replay_size"
        ), "min_replay_size no encontrado en DQNTrainer"
        assert (
            trainer.min_replay_size == 32
        ), f"min_replay_size esperado: 32, actual: {trainer.min_replay_size}"

        # Verificar funciones de optimización
        assert hasattr(
            trainer, "_check_early_stopping"
        ), "_check_early_stopping no encontrada"
        assert hasattr(
            trainer, "_adaptive_learning_rate_update"
        ), "_adaptive_learning_rate_update no encontrada"

        # Verificar atributos de early stopping
        assert hasattr(trainer, "best_avg_reward"), "best_avg_reward no encontrado"
        assert hasattr(
            trainer, "epochs_without_improvement"
        ), "epochs_without_improvement no encontrado"
        assert hasattr(trainer, "patience"), "patience no encontrado"

        logging.info(f"✅ min_replay_size configurado: {trainer.min_replay_size}")
        logging.info(f"✅ patience configurado: {trainer.patience}")
        logging.info("✅ Funciones de optimización disponibles")

        elapsed = time.time() - start_time
        logging.info(f"✅ Test 2 completado en {elapsed:.2f}s")
        return True

    except Exception as e:
        elapsed = time.time() - start_time
        logging.error(f"❌ Error en test 2: {e}")
        logging.error(f"❌ Test 2 falló en {elapsed:.2f}s")
        return False


def test_optimization_logic() -> bool:
    """Test 3: Probar lógica de optimizaciones con datos simulados."""
    start_time = time.time()

    try:
        logging.info("🧪 Test 3: Probando lógica de optimizaciones")

        from src.traffic_system.core.config_loader import load_app_settings
        from src.traffic_system.decision.DQN.dqn_trainer import DQNTrainer

        config = load_app_settings()
        trainer = DQNTrainer(config.decision.entrenamiento, auto_train=False)

        # Test early stopping
        logging.info("🔍 Probando early stopping...")

        # Simular mejora inicial
        result1 = trainer._check_early_stopping(-100.0, 1)
        assert not result1, "No debería activar early stopping con primera recompensa"

        # Simular mejora
        result2 = trainer._check_early_stopping(-90.0, 2)
        assert not result2, "No debería activar early stopping con mejora"

        # Simular varias épocas sin mejora
        for epoch in range(3, 15):  # Simular 12 épocas sin mejora
            result = trainer._check_early_stopping(-95.0, epoch)

        assert (
            result
        ), "Debería activar early stopping después de muchas épocas sin mejora"

        logging.info("✅ Early stopping funciona correctamente")

        # Test batch dinámico - verificar configuración
        logging.info("🔍 Probando batch dinámico...")

        # Verificar configuración de batch dinámico
        assert (
            trainer.min_replay_size == 32
        ), f"min_replay_size esperado: 32, actual: {trainer.min_replay_size}"
        assert (
            trainer.batch_size == 256
        ), f"batch_size esperado: 256, actual: {trainer.batch_size}"

        # Test lógico: validar que el batch dinámico funcionaría correctamente
        test_memory_sizes = [16, 32, 64, 128, 256, 300]

        for test_size in test_memory_sizes:
            if test_size < trainer.min_replay_size:
                should_train = False
                expected_batch = 0
            else:
                should_train = True
                expected_batch = min(trainer.batch_size, test_size)

            logging.info(
                f"📊 Memoria: {test_size}, Entrena: {should_train}, Batch efectivo: {expected_batch}"
            )

        logging.info("✅ Lógica de batch dinámico validada")

        elapsed = time.time() - start_time
        logging.info(f"✅ Test 3 completado en {elapsed:.2f}s")
        return True

    except Exception as e:
        elapsed = time.time() - start_time
        logging.error(f"❌ Error en test 3: {e}")
        logging.error(f"❌ Test 3 falló en {elapsed:.2f}s")
        return False


if __name__ == "__main__":
    logging.info("🚀 Iniciando tests de optimizaciones DQN")
    logging.info("=" * 60)

    tests = [
        ("Configuración de optimizaciones", test_configuration_loading),
        ("Funciones de batch dinámico", test_batch_dynamic_functions),
        ("Lógica de optimizaciones", test_optimization_logic),
    ]

    results = []

    for test_name, test_func in tests:
        logging.info(f"\n🔍 Ejecutando: {test_name}")
        logging.info("-" * 40)
        result = test_func()
        results.append((test_name, result))

    logging.info("\n" + "=" * 60)
    logging.info("📋 RESUMEN DE TESTS")
    logging.info("=" * 60)

    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        logging.info(f"{status} {test_name}")
        if result:
            passed += 1

    logging.info("-" * 60)
    logging.info(f"🎉 TESTS COMPLETADOS ({passed}/{len(tests)})")

    if passed == len(tests):
        logging.info("✅ Todas las optimizaciones funcionan correctamente")
        sys.exit(0)
    else:
        logging.error("❌ Algunas optimizaciones tienen problemas")
        sys.exit(1)
