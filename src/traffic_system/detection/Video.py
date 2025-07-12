import datetime
import os

import cv2

from src.traffic_system.detection.zonas.Zona import Zona


class VideoProcessor:
    """
    Inicializa un objeto Video.

    Args:
        origin_path (str): Ruta del video de entrada.
        zone (Zona): Zona de interés.
        result_path (str | None): Ruta para guardar el video procesado. Si es None, se genera automáticamente.
        fps (float | None): FPS del video. Si es None, se obtiene del archivo.
        resolution (tuple[int, int] | None): Resolución (ancho, alto). Si es None, se obtiene del archivo.
        scale_factor (float | None): Factor de escala. Si es None, se calcula automáticamente.
    """

    def __init__(
        self,
        origin_path: str,
        zone: Zona,
        result_path: str | None = None,
        fps: float | None = None,
        resolution: tuple[int, int] | None = None,
        scale_factor: float | None = None,
    ):
        self.zone = zone
        self.origin_path = origin_path
        self.fps = self.__get_fps() if fps is None else fps
        self.resolution = self.__get_resolution() if resolution is None else resolution

        if result_path is None:
            #! Crear la carpeta de resultados si no existe
            result_folder = os.path.join(os.getcwd(), "detection_results")
            if not os.path.exists(result_folder):
                os.makedirs(result_folder)
            self.result_path = os.path.join(
                result_folder,
                f"{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4",
            )
        else:
            self.result_path = result_path

        if not (
            isinstance(self.resolution, tuple)
            and len(self.resolution) == 2
            and all(isinstance(x, int) for x in self.resolution)
        ):
            raise ValueError(
                "resolution debe ser una tupla de dos enteros (ancho, alto)"
            )

        self.scale_factor: float = (
            self.__calculate_scale_factor() if scale_factor is None else scale_factor
        )

    def __get_resolution(self) -> tuple[int, int]:
        cap = cv2.VideoCapture(self.origin_path)
        ancho = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        alto = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        cap.release()
        return (ancho, alto)

    def __get_fps(self) -> float:
        cap = cv2.VideoCapture(self.origin_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        cap.release()
        return fps

    def __calculate_scale_factor(self) -> float:
        """
        Escala los distintos elementos (letras y lineas) en base a la resolución del video.
        Lo elementos fueron diseñados para una resolución de 1080x1920.
        """
        ancho_original = 1080
        # alto_original = 1920  # No se usa, solo ancho_original
        (
            ancho_actual,
            alto_actual,
        ) = self.resolution
        return ancho_actual / ancho_original
