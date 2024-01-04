import os, time, cv2
from Zona import Zona
import matplotlib.path as mplPath
import ultralytics as ul
import supervision as sv
import numpy as np

class Detector:
    def __init__(self, nombre_modelo, clases_seleccionadas, notificar):
        
        self.definir_modelo(nombre_modelo, clases_seleccionadas)
        self.definir_paths()

        self.resolucion_video_actual = None
        self.factor_escala_actual = None
        self.zona_actual = None
        self.notificar = notificar


    def definir_modelo(self, nombre_modelo, clases_seleccionadas):
        """
        - Cargar modelo pre-entrenado YOLOv8.
        - Definir las clases que se van a detectar.
        """
        self.modelo = ul.YOLO(f"Modelos/{nombre_modelo}")
        self.CLASES  = self.modelo.model.names
        self.CLASES_SELECCIONADAS = clases_seleccionadas


    def definir_paths(self):
        """
        """
        self.PATH_CARPETA_ORIGEN_VIDEOS = "Dataset_reescalado/"
        self.PATH_CARPETA_RESULTADO_VIDEOS = "Resultados/"


    def definir_parametros_supervision(self):
        """
        Define los parámetros de supervisión necesario para la edición de los frames en base a la resolución del video.
        """
        
        #! Instancia de ByteTracker, proporciona el seguimiento de los objetos.
        self.byte_tracker = sv.ByteTrack(track_thresh=0.25, track_buffer=30, match_thresh=0.8, frame_rate=30)

        #! Dibujar box en los objetos
        self.box_annotator = sv.BoxAnnotator(
            thickness=max(1, int(4 * self.factor_escala_actual)), 
            text_thickness=max(1, int(3 * self.factor_escala_actual)), 
            text_scale=max(1, int(2 * self.factor_escala_actual)),
        )

        #! Dibujar Trace (el recorrido) de un objeto
        self.trace_annotator = sv.TraceAnnotator(
            thickness=max(1, int(4 * self.factor_escala_actual)), 
            trace_length=max(1, int(50 * self.factor_escala_actual)),
        )

        #! Dibujar círculos en los objetos
        # self.circle_annotator = sv.CircleAnnotator(thickness=4)

        #! Polígono (sv) de detección
        self.poligono_zona = sv.PolygonZone(
            polygon=self.zona_actual.puntos_reescalados, 
            frame_resolution_wh=self.resolucion_video_actual
        )

        #! Dibujar polígono (sv)
        self.poligono_dibujado = sv.PolygonZoneAnnotator(
            zone=self.poligono_zona,
            color=sv.Color(255,0,0),
            thickness=max(1, int(4 * self.factor_escala_actual)),
            text_scale=max(1, int(2 * self.factor_escala_actual)),
            text_thickness=max(1, int(4 * self.factor_escala_actual)),
        )


    def obtener_resolucion(self, video_path):
        cap = cv2.VideoCapture(video_path)
        ancho = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        alto = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        cap.release()
        return ((ancho, alto))


    def calcular_factor_escala(self):
        """
        Escala los distintos elementos (letras y lineas) en base a la resolución del video.
        Lo elementos fueron diseñados para una resolución de 1080x1920.
        """
        ancho_original, alto_original = (1080, 1920)
        ancho_actual, alto_actual, = self.resolucion_video_actual 
        return ancho_actual / ancho_original


    def poligono_cv2(self, frame, detections):
        """
        - Dibuja el centro de los objetos y el polígono de detección. 
        - Cuenta los objetos que están dentro del polígono.
        """


        #! Dibujar el polígono de detección
        cv2.polylines(
            img=frame, 
            pts=[self.zona_actual.puntos_reescalados], 
            isClosed=True, 
            color=(0,0,255),  
            thickness=max(1, int(10 * self.factor_escala_actual)),
        )

        detecciones_poligono = 0
        for box in detections.xyxy:
            #! Centros
            #  xmin, ymin, xmax, ymax
            #   0     1     2     3
            x = int((box[0] + box[2])//2)
            y = int((box[1] + box[3])//2)

            #! Validar el punto dentro del poligono
            color = ""  # BGR
            if mplPath.Path(self.zona_actual.puntos_reescalados).contains_point((x,y)):
                detecciones_poligono += 1
                color = [255,80,0]

            else:
                color = [0,0,255]

            cv2.circle(
                img=frame, 
                center=(x,y), 
                radius=max(1, int(10 * self.factor_escala_actual)), 
                color=color, 
                thickness=max(1, int(10 * self.factor_escala_actual))
            )
            
        cv2.putText(
            img=frame, 
            text=f"Vehiculos {detecciones_poligono}", 
            org=(
                max(1, int(250 * self.factor_escala_actual)), 
                max(1, int(1800 * self.factor_escala_actual))
            ), 
            fontFace=cv2.FONT_HERSHEY_PLAIN, 
            fontScale=max(1, int(6 * self.factor_escala_actual)), 
            color=(50,50,200), 
            thickness=max(1, int(6 * self.factor_escala_actual)),
        )
        

        return frame


    def poligono_sv(self, frame, detections):
        """
        - Dibuja el centro de los objetos y el poligono de detección. 
        - Tiene el problema de que no cuenta bien los objetos dentro del poligono, no
        se si es porque cuenta cuando la box está completa dentro del poligono o si
        es por otro motivo.
        """
        detecciones = self.poligono_zona.trigger(detections)
        return self.poligono_dibujado.annotate(
            scene=frame,
        )


    def trace(self, frame, detections):
        """
        - Dibuja el recorrido de un objeto.
        """
        return self.trace_annotator.annotate(
            scene=frame,
            detections=detections
        )


    def box(self, frame, detections):
        """
        - Hace las etiquetas de cada box.
        - Dibuja una box por cada objeto.
        """
        etiquetas = []
        for xyxy, mask, confidence, class_id, tracker_id in detections:
            etiqueta = f"{self.CLASES[class_id]} {confidence:0.2f}"
            etiquetas.append(etiqueta)
            
        return self.box_annotator.annotate(
            scene=frame,
            detections=detections,
            labels=etiquetas,
        )


    def callback(self, frame: np.ndarray, index:int) -> np.ndarray:
        """
        - Procesamiento de video.
        - Se ejecuta por cada frame del video.
        """

        #! Realizar la detección/predicción de objetos
        results = self.modelo(frame, verbose=False)[0]
        detections = sv.Detections.from_ultralytics(results)

        #! Filtrar las clases que no se necesitan
        detections = detections[np.isin(detections.class_id, self.CLASES_SELECCIONADAS)]

        #! Seguimiento de objetos
        detections = self.byte_tracker.update_with_detections(detections)


        #! Nuevo frame para su edición
        new_frame = frame.copy()

        new_frame = self.poligono_cv2(new_frame, detections)
        # new_frame = poligono_sv(new_frame, detections)

        new_frame = self.trace(new_frame, detections)

        new_frame = self.box(new_frame, detections)

        #! Círculos en el centro de las boxes (descomentar CircleAnnotator)
        # new_frame = circle_annotator.annotate(
        #     scene=new_frame,
        #     detections=detections,
        # )

        return new_frame


    def preparar_parametros(self, zonas: list, carpeta_video: str, archivo_video_ruta_entrada: str, archivo_video_ruta_salida: str):
        
        #! Busca la clase correspondiente a la zona
        self.zona_actual = next((zona for zona in zonas if zona.nombre == carpeta_video), None)
        
        self.resolucion_video_actual = self.obtener_resolucion(archivo_video_ruta_entrada)
        
        self.zona_actual.escalar_puntos(self.resolucion_video_actual)
        
        self.factor_escala_actual = self.calcular_factor_escala()
        print(f"  Factor de escala: {self.factor_escala_actual}")
        
        self.definir_parametros_supervision()
        
        sv.process_video(
            source_path = archivo_video_ruta_entrada,
            target_path = archivo_video_ruta_salida,
            callback=self.callback
        )


    def analizar_carpeta_videos(self, zonas: list):
        print("Procesando videos...")
        i = 0
    
        #! Crear la carpeta de resultados si no existe
        if not os.path.exists(self.PATH_CARPETA_RESULTADO_VIDEOS):
            os.makedirs(self.PATH_CARPETA_RESULTADO_VIDEOS)

        #! Recorrer todas las carpetas en la carpeta de entrada
        for carpeta_video in os.listdir(self.PATH_CARPETA_ORIGEN_VIDEOS):
            carpeta_video_ruta = os.path.join(self.PATH_CARPETA_ORIGEN_VIDEOS, carpeta_video)

            #! Verificar si es una carpeta
            if os.path.isdir(carpeta_video_ruta):
                print(f"\nProcesando carpeta: {carpeta_video}")
                
                #! Crear la carpeta de salida espejo
                carpeta_salida_ruta = os.path.join(self.PATH_CARPETA_RESULTADO_VIDEOS, carpeta_video)
                if not os.path.exists(carpeta_salida_ruta):
                    os.makedirs(carpeta_salida_ruta)

                #! Procesar todos los archivos en la carpeta de video
                for archivo_video in os.listdir(carpeta_video_ruta):
                    archivo_video_ruta_entrada = os.path.join(carpeta_video_ruta, archivo_video)
                    archivo_video_ruta_salida = os.path.join(carpeta_salida_ruta, archivo_video)

                    #! Verificar si es un archivo y tiene una extensión de video
                    if os.path.isfile(archivo_video_ruta_entrada) and archivo_video_ruta_entrada.lower().endswith(('.mp4', '.avi', '.mkv')):
                        
                        i += 1
                        print(f" -Video N°{i}: {archivo_video}")
                        self.preparar_parametros(
                            zonas=zonas, 
                            carpeta_video=carpeta_video, 
                            archivo_video_ruta_entrada=archivo_video_ruta_entrada, 
                            archivo_video_ruta_salida=archivo_video_ruta_salida
                        )
                        print(f"  Videos procesado\n")
            if i >= 2:
                break
            
        print(f"\nVideos procesados con exito.")






# def procesar_un_video(self):
#     """
#     Ejecuta el modelo y realiza la detección de objetos en el video.
#     """
#     print("Procesando video...")
#     print(f"Factor de escala: {self.factor_escala}")
#     sv.process_video(
#         source_path = self.PATH_VIDEO_ORIGINAL,
#         target_path = self.PATH_VIDEO_RESULTADO,
#         callback=self.callback
#     )
#     print("Video procesado.")


# def escalar_puntos(self, zone, resolucion_video):
#     resolucion_puntos = zone[0]
#     if resolucion_puntos == resolucion_video:
#         return zone[1]
#     ZONE_objetivo = []
#     for punto in zone:
#         x_original, y_original = punto
#         x_objetivo = int(x_original * self.factor_escala_actual)
#         y_objetivo = int(y_original * self.factor_escala_actual)
#         ZONE_objetivo.append([x_objetivo, y_objetivo])
#     return np.array(ZONE_objetivo)