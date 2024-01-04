import os, time, cv2
import matplotlib.path as mplPath
import ultralytics as ul
import supervision as sv
import numpy as np

class Detector:
    def __init__(self, nombre_modelo, clases_seleccionadas):
        
        self.definir_modelo(nombre_modelo, clases_seleccionadas)
        self.definir_parametros_video()
        self.definir_parametros_supervision()
    
    
    def definir_modelo(self, nombre_modelo, clases_seleccionadas):
        """
        - Cargar modelo pre-entrenado YOLOv8.
        - Definir las clases que se van a detectar.
        """
        self.modelo = ul.YOLO(f"Modelos/{nombre_modelo}")
        self.CLASES  = self.modelo.model.names
        self.CLASES_SELECCIONADAS = clases_seleccionadas
    
    
    def definir_parametros_video(self):
        """
        - Define Paths, resolución del video y factor de escala.
        """
        self.PATH_VIDEO_ORIGINAL = "Pruebas/video-original.mp4"
        self.PATH_VIDEO_ORIGINAL = "Pruebas/video-reescalado-720x1280.mp4"
        self.PATH_VIDEO_RESULTADO = "Pruebas/video-deteccion.mp4"
        
        self.PATH_CARPETA_ORIGEN_VIDEOS = "Dataset_reescalado/"
        self.PATH_CARPETA_RESULTADO_VIDEOS = "Resultados/"
        
        
        self.RESOLUCION_VIDEO_ACTUAL = self.obtener_resolucion(self.PATH_VIDEO_ORIGINAL)
        self.factor_escala = self.calcular_factor_escala()


    def definir_parametros_supervision(self):
        """
        Define los parámetros de supervisión necesario para la edición de los frames.
        """
        
        #! Instancia de ByteTracker, proporciona el seguimiento de los objetos.
        self.byte_tracker = sv.ByteTrack(track_thresh=0.25, track_buffer=30, match_thresh=0.8, frame_rate=30)

        #! Dibujar box en los objetos
        self.box_annotator = sv.BoxAnnotator(
            thickness=max(1, int(4 * self.factor_escala)), 
            text_thickness=max(1, int(4 * self.factor_escala)), 
            text_scale=max(1, int(2 * self.factor_escala)),
        )

        #! Dibujar Trace (el recorrido) de un objeto
        self.trace_annotator = sv.TraceAnnotator(
            thickness=max(1, int(4 * self.factor_escala)), 
            trace_length=max(1, int(50 * self.factor_escala)),
        )

        #! Dibujar círculos en los objetos
        # self.circle_annotator = sv.CircleAnnotator(thickness=4)

        #! Polígono (sv) de detección
        self.poligono_zona = sv.PolygonZone(
            polygon=ZONE, 
            frame_resolution_wh=self.RESOLUCION_VIDEO_ACTUAL
        )

        #! Dibujar polígono (sv)
        self.poligono_dibujado = sv.PolygonZoneAnnotator(
            zone=self.poligono_zona,
            color=sv.Color(255,0,0),
            thickness=max(1, int(4 * self.factor_escala)),
            text_scale=max(1, int(2 * self.factor_escala)),
            text_thickness=max(1, int(4 * self.factor_escala)),
        )


    def obtener_resolucion(self, video_path):
        cap = cv2.VideoCapture(video_path)
        ancho = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        alto = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        cap.release()
        return ((ancho, alto))


    def escalar_puntos(self, ZONE, resolucion_video):
        
        if (2160, 3840) == resolucion_video:
            return ZONE
        
        ZONE_objetivo = []
        for punto in ZONE:
            x_original, y_original = punto
            ancho_original, alto_original = (2160, 3840)
            ancho_objetivo, alto_objetivo = resolucion_video

            # Calcular las proporciones de escala en x e y
            escala_x = ancho_objetivo / ancho_original
            escala_y = alto_objetivo / alto_original

            # Aplicar la escala al punto
            x_objetivo = int(x_original * escala_x)
            y_objetivo = int(y_original * escala_y)
            ZONE_objetivo.append([x_objetivo, y_objetivo])

        return np.array(ZONE_objetivo)


    def calcular_factor_escala(self):
        """
        - Devuelve el factor de escala entre la resolución original y la actual.
        - El objetivo es que los elementos (letras y lineas) se vean bien en cualquier resolución.
        """
        ancho_original, alto_original = (2160, 3840)
        ancho_actual, alto_actual, = self.RESOLUCION_VIDEO_ACTUAL 
        return ancho_actual / ancho_original


    def poligono_cv2(self, frame, detections):
        """
        - Dibuja el centro de los objetos y el polígono de detección. 
        - Cuenta los objetos que están dentro del polígono.
        """


        #! Dibujar el polígono de detección
        cv2.polylines(
            img=frame, 
            pts=[ZONE], 
            isClosed=True, 
            color=(0,0,255),  
            thickness=max(1, int(15 * self.factor_escala)),
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
            if mplPath.Path(ZONE).contains_point((x,y)):
                detecciones_poligono += 1
                color = [255,80,0]

            else:
                color = [0,0,255]

            cv2.circle(
                img=frame, 
                center=(x,y), 
                radius=max(1, int(15 * self.factor_escala)), 
                color=color, 
                thickness=max(1, int(15 * self.factor_escala))
            )

        cv2.putText(
            img=frame, 
            text=f"Vehiculos {detecciones_poligono}", 
            org=(
                max(1, int(250 * self.factor_escala)), 
                max(1, int(3150 * self.factor_escala))
            ), 
            fontFace=cv2.FONT_HERSHEY_PLAIN, 
            fontScale=max(1, int(9 * self.factor_escala)), 
            color=(50,50,200), 
            thickness=max(1, int(9 * self.factor_escala)),
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


    def procesar_un_video(self):
        """
        Ejecuta el modelo y realiza la detección de objetos en el video.
        """
        print("Procesando video...")
        print(f"Factor de escala: {self.factor_escala}")
        sv.process_video(
            source_path = self.PATH_VIDEO_ORIGINAL,
            target_path = self.PATH_VIDEO_RESULTADO,
            callback=self.callback
        )
        print("Video procesado.")


    def procesar_carpeta_videos(self):
        """
        """
        print("Procesando videos...")
        print(f"Factor de escala: {self.factor_escala}")
        
        i = 0
        
        #! Crear la carpeta de resultados si no existe
        if not os.path.exists(self.PATH_CARPETA_RESULTADO_VIDEOS):
            os.makedirs(self.PATH_CARPETA_RESULTADO_VIDEOS)

        #! Recorrer todas las carpetas en la carpeta de entrada
        for carpeta_video in os.listdir(self.PATH_CARPETA_ORIGEN_VIDEOS):
            carpeta_video_ruta = os.path.join(self.PATH_CARPETA_ORIGEN_VIDEOS, carpeta_video)

            #! Verificar si es una carpeta
            if os.path.isdir(carpeta_video_ruta):
                print(f"Procesando carpeta: {carpeta_video}")
                
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

                        self.factor_escala = self.calcular_factor_escala()
                        sv.process_video(
                            source_path = archivo_video_ruta_entrada,
                            target_path = archivo_video_ruta_salida,
                            callback=self.callback
                        )
                        i += 1
                        print(f"Videos procesados: {i}")
            
        print(f"Videos procesados con exito.")





#* ---------------------------------------------------------------------------------
if __name__ == "__main__":
    #! Puntos del polígono de detección
    ZONE = np.array([
        [444, 2064],
        [559, 1884],
        [1678, 1824],
        [1886, 1940],
        [1084, 2080],
    ])
    
    MODEL = "yolov8n.pt"
    # MODEL = "yolov8s.pt"
    # MODEL = "yolov8x.pt"
    
    detector = Detector(MODEL, [2, 3, 5, 7])
    
    ZONE = detector.escalar_puntos(ZONE, detector.RESOLUCION_VIDEO_ACTUAL)
    
    detector.procesar_carpeta_videos()
    # detector.procesar_un_video()




Ya se procesan las distintas carpetas de videos, 
ahora hay que agregar la detección en las distintas zonas dentro de los videos.



#TODO:
# [ ] Agregar la deteccion en las distintas Zonas.
# [ ] Hacer que devuelva la cantidad de vehiculos en cada zona.
# [ ]
# [ ]
# [ ]
# [ ] Agregar try/except.
# [ ] ¿Es necesario guardar los videos en la carpeta Resultados?
# [ ] Ver si puedo estabilizar los videos.
# [ ] Reemplazar cv2.circle por sv.CircleAnnotator

# [x] Cambiar tamaño fijo de letras y lineas por un factor de escala.
# [x] Borrar la linea de in/out