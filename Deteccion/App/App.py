from Notificador import Notificador
from Detector import Detector
from Video import Video
from Zona import Zona

import yaml, os
import numpy as np


class App:
    def __init__(self, modelo_nombre:str, zonas:list[Zona], notificar=False):
        
        self.detector = Detector(
            nombre_modelo=modelo_nombre, 
            notificador=Notificador(notificar)
        )
        self.zonas = zonas
    
    
    def analizar_carpeta_videos(self, origen:str, destino:str):
        print("Procesando videos...")
        i = 0
    
        #! Crear la carpeta de resultados si no existe
        if not os.path.exists(destino):
            os.makedirs(destino)

        #! Recorrer todas las carpetas en la carpeta de entrada
        for carpeta_video in os.listdir(origen):
            carpeta_video_ruta = os.path.join(origen, carpeta_video)

            #! Verificar si es una carpeta
            if os.path.isdir(carpeta_video_ruta):
                print(f"\nProcesando carpeta: {carpeta_video}")
                
                #! Crear la carpeta de salida espejo
                carpeta_salida_ruta = os.path.join(destino, carpeta_video)
                if not os.path.exists(carpeta_salida_ruta):
                    os.makedirs(carpeta_salida_ruta)

                #! Procesar todos los archivos en la carpeta de video
                for archivo_video in os.listdir(carpeta_video_ruta):
                    archivo_video_ruta_entrada = os.path.join(carpeta_video_ruta, archivo_video)
                    archivo_video_ruta_salida = os.path.join(carpeta_salida_ruta, archivo_video)

                    #! Verificar si es un archivo y tiene una extensión de video
                    if os.path.isfile(archivo_video_ruta_entrada) and archivo_video_ruta_entrada.lower().endswith(('.mp4', '.avi', '.mkv')):
                        
                        i += 1
                        
                        video = Video(
                            path_origen=archivo_video_ruta_entrada, 
                            path_resultado=archivo_video_ruta_salida,
                            zona=next((zona for zona in self.zonas if zona.nombre == carpeta_video), None),     #! Busca la clase correspondiente a la zona actual.
                        )
                        
                        print(f" -Video N°{i}: {archivo_video}")
                        self.detector.procesar_guardar(
                            video=video
                        )
                        print(f"  Videos procesado\n")
            # if i >= 1:
            #     break
            
        print(f"\nVideos procesados con éxito.")

    def vivo(self):
        """
        Ejecuta el modelo y realiza la detección de objetos en el video.
        """
        
        video = Video(
            path_origen="Pruebas/video-reescalado-576x1024-5fps.mp4",
            # path_origen="Pruebas/video-original.mp4",
            # path_origen="Pruebas/video-reescalado-720x1280-15fps.mp4",
            path_resultado=None,
            zona=next((zona for zona in self.zonas if zona.nombre == "FHD"), None),
        )
        
        print("Procesando video...")
        self.detector.procesar_vivo(
            guardar=False,
            video=video
        )
        print("Video procesado.")


if __name__ == "__main__":
    
    #! Definir modelo pre-entrenado a usar.
    modelo_nombre = "yolov8n.pt"

    #! Leer el archivo YAML de zonas.
    with open('zonas.yaml', 'r') as archivo:
        datos_yaml = yaml.safe_load(archivo)

    #! Lista de instancias de Zona.
    zonas = [Zona(zona['Nombre'], tuple(zona['Resolucion']), np.array(zona['Puntos'])) for zona in datos_yaml['Zonas']]

    app = App(
        modelo_nombre=modelo_nombre, 
        notificar=False, 
        zonas=zonas
    )   
    
    # app.analizar_carpeta_videos(
    #     origen="Dataset_reescalado-576x1024-5fps/", 
    #     destino="Resultados/",
    # )
    
    app.vivo()