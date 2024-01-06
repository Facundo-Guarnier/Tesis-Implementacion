from Notificador import Notificador
from Detector import Detector
from Video import Video
from Zona import Zona

import yaml, os
import numpy as np


class App:
    def __init__(self, modelo_nombre, zonas, notificar:False):
        
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
    
    app.analizar_carpeta_videos(
        origen="Dataset_reescalado-576x1024-5fps/", 
        destino="Resultados/",
    )





#TODO:

# [ ] Usar el callback de Detector en la clase de detectar en Vivo.
# [ ] Ver si puedo detectar varios videos a la vez.

# [ ] Agregar try/except.
# [ ] ¿Es necesario guardar los videos en la carpeta Resultados?
# [ ] Ver si puedo estabilizar los videos.
# [ ] Reemplazar cv2.circle por sv.CircleAnnotator

# [x] Ver si puedo hacer que el detector sea en vivo.
# [x] Sistema de notificaciones (productor/consumidor) para que el detector pueda enviar la cantidad de vehículos mediante socket.
# [x] Hacer que devuelva la cantidad de vehículos en cada zona.
# [x] Agregar la detección en las distintas Zonas.
# [x] Cambiar tamaño fijo de letras y lineas por un factor de escala.
# [x] Borrar la linea de in/out

