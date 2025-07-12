import datetime
import os

import cv2

from src.traffic_system.detection.zones.zone import Zone


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
        zone: Zone,
        result_path: str | None = None,
        fps: float | None = None,
        resolution: tuple[int, int] | None = None,
        scale_factor: float | None = None,
    ):
        self.zone = zone
        self.origin_path = origin_path
        self.fps = self._get_fps() if fps is None else fps
        self.resolution = self._get_resolution() if resolution is None else resolution

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
            self._calculate_scale_factor() if scale_factor is None else scale_factor
        )

    def _get_resolution(self) -> tuple[int, int]:
        cap = cv2.VideoCapture(self.origin_path)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        cap.release()
        return (width, height)

    def _get_fps(self) -> float:
        cap = cv2.VideoCapture(self.origin_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        cap.release()
        return fps

    def _calculate_scale_factor(self) -> float:
        """
        Escala los distintos elementos (letras y lineas) en base a la resolución del video.
        Lo elementos fueron diseñados para una resolución de 1080x1920.
        """
        original_width = 1080
        # original_height = 1920  # No se usa, solo original_width
        (
            current_width,
            current_height,
        ) = self.resolution
        return current_width / original_width
