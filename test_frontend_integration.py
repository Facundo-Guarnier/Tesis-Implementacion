#!/usr/bin/env python3
"""
Test de Integración del Frontend de Configuración

Verifica que el frontend se integre correctamente con:
- Sistema de configuración existente
- Validadores Pydantic
- Gestión de servicios
- Sistema de backups
"""

import logging
import os
import sys
import tempfile
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.absolute()))

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("FrontendIntegrationTest")


def test_imports() -> bool:
    """Test that all frontend modules can be imported."""
    logger.info("🧪 Probando importaciones del frontend...")

    try:
        # Core frontend modules
        from src.traffic_system.frontend.app import main
        from src.traffic_system.frontend.components.backup_manager import (
            render_advanced_backup_manager,
        )

        # Frontend components
        from src.traffic_system.frontend.components.config_editor import (
            render_advanced_config_editor,
        )
        from src.traffic_system.frontend.components.service_dashboard import (
            render_advanced_service_dashboard,
        )
        from src.traffic_system.frontend.utils.config_handler import ConfigHandler
        from src.traffic_system.frontend.utils.service_manager import ServiceManager
        from src.traffic_system.frontend.utils.validators import ConfigValidator

        logger.info("✅ Todas las importaciones exitosas")
        return True

    except ImportError as e:
        logger.error(f"❌ Error de importación: {e}")
        return False


def test_config_integration() -> bool:
    """Test integration with existing configuration system."""
    logger.info("🧪 Probando integración con sistema de configuración...")

    try:
        from src.traffic_system.frontend.utils.config_handler import ConfigHandler

        # Create temporary config for testing
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            test_config = """
services:
  port_simulation: 5000
  port_reporting: 5001

deteccion:
  modelo_yolo: "yolov8n.pt"
  confianza_minima: 0.5

decision:
  algoritmo: "DQN"
  epsilon: 0.1

sumo:
  gui: false
  step_length: 1.0

reporte:
  habilitado: true
  intervalo: 60
"""
            f.write(test_config)
            temp_config_path = f.name

        try:
            # Test config handler
            handler = ConfigHandler()
            handler.config_path = Path(temp_config_path)

            # Test loading
            config_data = handler.read_config()
            if not config_data:
                logger.error("❌ No se pudo cargar configuración de prueba")
                return False

            # Test basic config structure
            logger.info(f"✅ Configuración cargada: {len(config_data)} secciones")

            # Test saving
            config_data["test_field"] = "test_value"
            success = handler.write_config(config_data)
            if not success:
                logger.error("❌ No se pudo guardar configuración")
                return False

            logger.info("✅ Integración con configuración exitosa")
            return True

        finally:
            # Cleanup
            if os.path.exists(temp_config_path):
                os.unlink(temp_config_path)

    except Exception as e:
        logger.error(f"❌ Error en integración de configuración: {e}")
        return False


def test_validation_integration() -> bool:
    """Test integration with Pydantic validation system."""
    logger.info("🧪 Probando integración con sistema de validación...")

    try:
        from src.traffic_system.frontend.utils.validators import ConfigValidator

        validator = ConfigValidator()

        # Test valid configuration
        valid_config = {
            "services": {"port_simulation": 5000, "port_reporting": 5001},
            "deteccion": {"modelo_yolo": "yolov8n.pt", "confianza_minima": 0.5},
            "decision": {"algoritmo": "DQN", "epsilon": 0.1},
            "sumo": {"gui": False, "step_length": 1.0},
            "reporte": {"habilitado": True, "intervalo": 60},
        }

        is_valid, errors, _ = validator.validate_full_config(valid_config)
        if not is_valid:
            logger.error(f"❌ Configuración válida marcada como inválida: {errors}")
            return False

        # Test invalid configuration
        invalid_config = {
            "services": {
                "port_simulation": "invalid_port",  # Should be int
                "port_reporting": 5001,
            }
        }

        is_valid, errors, _ = validator.validate_full_config(invalid_config)
        if is_valid:
            logger.error("❌ Configuración inválida marcada como válida")
            return False

        logger.info("✅ Integración con validación exitosa")
        return True

    except Exception as e:
        logger.error(f"❌ Error en integración de validación: {e}")
        return False


def test_service_integration() -> bool:
    """Test integration with service management system."""
    logger.info("🧪 Probando integración con gestión de servicios...")

    try:
        from src.traffic_system.frontend.utils.service_manager import ServiceManager

        manager = ServiceManager()

        # Test service definitions
        if not manager.SERVICES:
            logger.error("❌ No hay servicios definidos")
            return False

        logger.info(f"✅ Servicios definidos: {list(manager.SERVICES.keys())}")

        # Test service status checking (should not fail even if services aren't running)
        for service_name in manager.SERVICES.keys():
            try:
                status = manager.get_service_status(service_name)
                logger.info(
                    f"   • {service_name}: {'🟢' if status.is_running else '🔴'}"
                )
            except Exception as e:
                logger.warning(f"   • {service_name}: Error obteniendo estado - {e}")

        # Test system resources
        try:
            resources = manager.get_system_resources()
            logger.info(
                f"✅ Recursos del sistema: CPU {resources['cpu_percent']:.1f}%, RAM {resources['memory_percent']:.1f}%"
            )
        except Exception as e:
            logger.warning(f"⚠️ No se pudieron obtener recursos del sistema: {e}")

        logger.info("✅ Integración con servicios exitosa")
        return True

    except Exception as e:
        logger.error(f"❌ Error en integración de servicios: {e}")
        return False


