from Notificador import Notificador
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

notificador = Notificador(False)

detector = Detector(MODEL, [2, 3, 5, 7], notificador)
detector.analizar_carpeta_videos(zonas)



#TODO:

# [ ] Ver si puedo hacer que el detector sea en vivo.
# [ ] Ver si puedo detectar varios videos a la vez.
# [ ]

# [ ] Agregar try/except.
# [ ] ¿Es necesario guardar los videos en la carpeta Resultados?
# [ ] Ver si puedo estabilizar los videos.
# [ ] Reemplazar cv2.circle por sv.CircleAnnotator

# [x] Sistema de notificaciones (productor/consumidor) para que el detector pueda enviar la cantidad de vehículos mediante socket.
# [x] Hacer que devuelva la cantidad de vehículos en cada zona.
# [x] Agregar la detección en las distintas Zonas.
# [x] Cambiar tamaño fijo de letras y lineas por un factor de escala.
# [x] Borrar la linea de in/out

