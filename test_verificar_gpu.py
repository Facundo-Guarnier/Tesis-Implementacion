#!/usr/bin/env python3
"""
Script para verificar si TensorFlow puede usar GPU para entrenamiento de DQN.
"""

import logging
import sys

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")
logger = logging.getLogger("VerificacionGPU")


def verificar_gpu() -> bool:
    """
    Verifica la configuración de GPU para TensorFlow.
    """
    logger.info("=" * 60)
    logger.info("VERIFICACIÓN DE GPU PARA ENTRENAMIENTO DQN")
    logger.info("=" * 60)

    # Verificar entorno WSL2
    logger.info("🐧 Verificando entorno...")
    try:
        import os
        import platform

        logger.info(f"   Sistema: {platform.system()} {platform.release()}")

        # Verificar si estamos en WSL
        if (
            "microsoft" in platform.release().lower()
            or "wsl" in platform.release().lower()
        ):
            logger.info("   🪟 Entorno: WSL2 detectado")

        # Verificar variables de entorno CUDA
        cuda_visible = os.environ.get("CUDA_VISIBLE_DEVICES", "No configurado")
        if cuda_visible != "No configurado":
            logger.info(f"   🎮 CUDA_VISIBLE_DEVICES: {cuda_visible}")

    except Exception as e:
        logger.warning(f"   ⚠️ No se pudo verificar el entorno: {e}")

    # Importar TensorFlow
    try:
        import tensorflow as tf

        logger.info("✅ TensorFlow importado exitosamente")
        logger.info(f"   Versión: {tf.__version__}")
    except ImportError as e:
        logger.error("❌ Error importando TensorFlow")
        logger.error(f"   {e}")
        return False

    # Verificar compatibilidad CUDA
    logger.info("🔍 Verificando compatibilidad CUDA...")
    cuda_available = tf.test.is_built_with_cuda()
    logger.info(f"   TensorFlow compilado con CUDA: {cuda_available}")

    if cuda_available:
        cuda_version = tf.sysconfig.get_build_info().get("cuda_version", "Desconocida")
        cudnn_version = tf.sysconfig.get_build_info().get(
            "cudnn_version", "Desconocida"
        )
        logger.info(f"   Versión CUDA: {cuda_version}")
        logger.info(f"   Versión cuDNN: {cudnn_version}")

    # Listar dispositivos físicos
    logger.info("🖥️  Dispositivos físicos disponibles:")
    physical_devices = tf.config.list_physical_devices()
    for device in physical_devices:
        logger.info(f"   {device}")

    # Verificar GPUs específicamente
    logger.info("🚀 Verificando GPUs...")
    gpu_devices = tf.config.list_physical_devices("GPU")

    if not gpu_devices:
        logger.warning("⚠️ No se encontraron GPUs disponibles")
        logger.info("💡 Para usar GPU, necesitas:")
        logger.info("   1. 🎮 GPU NVIDIA compatible (GTX/RTX series)")
        logger.info(
            "   2. 🔧 CUDA Toolkit (https://developer.nvidia.com/cuda-downloads)"
        )
        logger.info("   3. 📚 cuDNN (https://developer.nvidia.com/cudnn)")
        logger.info("   4. 🐍 TensorFlow con soporte GPU")
        return False

    logger.info(f"✅ {len(gpu_devices)} GPU(s) encontrada(s):")

    for i, gpu in enumerate(gpu_devices):
        logger.info(f"   GPU {i}: {gpu}")

        # Obtener detalles de la GPU
        try:
            details = tf.config.experimental.get_device_details(gpu)
            if details:
                logger.info(
                    f"      Nombre: {details.get('device_name', 'Desconocido')}"
                )
                logger.info(
                    f"      Memoria: {details.get('compute_capability', 'Desconocida')}"
                )
        except Exception as e:
            logger.warning(f"      No se pudieron obtener detalles: {e}")

        # Configurar crecimiento de memoria
        try:
            tf.config.experimental.set_memory_growth(gpu, True)
            logger.info("      ✅ Crecimiento dinámico de memoria configurado")
        except Exception as e:
            logger.warning(f"      ⚠️ Error configurando memoria: {e}")

    # Test de funcionamiento
    logger.info("🧪 Ejecutando test de GPU...")
    try:
        with tf.device("/GPU:0"):
            # Crear tensores de prueba
            a = tf.constant([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]])
            b = tf.constant([[1.0, 2.0], [3.0, 4.0], [5.0, 6.0]])
            c = tf.matmul(a, b)

            logger.info("   ✅ Operación matricial exitosa en GPU")
            logger.info(f"   📊 Resultado: {c.shape} tensor")
            logger.info(f"   🎯 Dispositivo: {c.device}")

    except Exception as e:
        logger.error(f"   ❌ Error en test de GPU: {e}")
        return False

    # Test de entrenamiento simple
    logger.info("🧠 Test de entrenamiento en GPU...")
    try:
        with tf.device("/GPU:0"):
            # Crear un modelo simple
            model = tf.keras.Sequential(
                [
                    tf.keras.layers.Dense(10, activation="relu", input_shape=(5,)),
                    tf.keras.layers.Dense(1, activation="linear"),
                ]
            )

            model.compile(optimizer="adam", loss="mse")

            # Datos de prueba
            import numpy as np

            X_test = np.random.random((100, 5))
            y_test = np.random.random((100, 1))

            # Entrenar por una época
            history = model.fit(X_test, y_test, epochs=1, verbose=0)

            logger.info("   ✅ Entrenamiento de modelo simple exitoso en GPU")
            logger.info(f"   📈 Loss final: {history.history['loss'][0]:.4f}")

    except Exception as e:
        logger.error(f"   ❌ Error en test de entrenamiento: {e}")
        return False

    # Verificar memoria GPU
    logger.info("💾 Información de memoria GPU:")
    try:
        # Obtener información de memoria (si está disponible)
        gpus = tf.config.experimental.list_physical_devices("GPU")
        for gpu in gpus:
            memory_info = tf.config.experimental.get_memory_info(
                gpu.name.replace("/physical_device:", "")
            )
            if memory_info:
                current_mb = memory_info["current"] / (1024**2)
                peak_mb = memory_info["peak"] / (1024**2)
                logger.info(
                    f"   GPU: Memoria actual: {current_mb:.1f} MB, Pico: {peak_mb:.1f} MB"
                )
    except Exception as e:
        logger.info(f"   ℹ️ Información de memoria no disponible: {e}")

    logger.info("🎉 ¡GPU configurada correctamente para DQN!")
    logger.info("💡 El entrenamiento debería ser significativamente más rápido")

    return True


