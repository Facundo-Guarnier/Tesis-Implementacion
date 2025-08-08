"""
Coordinador de stream - Orquesta el procesamiento de video/cámara
================================================================
"""

import logging
import time
from collections.abc import Callable
from typing import Any

import cv2
import numpy as np

from .output_manager import OutputManager
from .stream_sources import CameraStreamSource, StreamSource, VideoStreamSource
from .window_manager import WindowManager


class StreamCoordinator:
    """Coordina el procesamiento de streams de video/cámara"""

    def __init__(self, shutdown_event: Any = None):
        self.shutdown_event = shutdown_event
        self.logger = logging.getLogger(f"{self.__class__.__name__}")

    def process_stream(
        self,
        source_input: str | int,
        window_name: str,
        frame_processor: Callable[[np.ndarray, int], np.ndarray],
        save_output: bool = False,
        output_path: str | None = None,
        display_size: tuple[int, int] | None = None,
        scale_factor: float = 1.0,
    ) -> None:
        """
        Procesar stream de video o cámara

        Args:
            source_input: Path del video o índice de cámara
            window_name: Nombre de la ventana
            frame_processor: Función para procesar cada frame
            save_output: Si guardar el video procesado
            output_path: Path del archivo de salida
            display_size: Tamaño de visualización
            scale_factor: Factor de escala para FPS display
        """
        # Crear fuente de stream apropiada
        stream_source = self._create_stream_source(source_input, display_size)
        if not stream_source.setup():
            self.logger.error("❌ Error configurando fuente de stream")
            return

        # Configurar componentes
        window_manager = WindowManager(window_name)
        output_manager = OutputManager(output_path if save_output else None)

        try:
            # Configurar ventana
            if not window_manager.create_window(display_size):
                return

            # Configurar salida si se requiere
            if save_output and output_path:
                props = stream_source.get_properties()
                if not output_manager.setup_writer(
                    fps=props.get("fps", 30.0),
                    frame_width=props.get("width", 640),
                    frame_height=props.get("height", 480),
                ):
                    self.logger.warning("⚠️ No se pudo configurar salida de video")

            # Procesar stream
            self._process_frames(
                stream_source=stream_source,
                window_manager=window_manager,
                output_manager=output_manager,
                frame_processor=frame_processor,
                source_input=source_input,
                scale_factor=scale_factor,
            )

        finally:
            # Cleanup de todos los componentes
            stream_source.cleanup()
            window_manager.cleanup()
            output_manager.cleanup()

    def _create_stream_source(
        self, source_input: str | int, display_size: tuple[int, int] | None
    ) -> StreamSource:
        """Crear la fuente de stream apropiada"""
        if isinstance(source_input, int):
            return CameraStreamSource(source_input, display_size)
        else:
            return VideoStreamSource(source_input)

    def _process_frames(
        self,
        stream_source: StreamSource,
        window_manager: WindowManager,
        output_manager: OutputManager,
        frame_processor: Callable[[np.ndarray, int], np.ndarray],
        source_input: str | int,
        scale_factor: float = 1.0,
    ) -> None:
        """Procesar frames del stream"""
        fps = 0
        frames_in_second = 0
        second_start_time = time.time()
        total_frames_processed = 0

        while window_manager.is_active and (
            self.shutdown_event is None or not self.shutdown_event.is_set()
        ):
            frames_in_second += 1
            total_frames_processed += 1

            # Leer frame
            ret, frame = stream_source.read_frame()
            if not ret or frame is None:
                if isinstance(source_input, int):
                    self.logger.warning("⚠️ No se puede leer de la cámara")
                else:
                    self.logger.info("📺 Final del video alcanzado")
                break

            # Procesar frame
            frame = frame_processor(frame, total_frames_processed)

            # Agregar FPS al frame
            frame = self._add_fps_overlay(frame, fps, source_input, scale_factor)

            # Guardar frame si se requiere
            if output_manager.is_ready:
                output_manager.write_frame(frame)

            # Mostrar frame
            if not window_manager.show_frame(frame):
                break

            # Verificar entrada de teclado
            key = window_manager.check_keyboard_input()
            if key == "q":
                stream_type = "cámara" if isinstance(source_input, int) else "video"
                self.logger.info(f"⌨️ Tecla 'q' presionada, cerrando {stream_type}")
                break

            # Calcular FPS
            if time.time() - second_start_time >= 1:
                fps = frames_in_second
                frames_in_second = 0
                second_start_time = time.time()

    def _add_fps_overlay(
        self,
        frame: np.ndarray,
        fps: int,
        source_input: str | int,
        scale_factor: float = 1.0,
    ) -> np.ndarray:
        """Agregar overlay de FPS al frame"""

        cv2.putText(
            frame,
            f"FPS: {fps}",
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            1 * scale_factor,
            (0, 255, 0),
            2,
        )
        return frame
