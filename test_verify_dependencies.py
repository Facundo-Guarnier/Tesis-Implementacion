#!/usr/bin/env python3
"""
Script de verificación de dependencias multiplataforma.
Muestra cómo Poetry resuelve automáticamente las dependencias según el entorno.
"""

import logging
import platform
import subprocess
import sys
from typing import Any

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")
logger = logging.getLogger("VerificacionDependencias")


def get_system_info() -> dict[str, Any]:
    """Obtiene información del sistema actual."""
    return {
        "platform": platform.system(),
        "python_version": platform.python_version(),
        "python_version_info": sys.version_info,
        "architecture": platform.architecture()[0],
        "machine": platform.machine(),
    }


def check_tensorflow_installation() -> dict[str, Any]:
    """Verifica la instalación de TensorFlow."""
    try:
        import tensorflow as tf

        return {
            "installed": True,
            "version": tf.__version__,
            "gpu_available": tf.config.list_physical_devices("GPU"),
            "build_info": (
                tf.sysconfig.get_build_info()
                if hasattr(tf.sysconfig, "get_build_info")
                else "N/A"
            ),
        }
    except ImportError as e:
        return {"installed": False, "error": str(e)}


def get_poetry_info() -> dict[str, Any]:
    """Obtiene información sobre Poetry y las dependencias."""
    try:
        # Ejecutar poetry show para obtener las dependencias instaladas
        result = subprocess.run(
            ["poetry", "show", "--tree"], capture_output=True, text=True, timeout=30
        )

        return {
            "poetry_available": True,
            "dependencies_tree": (
                result.stdout if result.returncode == 0 else result.stderr
            ),
        }
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        return {"poetry_available": False, "error": str(e)}


def main():
    """Función principal de verificación."""
    logger.info("🔍 VERIFICACIÓN DE DEPENDENCIAS MULTIPLATAFORMA")
    logger.info("=" * 50)

    # Información del sistema
    system_info = get_system_info()
    logger.info("📊 INFORMACIÓN DEL SISTEMA:")
    logger.info(f"   Plataforma: {system_info['platform']}")
    logger.info(f"   Python: {system_info['python_version']}")
    logger.info(f"   Arquitectura: {system_info['architecture']}")
    logger.info(f"   Máquina: {system_info['machine']}")

    # Verificación de TensorFlow
    tf_info = check_tensorflow_installation()
    logger.info("🤖 TENSORFLOW:")
    if tf_info["installed"]:
        logger.info(f"   ✅ Instalado: v{tf_info['version']}")
        logger.info(
            f"   🎮 GPU disponible: {len(tf_info['gpu_available'])} dispositivos"
        )

        # Verificar configuración según plataforma
        if (
            system_info["platform"] == "Windows"
            and system_info["python_version_info"].minor == 11
        ):
            expected_version = "2.14.0"
            if tf_info["version"].startswith(expected_version):
                logger.info(
                    f"   ✅ Versión correcta para Windows + Python 3.11: {tf_info['version']}"
                )
            else:
                logger.warning(
                    f"   ⚠️  Versión inesperada. Esperada: {expected_version}, Actual: {tf_info['version']}"
                )

        elif (
            system_info["platform"] == "Linux"
            and system_info["python_version_info"].minor >= 12
        ):
            expected_version = "2.19.0"
            if tf_info["version"].startswith(expected_version):
                logger.info(
                    f"   ✅ Versión correcta para Linux + Python 3.12+: {tf_info['version']}"
                )
            else:
                logger.warning(
                    f"   ⚠️  Versión inesperada. Esperada: {expected_version}, Actual: {tf_info['version']}"
                )
        else:
            logger.info(
                "   ℹ️  Configuración no específicamente definida para esta combinación"
            )
    else:
        logger.error(f"   ❌ No instalado: {tf_info['error']}")

    # Información de Poetry
    poetry_info = get_poetry_info()
    logger.info("📦 POETRY:")
    if poetry_info["poetry_available"]:
        logger.info("   ✅ Poetry disponible")
        logger.info("   📋 Árbol de dependencias disponible")
    else:
        logger.error(f"   ❌ Poetry no disponible: {poetry_info['error']}")

    logger.info("🎯 RESUMEN:")
    logger.info(
        "   La configuración de environment markers en pyproject.toml permite que"
    )
    logger.info("   Poetry instale automáticamente las versiones correctas según:")
    logger.info("   • Windows + Python 3.11.x → TensorFlow 2.14.0 + dependencias Intel")
    logger.info("   • Linux + Python 3.12.x → TensorFlow 2.19.0")
    logger.info("   • Sin necesidad de scripts manuales o configuración adicional")


if __name__ == "__main__":
    main()
