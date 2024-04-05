import os, signal

from Deteccion.App.Api import DetectorFlask
from Deteccion.App.App import App as AppD
from SUMO.App import App as AppS
from SUMO.Api import SumoFlask
from threading import Thread


def señal(nro_senial:int, marco) -> None:
    print("Finalizando el proceso ID:", os.getpid())
    os._exit(0)


def run_app_deteccion() -> None:
    """
    Detección de vehículos.
    """
    app = AppD()
    
    #! Procesar todo el dataset
    # app.analizar_carpeta_videos(
    #     origen="Deteccion/Dataset/Dataset_reescalado-576x1024-5fps/", 
    #     destino="Resultados/",
    # )
    
    #! Procesar un video específico del dataset
    app.analizar_un_video(
        guardar=True,
        # path_video="Deteccion/Dataset/Dataset_original/Zona J/20240102_133419.mp4"
        path_video="Deteccion/Dataset/Dataset_reescalado-576x1024-5fps/Zona J/20240102_133419.mp4"
        # path_video="Deteccion/Dataset/Dataset_reescalado-720x1280-15fps/Zona J/20240102_133419.mp4"
        # path_video="Deteccion/Dataset/Pruebas/video-reescalado-576x1024-5fps.mp4",
    )


def run_flask_deteccion() -> None:
    """
    API flask de detección.
    """
    api = DetectorFlask(name="API Deteccion")
    api.run(debug=False) 


def run_app_sumo() -> None:
    """
    Simulación de tráfico con SUMO.
    """
    app = AppS()
    app.iniciar_simulacion()


def run_flask_sumo() -> None:
    """
    API flask de SUMO.
    """
    api = SumoFlask(name="API SUMO")
    api.run(debug=False) 


if __name__ == "__main__":
    
    signal.signal(signal.SIGINT, señal)
    
    #T* Deteccion 
    app_thread = Thread(target=run_app_deteccion)
    app_thread.start()
    run_flask_deteccion()


    #T* SUMO
    # app_thread = Thread(target=run_app_sumo)
    # app_thread.start()
    # run_flask_sumo()
    
    app_thread.join()