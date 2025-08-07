import datetime
import logging
import os
from typing import Any

import cv2

from src.traffic_system.core.config_loader import load_app_settings
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
        is_camera: bool = False,
    ):
        self.zone = zone
        self.origin_path = origin_path
        self.is_camera = is_camera or origin_path == ""  # Auto-detectar si es cámara
        self.logger = logging.getLogger(f"{self.__class__.__name__}[VideoProcessor]")

        # Cargar configuración para rutas
        self.settings = load_app_settings().deteccion

        self.fps = self._get_fps() if fps is None else fps
        self.resolution = self._get_resolution() if resolution is None else resolution

        if result_path is None:
            #! Crear la carpeta de resultados si no existe
            result_folder = self.settings.path_resultados_deteccion
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
            if self.is_camera:
                # Para cámara en vivo, abrir dispositivo de captura
                cap = cv2.VideoCapture(0)
                if not cap.isOpened():
                    self.logger.error("❌ No se pudo abrir la cámara")
                    raise ValueError("No se pudo abrir la cámara")

                width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                cap.release()

                self.logger.debug(f"📐 Resolución de cámara obtenida: {width}x{height}")
                return (width, height)
            else:
                # Para archivo de video
                cap = cv2.VideoCapture(self.origin_path)
                if not cap.isOpened():
                    self.logger.error(
                        f"❌ No se pudo abrir el video: {self.origin_path}"
                    )
                    raise ValueError(f"No se pudo abrir el video: {self.origin_path}")

                width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                cap.release()

                self.logger.debug(f"📐 Resolución obtenida: {width}x{height}")
                return (width, height)
        except Exception:
            self.logger.error(
                f"❌ Error obteniendo resolución del {'cámara' if self.is_camera else 'video'}: {self.origin_path}",
                exc_info=True,
            )
            raise

    def _get_fps(self) -> float:
        try:
            if self.is_camera:
                # Para cámara en vivo, abrir dispositivo de captura
                cap = cv2.VideoCapture(0)
                if not cap.isOpened():
                    self.logger.error("❌ No se pudo abrir la cámara para obtener FPS")
                    raise ValueError("No se pudo abrir la cámara")

                fps: float = cap.get(cv2.CAP_PROP_FPS)
                cap.release()

                # Si no se puede obtener FPS de la cámara, usar valor por defecto
                if fps <= 0:
                    fps = 30.0  # FPS por defecto para cámara
                    self.logger.debug(f"🎞️ FPS por defecto para cámara: {fps}")
                else:
                    self.logger.debug(f"🎞️ FPS de cámara obtenidos: {fps}")
                return fps
            else:
                # Para archivo de video
                cap = cv2.VideoCapture(self.origin_path)
                if not cap.isOpened():
                    self.logger.error(
                        f"❌ No se pudo abrir el video para obtener FPS: {self.origin_path}"
                    )
                    raise ValueError(f"No se pudo abrir el video: {self.origin_path}")

                video_fps: float = cap.get(cv2.CAP_PROP_FPS)
                cap.release()

                self.logger.debug(f"🎞️ FPS obtenidos: {video_fps}")
                return video_fps
        except Exception:
            self.logger.error(
                f"❌ Error obteniendo FPS del {'cámara' if self.is_camera else 'video'}: {self.origin_path}",
                exc_info=True,
            )
            raise

    def _calculate_scale_factor(self) -> float | Any:
        """
        Escala los distintos elementos (letras y lineas) en base a la resolución del video.

        NOTA: Este factor se usa para elementos de UI (texto, líneas, círculos).
        Las zonas se escalan independientemente usando su resolución base específica.
        """
        # Usar la resolución base de la zona específica si está disponible
        if hasattr(self.zone, "_resolution") and self.zone._resolution:
            base_width = self.zone._resolution[0]
            self.logger.debug(
                f"📍 Usando resolución base de zona '{self.zone.name}': {self.zone._resolution}"
            )
        else:
            # Fallback a resolución estándar FHD
            base_width = 1080
            self.logger.debug("📍 Usando resolución base por defecto: 1080x1920")

        current_width, current_height = self.resolution
        scale_factor = current_width / base_width

        self.logger.debug(
            f"⚖️ Factor de escala calculado: {scale_factor:.3f} "
            f"(base: {base_width}px → actual: {current_width}px)"
        )
        return scale_factor
