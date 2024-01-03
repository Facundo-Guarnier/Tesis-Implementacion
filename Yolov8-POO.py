import os, time, cv2
import matplotlib.path as mplPath
import ultralytics as ul
import supervision as sv
import numpy as np

class Detector:
    def __init__(self, nombre_modelo, clases_seleccionadas):
        
        #! Cargar modelo pre-entrenado YOLOv8
        self.modelo = ul.YOLO(f"Modelos/{nombre_modelo}")
        self.CLASES  = self.modelo.model.names
        self.clases_seleccionadas = clases_seleccionadas
        
        #! Info del video
        self.PATH_VIDEO_ORIGINAL = "Pruebas/video-original.mp4"
        # self.PATH_VIDEO_ORIGINAL = "Pruebas/video-reescalado.mp4"
        # self.PATH_VIDEO_ORIGINAL = "Pruebas/video-reescalado-(720, 1280).mp4"
        self.PATH_VIDEO_FINAL = "Pruebas/video-deteccion.mp4"
        
        self.RESOLUCION_VIDEO_ACTUAL = self.obtener_resolucion(self.PATH_VIDEO_ORIGINAL)

        self.FACTOR_ESCALA = self.set_factor_escala()

        #! Instancia de ByteTracker, proporciona el seguimiento de los objetos.
        self.byte_tracker = sv.ByteTrack(track_thresh=0.25, track_buffer=30, match_thresh=0.8, frame_rate=30)

        #! Dibujar box en los objetos
        self.box_annotator = sv.BoxAnnotator(
            thickness=max(1, int(4 * self.FACTOR_ESCALA)), 
            text_thickness=max(1, int(4 * self.FACTOR_ESCALA)), 
            text_scale=max(1, int(2 * self.FACTOR_ESCALA)),
        )

        #! Dibujar Trace (el recorrido) de un objeto
        self.trace_annotator = sv.TraceAnnotator(
            thickness=max(1, int(4 * self.FACTOR_ESCALA)), 
            trace_length=max(1, int(50 * self.FACTOR_ESCALA)),
        )

        #! Instancia de LineZone para usar "Linea contadora"
        # self.line_zone = sv.LineZone(start=LINE_START, end=LINE_END)

        #! Dibujar linea contadora
        # self.line_zone_annotator = sv.LineZoneAnnotator(thickness=4, text_thickness=4, text_scale=2)

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
            thickness=max(1, int(4 * self.FACTOR_ESCALA)),
            text_scale=max(1, int(2 * self.FACTOR_ESCALA)),
            text_thickness=max(1, int(4 * self.FACTOR_ESCALA)),
        )


    def obtener_resolucion(self, video_path):
        cap = cv2.VideoCapture(video_path)
        ancho = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        alto = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        cap.release()
        return ((ancho, alto))


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
            thickness=max(1, int(15 * self.FACTOR_ESCALA)),
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
                radius=max(1, int(15 * self.FACTOR_ESCALA)), 
                color=color, 
                thickness=max(1, int(15 * self.FACTOR_ESCALA))
            )

        cv2.putText(
            img=frame, 
            text=f"Vehiculos {detecciones_poligono}", 
            org=(
                max(1, int(250 * self.FACTOR_ESCALA)), 
                max(1, int(3150 * self.FACTOR_ESCALA))
            ), 
            fontFace=cv2.FONT_HERSHEY_PLAIN, 
            fontScale=max(1, int(9 * self.FACTOR_ESCALA)), 
            color=(50,50,200), 
            thickness=max(1, int(9 * self.FACTOR_ESCALA)),
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
        frame = self.poligono_dibujado.annotate(
            scene=frame,
        )
        return frame


    def trace(self, frame, detections):
        """
        - Dibuja el recorrido de un objeto.
        """
        frame = self.trace_annotator.annotate(
            scene=frame,
            detections=detections
        )
        return frame


    def box(self, frame, detections):
        """
        - Hace las etiquetas de cada box.
        - Dibuja una box por cada objeto.
        """
        etiquetas = []
        for xyxy, mask, confidence, class_id, tracker_id in detections:
            etiqueta = f"{self.CLASES[class_id]} {confidence:0.2f}"
            etiquetas.append(etiqueta)
            
        frame = self.box_annotator.annotate(
            scene=frame,
            detections=detections,
            labels=etiquetas,
        )
        return frame


    def callback(self, frame: np.ndarray, index:int) -> np.ndarray:
        """
        - Procesamiento de video.
        - Se ejecuta por cada frame del video.
        """

        #! Realizar la detección/predicción de objetos
        results = self.modelo(frame, verbose=False)[0]
        detections = sv.Detections.from_ultralytics(results)

        #! Filtrar las clases que no se necesitan
        detections = detections[np.isin(detections.class_id, CLASES_SELECCIONADAS)]

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


        #! Linea contadora
        # line_zone.trigger(detections)
        # new_frame = line_zone_annotator.annotate(
        #     scene=new_frame,
        #     line_counter=line_zone
        # )


        return new_frame


    def procesar_video(self):
        """
        Ejecuta el modelo y realiza la detección de objetos en el video.
        """
        print("Procesando video...")
        print(f"Factor de escala: {self.FACTOR_ESCALA}")
        sv.process_video(
            source_path = self.PATH_VIDEO_ORIGINAL,
            target_path = self.PATH_VIDEO_FINAL,
            callback=self.callback
        )
        print("Video procesado.")


    def escalar_punto(self, ZONE, resolucion_video):
        
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


    def set_factor_escala(self):
        """
        - Devuelve el factor de escala entre la resolución original y la actual.
        - El objetivo es que los elementos (letras y lineas) se vean bien en cualquier resolución.
        """
        ancho_original, alto_original = (2160, 3840)
        ancho_actual, alto_actual, = self.RESOLUCION_VIDEO_ACTUAL 
        return ancho_actual / ancho_original


#* ---------------------------------------------------------------------------------
if __name__ == "__main__":
    #! Puntos para la linea contadora
    # LINE_START = sv.Point(1080, 0) #xy
    # LINE_END = sv.Point(1080, 3800)

    #! Puntos del polígono de detección
    ZONE = np.array([
        [444, 2064],
        [559, 1884],
        [1678, 1824],
        [1886, 1940],
        [1084, 2080],
    ])
    
    MODEL = "yolov8n.pt"    #Nano 4k 30fps: 0:38 min
    # MODEL = "yolov8s.pt"    #Small 4k 30fps: 0:51 min
    # MODEL = "yolov8x.pt"    #Xtra Large 4k 30fps: 2:30 min
    CLASES_SELECCIONADAS = [2, 3, 5, 7]
    
    detector = Detector(MODEL, CLASES_SELECCIONADAS)
    
    ZONE = detector.escalar_punto(ZONE, detector.RESOLUCION_VIDEO_ACTUAL)
    
    detector.procesar_video()






#TODO:
# [ ] 
# [ ]
# [ ]
# [ ] Ver si puedo estabilizar los videos.
# [ ] Cambiar los pixeles por porcentajes, así puedo reducir la calidad del video sin que afecte al poligono.
# [ ] Reemplazar cv2.circle por sv.CircleAnnotator

# [x] Borrar la linea de in/out