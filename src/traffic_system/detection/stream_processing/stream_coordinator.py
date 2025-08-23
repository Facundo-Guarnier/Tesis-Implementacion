import logging
import time
from collections.abc import Callable
from typing import Any

import numpy as np

from src.traffic_system.core.types import Resolution

from ..ui import InfoOverlay
from .output_manager import OutputManager
from .stream_sources import CameraStreamSource, StreamSource, VideoStreamSource
from .window_manager import WindowManager


class StreamCoordinator:
    """Coordina el procesamiento de streams de video/cámara"""

    def __init__(self, shutdown_event: Any = None):
        self.shutdown_event = shutdown_event
        self.logger = logging.getLogger(f"{self.__class__.__name__}")
        self.info_overlay = InfoOverlay()  # Inicializar overlay de información

    def _compute_display_size(
        self, width: int, height: int, max_long_side: int = 820
    ) -> Resolution:
        """Calcular tamaño de ventana manteniendo relación de aspecto del stream"""
        try:
            if width <= 0 or height <= 0:
                return (460, 820)

            if height >= width:
                # Retrato
                new_height = max_long_side
                new_width = max(1, int(max_long_side * (width / height)))
            else:
                # Apaisado
                new_width = max_long_side
                new_height = max(1, int(max_long_side * (height / width)))

            return (new_width, new_height)
        except Exception:
            return (460, 820)

    def process_stream(
        self,
        source_input: str | int,
        window_name: str,
        frame_processor: Callable[[np.ndarray, int], np.ndarray],
        save_output: bool = False,
        output_path: str | None = None,
        display_size: Resolution | None = None,
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
        # Actualizar factor de escala del overlay
        self.info_overlay.scale_factor = scale_factor
        self.info_overlay._setup_style()

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
            computed_display_size = display_size
            if computed_display_size is None:
                props = stream_source.get_properties()
                computed_display_size = self._compute_display_size(
                    int(props.get("width", 0)), int(props.get("height", 0))
                )

            if not window_manager.create_window(computed_display_size):
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
        self, source_input: str | int, display_size: Resolution | None
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

        # Obtener FPS originales del video/fuente
        source_properties = stream_source.get_properties()
        original_fps = source_properties.get("fps", 0.0)
        source_type = source_properties.get("source_type", "unknown")

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

            # Agregar FPS al frame (reales y originales) - solo para streams sin procesamiento completo
            frame = self._add_fps_overlay(frame, fps, original_fps, source_type)

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
        real_fps: int,
        original_fps: float,
        source_type: str,
    ) -> np.ndarray:
        """Agregar overlay simplificado de FPS para streams sin detección completa"""
        return self.info_overlay.add_simple_fps_overlay(
            frame=frame,
            fps_real=real_fps,
            fps_original=original_fps,
            source_type=source_type,
        )

    def process_stream_with_fps_callback(
        self,
        source_input: str | int,
        window_name: str | None,
        frame_processor_with_fps: Callable[[np.ndarray, int, int], np.ndarray],
        save_output: bool = False,
        output_path: str | None = None,
        display_size: Resolution | None = None,
        scale_factor: float = 1.0,
    ) -> None:
        """
        Versión mejorada que pasa los FPS reales al frame processor

        Args:
            window_name: Nombre de ventana o None para procesamiento sin ventana (headless)
            frame_processor_with_fps: Función que acepta (frame, frame_number, fps_real)
        """
        # Actualizar factor de escala del overlay
        self.info_overlay.scale_factor = scale_factor
        self.info_overlay._setup_style()

        # Crear fuente de stream apropiada
        stream_source = self._create_stream_source(source_input, display_size)
        if not stream_source.setup():
            self.logger.error("❌ Error configurando fuente de stream")
            return

        # Configurar componentes
        window_manager = None
        if window_name is not None:
            window_manager = WindowManager(window_name)

        output_manager = OutputManager(output_path if save_output else None)

        try:
            # Configurar ventana solo si se requiere
            if window_manager is not None:
                computed_display_size = display_size
                if computed_display_size is None:
                    props = stream_source.get_properties()
                    computed_display_size = self._compute_display_size(
                        int(props.get("width", 0)), int(props.get("height", 0))
                    )

                if not window_manager.create_window(computed_display_size):
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

            # Procesar stream con FPS callback
            self._process_frames_with_fps_callback(
                stream_source=stream_source,
                window_manager=window_manager,
                output_manager=output_manager,
                frame_processor_with_fps=frame_processor_with_fps,
                source_input=source_input,
            )

        finally:
            # Cleanup de todos los componentes
            stream_source.cleanup()
            if window_manager is not None:
                window_manager.cleanup()
            output_manager.cleanup()

    def _process_frames_with_fps_callback(
        self,
        stream_source: StreamSource,
        window_manager: WindowManager | None,
        output_manager: OutputManager,
        frame_processor_with_fps: Callable[[np.ndarray, int, int], np.ndarray],
        source_input: str | int,
    ) -> None:
        """Procesar frames del stream pasando FPS al callback"""
        fps = 0
        frames_in_second = 0
        second_start_time = time.time()
        total_frames_processed = 0

        # Condición de loop: si hay ventana, usar window_manager.is_active; si no, usar shutdown_event
        while (window_manager is None or window_manager.is_active) and (
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

            # Procesar frame con FPS (el overlay se agrega dentro del processor)
            frame = frame_processor_with_fps(frame, total_frames_processed, fps)

            # Guardar frame si se requiere
            if output_manager.is_ready:
                output_manager.write_frame(frame)

            # Mostrar frame solo si hay ventana
            if window_manager is not None:
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
