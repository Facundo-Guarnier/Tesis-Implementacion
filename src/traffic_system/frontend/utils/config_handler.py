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
