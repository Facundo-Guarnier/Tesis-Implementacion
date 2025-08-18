import logging
import os
import threading
import time

import cv2
import matplotlib.path as mplPath
import numpy as np
import supervision as sv
import ultralytics as ul

from src.traffic_system.core.config_loader import load_app_settings
from src.traffic_system.core.config_models import DeteccionSettings
from src.traffic_system.core.types import Resolution
from src.traffic_system.detection.stream_processing import StreamCoordinator
from src.traffic_system.detection.ui import InfoOverlay
from src.traffic_system.detection.video_processor import VideoProcessor
from src.traffic_system.detection.zones.zone_list import ZoneList


class DetectorService:
    """
    Clase que procesa los videos, realiza la detección de objetos, dibuja
    los polígonos de zonas y los centros de cada objeto detectado.

    Attributes:
        __CLASES_SELECCIONADAS (list[int]): ID de clases seleccionadas para la detección.
        __CLASES (list[str]): Nombres de todas las clases del modelo.
        modelo (YOLO): Modelo de detección de objetos.
        tiempos_deteccion (dict): Diccionario para almacenar los tiempos de detección de los objetos.
        byte_tracker (ByteTrack): Proporciona el seguimiento de los objetos.
        video (Video): Video a procesar.
    """

    def __init__(
        self,
        detection_settings: DeteccionSettings | None = None,
        zones_instance: ZoneList | None = None,
        shutdown_event: threading.Event | None = None,
    ) -> None:
        # TODO: Eliminar el uso de load_app_settings, ya que deberia cargar desde la configuración global.
        self.settings = load_app_settings().deteccion
        self.model = ul.YOLO(f"assets/yolo_models/{self.settings.modelo}")
        self._selected_classes = [2, 3, 5, 7]  # Auto, Moto, Camion, Bus
        self._class_names = self.model.model.names

        self.zones = zones_instance if zones_instance is not None else ZoneList()

        self.detection_times_fps_normalized: dict[int, float] = (
            {}
        )  # Diccionario para almacenar tiempos de detección (normalizados por FPS)

        # Flags para control de ventanas (mantenidos para compatibilidad)
        self.window_active = False
        self.should_close = False
        self.shutdown_event = shutdown_event

        # Nuevo coordinador de streams
        self.stream_coordinator = StreamCoordinator(shutdown_event)

        # Sistema de overlay profesional
        self.info_overlay = InfoOverlay()

        self.logger = logging.getLogger(f"{self.__class__.__name__}[DetectorService]")

        # Rotación forzada configurable
        self._rotate_code: int | None = None

    def _create_fines_folder(self) -> None:
        """
        Crea la carpeta de multas si no existe y devuelve la ruta.
        """

        self.__fines_path = os.path.join(
            self.settings.path_resultados_deteccion,
            "multa",
            self.video_processor.zone.name,
            time.strftime("%Y-%m-%d_%H-%M-%S"),
        )
        log_dir = os.path.join(self.__fines_path)
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

    def _define_supervision_parameters(self) -> None:
        """
        Define los parámetros de supervisión necesario para la edición de los frames en base a la resolución del video.
        """

        # Actualizar factor de escala del overlay
        self.info_overlay.scale_factor = self.video_processor.scale_factor
        self.info_overlay._setup_style()

        #! Seguidor de los objetos.
        self.byte_tracker = sv.ByteTrack(
            # track_thresh=0.25,
            # match_thresh=0.8,
            # track_buffer=self.video.fps+25,    #! Cantidad de frames que se mantiene el seguimiento de un objeto (1 segundo)
            # frame_rate=self.video.fps,
        )

        #! Diseñador de lineas de seguimiento
        self.trace_annotator = sv.TraceAnnotator()

        #! Dibujador de box en los objetos.
        self.bounding_box_annotator = sv.BoxAnnotator(
            thickness=max(1, int(3 * self.video_processor.scale_factor)),
        )
        self.label_annotator = sv.LabelAnnotator(
            text_thickness=max(1, int(2 * self.video_processor.scale_factor)),
            text_scale=max(1, int(1 * self.video_processor.scale_factor)),
        )

        #! Escalar puntos de zona y línea de multas
        self.video_processor.zone.scale_points(self.video_processor.resolution)
        self.video_processor.zone.scale_fine_points(self.video_processor.resolution)
        self.line_zones: list[sv.LineZone] = []
        p = self.video_processor.zone.rescaled_fine_points
        for i in range(len(p) - 1):
            start = sv.Point(p[i][0], p[i][1])
            end = sv.Point(p[i + 1][0], p[i + 1][1])
            self.line_zones.append(
                sv.LineZone(
                    start=start, end=end, triggering_anchors=[sv.Position.CENTER]
                )
            )  #! Crear la línea de multa y cuenta los objetos cuando su centro cruzan la linea.

        #! Anotador de línea de multas
        self.line_zone_annotator = sv.LineZoneAnnotator(
            thickness=max(1, int(3 * self.video_processor.scale_factor)),
            text_thickness=max(1, int(2 * self.video_processor.scale_factor)),
            text_scale=max(1, int(1 * self.video_processor.scale_factor)),
        )

    def _zone_expects_portrait(self) -> bool:
        """Indicar si la zona configurada es de orientación vertical (alto >= ancho)."""
        try:
            base_w, base_h = self.video_processor.zone._resolution
            return base_h >= base_w
        except Exception:
            return True

    def _compute_display_size(
        self, width: int, height: int, max_long_side: int = 820
    ) -> Resolution:
        """Calcular tamaño de ventana manteniendo relación de aspecto."""
        if width <= 0 or height <= 0:
            return (460, 820)
        if height >= width:
            new_h = max_long_side
            new_w = max(1, int(max_long_side * (width / height)))
        else:
            new_w = max_long_side
            new_h = max(1, int(max_long_side * (height / width)))
        return (new_w, new_h)

    def _prepare_orientation_for_stream(self) -> Resolution:
        """Decidir rotación y resolución efectiva para mantener orientación de la zona.

        Returns:
            (eff_width, eff_height): Resolución efectiva tras rotación (si aplica)
        """
        width, height = self.video_processor.resolution
        zone_portrait = self._zone_expects_portrait()

        # 1) Si hay rotación forzada por configuración, aplicarla
        forced = getattr(self.settings, "forced_rotation_degrees", 0)
        forced_map = {
            0: None,
            90: cv2.ROTATE_90_CLOCKWISE,
            180: cv2.ROTATE_180,
            270: cv2.ROTATE_90_COUNTERCLOCKWISE,
        }
        self._rotate_code = forced_map.get(int(forced), None)
        if self._rotate_code is not None:
            if self._rotate_code in (
                cv2.ROTATE_90_CLOCKWISE,
                cv2.ROTATE_90_COUNTERCLOCKWISE,
            ):
                eff_w, eff_h = height, width
            else:
                eff_w, eff_h = width, height
        else:
            # 2) Si no hay forzada: Si la zona es vertical y el video llega horizontal, rotar 90° sentido horario
            if zone_portrait and width > height:
                self._rotate_code = cv2.ROTATE_90_CLOCKWISE
                eff_w, eff_h = height, width
            else:
                self._rotate_code = None
                eff_w, eff_h = width, height

        # Actualizar resolución y factor de escala si cambió
        if (eff_w, eff_h) != (width, height):
            self.video_processor.resolution = (eff_w, eff_h)
            self.video_processor.scale_factor = (
                self.video_processor._calculate_scale_factor() or 1.0
            )

        return eff_w, eff_h

    def _draw_zone_polygon(self, frame: np.ndarray) -> np.ndarray:
        """
        Dibuja el polígono de la zona de detección.
        Se ejecuta siempre, independientemente de si hay detecciones o no.
        """
        cv2.polylines(
            img=frame,
            pts=[self.video_processor.zone.rescaled_points],
            isClosed=True,
            color=(0, 0, 255),
            thickness=max(1, int(10 * self.video_processor.scale_factor)),
        )
        return frame

    def _calculate_wait_time(
        self, total_frames: float, fps_real: int | None = None
    ) -> int:
        """
        Calcula el tiempo de espera en segundos basado en el tipo de fuente.

        Args:
            total_frames: Total de frames acumulados en la zona (normalizados por FPS)
            fps_real: FPS reales de procesamiento (para streaming)

        Returns:
            Tiempo en segundos
        """
        # Lógica de cálculo de tiempo:
        # - Para videos grabados: usar FPS del video (tiempo relativo al video)
        # - Para cámara/streaming: usar FPS reales (tiempo de mundo real)
        if (
            hasattr(self.video_processor, "is_camera")
            and self.video_processor.is_camera
        ):
            # Cámara: usar FPS reales porque los frames perdidos se descartan
            fps_for_calculation = (
                fps_real
                if fps_real is not None and fps_real > 0
                else self.video_processor.fps
            )
        else:
            # Video grabado: usar FPS del video porque todos los frames se procesan secuencialmente
            fps_for_calculation = self.video_processor.fps

        if fps_for_calculation is None or fps_for_calculation <= 0:
            logging.error(
                f"FPS for calculation is invalid (value: {fps_for_calculation}). Returning wait time as 0."
            )
            return 0
        return round(total_frames / fps_for_calculation)

    def _update_zone_metrics(self, vehicle_count: int, wait_time_seconds: int) -> None:
        """
        Actualiza las métricas de la zona en el sistema.

        Args:
            vehicle_count: Número de vehículos en la zona
            wait_time_seconds: Tiempo de espera en segundos
        """
        # Actualizar zona en la lista global
        updated_zone = self.zones.get_zone_by_name(self.video_processor.zone.name)
        if updated_zone:
            updated_zone.detection_count = vehicle_count
            updated_zone.wait_time = wait_time_seconds

        # Actualizar zona local
        self.video_processor.zone.wait_time = wait_time_seconds

    def _draw_detection_centers(
        self, frame: np.ndarray, detections: sv.Detections
    ) -> tuple[np.ndarray, int]:
        """
        Dibuja los centros de los objetos detectados y cuenta los que están en la zona.

        Args:
            frame: Frame actual del video
            detections: Detecciones de objetos

        Returns:
            Tupla con (frame_modificado, cantidad_vehiculos_en_zona)
        """
        vehicles_in_zone = 0

        for box, _mask, _confidence, _class_id, tracker_id, _data in detections:
            # Calcular centro del objeto
            center_x = int((box[0] + box[2]) // 2)
            center_y = int((box[1] + box[3]) // 2)

            # Verificar si está dentro del polígono de la zona
            is_in_zone = mplPath.Path(
                self.video_processor.zone.rescaled_points
            ).contains_point((center_x, center_y))

            if is_in_zone:
                vehicles_in_zone += 1
                color = [255, 80, 0]  # Naranja para objetos en zona

                # CORRECCIÓN: Normalizar conteo de frames por FPS del video
                # para mantener consistencia temporal entre videos de diferentes FPS
                fps_normalization_factor = max(1.0, self.video_processor.fps / 30.0)

                # Contar frames de detección normalizados
                if tracker_id is not None:
                    if tracker_id in self.detection_times_fps_normalized:
                        self.detection_times_fps_normalized[
                            tracker_id
                        ] += fps_normalization_factor
                    else:
                        self.detection_times_fps_normalized[tracker_id] = (
                            fps_normalization_factor
                        )
            else:
                color = [0, 0, 255]  # Rojo para objetos fuera de zona
                # Reiniciar contador si sale de la zona
                if tracker_id is not None:
                    self.detection_times_fps_normalized[tracker_id] = 0.0

            # Dibujar centro
            cv2.circle(
                img=frame,
                center=(center_x, center_y),
                radius=max(1, int(10 * self.video_processor.scale_factor)),
                color=color,
                thickness=max(1, int(10 * self.video_processor.scale_factor)),
            )

        return frame, vehicles_in_zone

    def _process_detections_and_calculate_metrics(
        self, frame: np.ndarray, detections: sv.Detections, fps_real: int | None = None
    ) -> np.ndarray:
        """
        Procesa las detecciones, dibuja centros y calcula métricas de tiempo.

        Args:
            frame: Frame actual del video
            detections: Detecciones de objetos
            fps_real: FPS reales de procesamiento (para cálculo correcto de tiempo en streaming)
        """
        # Limpiar IDs de objetos que ya no están en la imagen
        if detections.tracker_id is not None:
            expired_tracker_ids = [
                tracker_id
                for tracker_id in self.detection_times_fps_normalized
                if tracker_id not in detections.tracker_id
            ]
            for tracker_id in expired_tracker_ids:
                del self.detection_times_fps_normalized[tracker_id]

        # Dibujar centros y contar vehículos en zona
        frame, vehicles_in_zone = self._draw_detection_centers(frame, detections)

        # Calcular métricas de tiempo
        total_frames_in_zone = sum(self.detection_times_fps_normalized.values())
        wait_time_seconds = self._calculate_wait_time(total_frames_in_zone, fps_real)

        # Actualizar métricas del sistema
        self._update_zone_metrics(vehicles_in_zone, wait_time_seconds)

        return frame

    def _add_info_overlay(self, frame: np.ndarray, fps_real: int = 0) -> np.ndarray:
        """
        Agregar overlay con información de detección.
        """
        # Obtener información del video/fuente
        fps_original = self.video_processor.fps
        source_type = "camera" if self.video_processor.is_camera else "video"

        # Obtener información de detección actual
        updated_zone = self.zones.get_zone_by_name(self.video_processor.zone.name)
        vehicle_count = updated_zone.detection_count if updated_zone else 0
        wait_time_seconds = updated_zone.wait_time if updated_zone else 0
        zone_name = self.video_processor.zone.name

        # Agregar overlay completo
        frame = self.info_overlay.add_info_overlay(
            frame=frame,
            fps_real=fps_real,
            fps_original=fps_original,
            source_type=source_type,
            vehicle_count=vehicle_count,
            wait_time_seconds=wait_time_seconds,
            zone_name=zone_name,
        )

        return frame

    def _annotate_boxes_sv(
        self, frame: np.ndarray, detections: sv.Detections
    ) -> np.ndarray:
        """
        - Dibuja una box por cada objeto.
        - Hace las etiquetas de cada box.
        """
        labels = []

        for (
            _xyxy,
            _mask,
            _confianza,
            _class_id,
            tracker_id,
            _data,
        ) in detections:
            if tracker_id is not None:
                detection_time_frames = self.detection_times_fps_normalized.get(
                    tracker_id, 0
                )
                # Convertir frames a segundos usando la misma lógica que _calculate_wait_time
                if (
                    hasattr(self.video_processor, "is_camera")
                    and self.video_processor.is_camera
                ):
                    # Para cámara: usar FPS del video (asumiendo que fps_real no está disponible aquí)
                    fps_for_calculation = self.video_processor.fps
                else:
                    # Para video grabado: usar FPS del video
                    fps_for_calculation = self.video_processor.fps

                detection_time_seconds = round(
                    detection_time_frames / fps_for_calculation
                )
                label = f"{detection_time_seconds}s"
                labels.append(label)
            else:
                labels.append("No ID")

        frame = self.bounding_box_annotator.annotate(scene=frame, detections=detections)
        frame = self.label_annotator.annotate(
            scene=frame, detections=detections, labels=labels
        )
        return frame

    def _process_fines(
        self, frame: np.ndarray, detections: sv.Detections
    ) -> np.ndarray:
        """
        Realiza la deteccion de multas y guarda la foto de la multa.

        Args:
            frame (np.ndarray): Frame actual.
            detections (sv.Detections): Detecciones de objetos en el frame.

        Returns:
            np.ndarray: Frame resultante con las multas."""
        # https://supervision.roboflow.com/latest/detection/tools/line_zone/#supervision.detection.line_zone.LineZone.trigger

        for line_zone in self.line_zones:
            crossed_in, crossed_out = line_zone.trigger(detections)
            if detections.tracker_id is not None:
                for i, tracker_id in enumerate(detections.tracker_id):
                    if crossed_out[i]:  #! Verificar si el objeto cruzó la línea
                        idx = np.where(detections.tracker_id == tracker_id)[0][0]
                        bbox = detections.xyxy[idx]
                        # class_id = detections.class_id[idx]  # Variable no utilizada

                        x1, y1, x2, y2 = map(
                            int, bbox
                        )  #! Convertir las coordenadas a enteros
                        cropped_image = frame[
                            round(y1 * 0.9) : round(y2 * 1.1),
                            round(x1 * 0.9) : round(x2 * 1.1),
                        ]

                        #! Guardar la imagen recortada
                        file_name = os.path.join(
                            self.__fines_path, f"multa_{time.strftime('%H-%M-%S')}.jpg"
                        )
                        cv2.imwrite(file_name, cropped_image)

            frame = self.line_zone_annotator.annotate(frame, line_zone)

        return frame

    def _process_frame_base(
        self, frame: np.ndarray, fps_real: int | None = None
    ) -> np.ndarray:
        """
        Lógica base de procesamiento de frames común a todos los métodos.

        Args:
            frame: Frame actual del video
            fps_real: FPS reales de procesamiento (opcional)

        Returns:
            Frame procesado con detecciones y polígono
        """
        # Ajustar orientación del frame si se definió rotación forzada
        if self._rotate_code is not None:
            frame = cv2.rotate(frame, self._rotate_code)

        # Realizar la detección/predicción de objetos
        model_results = self.model(frame, verbose=False)[0]
        detections = sv.Detections.from_ultralytics(model_results)

        # Filtrar las clases que no se necesitan
        if detections.class_id is not None:
            filtered_detections = detections[
                np.isin(detections.class_id, self._selected_classes)
            ]
            # Type guard: asegurar que el resultado sigue siendo Detections
            if isinstance(filtered_detections, sv.Detections):
                detections = filtered_detections

        # Seguimiento de objetos
        detections = self.byte_tracker.update_with_detections(detections)

        # Dibujar siempre el polígono de la zona, independientemente de si hay detecciones
        frame = self._draw_zone_polygon(frame)

        # Si hay detecciones, procesarlas
        if detections.tracker_id is not None and detections.tracker_id.size > 0:
            frame = self._process_detections_and_calculate_metrics(
                frame, detections, fps_real
            )
            frame = self.trace_annotator.annotate(frame, detections=detections)
            frame = self._annotate_boxes_sv(frame, detections)

            if self.video_processor.zone.fines_activated:
                frame = self._process_fines(frame, detections)
        else:
            # Cuando no hay detecciones activas, limpiar métricas
            self.detection_times_fps_normalized.clear()
            self._update_zone_metrics(0, 0)

        return frame

    def _process_frame_callback(
        self, frame: np.ndarray, frame_number: int
    ) -> np.ndarray:
        """
        Procesamiento de video sin información de FPS reales.
        Se ejecuta por cada frame del video grabado.
        """
        frame = self._process_frame_base(frame)
        frame = self._add_info_overlay(frame, fps_real=0)
        return frame

    def _process_frame_with_fps_callback(
        self, frame: np.ndarray, frame_number: int, fps_real: int = 0
    ) -> np.ndarray:
        """
        Procesamiento de video con información de FPS reales.
        Se ejecuta por cada frame del video en streaming/cámara.
        """
        frame = self._process_frame_base(frame, fps_real)

        # Voltear imagen horizontalmente para cámara ANTES del overlay (para que el texto se vea normal)
        if (
            hasattr(self.video_processor, "is_camera")
            and self.video_processor.is_camera
        ):
            frame = cv2.flip(frame, 1)

        frame = self._add_info_overlay(frame, fps_real=fps_real)
        return frame

    def _process_live_stream(
        self,
        source_input: str | int,
        window_name: str,
        save_output: bool = False,
        output_path: str | None = None,
        display_size: Resolution | None = None,
        override_display_size: Resolution | None = None,
    ) -> None:
        """
        Método unificado para procesar streams en vivo (video o cámara).
        Utiliza el nuevo StreamCoordinator para mejor separación de responsabilidades.

        Args:
            source_input: Path del video o índice de cámara (0 para cámara)
            window_name: Nombre de la ventana de visualización
            save_output: Si guardar el video procesado
            output_path: Path del archivo de salida (si save_output es True)
            display_size: Resolución forzada (ancho, alto) - solo para cámara
            override_display_size: Tamaño de ventana personalizado que anula la configuración
        """
        # Configurar resolución si se especifica (solo para cámara)
        if display_size and isinstance(source_input, int):
            self.video_processor.resolution = display_size
            self.video_processor.scale_factor = (
                self.video_processor._calculate_scale_factor() or 1.0
            )

        # Preparar orientación y resolución efectiva antes de escalar zonas
        eff_w, eff_h = self._prepare_orientation_for_stream()

        # Configurar parámetros de procesamiento
        self._create_fines_folder()
        self.video_processor.zone.scale_points((eff_w, eff_h))
        self.video_processor.zone.scale_fine_points((eff_w, eff_h))
        self._define_supervision_parameters()

        # Determinar path de salida
        final_output_path = None
        if save_output:
            final_output_path = output_path or self.video_processor.result_path

        # Usar StreamCoordinator para procesar con FPS callback
        # Configurar tamaño de ventana según configuración
        if override_display_size:
            # Usar el tamaño personalizado si se proporciona
            computed_display_size = override_display_size
        elif getattr(self.settings, "window_fixed", True):
            ws = getattr(self.settings, "window_size", [460, 820])
            computed_display_size = (int(ws[0]), int(ws[1]))
        else:
            computed_display_size = self._compute_display_size(eff_w, eff_h)
        self.stream_coordinator.process_stream_with_fps_callback(
            source_input=source_input,
            window_name=window_name,
            frame_processor_with_fps=self._process_frame_with_fps_callback,
            save_output=save_output,
            output_path=final_output_path,
            display_size=computed_display_size,
            scale_factor=getattr(self.video_processor, "scale_factor", 1.0),
        )

    def process_and_save_video(self, video_processor: VideoProcessor) -> None:
        """
        Procesa un video y guarda el resultado sin mostrarlo en una ventana en vivo.
        """

        self.video_processor = video_processor
        self._create_fines_folder()
        self.video_processor.zone.scale_points(self.video_processor.resolution)
        self.video_processor.zone.scale_fine_points(self.video_processor.resolution)
        self._define_supervision_parameters()
        self.logger.info(
            f"⚙️ Factor de escala aplicado: {self.video_processor.scale_factor}"
        )

        sv.process_video(
            source_path=video_processor.origin_path,
            target_path=video_processor.result_path,
            callback=self._process_frame_callback,
        )

    def process_and_show_live_video(self, video_processor: VideoProcessor) -> None:
        """
        Procesa un video y muestra el resultado en vivo.
        """
        self.video_processor = video_processor
        save_output = self.settings.un_video.guardar

        # Para videos: SIEMPRE usar el window_size del config [460, 820]
        ws = getattr(self.settings, "window_size", [460, 820])
        video_display_size = (int(ws[0]), int(ws[1]))

        self._process_live_stream(
            source_input=video_processor.origin_path,
            window_name="Detectando en un video",
            save_output=save_output,
            output_path=video_processor.result_path if save_output else None,
            override_display_size=video_display_size,
        )

    def process_camera(self, video_processor: VideoProcessor) -> None:
        """
        Procesa la cámara en vivo y muestra el resultado en tiempo real.
        """
        self.video_processor = video_processor

        # Usar tamaño apropiado para cámara 4:3 (800x600)
        # Esto es más apropiado que el hardcodeado anterior (820x460)
        camera_display_size = (800, 600)

        self._process_live_stream(
            source_input=0,  # Cámara
            window_name="Detectando con camara",
            save_output=False,
            output_path=None,
            display_size=camera_display_size,
            override_display_size=camera_display_size,
        )
