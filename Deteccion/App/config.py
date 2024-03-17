import yaml

def cargar_configuracion(ruta_archivo):
    with open(ruta_archivo, 'r') as archivo:
        configuracion = yaml.safe_load(archivo)
    return configuracion

configuracion = cargar_configuracion('App/config.yaml')
