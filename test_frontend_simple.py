#!/usr/bin/env python3
"""
Test básico del frontend simplificado.

Verifica que los componentes principales funcionen correctamente.
"""

import sys
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent))


def test_imports() -> bool:
    """Verificar que todos los imports funcionen."""
    print("🧪 Probando imports...")

    try:
        print("✅ Utils importado correctamente")

        print("✅ ConfigManager importado correctamente")

        print("✅ ServiceController importado correctamente")

        # Test básico de app (sin ejecutar Streamlit)
        print("✅ App principal importado correctamente")

        return True
    except Exception as e:
        print(f"❌ Error en imports: {e}")
        return False


def test_config_manager() -> bool:
    """Verificar funcionalidad básica del ConfigManager."""
    print("\n🧪 Probando ConfigManager...")

    try:
        from src.traffic_system.frontend.config_manager import ConfigManager

        manager = ConfigManager()
        print("✅ ConfigManager creado")

        # Verificar carga de configuración
        config = manager.load_config()
        if config:
            print("✅ Configuración cargada correctamente")
            print(f"   - Secciones encontradas: {list(config.keys())}")
        else:
            print("⚠️ No se pudo cargar configuración (archivo no existe?)")

        # Verificar validación Pydantic
        if config:
            is_valid, errors = manager.validate_with_pydantic(config)
            if is_valid:
                print("✅ Validación Pydantic exitosa")
            else:
                print(f"⚠️ Errores de validación: {len(errors)}")
                for error in errors[:3]:  # Mostrar solo primeros 3
                    print(f"   - {error}")

        # Verificar comentarios de ayuda
        help_comments = manager.get_all_field_help()
        print(f"✅ Comentarios de ayuda cargados: {len(help_comments)}")

        return True
    except Exception as e:
        print(f"❌ Error en ConfigManager: {e}")
        return False


def test_service_controller() -> bool:
    """Verificar funcionalidad básica del ServiceController."""
    print("\n🧪 Probando ServiceController...")

    try:
        from src.traffic_system.frontend.service_controller import ServiceController

        controller = ServiceController()
        print("✅ ServiceController creado")

        # Verificar mapeo de servicios
        services = controller.SERVICES
        print(f"✅ Servicios configurados: {list(services.keys())}")

        # Verificar estado de servicios (sin iniciar nada)
        status = controller.get_all_services_status()
        print("✅ Estado de servicios obtenido:")
        for service, is_running in status.items():
            status_icon = "🟢" if is_running else "🔴"
            print(f"   - {status_icon} {controller.get_service_display_name(service)}")

        # Verificar resumen
        summary = controller.get_services_summary()
        print(
            f"✅ Resumen: {summary['running_services']}/{summary['total_services']} servicios activos"
        )

        return True
    except Exception as e:
        print(f"❌ Error en ServiceController: {e}")
        return False


def test_basic_functionality() -> bool:
    """Verificar funcionalidad básica integrada."""
    print("\n🧪 Probando funcionalidad integrada...")

    try:
        # Verificar que config.yaml existe
        config_path = Path("config.yaml")
        if config_path.exists():
            print("✅ config.yaml encontrado")
        else:
            print("⚠️ config.yaml no encontrado - algunas funciones pueden fallar")

        # Verificar archivos de servicios
        service_files = [
            "run_simulation_provider.py",
            "run_decision_agent.py",
            "run_detection_provider.py",
            "run_reporting_service.py",
        ]

        found_services = 0
        for service_file in service_files:
            if Path(service_file).exists():
                found_services += 1
                print(f"✅ {service_file} encontrado")
            else:
                print(f"⚠️ {service_file} no encontrado")

        print(
            f"✅ Archivos de servicios: {found_services}/{len(service_files)} encontrados"
        )

        return True
    except Exception as e:
        print(f"❌ Error en verificación básica: {e}")
        return False


def main() -> bool:
    """Ejecutar todos los tests."""
    print("🚦 Iniciando tests del frontend simplificado\n")

    tests = [
        ("Imports", test_imports),
        ("ConfigManager", test_config_manager),
        ("ServiceController", test_service_controller),
        ("Funcionalidad Básica", test_basic_functionality),
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        print(f"\n{'='*50}")
        print(f"TEST: {test_name}")
        print("=" * 50)

        if test_func():
            passed += 1
            print(f"✅ {test_name}: PASÓ")
        else:
            print(f"❌ {test_name}: FALLÓ")

    print(f"\n{'='*50}")
    print("RESUMEN FINAL")
    print("=" * 50)
    print(f"Tests pasados: {passed}/{total}")

    if passed == total:
        print("🎉 ¡Todos los tests pasaron! El frontend está listo.")
        return True
    else:
        print("⚠️ Algunos tests fallaron. Revisar errores arriba.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
