import os, time, cv2
from Notificador import Notificador
from Video import Video
from Zona import Zona
import matplotlib.path as mplPath
import ultralytics as ul
import supervision as sv
import numpy as np

class Detector:
    def __init__(self, nombre_modelo:str, notificador: Notificador):
        
        self.notificador = notificador
        
        self.modelo = ul.YOLO(f"Modelos/{nombre_modelo}")
        self.CLASES_SELECCIONADAS = [2, 3, 5, 7] # Auto, Moto, Camion, Bus CREO
        self.CLASES  = self.modelo.model.names


    def __definir_parametros_supervision(self):
        """
        Define los parámetros de supervisión necesario para la edición de los frames en base a la resolución del video.
        """
        
        #! Instancia de ByteTracker, proporciona el seguimiento de los objetos.
        self.byte_tracker = sv.ByteTrack(
            track_thresh=0.25, 
            match_thresh=0.8, 
            track_buffer=self.video.fps,    #! Cantidad de frames que se mantiene el seguimiento de un objeto (1 segundo) 
            frame_rate=self.video.fps,
        )

        #! Dibujar box en los objetos
        self.box_annotator = sv.BoxAnnotator(
            thickness=max(1, int(4 * self.video.factor_escala)), 
            text_thickness=max(1, int(3 * self.video.factor_escala)), 
            text_scale=max(1, int(2 * self.video.factor_escala)),
        )

        #! Polígono (sv) de detección
        self.poligono_zona = sv.PolygonZone(
            polygon=self.video.zona.puntos_reescalados, 
            frame_resolution_wh=self.video.resolucion
        )

        #! Dibujar polígono (sv)
        self.poligono_dibujado = sv.PolygonZoneAnnotator(
            zone=self.poligono_zona,
            color=sv.Color(255,0,0),
            thickness=max(1, int(4 * self.video.factor_escala)),
            text_scale=max(1, int(2 * self.video.factor_escala)),
            text_thickness=max(1, int(4 * self.video.factor_escala)),
        )


    def __poligono_cv2(self, frame, detections):
        """
        - Dibuja el centro de los objetos y el polígono de detección. 
        - Cuenta los objetos que están dentro del polígono.
        """

        #! Dibujar el polígono de detección
        cv2.polylines(
            img=frame, 
            pts=[self.video.zona.puntos_reescalados], 
            isClosed=True, 
            color=(0,0,255),  
            thickness=max(1, int(10 * self.video.factor_escala)),
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
            if mplPath.Path(self.video.zona.puntos_reescalados).contains_point((x,y)):
                detecciones_poligono += 1
                color = [255,80,0]

            else:
                color = [0,0,255]

            cv2.circle(
                img=frame, 
                center=(x,y), 
                radius=max(1, int(10 * self.video.factor_escala)), 
                color=color, 
                thickness=max(1, int(10 * self.video.factor_escala))
            )
            
        cv2.putText(
            img=frame, 
            text=f"Vehiculos {detecciones_poligono}", 
            org=(
                max(1, int(250 * self.video.factor_escala)), 
                max(1, int(1800 * self.video.factor_escala))
            ), 
            fontFace=cv2.FONT_HERSHEY_PLAIN, 
            fontScale=max(1, int(6 * self.video.factor_escala)), 
            color=(50,50,200), 
            thickness=max(1, int(6 * self.video.factor_escala)),
        )
        
        self.notificador.notificar(f"{self.video.nombre} {detecciones_poligono} | ")

        return frame


    def __box(self, frame, detections):
        """
        - Hace las etiquetas de cada box.
        - Dibuja una box por cada objeto.
        """
        etiquetas = []
        for xyxy, mask, confianza, class_id, tracker_id in detections:
            etiqueta = f"{self.CLASES[class_id]} {confianza:0.2f}"
            etiquetas.append(etiqueta)
            
        return self.box_annotator.annotate(
            scene=frame,
            detections=detections,
            labels=etiquetas,
        )


    def __callback(self, frame: np.ndarray, index:int) -> np.ndarray:
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

        frame = self.__poligono_cv2(frame, detections)

        frame = self.__box(frame, detections)

        return frame


    def procesar_guardar(self, video: Video):
        
        self.video = video
        self.video.zona.escalar_puntos(self.video.resolucion)
        
        print(f"  Factor de escala: {self.video.factor_escala}")
        
        self.__definir_parametros_supervision()
        
        sv.process_video(
            source_path = video.path_origen,
            target_path = video.path_resultado,
            callback=self.__callback
        )







#! Círculos en el centro de las boxes (descomentar CircleAnnotator)
# frame = circle_annotator.annotate(
#     scene=frame,
#     detections=detections,
# )

# def __trace(self, frame, detections):
#     """
#     - Dibuja el recorrido de un objeto.
#     """
#     return self.trace_annotator.annotate(
#         scene=frame,
#         detections=detections
#     )


# def __poligono_sv(self, frame, detections):
#     """
#     - Dibuja el centro de los objetos y el poligono de detección. 
#     - Tiene el problema de que no cuenta bien los objetos dentro del poligono, no
#     se si es porque cuenta cuando la box está completa dentro del poligono o si
#     es por otro motivo.
#     """
#     detecciones = self.poligono_zona.trigger(detections)
#     return self.poligono_dibujado.annotate(
#         scene=frame,
#     )


# def procesar_un_video(self):
#     """
#     Ejecuta el modelo y realiza la detección de objetos en el video.
#     """
#     print("Procesando video...")
#     print(f"Factor de escala: {self.factor_escala}")
#     sv.process_video(
#         source_path = self.PATH_VIDEO_ORIGINAL,
#         target_path = self.PATH_VIDEO_RESULTADO,
#         __callback=self.__callback
#     )
#     print("Video procesado.")


# def escalar_puntos(self, zone, resolucion_video):
#     resolucion_puntos = zone[0]
#     if resolucion_puntos == resolucion_video:
#         return zone[1]
#     ZONE_objetivo = []
#     for punto in zone:
#         x_original, y_original = punto
#         x_objetivo = int(x_original * self.video.factor_escala)
#         y_objetivo = int(y_original * self.video.factor_escala)
#         ZONE_objetivo.append([x_objetivo, y_objetivo])
#     return np.array(ZONE_objetivo)