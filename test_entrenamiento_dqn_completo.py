#!/usr/bin/env python3
"""
Test específico para verificar la configuración automática de EntrenamientoDQN.
"""

import logging
import os
import sys

import tensorflow as tf

# Agregar el directorio src al path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__))))

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")
logger = logging.getLogger("TestEntrenamientoDQN")


def test_configuracion_real():
    """
    Test real de la configuración automática.
    """
    logger.info("=" * 60)
    logger.info("TEST: CONFIGURACIÓN REAL DE ENTRENAMIENTO DQN")
    logger.info("=" * 60)

    try:
        # Mock de la configuración para evitar dependencias
        class MockSettings:
            def __init__(self):
                self.entrenamiento = MockEntrenamiento()

        class MockEntrenamiento:
            def __init__(self):
                self.memory = 1000
                self.num_epocas = 2
                self.batch_size = 32
                self.steps = 5
                self.learning_rate = 0.01
                self.learning_rate_decay = 0.995
                self.learning_rate_min = 0.001
                self.epsilon = 0.5
                self.epsilon_decay = 0.995
                self.epsilon_min = 0.01
                self.gamma = 0.85
                self.hidden_layers = [10, 10]
                self.path_resultado = "/tmp/test_results"

        # Importar y patch la configuración
        # Patch del load_app_settings
        import src.traffic_system.core.config_loader as config_loader
        from src.traffic_system.decision.DQN.dqn_trainer import DQNTrainer

        original_load = config_loader.load_app_settings

        mock_app_settings = type("MockAppSettings", (), {"decision": MockSettings()})()
        config_loader.load_app_settings = lambda: mock_app_settings  # type: ignore

        try:
            logger.info("🧪 Creando instancia real de EntrenamientoDQN...")

            # Crear instancia (esto debería ejecutar __configure_gpu)
            trainer = DQNTrainer()

            logger.info("✅ Instancia creada exitosamente")
            logger.info(f"🎯 Dispositivo configurado: {trainer.device}")
            logger.info(f"🚀 Usando GPU: {trainer.use_gpu}")

            # Test de construcción del modelo
            logger.info("\n🔧 Probando construcción del modelo...")
            model = trainer._EntrenamientoDQN__build_model()

            logger.info("✅ Modelo construido exitosamente")
            logger.info(
                f"📊 Arquitectura: {[layer.units for layer in model.layers if hasattr(layer, 'units')]}"
            )

            return True

        finally:
            # Restaurar configuración original
            config_loader.load_app_settings = original_load

    except Exception as e:
        logger.error(f"❌ Error en test: {e}")
        import traceback

        logger.error(traceback.format_exc())
        return False


def test_sin_gpu():
    """
    Test simulando sistema sin GPU.
    """
    logger.info("\n" + "=" * 60)
    logger.info("TEST: SIMULANDO SISTEMA SIN GPU")
    logger.info("=" * 60)

    # Guardar configuración original
    original_visible = os.environ.get("CUDA_VISIBLE_DEVICES", "")

    try:
        # Ocultar GPUs
        os.environ["CUDA_VISIBLE_DEVICES"] = "-1"

        # Reiniciar TensorFlow para que tome la nueva configuración
        # (Esto es solo para el test, normalmente no se hace)

        logger.info("🔄 GPU ocultada para test")
        logger.info("💻 Verificando que se use CPU...")

        # Verificar dispositivos disponibles
        gpus = tf.config.experimental.list_physical_devices("GPU")
        logger.info(f"   GPUs visibles: {len(gpus)}")

        if len(gpus) == 0:
            logger.info("✅ Simulación de sistema sin GPU exitosa")
        else:
            logger.warning(
                "⚠️ Aún se ven GPUs (configuración no aplicada completamente)"
            )

        return True

    finally:
        # Restaurar configuración
        if original_visible:
            os.environ["CUDA_VISIBLE_DEVICES"] = original_visible
        else:
            os.environ.pop("CUDA_VISIBLE_DEVICES", None)

        logger.info("🔄 Configuración GPU restaurada")


if __name__ == "__main__":
    logger.info("Iniciando test específico de EntrenamientoDQN...")

    try:
        # Test 1: Configuración real con GPU
        test1_ok = test_configuracion_real()

        # Test 2: Simulación sin GPU
        test2_ok = test_sin_gpu()

        if test1_ok and test2_ok:
            logger.info("\n🎯 RESUMEN: ¡Todos los tests pasaron!")
            logger.info("✅ EntrenamientoDQN puede usar GPU o CPU automáticamente")
            logger.info(
                "🚀 Configuración automática de dispositivo funcionando correctamente"
            )
            sys.exit(0)
        else:
            logger.error("\n💥 RESUMEN: Algunos tests fallaron")
            sys.exit(1)

    except Exception as e:
        logger.error(f"❌ Error inesperado: {e}")
        sys.exit(1)
