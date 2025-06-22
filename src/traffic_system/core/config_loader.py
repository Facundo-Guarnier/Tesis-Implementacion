import yaml


def load_configuration(ruta_archivo: str) -> dict:
    """Cargar configuración desde un archivo YAML.

    Args:
        ruta_archivo (str): Ruta del archivo YAML.

    Returns:
        dict: Configuración. Ej: {'key': 'value'}
    """
    with open(ruta_archivo, "r") as archivo:
        return yaml.safe_load(archivo)


app_settings = load_configuration("config.yaml")