def verificar_dependencias() -> bool:
    """
    Verifica las dependencias necesarias para el entrenamiento.
    """
    logger.info("📦 Verificando dependencias adicionales...")

    dependencias = [
        ("numpy", "NumPy"),
        ("tensorflow", "TensorFlow"),
    ]

    missing = []
    for module, name in dependencias:
        try:
            __import__(module)
            logger.info(f"   ✅ {name}")
        except ImportError:
            logger.error(f"   ❌ {name}")
            missing.append(name)

    if missing:
        logger.error(f"❌ Dependencias faltantes: {', '.join(missing)}")
        return False

    logger.info("   ✅ Todas las dependencias están disponibles")
    return True


if __name__ == "__main__":
    logger.info("Iniciando verificación de GPU para entrenamiento DQN...")

    try:
        # Verificar dependencias
        deps_ok = verificar_dependencias()

        # Verificar GPU
        gpu_ok = verificar_gpu()

        if deps_ok and gpu_ok:
            logger.info(
                "🎯 RESUMEN: Sistema configurado correctamente para entrenamiento DQN en GPU"
            )
            logger.info("🚀 Puedes proceder con el entrenamiento usando GPU")
            sys.exit(0)
        else:
            logger.error("💥 Verificación de GPU fallida")
            sys.exit(1)

    except Exception as e:
        logger.error(f"❌ Error inesperado durante la verificación: {e}")
        sys.exit(1)
