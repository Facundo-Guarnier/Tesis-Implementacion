import logging
from abc import ABC, abstractmethod

import cv2
import numpy as np

from src.traffic_system.core.types import Resolution


class StreamSource(ABC):
    """Clase base abstracta para fuentes de stream (video/cámara)"""

    def __init__(self, source_input: str | int):
        self.source_input = source_input
        self.cap: cv2.VideoCapture | None = None
        self.logger = logging.getLogger(f"{self.__class__.__name__}")

    @abstractmethod
    def setup(self) -> bool:
        """Configurar la fuente de stream"""
        pass

    @abstractmethod
    def read_frame(self) -> tuple[bool, np.ndarray | None]:
        """Leer el siguiente frame"""
        pass

    @abstractmethod
    def get_properties(self) -> dict:
        """Obtener propiedades del stream"""
        pass

    def cleanup(self) -> None:
        """Limpiar recursos"""
        if self.cap:
            self.cap.release()
            self.cap = None


class VideoStreamSource(StreamSource):
    """Fuente de stream para archivos de video"""

    def __init__(self, video_path: str):
        super().__init__(video_path)
        self.video_path = video_path

    def setup(self) -> bool:
        """Configurar el video"""
        self.cap = cv2.VideoCapture(self.video_path)
        success = self.cap.isOpened()
        if success:
            self.logger.info(f"🎥 Video cargado: {self.video_path}")
        else:
            self.logger.error(f"❌ Error cargando video: {self.video_path}")
        return success

    def read_frame(self) -> tuple[bool, np.ndarray | None]:
        """Leer frame del video"""
        if not self.cap:
            return False, None
        ret, frame = self.cap.read()
        return ret, frame if ret else None

    def get_properties(self) -> dict:
        """Obtener propiedades del video"""
        if not self.cap:
            return {}

        return {
            "fps": self.cap.get(cv2.CAP_PROP_FPS),
            "width": int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            "height": int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            "frame_count": int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT)),
            "source_type": "video",
        }


class LoopingVideoStreamSource(VideoStreamSource):
    """Fuente de stream para archivos de video con loop infinito"""

    def __init__(self, video_path: str):
        super().__init__(video_path)
        self.total_loops = 0

    def read_frame(self) -> tuple[bool, np.ndarray | None]:
        """Leer frame del video con reinicio automático al final"""
        if not self.cap:
            return False, None

        ret, frame = self.cap.read()

        # Si llegamos al final del video, reiniciarlo
        if not ret:
            self.total_loops += 1
            self.logger.info(
                f"🔄 Reiniciando video (loop #{self.total_loops}): {self.video_path}"
            )

            # Reiniciar el video al frame 0
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ret, frame = self.cap.read()

        return ret, frame if ret else None


class CameraStreamSource(StreamSource):
    """Fuente de stream para cámara"""

    def __init__(self, camera_index: int, display_size: Resolution | None = None):
        super().__init__(camera_index)
        self.camera_index = camera_index
        self.display_size = display_size

    def setup(self) -> bool:
        """Configurar la cámara"""
        self.cap = cv2.VideoCapture(self.camera_index)
        success = self.cap.isOpened()
        if success:
            self.logger.info(f"📹 Cámara conectada: índice {self.camera_index}")
            # Configurar resolución si se especifica
            if self.display_size:
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.display_size[0])
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.display_size[1])
        else:
            self.logger.error(f"❌ Error conectando cámara: índice {self.camera_index}")
        return success

    def read_frame(self) -> tuple[bool, np.ndarray | None]:
        """Leer frame de la cámara"""
        if not self.cap:
            return False, None

        ret, frame = self.cap.read()

        # Redimensionar si se especifica display_size
        if ret and frame is not None and self.display_size:
            frame = cv2.resize(frame, self.display_size)

        return ret, frame if ret else None

    def get_properties(self) -> dict:
        """Obtener propiedades de la cámara"""
        if not self.cap:
            return {}

        return {
            "fps": self.cap.get(cv2.CAP_PROP_FPS),
            "width": int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            "height": int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            "frame_count": -1,  # Indefinido para cámara
            "source_type": "camera",
        }
