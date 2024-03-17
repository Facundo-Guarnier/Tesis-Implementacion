from App.Detector import Detector
from App.Video import Video
from App.zonas.Zona import Zona

import os

from App.zonas.ZonaList import ZonaList


class App:

    def __init__(self):
        
        self.detector = Detector()


    def analizar_carpeta_videos(self, origen:str, destino:str):
        """
        Procesa todos los videos en la carpeta de origen y guarda los resultados en la carpeta de destino.
        """
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
            
        print(f"\nVideos procesados con éxito.")


    def analizar_un_video(self, path_video:str, guardar:bool=False):
        """
        Ejecuta el modelo y realiza la detección de objetos en el video mostrando el resultado en tiempo real.
        """
        zonas = ZonaList()
        
        video = Video(
            path_origen=path_video,
            path_resultado=None,
            zona=next((zona for zona in zonas.get_zonas() if zona.nombre == "Zona J"), None),
        )
        
        print("Procesando video...")
        self.detector.procesar_vivo(
            guardar=guardar,
            video=video
        )
        print("Video procesado.")