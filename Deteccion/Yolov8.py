import os, time, cv2
import matplotlib.path as mplPath
import ultralytics as ul
import supervision as sv
import numpy as np



#T* Cargar modelo pre-entrenado YOLOv8
MODEL = "yolov8n.pt"    #Nano: 0:38 min
# MODEL = "yolov8s.pt"    #Small: 0:51 min
# MODEL = "yolov8x.pt"    #Xtra Large: 2:30 min
modelo = ul.YOLO(MODEL)
CLASES  = modelo.model.names
CLASES_SELECCIONADAS = [2, 3, 5, 7]


#T* Configuración de la detección
#! Info del video
PATH_VIDEO_ORIGINAL = "video-original.mp4"
PATH_VIDEO_FINAL = f"video-deteccion.mp4"
RESOLUCION_VIDEO = (2160, 3840)

#! Puntos para la linea contadora
LINE_START = sv.Point(1080, 0) #xy
LINE_END = sv.Point(1080, 3800)

#! Puntos del polígono de detección
ZONE = np.array([
    [444, 2064],
    [559, 1884],
    [1678, 1824],
    [1886, 1940],
    [1084, 2080],
])

#! Instancia de ByteTracker, proporciona el seguimiento de los objetos.
byte_tracker = sv.ByteTrack(track_thresh=0.25, track_buffer=30, match_thresh=0.8, frame_rate=30)

#! Dibujar box en los objetos
box_annotator = sv.BoxAnnotator(thickness=4, text_thickness=4, text_scale=2)

#! Dibujar Trace (el recorrido) de un objeto
trace_annotator = sv.TraceAnnotator(thickness=4, trace_length=50)

#! Linea contadora
# line_zone = sv.LineZone(start=LINE_START, end=LINE_END)

#! Dibujar linea contadora
# line_zone_annotator = sv.LineZoneAnnotator(thickness=4, text_thickness=4, text_scale=2)

#! Dibujar círculos en los objetos
# circle_annotator = sv.CircleAnnotator(thickness=4)

#! Polígono (sv) de detección
poligono_zona = sv.PolygonZone(
    polygon=ZONE, 
    frame_resolution_wh=RESOLUCION_VIDEO
)

#! Dibujar polígono (sv)
poligono_dibujado = sv.PolygonZoneAnnotator(
    zone=poligono_zona,
    color=sv.Color(255,0,0),
    thickness=4,
    text_scale=2,
    text_thickness=4,
)

#T* Detección de vehículos

def poligono_cv2(frame, detections):
    """
    - Dibuja el centro de los objetos y el poligono de deteccion. 
    - Cuenta los objetos que estan dentro del poligono.
    """

    # Dibujar el poligono de deteccion
    cv2.polylines(img=frame, pts=[ZONE], isClosed=True, color=(0,0,255),  thickness=15)

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

        cv2.circle(img=frame, center=(x,y), radius=15, color=color, thickness=15)

    cv2.putText(img=frame, text=f"Vehiculos {detecciones_poligono}", org=(100,100), fontFace=cv2.FONT_HERSHEY_PLAIN, fontScale=9, color=(0,0,255), thickness=9)

    return frame


def poligono_sv(frame, detections):
    """
    - Dibuja el centro de los objetos y el poligono de deteccion. 
    - Tiene el problema de que no cuenta bien los objetos dentro del poligono, no
    se si es porque cuenta cuando la box está completa dentro del poligono o si
    es por otro motivo.
    """
    detecciones = poligono_zona.trigger(detections)
    frame = poligono_dibujado.annotate(
        scene=frame,
    )
    return frame


def callback(frame: np.ndarray, index:int) -> np.ndarray:
    """
    - Procesamiento de video.
    - Se ejecuta por cada frame del video.
    """

    #! Realizar la deteccion/prediccion de objetos
    results = modelo(frame, verbose=False)[0]
    detections = sv.Detections.from_ultralytics(results)

    #! Filtrar las clases que no se necesitan
    detections = detections[np.isin(detections.class_id, CLASES_SELECCIONADAS)]

    #! Seguimiento de objetos
    detections = byte_tracker.update_with_detections(detections)

    #! Etiqueta sobre las boxes
    etiquetas = []
    for xyxy, mask, confidence, class_id, tracker_id in detections:
        etiqueta = f"{CLASES[class_id]} {confidence:0.2f}"
        etiquetas.append(etiqueta)

    #! Nuevo frame para su edicion
    new_frame = frame.copy()


    #! Poligono de deteccion
    new_frame = poligono_cv2(new_frame, detections)
    # new_frame = poligono_sv(new_frame, detections)


    #! Dibujar Trace (el recorrido) de un objeto
    new_frame = trace_annotator.annotate(
        scene=new_frame,
        detections=detections
    )


    #! Dibujar box en los objetos
    new_frame = box_annotator.annotate(
        scene=new_frame,
        detections=detections,
        labels=etiquetas
    )


    #! Circulos en el centro de las boxes (descomentar CircleAnnotator)
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

#! Procesar el video
print("Procesando video...")
sv.process_video(
    source_path = PATH_VIDEO_ORIGINAL,
    target_path = PATH_VIDEO_FINAL,
    callback=callback
)
print("Video procesado.")

#TODO:
# [ ] Cambiar los pixeles por porcentajes, así puedo reducir la calidad del video sin que afecte al poligono.
# [ ] Reemplazar cv2.circle por sv.CircleAnnotator
# [x] Borrar la linea de in/out