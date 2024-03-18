import yaml

def cargar_configuracion(ruta_archivo:str):
    with open(ruta_archivo, 'r') as archivo:
        configuracion = yaml.safe_load(archivo)
    return configuracion

configuracion = cargar_configuracion('Deteccion/App/config.yaml')