def test_backup_integration() -> bool:
    """Test integration with backup system."""
    logger.info("🧪 Probando integración con sistema de backups...")

    try:
        from src.traffic_system.frontend.utils.config_handler import ConfigHandler

        # Create temporary directories for testing
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            config_path = temp_path / "test_config.yaml"
            backup_dir = temp_path / "backups"
            backup_dir.mkdir()

            # Create test config
            with open(config_path, "w") as f:
                f.write(
                    """
services:
  port_simulation: 5000
deteccion:
  modelo_yolo: "yolov8n.pt"
"""
                )

            # Test backup functionality
            handler = ConfigHandler()
            handler.config_path = config_path
            handler.backup_dir = backup_dir

            # Create backup
            backup_path = handler.create_backup()
            if not backup_path:
                logger.error("❌ No se pudo crear backup")
                return False

            backup_filename = backup_path.name
            logger.info(f"✅ Backup creado: {backup_filename}")

            # List backups
            backups = handler.list_backups()
            if not backups:
                logger.error("❌ No se pudieron listar backups")
                return False

            logger.info(f"✅ Backups listados: {len(backups)} encontrados")

            # Test restore (modify config first)
            original_config = handler.read_config()
            modified_config = original_config.copy()
            modified_config["test_field"] = "modified"
            handler.write_config(modified_config)

            # Restore backup
            success = handler.restore_backup(backup_filename)
            if not success:
                logger.error("❌ No se pudo restaurar backup")
                return False

            # Verify restoration
            restored_config = handler.read_config()
            if "test_field" in restored_config:
                logger.error("❌ Backup no se restauró correctamente")
                return False

            logger.info("✅ Integración con backups exitosa")
            return True

    except Exception as e:
        logger.error(f"❌ Error en integración de backups: {e}")
        return False


def test_frontend_launcher() -> bool:
    """Test that the frontend launcher script works."""
    logger.info("🧪 Probando script de lanzamiento del frontend...")

    try:
        # Test that the launcher script can be imported and has required functions
        import run_frontend

        # Check that required functions exist
        required_functions = [
            "check_dependencies",
            "check_configuration",
            "setup_directories",
        ]
        for func_name in required_functions:
            if not hasattr(run_frontend, func_name):
                logger.error(f"❌ Función faltante en launcher: {func_name}")
                return False

        # Test dependency checking
        deps_ok = run_frontend.check_dependencies()
        if not deps_ok:
            logger.warning("⚠️ Algunas dependencias pueden estar faltando")
        else:
            logger.info("✅ Dependencias verificadas")

        # Test configuration checking
        config_ok = run_frontend.check_configuration()
        if not config_ok:
            logger.warning("⚠️ Problemas con configuración detectados")
        else:
            logger.info("✅ Configuración verificada")

        logger.info("✅ Script de lanzamiento funcional")
        return True

    except Exception as e:
        logger.error(f"❌ Error probando launcher: {e}")
        return False


def run_integration_tests() -> bool:
    """Run all integration tests."""
    logger.info("🚀 Iniciando tests de integración del frontend...")
    logger.info("=" * 60)

    tests = [
        ("Importaciones", test_imports),
        ("Integración de Configuración", test_config_integration),
        ("Integración de Validación", test_validation_integration),
        ("Integración de Servicios", test_service_integration),
        ("Integración de Backups", test_backup_integration),
        ("Script de Lanzamiento", test_frontend_launcher),
    ]

    results = []

    for test_name, test_func in tests:
        logger.info(f"\n🔍 Ejecutando: {test_name}")
        logger.info("-" * 40)

        try:
            result = test_func()
            results.append((test_name, result))

            if result:
                logger.info(f"✅ {test_name}: EXITOSO")
            else:
                logger.error(f"❌ {test_name}: FALLÓ")

        except Exception as e:
            logger.error(f"💥 {test_name}: ERROR CRÍTICO - {e}")
            results.append((test_name, False))

    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("📊 RESUMEN DE TESTS DE INTEGRACIÓN")
    logger.info("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ EXITOSO" if result else "❌ FALLÓ"
        logger.info(f"   {test_name}: {status}")

    logger.info("-" * 60)
    logger.info(
        f"📈 Resultado: {passed}/{total} tests exitosos ({passed/total*100:.1f}%)"
    )

    if passed == total:
        logger.info("🎉 ¡Todos los tests de integración pasaron!")
        logger.info("🚀 El frontend está listo para usar")
        return True
    else:
        logger.error(f"⚠️ {total - passed} tests fallaron")
        logger.error("🔧 Revisa los errores antes de usar el frontend")
        return False


if __name__ == "__main__":
    success = run_integration_tests()
    sys.exit(0 if success else 1)
