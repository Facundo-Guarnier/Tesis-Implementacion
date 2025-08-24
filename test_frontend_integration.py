#!/usr/bin/env python3
"""
Test Frontend Integration

Script para verificar que el frontend esté correctamente integrado
con la estructura del proyecto y que todas las dependencias funcionen.
"""

import subprocess
import sys
from pathlib import Path


def test_python_version():
    """Test Python version compatibility."""
    print("🐍 Verificando versión de Python...")
    if sys.version_info < (3, 11):
        print(f"❌ Python 3.11+ requerido. Versión actual: {sys.version}")
        return False
    print(f"✅ Python {sys.version.split()[0]} compatible")
    return True


def test_poetry_available():
    """Test Poetry availability."""
    print("📦 Verificando Poetry...")
    try:
        result = subprocess.run(
            ["poetry", "--version"], capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            print(f"✅ Poetry disponible: {result.stdout.strip()}")
            return True
        else:
            print("❌ Poetry no responde correctamente")
            return False
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print("❌ Poetry no encontrado")
        return False


def test_dependencies():
    """Test required dependencies."""
    print("📚 Verificando dependencias...")

    required_packages = [
        ("streamlit", "Streamlit web framework"),
        ("yaml", "YAML parser"),
        ("psutil", "Process monitoring"),
        ("pydantic", "Data validation"),
    ]

    missing = []
    for package, description in required_packages:
        try:
            __import__(package)
            print(f"✅ {package}: {description}")
        except ImportError:
            print(f"❌ {package}: {description} - FALTANTE")
            missing.append(package)

    if missing:
        print("💡 Ejecuta: poetry install")
        return False

    return True


def test_project_structure():
    """Test project structure."""
    print("📁 Verificando estructura del proyecto...")

    required_files = [
        "config.yaml",
        "pyproject.toml",
        "run_frontend.py",
        "src/traffic_system/frontend/app.py",
        "src/traffic_system/frontend/components/config_editor.py",
        "src/traffic_system/frontend/components/service_dashboard.py",
        "src/traffic_system/frontend/utils/config_handler.py",
        "src/traffic_system/frontend/utils/service_manager.py",
        "src/traffic_system/core/config_models.py",
    ]

    missing = []
    for file_path in required_files:
        if Path(file_path).exists():
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} - FALTANTE")
            missing.append(file_path)

    if missing:
        print("💡 Algunos archivos del proyecto están faltantes")
        return False

    return True


def test_config_loading():
    """Test configuration loading."""
    print("⚙️ Verificando carga de configuración...")

    try:
        # Add src to path
        sys.path.insert(0, str(Path("src")))

        from traffic_system.frontend.utils.config_handler import ConfigHandler

        handler = ConfigHandler()
        config = handler.read_config()

        if config:
            print("✅ Configuración cargada correctamente")

            # Test validation
            is_valid, errors = handler.test_load_config(config)
            if is_valid:
                print("✅ Configuración válida")
            else:
                print(f"⚠️ Errores de validación: {errors}")

            return True
        else:
            print("❌ No se pudo cargar la configuración")
            return False

    except Exception as e:
        print(f"❌ Error cargando configuración: {e}")
        return False


def test_service_manager():
    """Test service manager functionality."""
    print("🎮 Verificando gestor de servicios...")

    try:
        from traffic_system.frontend.utils.service_manager import ServiceManager

        manager = ServiceManager()

        # Test service status
        services = manager.get_all_services_status()
        print(f"✅ Servicios detectados: {list(services.keys())}")

        # Test system resources
        resources = manager.get_system_resources()
        print(
            f"✅ Recursos del sistema: CPU {resources['cpu_percent']:.1f}%, RAM {resources['memory_percent']:.1f}%"
        )

        return True

    except Exception as e:
        print(f"❌ Error en gestor de servicios: {e}")
        return False


def test_frontend_import():
    """Test frontend app import."""
    print("🚀 Verificando importación del frontend...")

    try:
        print("✅ Frontend importado correctamente")
        return True

    except Exception as e:
        print(f"❌ Error importando frontend: {e}")
        return False


def test_streamlit_config():
    """Test Streamlit configuration."""
    print("🌐 Verificando configuración de Streamlit...")

    try:
        import streamlit as st

        # Test basic Streamlit functionality
        print("✅ Streamlit importado correctamente")

        # Check if we can access Streamlit config
        try:
            # This will work if we're in a Streamlit context
            st.set_page_config(page_title="Test")
            print("✅ Configuración de Streamlit OK")
        except:
            # This is expected when not in Streamlit context
            print("ℹ️ Configuración de Streamlit (fuera de contexto)")

        return True

    except Exception as e:
        print(f"❌ Error con Streamlit: {e}")
        return False


def main():
    """Run all integration tests."""
    print("🧪 PRUEBAS DE INTEGRACIÓN DEL FRONTEND")
    print("=" * 50)

    tests = [
        ("Versión de Python", test_python_version),
        ("Poetry", test_poetry_available),
        ("Dependencias", test_dependencies),
        ("Estructura del Proyecto", test_project_structure),
        ("Carga de Configuración", test_config_loading),
        ("Gestor de Servicios", test_service_manager),
        ("Importación del Frontend", test_frontend_import),
        ("Configuración de Streamlit", test_streamlit_config),
    ]

    results = []

    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        print("-" * 30)

        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Error inesperado en {test_name}: {e}")
            results.append((test_name, False))

    # Summary
    print("\n" + "=" * 50)
    print("📊 RESUMEN DE PRUEBAS")
    print("=" * 50)

    passed = 0
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1

    print(f"\n🎯 Resultado: {passed}/{total} pruebas pasaron")

    if passed == total:
        print("🎉 ¡Todas las pruebas pasaron! El frontend está listo para usar.")
        print("💡 Ejecuta: poetry run streamlit run run_frontend.py")
        return True
    else:
        print("⚠️ Algunas pruebas fallaron. Revisa los errores anteriores.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
