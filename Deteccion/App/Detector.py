import matplotlib.path as mplPath
import ultralytics as ul 
import supervision as sv 
import numpy as np
import time, cv2

from Deteccion.App.config import configuracion
from Deteccion.App.Video import Video


class Detector:
    """
    Clase que procesa los videos, realiza la detección de objetos, dibuja 
    los polígonos de zonas y los centros de cada objeto detectado. 
    """
    
    def __init__(self):
        self.modelo = ul.YOLO(f"Deteccion/Modelos/{configuracion['modelo']}")
        self.CLASES_SELECCIONADAS = [2, 3, 5, 7] # Auto, Moto, Camion, Bus
        self.CLASES  = self.modelo.model.names


    def __definir_parametros_supervision(self) -> None:
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

        # #! Polígono (sv) de detección
        # self.poligono_zona = sv.PolygonZone(
        #     polygon=self.video.zona.puntos_reescalados, 
        #     frame_resolution_wh=self.video.resolucion
        # )

        # #! Dibujador polígono (sv)
        # self.poligono_dibujador = sv.PolygonZoneAnnotator(
        #     zone=self.poligono_zona,
        #     color=sv.Color(255,0,0),
        #     thickness=max(1, int(4 * self.video.factor_escala)),
        #     text_scale=max(1, int(2 * self.video.factor_escala)),
        #     text_thickness=max(1, int(4 * self.video.factor_escala)),
        # )


    def __poligono_cv2(self, frame, detections:sv.Detections) -> np.ndarray:
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
            color:list[int]  # BGR
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
        
        #! Escribir la cantidad de detecciones en el frame
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
        
        #! Guardar la cantidad de detecciones en la clase Zona para la API.
        self.video.zona.cantidad_detecciones = detecciones_poligono
        
        return frame


    def __box_sv(self, frame:np.ndarray, detections:sv.Detections) -> np.ndarray:
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


    def __callback(self, frame:np.ndarray, n_frame:int) -> np.ndarray:
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

        frame = self.__box_sv(frame, detections)

        return frame


    def procesar_guardar(self, video:Video) -> None:
        """
        Procesa un video y guarda el resultado sin mostrarlo en una ventana en vivo.
        """
        
        self.video = video
        self.video.zona.escalar_puntos(self.video.resolucion)
        self.__definir_parametros_supervision()
        print(f"  Factor de escala: {self.video.factor_escala}")
        
        
        sv.process_video(
            source_path = video.path_origen,
            target_path = video.path_resultado,
            callback=self.__callback
        )


    def procesar_vivo(self, video:Video, guardar:bool=False) -> None:
        """
        - Procesa un video y muestra el resultado en vivo.
        - Si guardar=True, guarda el resultado.
        """
        
        self.video = video
        
        cap = cv2.VideoCapture(self.video.path_origen)
        self.video.zona.escalar_puntos(self.video.resolucion)
        self.__definir_parametros_supervision()
        
        if guardar:
            out_guardar = cv2.VideoWriter(
                filename=self.video.path_resultado, 
                fourcc=1983148141,      #! mp4v 
                fps=cap.get(cv2.CAP_PROP_FPS), 
                frameSize=(
                    int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),     #! width 
                    int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),    #! height
                    )
            )

        fps = 0
        frame_count = 0
        start_time = time.time()
        total_frames = 0
        
        cv2.namedWindow('Detectando en un video', cv2.WINDOW_NORMAL)
        cv2.resizeWindow('Detectando en un video', 460, 820) 
        
        while True:
            frame_count += 1
            total_frames += 1

            #! Salir si no hay más frames
            ret, frame = cap.read()
            if not ret:
                break
            
            #! Procesar el frame
            frame = self.__callback(frame, total_frames)
            
            #! Guardar el frame sin mostrar los fps.
            if guardar:
                out_guardar.write(frame)
            
            #! Mostrar el FPS
            if time.time() - start_time >= 1:
                fps = frame_count
                frame_count = 0
                start_time = time.time()
            
            cv2.putText(frame, f'FPS: {fps}', (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1*self.video.factor_escala, (0, 255, 0), 2)
            
            #! Mostrar el frame en la ventana
            cv2.imshow('Detectando en un video', frame)

            #! Salir del bucle con la tecla 'q'.
            if cv2.waitKey(1) & 0xFF == ord('q'):  
                break

        cap.release()
        cv2.destroyAllWindows()
        if guardar:
            print("Guardado en: ", self.video.path_resultado)   


    def procesar_camara(self) -> None:
        """
        Procesa la cámara en vivo y muestra el resultado en tiempo real.
        """
        
        cap = cv2.VideoCapture(0)
        
        self.__definir_parametros_supervision()
        
        fps = 0
        frame_count = 0
        start_time = time.time()
        total_frames = 0
        
        cv2.namedWindow('Detectando con cámara', cv2.WINDOW_NORMAL)
        cv2.resizeWindow('Detectando con cámara', 820, 460) 
        
        while True:
            frame_count += 1

            #! Salir si no hay más frames
            ret, frame = cap.read()
            if not ret:
                break
            
            #! Procesar el frame
            frame = self.__callback(frame, total_frames)
            
            #! Mostrar el FPS
            if time.time() - start_time >= 1:
                fps = frame_count
                frame_count = 0
                start_time = time.time()
            
            cv2.putText(frame, f'FPS: {fps}', (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            
            #! Mostrar el frame en la ventana
            cv2.imshow('Detectando con cámara', frame)  

            #! Salir del bucle con la tecla 'q'.
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        cap.release()
        cv2.destroyAllWindows()



# #! Círculos en el centro de las boxes (descomentar CircleAnnotator)
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
#     return self.poligono_dibujador.annotate(
#         scene=frame,
#     )