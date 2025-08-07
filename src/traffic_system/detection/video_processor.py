import datetime
import logging
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
        self.logger = logging.getLogger(f"{self.__class__.__name__}[VideoProcessor]")

        self.fps = self._get_fps() if fps is None else fps
        self.resolution = self._get_resolution() if resolution is None else resolution

        if result_path is None:
            #! Crear la carpeta de resultados si no existe
            result_folder = os.path.join(os.getcwd(), "detection_results")
            if not os.path.exists(result_folder):
                os.makedirs(result_folder)
                self.logger.info(f"📁 Carpeta de resultados creada: {result_folder}")
            self.result_path = os.path.join(
                result_folder,
                f"{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4",
            )
            self.logger.info(f"📹 Ruta de resultado generada: {self.result_path}")
        else:
            self.result_path = result_path

        if not (
            isinstance(self.resolution, tuple)
            and len(self.resolution) == 2
            and all(isinstance(x, int) for x in self.resolution)
        ):
            self.logger.error(f"❌ Resolución inválida: {self.resolution}")
            raise ValueError(
                "resolution debe ser una tupla de dos enteros (ancho, alto)"
            )

        self.scale_factor: float = (
            self._calculate_scale_factor() if scale_factor is None else scale_factor
        )

        self.logger.info("🎬 VideoProcessor inicializado:")
        self.logger.info(f"   📂 Origen: {self.origin_path}")
        self.logger.info(f"   🎯 Zona: {self.zone.name}")
        self.logger.info(f"   📐 Resolución: {self.resolution}")
        self.logger.info(f"   🎞️ FPS: {self.fps}")
        self.logger.info(f"   ⚖️ Factor de escala: {self.scale_factor:.3f}")

    def _get_resolution(self) -> tuple[int, int]:
        try:
            cap = cv2.VideoCapture(self.origin_path)
            if not cap.isOpened():
                self.logger.error(f"❌ No se pudo abrir el video: {self.origin_path}")
                raise ValueError(f"No se pudo abrir el video: {self.origin_path}")

            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            cap.release()

            self.logger.debug(f"📐 Resolución obtenida: {width}x{height}")
            return (width, height)
        except Exception:
            self.logger.error(
                f"❌ Error obteniendo resolución del video: {self.origin_path}",
                exc_info=True,
            )
            raise

    def _get_fps(self) -> float:
        try:
            cap = cv2.VideoCapture(self.origin_path)
            if not cap.isOpened():
                self.logger.error(
                    f"❌ No se pudo abrir el video para obtener FPS: {self.origin_path}"
                )
                raise ValueError(f"No se pudo abrir el video: {self.origin_path}")

            fps: float = cap.get(cv2.CAP_PROP_FPS)
            cap.release()

            self.logger.debug(f"🎞️ FPS obtenidos: {fps}")
            return fps
        except Exception:
            self.logger.error(
                f"❌ Error obteniendo FPS del video: {self.origin_path}", exc_info=True
            )
            raise

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
        scale_factor = current_width / original_width

        self.logger.debug(
            f"⚖️ Factor de escala calculado: {scale_factor:.3f} (base: {original_width}px → actual: {current_width}px)"
        )
        return scale_factor
