import yaml
from pydantic import ValidationError

from src.traffic_system.core.config_exceptions import ConfigValidationError
from src.traffic_system.core.config_models import AppSettings


def load_app_settings(config_path: str = "config.yaml") -> AppSettings:
    """
    Carga y valida la configuración desde un archivo YAML.
    Lanza ConfigValidationError si hay un problema.
    """
    try:
        with open(config_path, "r") as f:
            config_data = yaml.safe_load(f)

        # ¡La magia de Pydantic! Parsea y valida el diccionario.
        # Si falta una clave, el tipo es incorrecto o hay un error, fallará aquí con un mensaje claro.
        settings = AppSettings(**config_data)
        return settings

    except FileNotFoundError:
        # Lanzamos nuestra excepción con un mensaje claro
        raise ConfigValidationError(
            f"Error: El archivo de configuración en la ruta '{config_path}' no fue encontrado."
        )

    except ValidationError as e:
        # Lanzamos nuestra excepción, pero con el mensaje formateado que ya creamos.
        raise ConfigValidationError(_format_pydantic_error(e))


def _format_pydantic_error(error: ValidationError) -> str:
    """Convierte un error de Pydantic en un mensaje legible para el usuario."""
    error_messages = [
        "El archivo 'config.yaml' tiene errores de formato o campos faltantes:"
    ]
    for err in error.errors():
        path = " -> ".join(map(str, err["loc"]))
        message = err["msg"]

        if err["type"] == "missing":
            mensaje_traducido = f"  - Falta el campo obligatorio: '{path}'."
        elif "type_error" in err["type"]:
            mensaje_traducido = f"  - El campo '{path}' tiene un tipo de dato incorrecto. ({message.capitalize()})"
        else:
            mensaje_traducido = f"  - Error en el campo '{path}': {message}."

        error_messages.append(mensaje_traducido)

    return "\n".join(error_messages)


# Opcional: puedes dejar una instancia global si quieres, pero es mejor inyectarla.
# app_settings = load_app_settings()
