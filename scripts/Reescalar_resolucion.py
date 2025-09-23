import os

# Importar tipo Resolution desde el core del proyecto
import sys

import cv2
import numpy as np

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from src.traffic_system.core.types import Resolution


def detectar_y_corregir_orientacion(
    frame: np.ndarray, es_video_vertical: bool = True
) -> np.ndarray:
    """
    Detecta si un frame necesita rotación y la aplica automáticamente.

    Args:
        frame: El frame de video a verificar
        es_video_vertical: True si el video debería ser vertical (alto > ancho)

    Returns:
        Frame corregido con la orientación correcta
    """
    alto, ancho = frame.shape[:2]

    # Si esperamos un video vertical pero el frame es horizontal, rotar
    if es_video_vertical and ancho > alto:
        # Rotar 90° en sentido horario para corregir la orientación
        frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
    # Si esperamos un video horizontal pero el frame es vertical, rotar
    elif not es_video_vertical and alto > ancho:
        # Rotar 90° en sentido antihorario para corregir la orientación
        frame = cv2.rotate(frame, cv2.ROTATE_90_COUNTERCLOCKWISE)

    return frame


def reescalar_video(
    ruta_entrada: str,
    ruta_salida: str,
    nueva_resolucion: Resolution,
    factor_reduccion_fps: float = 3,
) -> None:
    """
    - Reduce a un tercio los fps.
    - Reescala un video a una nueva resolución.
    - Corrige automáticamente problemas de orientación.
    """
    cap = cv2.VideoCapture(ruta_entrada)

    # Las dimensiones originales no se usan en este script
    # ancho_original = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    # alto_original = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    #! Obtener la tasa de fotogramas original
    fps_original = cap.get(cv2.CAP_PROP_FPS)

    #! Calcular la nueva tasa de fotogramas
    fps_nuevo = fps_original / factor_reduccion_fps

    _, extension = os.path.splitext(ruta_entrada)
    nombre_base, _ = os.path.splitext(ruta_salida)

    # ruta_salida = nombre_base + f"-{nueva_resolucion[0]}x{nueva_resolucion[1]}-{round(fps_nuevo)}fps{extension}"

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")  # type: ignore[attr-defined]
    out = cv2.VideoWriter(ruta_salida, fourcc, fps_nuevo, nueva_resolucion)

    # Determinar si el video objetivo es vertical (altura > anchura)
    es_video_vertical = nueva_resolucion[1] > nueva_resolucion[0]

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Reducir a un tercio los fps
        if cap.get(cv2.CAP_PROP_POS_FRAMES) % factor_reduccion_fps != 0:
            continue

        # Corregir orientación si es necesario
        frame = detectar_y_corregir_orientacion(frame, es_video_vertical)

        # Reescalar el frame
        frame_reescalado = cv2.resize(frame, nueva_resolucion)

        # Escribir el frame reescalado en el nuevo video
        out.write(frame_reescalado)

    #! Liberar recursos
    cap.release()
    out.release()
    print(f"Video reescalado: {ruta_salida}")


def reescalar_carpeta_videos(
    carpeta_entrada: str,
    carpeta_salida: str,
    nueva_resolucion: Resolution,
    factor_reduccion_fps: int,
) -> None:
    #! Crear la carpeta de salida si no existe
    carpeta_salida = f"{carpeta_salida}-{nueva_resolucion[0]}x{nueva_resolucion[1]}-{round(30/factor_reduccion_fps)}fps"
    if not os.path.exists(carpeta_salida):
        os.makedirs(carpeta_salida)

    #! Recorrer todas las carpetas en la carpeta de entrada
    for carpeta_video in os.listdir(carpeta_entrada):
        carpeta_video_ruta = os.path.join(carpeta_entrada, carpeta_video)

        #! Verificar si es una carpeta
        if os.path.isdir(carpeta_video_ruta):
            #! Crear la carpeta de salida espejo
            carpeta_salida_ruta = os.path.join(carpeta_salida, carpeta_video)
            if not os.path.exists(carpeta_salida_ruta):
                os.makedirs(carpeta_salida_ruta)

            #! Procesar todos los archivos en la carpeta de video
            for archivo_video in os.listdir(carpeta_video_ruta):
                archivo_video_ruta_entrada = os.path.join(
                    carpeta_video_ruta, archivo_video
                )
                archivo_video_ruta_salida = os.path.join(
                    carpeta_salida_ruta, archivo_video
                )

                #! Verificar si es un archivo y tiene una extensión de video
                if os.path.isfile(
                    archivo_video_ruta_entrada
                ) and archivo_video_ruta_entrada.lower().endswith(
                    (".mp4", ".avi", ".mkv")
                ):
                    #! Reescalar el video
                    reescalar_video(
                        archivo_video_ruta_entrada,
                        archivo_video_ruta_salida,
                        nueva_resolucion,
                        factor_reduccion_fps,
                    )


nueva_resolucion = (1080, 1920)
factor_reduccion_fps = 2  #! 30/factor = fps

# #! Reescalar todos los videos carpetas
# carpeta_entrada = "C:\\Users\\facun\\Desktop\\nuevos_video"
# carpeta_salida = "C:\\Users\\facun\\Desktop\\nuevos_video_salida"
# reescalar_carpeta_videos(
#     carpeta_entrada, carpeta_salida, nueva_resolucion, factor_reduccion_fps
# )

#! Reescalar un único video
ruta_video_entrada = (
    "assets\\dataset-nuevos_video_3\\Zona B\\20250914_122919 - Clipchamp.mp4"
)
ruta_video_salida = (
    "assets\\dataset-nuevos_video_3\\Zona B\\20250914_122919 - Clipchamp - 2.mp4"
)
reescalar_video(
    ruta_video_entrada, ruta_video_salida, nueva_resolucion, factor_reduccion_fps
)
