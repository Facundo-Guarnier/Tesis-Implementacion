import os, signal, logging, inspect
from threading import Thread
from traci.exceptions import FatalTraCIError

from Decision.DQN.App import AppDecision

from Deteccion.App.App import AppDetection
from Deteccion.App.Api import ApiDeteccion

from SUMO.App import AppSUMO
from SUMO.Api import ApiSUMO

from config import configuracion


def cerrar(nro_senial:int, marco) -> None:
    logger = logging.getLogger(f' {__name__}.{inspect.currentframe().f_code.co_name}') # type: ignore
    logger.info("Finalizando el proceso ID:", os.getpid())
    os._exit(0)


#T* Deteccion
def run_app_deteccion() -> None:
    """
    Inicia la detección de vehículos con YOLO.
    """
    try: 
        app = AppDetection()
        
        #! Procesar toda la carpetas del dataset.
        if configuracion["deteccion"]["carpeta_dataset"]["procesar"]:
            app.analizar_carpeta_videos()
        
        #! Procesar un video específico del dataset.
        if configuracion["deteccion"]["un_video"]["procesar"]:
            app.analizar_un_video()
        
        #! Deteccion con cámara en vivo.
        if configuracion["deteccion"]["procesar_camara"]:
            app.analizar_camara()
    
    except Exception as e:
        print("Error:", e)
        cerrar(0, 0)


def run_api_deteccion() -> None:
    """
    Inicia la API de detección de vehículos.
    """
    api = ApiDeteccion(name="API Deteccion")
    api.run(debug=False) 


#T* SUMO
def run_app_sumo() -> None:
    """
    Simulación de tráfico con SUMO.
    """
    logger = logging.getLogger(f' {__name__}.{inspect.currentframe().f_code.co_name}') # type: ignore
    
    try:
        app = AppSUMO()
        app.iniciar()
    except FatalTraCIError as e:
        logger.error(" Error en la simulación de tráfico:", e)
        cerrar(0, 0)
        exit(1)


def run_api_sumo() -> None:
    """
    Inicia la API de SUMO.
    """
    api = ApiSUMO(name="API SUMO")
    api.run(debug=False) 


#T* Decision
def run_app_decision() -> None:
    """
    Inicial el modelo de toma de decisiones.
    Puede: 
    - Entrenar el modelo.
    - Utilizar un modelo ya entrenado.
    """
    app = AppDecision()
    if configuracion["decision"]["entrenamiento"]["entrenar"]:
        app.entrenar()
        cerrar(0, 0)
    
    else:
        app.usar()


#T* Reporte
def run_app_reporte() -> None:
    """
    Genera el reporte de la simulación.
    """
    from Reporte.App import AppReporte
    app = AppReporte()
    app.generar_reporte()

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    os.environ["SUMO_HOME"] = configuracion["sumo"]["path_sumo"]
    signal.signal(signal.SIGINT, cerrar)
    
    
    if configuracion["deteccion"]["detectar"]:
        app = Thread(target=run_app_deteccion)
        app.start()
        run_api_deteccion()
    
    
    if configuracion["sumo"]["simular"]:
        app = Thread(target=run_app_sumo)
        app.start()
    
    
    if configuracion["decision"]["decision"]:
        app2 = Thread(target=run_app_decision)
        app2.start()
    
    
    if configuracion["reporte"]["generar"]:
        reporte = Thread(target=run_app_reporte)
        reporte.start()
    
    
    #? Estos va siempre al final
    if configuracion["sumo"]["simular"]:
        run_api_sumo()
    
    app.join()
    if configuracion["decision"]["decision"]:
        app2.join()
    
    if configuracion["reporte"]["generar"]:
        reporte.join()