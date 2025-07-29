#!/usr/bin/env python3
"""
Script de configuración para ejecutar el DQN Simplificado con Poetry.

Este script verifica dependencias y configura el entorno para ejecutar
el entrenador DQN simplificado correctamente.
"""

import subprocess
import sys
import os
from pathlib import Path


def check_poetry_installed():
    """Verifica si poetry está instalado."""
    try:
        result = subprocess.run(['poetry', '--version'],
                              capture_output=True, text=True, check=True)
        print(f"✅ Poetry instalado: {result.stdout.strip()}")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Poetry no está instalado")
        print("📝 Instala Poetry desde: https://python-poetry.org/docs/#installation")
        return False


def check_dependencies():
    """Verifica que las dependencias estén instaladas."""
    try:
        result = subprocess.run(['poetry', 'check'],
                              capture_output=True, text=True, check=True)
        print("✅ Dependencias verificadas correctamente")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error verificando dependencias: {e.stderr}")
        return False


def install_dependencies():
    """Instala las dependencias con poetry."""
    print("📦 Instalando dependencias...")
    try:
        result = subprocess.run(['poetry', 'install'],
                              check=True, text=True)
        print("✅ Dependencias instaladas exitosamente")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error instalando dependencias: {e}")
        return False


def check_config_file():
    """Verifica que el archivo de configuración exista."""
    config_path = Path("config.yaml")
    if config_path.exists():
        print("✅ Archivo config.yaml encontrado")
        return True
    else:
        print("❌ Archivo config.yaml no encontrado")
        print("📝 Asegúrate de tener el archivo config.yaml en el directorio raíz")
        return False


def check_tensorflow_gpu():
    """Verifica la configuración de TensorFlow y GPU."""
    try:
        # Ejecutar en el entorno de poetry
        result = subprocess.run([
            'poetry', 'run', 'python', '-c',
            'import tensorflow as tf; print(f"TensorFlow: {tf.__version__}"); '
            'print(f"GPU disponible: {len(tf.config.experimental.list_physical_devices(\"GPU\")) > 0}")'
        ], capture_output=True, text=True, check=True)

        print("✅ TensorFlow verificado:")
        for line in result.stdout.strip().split('\n'):
            print(f"   {line}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error verificando TensorFlow: {e.stderr}")
        return False


def run_simplified_training():
    """Ejecuta el entrenamiento simplificado."""
    print("\n🚀 Ejecutando entrenamiento DQN simplificado...")
    print("📝 Comando: poetry run python run_decision_agent.py")
    print("⏹️ Para detener: Ctrl+C")

    try:
        # Ejecutar con poetry
        subprocess.run(['poetry', 'run', 'python', 'run_decision_agent.py'],
                      check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Error ejecutando entrenamiento: {e}")
        return False
    except KeyboardInterrupt:
        print("\n⏹️ Entrenamiento detenido por el usuario")
        return True

    return True


def main():
    """Función principal del script de configuración."""
    print("🔧 === CONFIGURACIÓN DQN SIMPLIFICADO ===\n")

    # Verificaciones preliminares
    checks = [
        ("Poetry", check_poetry_installed),
        ("Archivo de configuración", check_config_file),
        ("Dependencias", check_dependencies),
        ("TensorFlow", check_tensorflow_gpu),
    ]

    failed_checks = []
    for check_name, check_func in checks:
        print(f"\n📋 Verificando {check_name}...")
        if not check_func():
            failed_checks.append(check_name)

    if failed_checks:
        print(f"\n❌ Verificaciones fallidas: {', '.join(failed_checks)}")
        print("\n🔧 Intentando reparación automática...")

        # Intentar instalar dependencias si falló esa verificación
        if "Dependencias" in failed_checks:
            if not install_dependencies():
                print("❌ No se pudieron instalar las dependencias automáticamente")
                return 1

        # Verificar nuevamente TensorFlow después de instalar
        if "TensorFlow" in failed_checks:
            print("\n📋 Verificando TensorFlow nuevamente...")
            if not check_tensorflow_gpu():
                print("⚠️ TensorFlow puede tener problemas, pero continuaremos")

    print("\n✅ === CONFIGURACIÓN COMPLETADA ===")

    # Preguntar si ejecutar entrenamiento
    print("\n🎯 Configuración lista para ejecutar el DQN simplificado")
    print("\n📋 Características del entrenador simplificado:")
    print("   • Solo epsilon-greedy (sin noisy networks)")
    print("   • Learning rate fijo: 0.0001")
    print("   • Arquitectura: [256, 256]")
    print("   • Double DQN + Dueling DQN")
    print("   • Sin PER, sin batch norm, sin dropout")

    response = input("\n¿Ejecutar entrenamiento ahora? (y/N): ").lower().strip()

    if response in ['y', 'yes', 'sí', 's']:
        return 0 if run_simplified_training() else 1
    else:
        print("\n📝 Para ejecutar manualmente:")
        print("   poetry run python run_decision_agent.py")
        print("\n📊 Los resultados se guardarán en:")
        print("   results/training/SimplifiedDQN_YYYY-MM-DD_HH-MM/")
        return 0


if __name__ == "__main__":
    sys.exit(main())
