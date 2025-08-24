"""
Configuration Handler for YAML Operations

Provides safe and atomic operations for reading, writing, and backing up
the config.yaml file with proper error handling and validation.
"""

import logging
import os
import shutil
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from src.traffic_system.core.config_models import AppSettings

logger = logging.getLogger(__name__)


class ConfigHandler:
    """Handles YAML configuration file operations with backup and validation."""

    def __init__(self, config_path: str = "config.yaml"):
        """
        Initialize the configuration handler.

        Args:
            config_path: Path to the configuration file
        """
        self.config_path = Path(config_path)
        self.backup_dir = Path("backups/config")
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def read_config(self) -> dict[str, Any]:
        """
        Read configuration from YAML file.

        Returns:
            Dictionary containing configuration data

        Raises:
            FileNotFoundError: If config file doesn't exist
            yaml.YAMLError: If YAML parsing fails
        """
        try:
            if not self.config_path.exists():
                raise FileNotFoundError(
                    f"Configuration file not found: {self.config_path}"
                )

            with open(self.config_path, encoding="utf-8") as file:
                config = yaml.safe_load(file)

            # Validate loaded configuration
            if config is None:
                logger.warning(
                    "⚠️ Configuration file is empty or contains only null values"
                )
                return {}
            elif not isinstance(config, dict):
                logger.error(f"❌ Configuration is not a dictionary: {type(config)}")
                return {}
            elif len(config) == 0:
                logger.warning("⚠️ Configuration dictionary is empty")

            logger.info(f"✅ Configuración cargada desde {self.config_path}")
            return config or {}

        except yaml.YAMLError as e:
            logger.error(f"❌ Error parsing YAML: {e}")
            raise
        except Exception as e:
            logger.error(f"❌ Error reading config file: {e}")
            raise

    def write_config(self, config: dict[str, Any], create_backup: bool = True) -> bool:
        """
        Write configuration to YAML file atomically.

        Args:
            config: Configuration dictionary to write
            create_backup: Whether to create backup before writing

        Returns:
            True if successful, False otherwise
        """
        try:
            # Create backup if requested and file exists
            if create_backup and self.config_path.exists():
                backup_path = self.create_backup()
                logger.info(f"📦 Backup creado: {backup_path}")

            # Write to temporary file first (atomic operation)
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                suffix=".yaml",
                dir=self.config_path.parent,
                delete=False,
            ) as temp_file:
                yaml.dump(
                    config,
                    temp_file,
                    default_flow_style=False,
                    allow_unicode=True,
                    sort_keys=False,
                    indent=2,
                )
                temp_path = temp_file.name

            # Atomic move to final location
            shutil.move(temp_path, self.config_path)

            logger.info(f"✅ Configuración guardada en {self.config_path}")
            return True

        except Exception as e:
            logger.error(f"❌ Error writing config file: {e}")
            # Clean up temp file if it exists
            if "temp_path" in locals() and os.path.exists(temp_path):
                os.unlink(temp_path)
            return False

    def create_backup(self, custom_name: str | None = None) -> Path:
        """
        Create a timestamped backup of the current configuration.

        Args:
            custom_name: Optional custom name for backup file

        Returns:
            Path to the created backup file

        Raises:
            FileNotFoundError: If source config file doesn't exist
        """
        if not self.config_path.exists():
            raise FileNotFoundError(
                f"Cannot backup non-existent file: {self.config_path}"
            )

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if custom_name:
            backup_filename = f"{custom_name}_{timestamp}.yaml"
        else:
            backup_filename = f"config_backup_{timestamp}.yaml"

        backup_path = self.backup_dir / backup_filename

        try:
            shutil.copy2(self.config_path, backup_path)
            logger.info(f"📦 Backup creado: {backup_path}")
            return backup_path

        except Exception as e:
            logger.error(f"❌ Error creating backup: {e}")
            raise

    def list_backups(self) -> list[dict[str, Any]]:
        """
        List all available backup files with metadata.

        Returns:
            List of dictionaries containing backup information
        """
        backups: list[dict[str, Any]] = []

        try:
            if not self.backup_dir.exists():
                return backups

            for backup_file in self.backup_dir.glob("*.yaml"):
                stat = backup_file.stat()
                backups.append(
                    {
                        "filename": backup_file.name,
                        "path": str(backup_file),
                        "size": stat.st_size,
                        "created": datetime.fromtimestamp(stat.st_ctime),
                        "modified": datetime.fromtimestamp(stat.st_mtime),
                    }
                )

            # Sort by creation time (newest first)
            backups.sort(key=lambda x: x["created"], reverse=True)

        except Exception as e:
            logger.error(f"❌ Error listing backups: {e}")

        return backups

    def restore_backup(self, backup_path: str | Path) -> bool:
        """
        Restore configuration from a backup file.

        Args:
            backup_path: Path to the backup file to restore

        Returns:
            True if successful, False otherwise
        """
        backup_path = Path(backup_path)

        try:
            if not backup_path.exists():
                logger.error(f"❌ Backup file not found: {backup_path}")
                return False

            # Validate backup file by trying to load it
            with open(backup_path, encoding="utf-8") as file:
                backup_config = yaml.safe_load(file)

            if backup_config is None:
                logger.error(f"❌ Backup file is empty or invalid: {backup_path}")
                return False

            # Create backup of current config before restoring
            if self.config_path.exists():
                current_backup = self.create_backup("pre_restore")
                logger.info(
                    f"📦 Backup actual creado antes de restaurar: {current_backup}"
                )

            # Copy backup to config location
            shutil.copy2(backup_path, self.config_path)

            logger.info(f"✅ Configuración restaurada desde: {backup_path}")
            return True

        except yaml.YAMLError as e:
            logger.error(f"❌ Invalid YAML in backup file: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Error restoring backup: {e}")
            return False

    def validate_config_structure(
        self, config: dict[str, Any]
    ) -> tuple[bool, list[str]]:
        """
        Basic validation of configuration structure.

        Args:
            config: Configuration dictionary to validate

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []

        # Check for required top-level sections
        required_sections = ["services", "deteccion", "decision", "sumo", "reporte"]

        for section in required_sections:
            if section not in config:
                errors.append(f"Missing required section: {section}")

        # Basic type checking for critical values
        if "services" in config:
            services = config["services"]
            for port_key in ["simulation_port", "detection_port", "reporting_port"]:
                if port_key in services:
                    if not isinstance(services[port_key], int):
                        errors.append(f"services.{port_key} must be an integer")
                    elif not (1024 <= services[port_key] <= 65535):
                        errors.append(
                            f"services.{port_key} must be between 1024 and 65535"
                        )

        # Check boolean flags
        boolean_paths = [
            ("deteccion", "detectar"),
            ("decision", "decision"),
            ("sumo", "simular"),
            ("reporte", "generar"),
        ]

        for section, key in boolean_paths:
            if section in config and key in config[section]:
                if not isinstance(config[section][key], bool):
                    errors.append(f"{section}.{key} must be a boolean")

        is_valid = len(errors) == 0
        return is_valid, errors

    def validate_config_with_pydantic(
        self, config: dict[str, Any]
    ) -> tuple[bool, list[str], AppSettings | None]:
        """
        Comprehensive validation using Pydantic models.

        Args:
            config: Configuration dictionary to validate

        Returns:
            Tuple of (is_valid, list_of_errors, validated_model_or_none)
        """
        try:
            # Attempt to create AppSettings model from config
            validated_config = AppSettings(**config)
            logger.info("✅ Configuración validada exitosamente con Pydantic")
            return True, [], validated_config

        except ValidationError as e:
            # Extract detailed error messages
            errors = []
            for error in e.errors():
                field_path = " -> ".join(str(loc) for loc in error["loc"])
                error_msg = error["msg"]
                error_type = error["type"]

                # Create user-friendly error message
                if field_path:
                    errors.append(
                        f"Campo '{field_path}': {error_msg} (tipo: {error_type})"
                    )
                else:
                    errors.append(
                        f"Error de validación: {error_msg} (tipo: {error_type})"
                    )

            logger.warning(
                f"⚠️ Errores de validación Pydantic: {len(errors)} errores encontrados"
            )
            return False, errors, None

        except Exception as e:
            logger.error(f"❌ Error inesperado durante validación Pydantic: {e}")
            return False, [f"Error inesperado: {str(e)}"], None

    def test_load_config(self, config: dict[str, Any]) -> tuple[bool, list[str]]:
        """
        Test-load configuration without saving to verify it's valid.

        Args:
            config: Configuration dictionary to test

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        try:
            # First, basic structure validation
            basic_valid, basic_errors = self.validate_config_structure(config)

            # Then, comprehensive Pydantic validation
            pydantic_valid, pydantic_errors, _ = self.validate_config_with_pydantic(
                config
            )

            # Combine results
            all_errors = basic_errors + pydantic_errors
            is_valid = basic_valid and pydantic_valid

            if is_valid:
                logger.info("✅ Test de configuración exitoso")
            else:
                logger.warning(
                    f"⚠️ Test de configuración falló: {len(all_errors)} errores"
                )

            return is_valid, all_errors

        except Exception as e:
            logger.error(f"❌ Error durante test de configuración: {e}")
            return False, [f"Error durante test: {str(e)}"]

    def validate_and_write_config(
        self, config: dict[str, Any], create_backup: bool = True
    ) -> tuple[bool, list[str]]:
        """
        Validate configuration before writing, with automatic rollback on failure.

        Args:
            config: Configuration dictionary to validate and write
            create_backup: Whether to create backup before writing

        Returns:
            Tuple of (success, list_of_errors)
        """
        try:
            # Step 1: Test-load configuration
            logger.info("🔍 Validando configuración antes de guardar...")
            is_valid, errors = self.test_load_config(config)

            if not is_valid:
                logger.error(
                    f"❌ Configuración inválida, no se guardará: {len(errors)} errores"
                )
                return False, errors

            # Step 2: Create backup if requested
            backup_path = None
            if create_backup and self.config_path.exists():
                backup_path = self.create_backup("pre_save")
                logger.info(f"📦 Backup de seguridad creado: {backup_path}")

            # Step 3: Write configuration
            success = self.write_config(
                config, create_backup=False
            )  # Backup already created

            if success:
                logger.info("✅ Configuración validada y guardada exitosamente")
                return True, []
            else:
                logger.error("❌ Error escribiendo configuración")
                return False, ["Error escribiendo archivo de configuración"]

        except Exception as e:
            logger.error(f"❌ Error durante validación y escritura: {e}")

            # Try to rollback if we have a backup
            if backup_path and backup_path.exists():
                logger.warning("🔄 Intentando restaurar backup de seguridad...")
                try:
                    shutil.copy2(backup_path, self.config_path)
                    logger.info("✅ Backup restaurado exitosamente")
                except Exception as rollback_error:
                    logger.error(f"❌ Error durante rollback: {rollback_error}")

            return False, [f"Error crítico: {str(e)}"]

    def format_validation_errors_for_ui(self, errors: list[str]) -> str:
        """
        Format validation errors for user-friendly display in UI.

        Args:
            errors: List of error messages

        Returns:
            Formatted error message string
        """
        if not errors:
            return ""

        formatted_lines = ["**Errores de Validación Encontrados:**", ""]

        for i, error in enumerate(errors, 1):
            # Add emoji based on error type
            if "missing" in error.lower() or "required" in error.lower():
                emoji = "❌"
            elif "must be" in error.lower() or "invalid" in error.lower():
                emoji = "⚠️"
            elif "path" in error.lower() or "file" in error.lower():
                emoji = "📁"
            else:
                emoji = "🔍"

            formatted_lines.append(f"{emoji} **Error {i}:** {error}")

        formatted_lines.extend(
            [
                "",
                "**Recomendaciones:**",
                "• Revisa los campos marcados con errores",
                "• Verifica que los tipos de datos sean correctos",
                "• Asegúrate de que todos los campos requeridos estén completos",
                "• Consulta la documentación si necesitas ayuda con algún campo",
            ]
        )

        return "\n".join(formatted_lines)

    def cleanup_old_backups(self, keep_count: int = 10) -> int:
        """
        Clean up old backup files, keeping only the most recent ones.

        Args:
            keep_count: Number of recent backups to keep

        Returns:
            Number of files deleted
        """
        try:
            backups = self.list_backups()

            if len(backups) <= keep_count:
                return 0

            # Delete oldest backups
            to_delete = backups[keep_count:]
            deleted_count = 0

            for backup in to_delete:
                try:
                    os.unlink(backup["path"])
                    deleted_count += 1
                    logger.info(f"🗑️ Backup eliminado: {backup['filename']}")
                except Exception as e:
                    logger.warning(
                        f"⚠️ No se pudo eliminar backup {backup['filename']}: {e}"
                    )

            logger.info(f"🧹 Limpieza completada: {deleted_count} backups eliminados")
            return deleted_count

        except Exception as e:
            logger.error(f"❌ Error during backup cleanup: {e}")
            return 0
