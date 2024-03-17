from App.Api import DetectorFlask
from App.App import App
import multiprocessing

def api():
    api = DetectorFlask(name="Nombre de la API")
    api.run(debug=True) 


def app():
    app = App()
    
    # app.analizar_carpeta_videos(
    #     origen="Dataset_reescalado-576x1024-5fps/", 
    #     destino="Resultados/",
    # )
    
    # app.analizar_un_video(
    #     guardar=True,
    #     # path_video="Dataset/Zona J/20240102_133419.mp4"
    #     path_video="Dataset_reescalado-576x1024-5fps/Zona J/20240102_133419.mp4"
    #     # path_video="Dataset_reescalado-720x1280-15fps/Zona J/20240102_133419.mp4"
    #     # path_video="Pruebas/video-reescalado-576x1024-5fps.mp4",
    # )


if __name__ == "__main__":
    multiprocessing.set_start_method('spawn')
    p1 = multiprocessing.Process(target=api)
    p2 = multiprocessing.Process(target=app)
    p1.start()
    p2.start()
    p1.join()
    p2.join()