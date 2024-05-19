import matplotlib.path as mplPath
import ultralytics as ul 
import supervision as sv 
import numpy as np
import time, cv2

from config import configuracion
from Deteccion.App.Video import Video
from Deteccion.App.zonas.Zona import Zona


class Detector:
    """
    Clase que procesa los videos, realiza la detección de objetos, dibuja 
    los polígonos de zonas y los centros de cada objeto detectado. 
    
    Attributes:
        __CLASES_SELECCIONADAS (list[int]): ID de clases seleccionadas para la detección.
        __CLASES (list[str]): Nombres de todas las clases del modelo.
        modelo (YOLO): Modelo de detección de objetos.
        tiempos_deteccion (dict): Diccionario para almacenar los tiempos de detección de los objetos.
        byte_tracker (ByteTrack): Proporciona el seguimiento de los objetos.
        box_annotator (BoxAnnotator): Dibuja las box de los objetos.
        video (Video): Video a procesar.
        
    """
    
    def __init__(self):
        self.modelo = ul.YOLO(f"Deteccion/Modelos/{configuracion['deteccion']['modelo']}")
        self.__CLASES_SELECCIONADAS = [2, 3, 5, 7] # Auto, Moto, Camion, Bus
        self.__CLASES  = self.modelo.model.names
        self.tiempos_deteccion = {}  # Diccionario para almacenar tiempos de detección
    
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
            thickness=max(1, int(3 * self.video.factor_escala)), 
            text_thickness=max(1, int(2 * self.video.factor_escala)), 
            text_scale=max(1, int(1 * self.video.factor_escala)),
        )
        
        #! Linea contadora
        self.line_counter = sv.LineZone(start=sv.Point(50, 150), end=sv.Point(50, 350))
    
    
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
        
        
        #! Lista de IDs de objetos que ya no están en la imagen
        ids_fuera_imagen = [id for id in self.tiempos_deteccion if id not in detections.tracker_id]
        for id in ids_fuera_imagen:
            del self.tiempos_deteccion[id]
        
        
        
        
        
        detecciones_poligono = 0
        for box, mask, confianza, class_id, tracker_id in detections:
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
                
                #! Contar el tiempo de detección
                if tracker_id in self.tiempos_deteccion:
                    self.tiempos_deteccion[tracker_id] += 1
                else:
                    self.tiempos_deteccion[tracker_id] = 1
                
                
            else:
                color = [0,0,255]
                #! Reiniciar el tiempo de detección
                self.tiempos_deteccion[tracker_id] = 0
            
            cv2.circle(
                img=frame, 
                center=(x,y), 
                radius=max(1, int(10 * self.video.factor_escala)), 
                color=color, 
                thickness=max(1, int(10 * self.video.factor_escala))
            )
        
        
        frame_total = sum(self.tiempos_deteccion.values())
        tiempo_total = frame_total // self.video.fps
        
        #! Escribir la cantidad de detecciones en el frame
        cv2.putText(
            img=frame, 
            text=f"Vehiculos {detecciones_poligono} {tiempo_total}", 
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
        self.video.zona.tiempo_espera = tiempo_total
        
        return frame
    
    
    def __box_sv(self, frame:np.ndarray, detections:sv.Detections) -> np.ndarray:
        """
        - Hace las etiquetas de cada box.
        - Dibuja una box por cada objeto.
        """
        etiquetas = []
        for xyxy, mask, confianza, class_id, tracker_id in detections:
            tiempo_deteccion = self.tiempos_deteccion.get(tracker_id, 0)
            etiqueta = f"{tiempo_deteccion} frames"
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
        detections = detections[np.isin(detections.class_id, self.__CLASES_SELECCIONADAS)]
        
        #! Seguimiento de objetos
        detections = self.byte_tracker.update_with_detections(detections)
        
        frame = self.__poligono_cv2(frame, detections)
        
        frame = self.__box_sv(frame, detections)
        
        #TODO ACA ESTOY, DIBUJANDO LA LINEA DE CONTEO DE VEHICULOS, Y EN LA 55
        # https://supervision.roboflow.com/latest/detection/tools/line_zone/#supervision.detection.line_zone.LineZone.trigger 
        # cv2.line(frame, (50, 550), (50, 850), (0, 255, 0), 3)
        # crossed_in, crossed_out = self.line_counter.trigger(detections)
        # print(f"Vehiculos que cruzaron la linea: {self.line_counter.in_count}, Vehiculos que salieron: {self.line_counter.out_count}") 
        return frame
    
    
    def procesar_y_guardar_video(self, video:Video) -> None:
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
    
    
    def procesar_y_mostrar_resultado_en_vivo(self, video:Video) -> None:
        """
        Procesa un video y muestra el resultado en vivo.
        """
        
        self.video = video
        guardar = configuracion["deteccion"]["un_video"]["guardar"]
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
    
    
    def procesar_camara(self, video:Video) -> None:
        """
        Procesa la cámara en vivo y muestra el resultado en tiempo real.
        """
        
        cap = cv2.VideoCapture(0)
        self.video = video
        self.__definir_parametros_supervision()
        
        fps = 0
        frame_count = 0
        start_time = time.time()
        total_frames = 0
        
        cv2.namedWindow('Detectando con camara', cv2.WINDOW_NORMAL)
        cv2.resizeWindow('Detectando con camara', 820, 460) 
        
        while True:
            frame_count += 1
            
            #! Salir si no hay más frames
            ret, frame = cap.read()
            if not ret:
                break
            
            #! Rescalar el frame
            frame = cv2.resize(frame, (820, 460))
            
            #! Procesar el frame
            frame = self.__callback(frame, total_frames)
            
            #! Mostrar el FPS
            if time.time() - start_time >= 1:
                fps = frame_count
                frame_count = 0
                start_time = time.time()
            
            cv2.putText(frame, f'FPS: {fps}', (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            
            #! Mostrar el frame en la ventana
            cv2.imshow('Detectando con camara', frame)  
            
            #! Salir del bucle con la tecla 'q'.
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        
        cap.release()
        cv2.destroyAllWindows()
