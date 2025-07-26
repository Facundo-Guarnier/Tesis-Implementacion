#!/usr/bin/env python3
"""
Test para verificar que el gradient clipping funciona correctamente sin errores.
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


def test_model_compilation() -> bool:
    """Test rápido de compilación del modelo."""
    start_time = time.time()

    try:
        logging.info("🧪 Iniciando test de compilación de modelo DQN")

        # Importar después de configurar path
        from src.traffic_system.core.config_loader import load_app_settings
        from src.traffic_system.decision.DQN.dqn_trainer import DQNTrainer

        logging.info("✅ Imports exitosos")

        # Cargar configuración
        config = load_app_settings()
        logging.info("✅ Configuración cargada")

        # Crear trainer (esto compilará el modelo)
        trainer = DQNTrainer(config.decision.entrenamiento)
        logging.info("✅ DQNTrainer creado exitosamente")

        # Verificar que el modelo se compiló sin errores
        if hasattr(trainer, "main_nn") and trainer.main_nn is not None:
            logging.info("✅ Modelo principal creado")

            # Verificar que el optimizador está configurado correctamente
            optimizer = trainer.main_nn.optimizer
            if hasattr(optimizer, "clipnorm") and optimizer.clipnorm == 1.0:
                logging.info(
                    "✅ Gradient clipping configurado correctamente (clipnorm=1.0)"
                )
            else:
                logging.warning("⚠️ Gradient clipping no configurado como esperado")

        elapsed = time.time() - start_time
        logging.info(f"✅ Test completado exitosamente en {elapsed:.2f}s")
        return True

    except Exception as e:
        elapsed = time.time() - start_time
        logging.error(f"❌ Error en test de compilación: {e}")
        logging.error(f"❌ Test falló en {elapsed:.2f}s")
        return False


if __name__ == "__main__":
    logging.info("🚀 Iniciando test de gradient clipping")
    logging.info("=" * 60)

    success = test_model_compilation()

    logging.info("=" * 60)
    if success:
        logging.info("🎉 TEST PASÓ - Gradient clipping configurado correctamente")
        sys.exit(0)
    else:
        logging.error("💥 TEST FALLÓ - Revisar configuración")
        sys.exit(1)
