import os, signal, logging, inspect
from threading import Thread
from traci.exceptions import FatalTraCIError

from Decision.DQN.App import AppDecision

from Deteccion.App.App import AppDetection
from Deteccion.App.Api import ApiDeteccion

from SUMO.App import AppSUMO
from SUMO.Api import ApiSUMO



def cerrar(nro_senial:int, marco) -> None:
    logger = logging.getLogger(f' {__name__}.{inspect.currentframe().f_code.co_name}') # type: ignore
    logger.info("Finalizando el proceso ID:", os.getpid())
    os._exit(0)


#T* Deteccion
def run_app_deteccion() -> None:
    """
    Detección de vehículos.
    """
    app = AppDetection()
    
    #! Procesar todo el dataset
    # app.analizar_carpeta_videos(
    #     origen="Dataset/Dataset_reescalado-576x1024-5fps/", 
    #     destino="Resultados_deteccion/",
    # )
    
    #! Procesar un video específico del dataset
    app.analizar_un_video(
        guardar=True,
        # path_video="Dataset/Dataset_original/Zona J/20240102_133419.mp4"
        path_video="Dataset/Dataset_reescalado-576x1024-5fps/Zona J/20240102_133419.mp4"
        # path_video="Dataset/Dataset_reescalado-720x1280-15fps/Zona J/20240102_133419.mp4"
        # path_video="Dataset/Pruebas/video-reescalado-576x1024-5fps.mp4",
    )
    
    #! Deteccion con cámara
    # app.analizar_camara()

def run_api_deteccion() -> None:
    """
    API flask de detección.
    """
    api = ApiDeteccion(name="API Deteccion")
    api.run(debug=False) 


#T* SUMO
def run_app_sumo(gui: bool) -> None:
    """
    Simulación de tráfico con SUMO.
    """
    logger = logging.getLogger(f' {__name__}.{inspect.currentframe().f_code.co_name}') # type: ignore
    
    try:
        app = AppSUMO()
        app.setGUI(gui)
        app.iniciar()
    except FatalTraCIError as e:
        logger.error(" Error en la simulación de tráfico:", e)
        cerrar(0, 0)
        exit(1)


def run_api_sumo(gui) -> None:
    """
    API flask de SUMO.
    """
    api = ApiSUMO(name="API SUMO")
    api.run(debug=False) 


#T* Decision
def run_app_decision(entrenar=False) -> None:
    """
    Toma de decisiones.
    """
    app = AppDecision()
    if entrenar:
        app.entrenar(
            base_path="",
            num_epocas=15,
            batch_size=128,
            steps=10,
            memory=6000,

            #! Tasa de aprendizaje
            learning_rate=0.1,
            learning_rate_decay=0.9995,
            learning_rate_min=0.001,
            
            #! Exploración
            epsilon=1,
            epsilon_decay=0.9995,
            epsilon_min=0.01,
            
            #! Importancia futuras
            gamma=0.99,
            
            #! Red
            hidden_layers=[32, 32, 32],
        )
    else:
        # app.usar(path_modelo="Resultados_entrenamiento/DQN_2024-04-21_16-21/epoca_30.h5")    #! Si funciona: 665
        # app.usar(path_modelo="Resultados_entrenamiento/DQN_2024-04-21_19-55/epoca_18.h5")    #! No funciona: 1235
        # app.usar(path_modelo="Resultados_entrenamiento/DQN_2024-04-22_11-26/epoca_29.h5")    #! Si funciona: 772
        # app.usar(path_modelo="Resultados_entrenamiento-2/DQN_2024-05-02_15-33/epoca_14.h5")    #! Si funciona: 1322
        app.usar(path_modelo="Resultados_entrenamiento/DQN_2024-05-06_12-21/epoca_13.h5")    #! Si funciona: 1322


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    os.environ["SUMO_HOME"] = "/usr/share/sumo"
    signal.signal(signal.SIGINT, cerrar)
    
    #T* Deteccion 
    app = Thread(target=run_app_deteccion)
    app.start()
    run_api_deteccion()
    
    
    # #T* SUMO
    # gui = True
    # app = Thread(target=run_app_sumo, args=(gui,))
    # app.start()
    
    
    # # T* Decision
    # entrenar = False
    # app2 = Thread(target=run_app_decision, args=(entrenar,))
    # app2.start()
    
    # run_api_sumo(gui=gui)
    
    app.join()
    # app2.join()