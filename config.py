import yaml

def cargar_configuracion(ruta_archivo:str) ->  dict:
    """Cargar configuración desde un archivo YAML.

    Args:
        ruta_archivo (str): Ruta del archivo YAML.

    Returns:
        dict: Configuración. Ej: {'key': 'value'}
    """
    with open(ruta_archivo, 'r') as archivo:
        configuracion:dict = yaml.safe_load(archivo)
    return configuracion


configuracion = cargar_configuracion('config.yaml')