"""
Gestor de configuración simplificado para config.yaml.

Maneja carga, guardado y validación de la configuración del sistema.
"""

import re
from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from src.traffic_system.core.config_models import AppSettings
from src.traffic_system.frontend.utils import (
    log_error,
    log_info,
    log_success,
    log_warning,
    set_nested_value,
)


class ConfigManager:
    """Gestor simplificado para la configuración del sistema."""

    def __init__(self, config_path: str = "config.yaml"):
        """
        Inicializar el gestor de configuración.

        Args:
            config_path: Ruta al archivo de configuración
        """
        self.config_path = Path(config_path)
        self._comments_cache: dict[str, str] = {}
        self._load_comments()

    def _create_default_config(self) -> dict[str, Any]:
        """
        Crear configuración por defecto.

        Returns:
            Diccionario con configuración por defecto
        """
        return {
            "services": {
                "simulation_port": 5000,
                "detection_port": 5000,
                "reporting_port": 5001,
                "remote": {
                    "decision": {
                        "ip": "10.10.1.2",
                        "port": 8080,
                    },
                    "reporting": {
                        "ip": "10.10.1.2",
                        "port": 8081,
                    },
                },
            },
            "deteccion": {
                "detectar": True,
                "model_path": "assets/yolo_models/yolov8n.pt",
                "confidence_threshold": 0.5,
            },
            "decision": {
                "decision": True,
                "model_path": "assets/dqn_models/",
                "training_enabled": False,
            },
            "sumo": {
                "simular": True,
                "gui": False,
                "step_length": 1.0,
                "map_path": "assets/sumo_maps/MapaDe0/mapa.sumocfg",
            },
            "reporte": {
                "generar": True,
                "output_dir": "results/reportes",
                "format": "json",
            },
        }

    def load_config(self) -> dict[str, Any]:
        """
        Cargar configuración desde config.yaml.

        Returns:
            Diccionario con la configuración cargada
        """
        try:
            if not self.config_path.exists():
                log_warning(
                    f"Archivo de configuración no encontrado: {self.config_path}"
                )
                # log_info("Creando configuración por defecto...")
                default_config = self._create_default_config()

                # Guardar configuración por defecto
                success, errors = self.save_config(default_config)
                if success:
                    # log_success("Configuración por defecto creada")
                    return default_config
                else:
                    log_error(f"Error creando configuración por defecto: {errors}")
                    return default_config

            with open(self.config_path, encoding="utf-8") as file:
                config = yaml.safe_load(file)

            if config is None or not config:
                log_warning("Archivo de configuración vacío, usando por defecto")
                default_config = self._create_default_config()

                # Guardar configuración por defecto
                success, errors = self.save_config(default_config)
                if success:
                    # log_success("Configuración por defecto guardada")
                    pass
                return default_config

            if not isinstance(config, dict):
                log_error(
                    "El archivo de configuración no contiene un diccionario válido"
                )
                return self._create_default_config()

            # Log de carga exitosa solo en nivel DEBUG para reducir spam
            # log_success(f"Configuración cargada desde {self.config_path}")
            return config

        except yaml.YAMLError as e:
            log_error(f"Error de formato YAML: {e}")
            return self._create_default_config()

        except Exception as e:
            log_error(f"Error inesperado cargando configuración: {e}")
            return self._create_default_config()

    def save_config(self, config: dict[str, Any]) -> tuple[bool, list[str]]:
        """
        Guardar configuración a config.yaml.

        Args:
            config: Diccionario de configuración a guardar

        Returns:
            Tupla (éxito, lista_de_errores)
        """
        try:
            # Crear backup del archivo actual
            backup_path = self.config_path.with_suffix(".yaml.backup")
            if self.config_path.exists():
                backup_path.write_text(
                    self.config_path.read_text(encoding="utf-8"), encoding="utf-8"
                )
                log_info(f"Backup creado: {backup_path}")

            # Guardar nueva configuración
            with open(self.config_path, "w", encoding="utf-8") as file:
                yaml.dump(
                    config,
                    file,
                    default_flow_style=False,
                    allow_unicode=True,
                    indent=2,
                    sort_keys=False,
                )

            log_success(f"Configuración guardada en {self.config_path}")
            return True, []

        except Exception as e:
            error_msg = f"Error guardando configuración: {e}"
            log_error(error_msg)

            # Intentar restaurar backup si existe
            backup_path = self.config_path.with_suffix(".yaml.backup")
            if backup_path.exists():
                try:
                    self.config_path.write_text(
                        backup_path.read_text(encoding="utf-8"), encoding="utf-8"
                    )
                    log_warning("Configuración restaurada desde backup")
                except Exception as restore_error:
                    log_error(f"Error restaurando backup: {restore_error}")

            return False, [error_msg]

    def _load_comments(self) -> None:
        """Cargar comentarios del archivo YAML para ayuda contextual."""
        try:
            if not self.config_path.exists():
                return

            with open(self.config_path, encoding="utf-8") as file:
                lines = file.readlines()

            current_path: list[str] = []

            for line in lines:
                line = line.rstrip()

                # Detectar nivel de indentación
                indent_level = (len(line) - len(line.lstrip())) // 2

                # Ajustar path actual según indentación
                current_path = current_path[:indent_level]

                # Extraer comentarios
                if "#" in line:
                    comment_match = re.search(r"#[!*]?\s*(.+)", line)
                    if comment_match:
                        comment = comment_match.group(1).strip()

                        # Extraer clave si existe en la línea
                        key_match = re.search(r"^(\s*)([^:#]+):", line)
                        if key_match:
                            key = key_match.group(2).strip()
                            current_path.append(key)
                            field_path = ".".join(current_path)
                            self._comments_cache[field_path] = comment
                            current_path.pop()  # Remover para próxima iteración

                # Actualizar path para claves sin comentarios
                elif ":" in line and not line.strip().startswith("#"):
                    key_match = re.search(r"^(\s*)([^:#]+):", line)
                    if key_match:
                        key = key_match.group(2).strip()
                        if indent_level < len(current_path):
                            current_path = current_path[:indent_level]
                        current_path.append(key)

            # Comentar para evitar spam de logs
            # if len(self._comments_cache) > 0:
            #     log_info(f"Cargados {len(self._comments_cache)} comentarios de ayuda")

        except Exception as e:
            log_warning(f"Error cargando comentarios: {e}")

    def get_field_help(self, field_path: str) -> str:
        """
        Obtener comentario de ayuda para un campo específico.

        Args:
            field_path: Ruta del campo (ej: 'services.simulation_port')

        Returns:
            Comentario de ayuda o cadena vacía si no existe
        """
        return self._comments_cache.get(field_path, "")

    def get_all_field_help(self) -> dict[str, str]:
        """
        Obtener todos los comentarios de ayuda disponibles.

        Returns:
            Diccionario con rutas de campos y sus comentarios
        """
        return self._comments_cache.copy()

    def validate_basic_types(self, config: dict[str, Any]) -> tuple[bool, list[str]]:
        """
        Validación básica de tipos de datos.

        Args:
            config: Configuración a validar

        Returns:
            Tupla (es_válido, lista_de_errores)
        """
        errors = []

        try:
            # Validaciones básicas de estructura
            required_sections = ["services", "deteccion", "decision", "sumo", "reporte"]

            for section in required_sections:
                if section not in config:
                    errors.append(f"Sección requerida faltante: {section}")

            # Validar tipos específicos conocidos
            if "services" in config:
                services = config["services"]
                for port_field in [
                    "simulation_port",
                    "detection_port",
                    "reporting_port",
                ]:
                    if port_field in services:
                        if not isinstance(services[port_field], int):
                            errors.append(
                                f"services.{port_field} debe ser un número entero"
                            )
                        elif not (1 <= services[port_field] <= 65535):
                            errors.append(
                                f"services.{port_field} debe estar entre 1 y 65535"
                            )

                # Validar servicios remotos
                if "remote" in services:
                    remote = services["remote"]
                    for service_name in ["decision", "reporting"]:
                        if service_name in remote:
                            service = remote[service_name]

                            # Validar IP
                            if "ip" in service:
                                ip_value = service["ip"]
                                if (
                                    not isinstance(ip_value, str)
                                    or not ip_value.strip()
                                ):
                                    errors.append(
                                        f"services.remote.{service_name}.ip debe ser una IP válida"
                                    )

                            # Validar puerto remoto
                            if "port" in service:
                                port_value = service["port"]
                                if not isinstance(port_value, int):
                                    errors.append(
                                        f"services.remote.{service_name}.port debe ser un número entero"
                                    )
                                elif not (1 <= port_value <= 65535):
                                    errors.append(
                                        f"services.remote.{service_name}.port debe estar entre 1 y 65535"
                                    )

            # Validar campos booleanos conocidos
            boolean_fields = [
                "deteccion.detectar",
                "decision.decision",
                "sumo.simular",
                "sumo.gui",
                "reporte.generar",
            ]

            for field_path in boolean_fields:
                value = self._get_nested_value(config, field_path)
                if value is not None and not isinstance(value, bool):
                    errors.append(f"{field_path} debe ser verdadero o falso")

            is_valid = len(errors) == 0

            # Solo log errores de validación, no éxitos (reduce spam)
            if not is_valid:
                log_warning(f"Validación básica falló con {len(errors)} errores")

            return is_valid, errors

        except Exception as e:
            error_msg = f"Error en validación básica: {e}"
            log_error(error_msg)
            return False, [error_msg]

    def _get_nested_value(self, config: dict[str, Any], field_path: str) -> Any:
        """Obtener valor anidado usando notación de puntos."""
        keys = field_path.split(".")
        current = config

        try:
            for key in keys:
                current = current[key]
            return current
        except (KeyError, TypeError):
            return None

    def validate_with_pydantic(self, config: dict[str, Any]) -> tuple[bool, list[str]]:
        """
        Validación completa usando AppSettings de Pydantic.

        Args:
            config: Configuración a validar

        Returns:
            Tupla (es_válido, lista_de_errores)
        """
        try:
            # Intentar crear instancia de AppSettings
            AppSettings(**config)
            # Solo log errores, no éxitos (reduce spam)
            # log_success("Validación Pydantic exitosa")
            return True, []

        except ValidationError as e:
            # Extraer errores específicos
            errors = []
            for error in e.errors():
                field_path = ".".join(str(loc) for loc in error["loc"])
                message = error["msg"]
                error_type = error.get("type", "unknown")

                # Formatear mensaje de error más amigable
                if error_type == "missing":
                    formatted_error = f"❌ {field_path}: Campo requerido faltante"
                elif error_type == "type_error":
                    formatted_error = f"❌ {field_path}: {message}"
                else:
                    formatted_error = f"❌ {field_path}: {message}"

                errors.append(formatted_error)

            log_warning(f"Validación Pydantic falló con {len(errors)} errores")
            return False, errors

        except Exception as e:
            error_msg = f"Error inesperado en validación Pydantic: {e}"
            log_error(error_msg)
            return False, [error_msg]

    def validate_field_change(
        self, field_path: str, new_value: Any, current_config: dict[str, Any]
    ) -> tuple[bool, str]:
        """
        Validar cambio de un campo individual en tiempo real.

        Args:
            field_path: Ruta del campo (ej: 'services.simulation_port')
            new_value: Nuevo valor a validar
            current_config: Configuración actual completa

        Returns:
            Tupla (es_válido, mensaje_de_error)
        """
        try:
            # Crear configuración temporal con el nuevo valor
            temp_config = current_config.copy()
            set_nested_value(temp_config, field_path, new_value)

            # Validar con Pydantic
            AppSettings(**temp_config)
            return True, "✅ Valor válido"

        except ValidationError as e:
            # Buscar error específico para este campo
            for error in e.errors():
                error_field_path = ".".join(str(loc) for loc in error["loc"])
                if field_path in error_field_path or error_field_path in field_path:
                    return False, f"❌ {error['msg']}"

            # Si no se encuentra error específico, devolver error genérico
            return False, "❌ Error de validación"

        except Exception as e:
            log_error(f"Error validando campo {field_path}: {e}")
            return False, f"❌ Error inesperado: {e}"

    def get_field_constraints(self, field_path: str) -> dict[str, Any]:
        """
        Obtener restricciones de validación para un campo específico.

        Args:
            field_path: Ruta del campo

        Returns:
            Diccionario con restricciones del campo
        """
        # Esta es una implementación básica
        # En una versión más avanzada se podría extraer info del modelo Pydantic
        constraints = {}

        # Restricciones conocidas para campos específicos
        if "port" in field_path:
            constraints = {
                "type": "integer",
                "minimum": 1,
                "maximum": 65535,
                "description": "Puerto de red válido",
            }
        elif (
            field_path.endswith(".detectar")
            or field_path.endswith(".decision")
            or field_path.endswith(".simular")
        ):
            constraints = {"type": "boolean", "description": "Verdadero o falso"}
        elif "ponderaciones_zonas" in field_path:
            constraints = {
                "type": "array",
                "items": "float",
                "length": 12,
                "description": "Lista de 12 valores decimales para zonas A-L",
            }

        return constraints

    def get_field_help_with_constraints(self, field_path: str) -> str:
        """
        Obtener ayuda completa para un campo incluyendo comentarios y restricciones.

        Args:
            field_path: Ruta del campo

        Returns:
            Texto de ayuda completo
        """
        help_text = self.get_field_help(field_path)
        constraints = self.get_field_constraints(field_path)

        if not help_text and not constraints:
            return ""

        result = []

        if help_text:
            result.append(help_text)

        if constraints:
            if constraints.get("type") == "integer":
                min_val = constraints.get("minimum")
                max_val = constraints.get("maximum")
                if min_val is not None and max_val is not None:
                    result.append(f"Rango: {min_val}-{max_val}")

            elif constraints.get("type") == "array":
                length = constraints.get("length")
                if length:
                    result.append(f"Requiere {length} elementos")

        return " | ".join(result)

    def reload_comments(self) -> None:
        """Recargar comentarios desde el archivo YAML."""
        self._comments_cache.clear()
        self._load_comments()
        # Solo log si es necesario (evitar spam en recargas)
        # log_info("Comentarios de ayuda recargados")
