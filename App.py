from Detector import Detector
import yaml
from Zona import Zona
import numpy as np

MODEL = "yolov8n.pt"
# MODEL = "yolov8s.pt"
# MODEL = "yolov8x.pt"

#! Leer el archivo YAML de zonas
with open('zonas.yaml', 'r') as archivo:
    datos_yaml = yaml.safe_load(archivo)

zonas = [Zona(zona['Nombre'], tuple(zona['Resolucion']), np.array(zona['Puntos'])) for zona in datos_yaml['Zonas']]


detector = Detector(MODEL, [2, 3, 5, 7])
detector.analizar_carpeta_videos(zonas)








#TODO:
# [ ] Hacer que devuelva la cantidad de vehiculos en cada zona.

# [ ]
# [ ]
# [ ]

# [ ] Agregar try/except.
# [ ] ¿Es necesario guardar los videos en la carpeta Resultados?
# [ ] Ver si puedo estabilizar los videos.
# [ ] Reemplazar cv2.circle por sv.CircleAnnotator

# [x] Agregar la deteccion en las distintas Zonas.
# [x] Cambiar tamaño fijo de letras y lineas por un factor de escala.
# [x] Borrar la linea de in/out

