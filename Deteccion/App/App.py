import os

import numpy as np

from Deteccion.App.zonas.Zona import Zona
from Deteccion.App.zonas.ZonaList import ZonaList
from Deteccion.App.Detector import Detector
from Deteccion.App.Video import Video


class AppDetection:

    def __init__(self):
        
        self.detector = Detector()
        self.zonas = ZonaList()


    def analizar_carpeta_videos(self, origen:str, destino:str) -> None:
        """
        Procesa todos los videos en la carpeta de origen y guarda los resultados en la carpeta de destino.
        """
        print("Procesando videos...")
        i = 0
    
        #! Crear la carpeta de resultados si no existe
        if not os.path.exists(destino):
            os.makedirs(destino)

        try: 
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
                                zona=next((zona for zona in self.zonas.get() if zona.nombre == carpeta_video), self.zonas.get()[0]),     #! Busca la clase correspondiente a la zona actual, sino devuelve la primera zona (Default).
                            )
                            
                            print(f" -Video N°{i}: {archivo_video}")
                            self.detector.procesar_guardar(
                                video=video
                            )
                            print(f"  Videos procesado\n")
            
            print(f"\nVideos procesados con éxito.")
        
        except Exception as e:
            print(f"[ERROR Deteccion.App.App]: Error al procesar la carpeta: {origen} \n{e}")


    def analizar_un_video(self, path_video:str, guardar:bool=False) -> None:
        """
        Ejecuta el modelo y realiza la detección de objetos en el video mostrando el resultado en tiempo real.
        """
                
        video = Video(
            path_origen=path_video,
            zona=next((zona for zona in self.zonas.get() if zona.nombre == "Zona J"), self.zonas.get()[0]),
        )
        
        print("Procesando video...")
        self.detector.procesar_vivo(
            guardar=guardar,
            video=video
        )
        print("Video procesado.")
    
    
    def analizar_camara(self) -> None:
        """
        Ejecuta el modelo y realiza la detección de objetos en tiempo real.
        """
        
        video = Video(
            path_origen="",
            factor_escala=0.2,
            zona=next((zona for zona in self.zonas.get() if zona.nombre == "Camara"), self.zonas.get()[0]),
        )
        
        print("Procesando cámara...")
        self.detector.procesar_camara(video=video)
        print("Cámara procesada.")