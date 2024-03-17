import time, os, signal
from App.Api import DetectorFlask
from App.App import App

from threading import Thread

#! API flask
def run_flask():
    api = DetectorFlask(name="Nombre de la API")
    api.run(debug=False) 

#! Deteccionde vehiculos
def run_app():
    app = App()
    
    # app.analizar_carpeta_videos(
    #     origen="Dataset_reescalado-576x1024-5fps/", 
    #     destino="Resultados/",
    # )
    
    app.analizar_un_video(
        guardar=True,
        # path_video="Dataset/Zona J/20240102_133419.mp4"
        path_video="Dataset/Dataset_reescalado-576x1024-5fps/Zona J/20240102_133419.mp4"
        # path_video="Dataset_reescalado-720x1280-15fps/Zona J/20240102_133419.mp4"
        # path_video="Pruebas/video-reescalado-576x1024-5fps.mp4",
    )


def señal(nro_senial, marco):
    print("Finalizando el proceso ID:", os.getpid())
    os._exit(0)


if __name__ == "__main__":
    signal.signal(signal.SIGINT, señal)
    
    app_thread = Thread(target=run_app)
    app_thread.start()

    run_flask()
    
    app_thread.join()
