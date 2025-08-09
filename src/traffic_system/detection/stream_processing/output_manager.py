import logging
from pathlib import Path

import cv2
import numpy as np


class OutputManager:
    """Gestiona la escritura de videos procesados"""

    def __init__(self, output_path: str | None = None):
        self.output_path = output_path
        self.writer: cv2.VideoWriter | None = None
        self.logger = logging.getLogger(f"{self.__class__.__name__}")

    def setup_writer(
        self,
        fps: float,
        frame_width: int,
        frame_height: int,
        fourcc: int = cv2.VideoWriter_fourcc(*"mp4v"),  # type: ignore
    ) -> bool:
        """
        Configurar el escritor de video

        Args:
            fps: Frames por segundo
            frame_width: Ancho del frame
            frame_height: Alto del frame
            fourcc: Codec de video

        Returns:
            bool: True si se configuró exitosamente
        """
        if not self.output_path:
            return False

        try:
            # Crear directorio si no existe
            Path(self.output_path).parent.mkdir(parents=True, exist_ok=True)

            self.writer = cv2.VideoWriter(
                filename=self.output_path,
                fourcc=fourcc,
                fps=fps,
                frameSize=(frame_width, frame_height),
            )

            if self.writer.isOpened():
                self.logger.info(f"📹 Video de salida configurado: {self.output_path}")
                return True
            else:
                self.logger.error(
                    f"❌ Error configurando video de salida: {self.output_path}"
                )
                return False

        except Exception as e:
            self.logger.error(f"❌ Error configurando OutputManager: {e}")
            return False

    def write_frame(self, frame: cv2.Mat | np.ndarray) -> bool:
        """
        Escribir frame al video de salida

        Args:
            frame: Frame a escribir

        Returns:
            bool: True si se escribió exitosamente
        """
        if not self.writer:
            return False

        try:
            self.writer.write(frame)
            return True
        except Exception as e:
            self.logger.error(f"❌ Error escribiendo frame: {e}")
            return False

    def cleanup(self) -> None:
        """Limpiar recursos del escritor"""
        if self.writer:
            self.writer.release()
            self.writer = None
            if self.output_path:
                self.logger.info(f"💾 Video guardado: {self.output_path}")

    @property
    def is_ready(self) -> bool:
        """Verificar si el escritor está listo"""
        return self.writer is not None and self.writer.isOpened()
