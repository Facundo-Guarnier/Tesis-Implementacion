#!/usr/bin/env python3
"""
Sistema de Validación y Logging para el Frontend

Este script valida que todos los componentes críticos del frontend
estén funcionando correctamente y logs las validaciones.
"""

import logging
import sys
from pathlib import Path
from typing import Any

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class FrontendValidator:
    """Validador para el sistema frontend."""

    def __init__(self) -> None:
        """Inicializar el validador."""
        self.validation_errors: list[str] = []
        self.validation_warnings: list[str] = []

    def validate_session_state_integrity(self) -> bool:
        """
        Validar la integridad del session state.

        Returns:
            True si todo está correcto, False si hay problemas
        """
        logger.info("🔍 Validando integridad del session state...")

        try:
            import streamlit as st

            # Simular inicialización
            required_keys = [
                "config_handler",
                "service_manager",
                "validator",
                "current_config",
            ]

            missing_keys = []
            null_keys = []

            for key in required_keys:
                if key not in st.session_state:
                    missing_keys.append(key)
                    logger.error(f"❌ Missing session state key: {key}")
                elif st.session_state.get(key) is None:
                    null_keys.append(key)
                    logger.warning(f"⚠️ Session state key is None: {key}")

            if missing_keys:
                self.validation_errors.append(
                    f"Missing session state keys: {missing_keys}"
                )

            if null_keys:
                self.validation_warnings.append(f"Null session state keys: {null_keys}")

            return len(missing_keys) == 0

        except Exception as e:
            logger.error(f"❌ Error validating session state: {e}")
            self.validation_errors.append(f"Session state validation failed: {e}")
            return False

    def validate_configuration_integrity(self) -> bool:
        """
        Validar la integridad de la configuración.

        Returns:
            True si todo está correcto, False si hay problemas
        """
        logger.info("🔍 Validando integridad de la configuración...")

        try:
            from src.traffic_system.frontend.utils.config_handler import ConfigHandler

            config_handler = ConfigHandler()
            config = config_handler.read_config()

            # Validar que la configuración no esté vacía
            if not config:
                logger.error("❌ Configuration is empty or None")
                self.validation_errors.append("Configuration is empty")
                return False

            # Validar secciones críticas
            critical_sections = ["services", "deteccion", "decision", "sumo", "reporte"]
            missing_sections = []

            for section in critical_sections:
                if section not in config:
                    missing_sections.append(section)
                    logger.warning(f"⚠️ Missing configuration section: {section}")
                elif not config[section]:
                    logger.warning(f"⚠️ Empty configuration section: {section}")

            if missing_sections:
                self.validation_warnings.append(
                    f"Missing config sections: {missing_sections}"
                )

            # Validar puertos
            services_config = config.get("services", {})
            ports = []

            for key, value in services_config.items():
                if "port" in key and isinstance(value, int):
                    ports.append(value)
                    if not (1024 <= value <= 65535):
                        logger.error(f"❌ Invalid port range: {key}={value}")
                        self.validation_errors.append(f"Invalid port: {key}={value}")

            # Verificar puertos duplicados
            duplicate_ports = [port for port in set(ports) if ports.count(port) > 1]
            if duplicate_ports:
                logger.error(f"❌ Duplicate ports found: {duplicate_ports}")
                self.validation_errors.append(f"Duplicate ports: {duplicate_ports}")

            return len(self.validation_errors) == 0

        except Exception as e:
            logger.error(f"❌ Error validating configuration: {e}")
            self.validation_errors.append(f"Configuration validation failed: {e}")
            return False

    def validate_service_dependencies(self) -> bool:
        """
        Validar dependencias de servicios.

        Returns:
            True si todo está correcto, False si hay problemas
        """
        logger.info("🔍 Validando dependencias de servicios...")

        try:
            from src.traffic_system.frontend.utils.service_manager import ServiceManager

            service_manager = ServiceManager()

            # Validar configuración de servicios
            for service_name, service_config in service_manager.SERVICES.items():
                if not service_config:
                    logger.error(f"❌ Empty service config for: {service_name}")
                    self.validation_errors.append(
                        f"Empty service config: {service_name}"
                    )
                    continue

                # Validar campos requeridos
                required_fields = ["command", "port", "description"]
                missing_fields = []

                for field in required_fields:
                    if field not in service_config:
                        missing_fields.append(field)
                        logger.warning(
                            f"⚠️ Missing field '{field}' in service '{service_name}'"
                        )

                if missing_fields:
                    self.validation_warnings.append(
                        f"Service {service_name} missing fields: {missing_fields}"
                    )

                # Validar dependencias específicas
                if service_name == "detection":
                    try:
                        import importlib.util

                        cv2_spec = importlib.util.find_spec("cv2")
                        if cv2_spec is not None:
                            logger.info("✅ OpenCV dependency available")
                        else:
                            logger.warning(
                                "⚠️ OpenCV not available for detection service"
                            )
                            self.validation_warnings.append("OpenCV dependency missing")
                    except ImportError:
                        logger.warning("⚠️ OpenCV not available for detection service")
                        self.validation_warnings.append("OpenCV dependency missing")

                    try:
                        import importlib.util

                        ultralytics_spec = importlib.util.find_spec("ultralytics")
                        if ultralytics_spec is not None:
                            logger.info("✅ Ultralytics dependency available")
                        else:
                            logger.warning(
                                "⚠️ Ultralytics not available for detection service"
                            )
                            self.validation_warnings.append(
                                "Ultralytics dependency missing"
                            )
                    except ImportError:
                        logger.warning(
                            "⚠️ Ultralytics not available for detection service"
                        )
                        self.validation_warnings.append(
                            "Ultralytics dependency missing"
                        )

            return True

        except Exception as e:
            logger.error(f"❌ Error validating service dependencies: {e}")
            self.validation_errors.append(
                f"Service dependencies validation failed: {e}"
            )
            return False

    def validate_backup_system(self) -> bool:
        """
        Validar sistema de backups.

        Returns:
            True si todo está correcto, False si hay problemas
        """
        logger.info("🔍 Validando sistema de backups...")

        try:
            from src.traffic_system.frontend.utils.config_handler import ConfigHandler

            config_handler = ConfigHandler()
            backup_dir = config_handler.backup_dir

            # Verificar que el directorio de backups existe
            if not backup_dir.exists():
                logger.warning(f"⚠️ Backup directory does not exist: {backup_dir}")
                self.validation_warnings.append("Backup directory missing")

            # Verificar permisos de escritura
            try:
                test_file = backup_dir / "test_write_permissions.tmp"
                test_file.write_text("test")
                test_file.unlink()
                logger.info("✅ Backup directory writable")
            except Exception as e:
                logger.error(f"❌ Cannot write to backup directory: {e}")
                self.validation_errors.append("Backup directory not writable")
                return False

            # Validar backups existentes
            backups = config_handler.list_backups()

            invalid_backups = []
            for backup in backups:
                backup_path = Path(backup["path"])

                if not backup_path.exists():
                    invalid_backups.append(backup["filename"])
                    logger.warning(f"⚠️ Backup file missing: {backup['filename']}")
                elif backup_path.stat().st_size == 0:
                    invalid_backups.append(backup["filename"])
                    logger.warning(f"⚠️ Empty backup file: {backup['filename']}")

            if invalid_backups:
                self.validation_warnings.append(
                    f"Invalid backup files: {invalid_backups}"
                )

            return True

        except Exception as e:
            logger.error(f"❌ Error validating backup system: {e}")
            self.validation_errors.append(f"Backup system validation failed: {e}")
            return False

    def validate_performance_system(self) -> bool:
        """
        Validar sistema de performance.

        Returns:
            True si todo está correcto, False si hay problemas
        """
        logger.info("🔍 Validando sistema de performance...")

        try:
            from src.traffic_system.frontend.utils.performance import (
                get_performance_optimizer,
                get_session_manager,
                get_ui_optimizer,
            )

            # Verificar que los optimizadores se pueden inicializar
            try:
                get_performance_optimizer()
                logger.info("✅ Performance optimizer available")
            except Exception as e:
                logger.warning(f"⚠️ Performance optimizer failed: {e}")
                self.validation_warnings.append("Performance optimizer unavailable")

            try:
                get_session_manager()
                logger.info("✅ Session manager available")
            except Exception as e:
                logger.warning(f"⚠️ Session manager failed: {e}")
                self.validation_warnings.append("Session manager unavailable")

            try:
                get_ui_optimizer()
                logger.info("✅ UI optimizer available")
            except Exception as e:
                logger.warning(f"⚠️ UI optimizer failed: {e}")
                self.validation_warnings.append("UI optimizer unavailable")

            return True

        except ImportError:
            logger.warning("⚠️ Performance utilities not available")
            self.validation_warnings.append("Performance utilities not installed")
            return True  # No es crítico

        except Exception as e:
            logger.error(f"❌ Error validating performance system: {e}")
            self.validation_errors.append(f"Performance system validation failed: {e}")
            return False

    def run_full_validation(self) -> tuple[bool, dict[str, Any]]:
        """
        Ejecutar validación completa del frontend.

        Returns:
            Tuple de (success, report)
        """
        logger.info("🚀 Iniciando validación completa del frontend...")

        validations = [
            ("Configuration Integrity", self.validate_configuration_integrity),
            ("Service Dependencies", self.validate_service_dependencies),
            ("Backup System", self.validate_backup_system),
            ("Performance System", self.validate_performance_system),
        ]

        results = {}
        overall_success = True

        for name, validation_func in validations:
            logger.info(f"🔍 Running: {name}")
            try:
                success = validation_func()
                results[name] = {"success": success, "errors": [], "warnings": []}

                if not success:
                    overall_success = False
                    logger.error(f"❌ {name} validation failed")
                else:
                    logger.info(f"✅ {name} validation passed")

            except Exception as e:
                logger.error(f"❌ {name} validation crashed: {e}")
                results[name] = {"success": False, "errors": [str(e)], "warnings": []}
                overall_success = False

        # Generar reporte
        report = {
            "overall_success": overall_success,
            "total_errors": len(self.validation_errors),
            "total_warnings": len(self.validation_warnings),
            "all_errors": self.validation_errors,
            "all_warnings": self.validation_warnings,
            "validation_results": results,
            "recommendations": self._generate_recommendations(),
        }

        # Logging de resumen
        if overall_success:
            logger.info("✅ Frontend validation completed successfully")
            logger.info(
                f"📊 Summary: {len(self.validation_warnings)} warnings, {len(self.validation_errors)} errors"
            )
        else:
            logger.error("❌ Frontend validation failed")
            logger.error(
                f"📊 Summary: {len(self.validation_warnings)} warnings, {len(self.validation_errors)} errors"
            )

        return overall_success, report

    def _generate_recommendations(self) -> list[str]:
        """Generar recomendaciones basadas en los errores encontrados."""
        recommendations = []

        if "Configuration is empty" in str(self.validation_errors):
            recommendations.append(
                "Verificar que el archivo config.yaml existe y tiene contenido válido"
            )

        if "Backup directory not writable" in str(self.validation_errors):
            recommendations.append(
                "Verificar permisos de escritura en el directorio de backups"
            )

        if "OpenCV dependency missing" in str(self.validation_warnings):
            recommendations.append("Instalar OpenCV: poetry add opencv-python")

        if "Ultralytics dependency missing" in str(self.validation_warnings):
            recommendations.append("Instalar Ultralytics: poetry add ultralytics")

        if "Performance utilities not installed" in str(self.validation_warnings):
            recommendations.append(
                "Las utilidades de performance son opcionales pero recomendadas para mejor rendimiento"
            )

        return recommendations


def main() -> None:
    """Función principal para ejecutar validación."""
    logger.info("🚀 Iniciando validación del sistema frontend...")

    validator = FrontendValidator()
    success, report = validator.run_full_validation()

    # Mostrar resultado
    print("\n" + "=" * 60)
    print("📋 REPORTE DE VALIDACIÓN DEL FRONTEND")
    print("=" * 60)

    if success:
        print("✅ Estado: EXITOSO")
    else:
        print("❌ Estado: FALLÓ")

    print(f"📊 Errores: {report['total_errors']}")
    print(f"⚠️ Advertencias: {report['total_warnings']}")

    if report["all_errors"]:
        print("\n🚨 ERRORES ENCONTRADOS:")
        for error in report["all_errors"]:
            print(f"  • {error}")

    if report["all_warnings"]:
        print("\n⚠️ ADVERTENCIAS:")
        for warning in report["all_warnings"]:
            print(f"  • {warning}")

    if report["recommendations"]:
        print("\n💡 RECOMENDACIONES:")
        for rec in report["recommendations"]:
            print(f"  • {rec}")

    print("\n" + "=" * 60)

    # Exit code basado en el resultado
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
