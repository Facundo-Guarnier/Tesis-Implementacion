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

        # Sistema de multas mejorado - Una carpeta por sesión
        self._session_timestamp = time.strftime("%Y-%m-%d_%H-%M-%S")
        self._fines_folder_created = False
        self.__fines_path = ""  # Se inicializa cuando sea necesario

        # Sistema de histéresis para prevenir ruido en detecciones de líneas
        self._vehicle_crossing_history: dict[int, dict[str, str | float]] = {}
        # Tiempo en segundos para ignorar direcciones opuestas
        self._hysteresis_time_seconds = 2.0

        # Contador para limpieza periódica del historial de cruzamientos
        self._cleanup_counter: int = 0

        # Sistema de memoria temporal para preservar tiempos durante oclusiones
        self._temporary_time_memory: dict[int, float] = {}  # ID -> tiempo_acumulado
        self._time_memory_timeout = (
            3.0  # Segundos para mantener memoria de IDs perdidos
        )
        self._last_seen_timestamp: dict[int, float] = (
            {}
        )  # ID -> timestamp_ultima_vez_visto

    def _create_fines_folder(self) -> None:
        """
        Crea la carpeta de multas con el nuevo formato si no existe.
        Formato: results/detection_results/multa/<fecha-hora-sesion>/Zona A
        Solo se crea cuando efectivamente se va a guardar una multa.
        """
        if self._fines_folder_created:
            return  # Ya se creó la carpeta para esta sesión y zona

        self.__fines_path = os.path.join(
            self.settings.path_resultados_deteccion,
            "multa",
            self._session_timestamp,
            self.video_processor.zone.name,
        )

        if not os.path.exists(self.__fines_path):
            os.makedirs(self.__fines_path)
            self.logger.info(f"📁 Carpeta de multas creada: {self.__fines_path}")

        self._fines_folder_created = True

    def _define_supervision_parameters(self) -> None:
        """
        Define los parámetros de supervisión necesario para la edición de los frames en base a la resolución del video.
        """

        # Actualizar factor de escala del overlay
        self.info_overlay.scale_factor = self.video_processor.scale_factor
        self.info_overlay._setup_style()

        #! Seguidor de los objetos - Configuración optimizada para persistencia
        self.byte_tracker = sv.ByteTrack(
            track_activation_threshold=0.3,
            minimum_matching_threshold=0.8,
            lost_track_buffer=int(self.video_processor.fps * 2),
            frame_rate=int(self.video_processor.fps),
            minimum_consecutive_frames=1,
        )

        #! Diseñador de lineas de seguimiento
        self.trace_annotator = sv.TraceAnnotator()

        #! Dibujador de box en los objetos (sin color fijo - será dinámico)
        self.bounding_box_annotator = sv.BoxAnnotator(
            thickness=max(1, int(3 * self.video_processor.scale_factor)),
        )
        self.label_annotator = sv.LabelAnnotator(
            text_thickness=max(1, int(2 * self.video_processor.scale_factor)),
            text_scale=max(1, int(1 * self.video_processor.scale_factor)),
        )

        # Colores pasteles para objetos dentro y fuera de zona
        self.color_inside_zone = (144, 238, 144)  # Verde pastel claro (Light Green)
        self.color_outside_zone = (255, 182, 193)  # Rosa pastel claro (Light Pink)

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
                center_color = (144, 238, 144)  # Verde pastel - mismo color que borde

                # CORRECCIÓN: Normalizar conteo de frames por FPS del video
                # para mantener consistencia temporal entre videos de diferentes FPS
                fps_normalization_factor = max(1.0, self.video_processor.fps / 30.0)

                # Sistema mejorado: preservar tiempo acumulado durante oclusiones
                if tracker_id is not None:
                    current_time = time.time()
                    self._last_seen_timestamp[tracker_id] = current_time

                    # CASO 1: Retorno DENTRO del polígono tras oclusión
                    if tracker_id in self._temporary_time_memory:
                        # Restaurar tiempo desde memoria temporal
                        restored_time = self._temporary_time_memory[tracker_id]
                        self.detection_times_fps_normalized[tracker_id] = restored_time
                        # Limpiar de memoria temporal ya que está activo
                        del self._temporary_time_memory[tracker_id]
                        self.logger.debug(
                            f"🔄 ID {tracker_id}: Retornó DENTRO del polígono, tiempo restaurado: {restored_time:.1f}"
                        )

                    # Continuar acumulando tiempo normalmente
                    if tracker_id in self.detection_times_fps_normalized:
                        self.detection_times_fps_normalized[
                            tracker_id
                        ] += fps_normalization_factor
                    else:
                        self.detection_times_fps_normalized[tracker_id] = (
                            fps_normalization_factor
                        )
            else:
                center_color = (255, 182, 193)  # Rosa pastel - mismo color que borde

                # CASO 2: Retorno FUERA del polígono tras oclusión
                if tracker_id is not None and tracker_id in self._temporary_time_memory:
                    # El vehículo reapareció pero FUERA del polígono → descartar tiempo
                    lost_time = self._temporary_time_memory[tracker_id]
                    del self._temporary_time_memory[tracker_id]
                    if tracker_id in self._last_seen_timestamp:
                        del self._last_seen_timestamp[tracker_id]
                    self.logger.debug(
                        f"❌ ID {tracker_id}: Retornó FUERA del polígono, tiempo descartado: {lost_time:.1f}"
                    )

                # CASO 3: Salida física visible (cuando estaba dentro y ahora sale)
                elif (
                    tracker_id is not None
                    and tracker_id in self.detection_times_fps_normalized
                ):
                    current_time = time.time()
                    accumulated_time = self.detection_times_fps_normalized[tracker_id]

                    if accumulated_time > 0:
                        self._temporary_time_memory[tracker_id] = accumulated_time
                        self._last_seen_timestamp[tracker_id] = current_time
                        self.logger.debug(
                            f"↗️ ID {tracker_id}: Salió FÍSICAMENTE del polígono, tiempo guardado en memoria: {accumulated_time:.1f}"
                        )

                    # Limpiar del contador activo
                    del self.detection_times_fps_normalized[tracker_id]

            # Dibujar punto relleno pequeño en el centro del objeto (mismo color que borde)
            cv2.circle(
                img=frame,
                center=(center_x, center_y),
                radius=max(
                    1, int(10 * self.video_processor.scale_factor)
                ),  # Punto pequeño
                color=center_color,  # Mismo color que el borde del rectángulo
                thickness=-1,  # -1 significa relleno completo
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
        # Gestión inteligente de IDs que desaparecen: mover a memoria temporal en lugar de eliminar
        if detections.tracker_id is not None:
            current_time = time.time()

            # Encontrar IDs que ya no están presentes en las detecciones actuales
            expired_tracker_ids = [
                tracker_id
                for tracker_id in self.detection_times_fps_normalized
                if tracker_id not in detections.tracker_id
            ]

            # Mover IDs expirados a memoria temporal en lugar de eliminarlos
            for tracker_id in expired_tracker_ids:
                # Solo mover a memoria temporal si tenía tiempo acumulado significativo
                accumulated_time = self.detection_times_fps_normalized[tracker_id]
                if accumulated_time > 0:
                    self._temporary_time_memory[tracker_id] = accumulated_time
                    self.logger.debug(
                        f"💾 ID {tracker_id}: Movido a memoria temporal ({accumulated_time:.1f} frames)"
                    )

                # Remover de contador activo
                del self.detection_times_fps_normalized[tracker_id]

            # Limpiar memoria temporal de IDs muy antiguos (que exceden el timeout)
            expired_memory_ids = [
                tracker_id
                for tracker_id, last_seen in self._last_seen_timestamp.items()
                if current_time - last_seen > self._time_memory_timeout
                and tracker_id in self._temporary_time_memory
            ]

            for tracker_id in expired_memory_ids:
                lost_time = self._temporary_time_memory[tracker_id]
                del self._temporary_time_memory[tracker_id]
                if tracker_id in self._last_seen_timestamp:
                    del self._last_seen_timestamp[tracker_id]
                self.logger.debug(
                    f"🗑️ ID {tracker_id}: Memoria temporal expirada ({lost_time:.1f} frames perdidos)"
                )

        # Incluir tiempo de memoria temporal en el cálculo total
        total_frames_active = sum(self.detection_times_fps_normalized.values())
        total_frames_in_memory = sum(self._temporary_time_memory.values())
        total_frames_in_zone = total_frames_active + total_frames_in_memory

        # Dibujar centros y contar vehículos en zona
        frame, vehicles_in_zone = self._draw_detection_centers(frame, detections)
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
            show_fps=self.settings.debug.show_fps,
        )

        return frame

    def _annotate_boxes_sv(
        self, frame: np.ndarray, detections: sv.Detections
    ) -> np.ndarray:
        """
        - Dibuja una box por cada objeto con colores pasteles.
        - Verde pastel para objetos dentro de la zona, rosa pastel para objetos fuera.
        """
        # Crear anotadores separados para cada tipo de objeto
        box_annotator_inside = sv.BoxAnnotator(
            color=sv.Color(r=144, g=238, b=144),  # Verde pastel
            thickness=max(1, int(3 * self.video_processor.scale_factor)),
        )
        box_annotator_outside = sv.BoxAnnotator(
            color=sv.Color(r=255, g=182, b=193),  # Rosa pastel
            thickness=max(1, int(3 * self.video_processor.scale_factor)),
        )

        # Separar detecciones por ubicación
        inside_masks = []
        outside_masks = []

        for box, _mask, _confidence, _class_id, _tracker_id, _data in detections:
            # Calcular centro del objeto
            center_x = int((box[0] + box[2]) // 2)
            center_y = int((box[1] + box[3]) // 2)

            # Verificar si está dentro del polígono de la zona
            is_in_zone = mplPath.Path(
                self.video_processor.zone.rescaled_points
            ).contains_point((center_x, center_y))

            if is_in_zone:
                inside_masks.append(True)
                outside_masks.append(False)
            else:
                inside_masks.append(False)
                outside_masks.append(True)

        # Crear detecciones filtradas
        if len(inside_masks) > 0:
            inside_filter = np.array(inside_masks)
            if np.any(inside_filter):
                inside_detections = detections[inside_filter]
                frame = box_annotator_inside.annotate(
                    scene=frame, detections=inside_detections
                )

            outside_filter = np.array(outside_masks)
            if np.any(outside_filter):
                outside_detections = detections[outside_filter]
                frame = box_annotator_outside.annotate(
                    scene=frame, detections=outside_detections
                )

        # Mostrar IDs de tracking si está activado en debug
        if self.settings.debug.show_object_ids and detections.tracker_id is not None:
            labels = [f"ID: {tracker_id}" for tracker_id in detections.tracker_id]
            frame = self.label_annotator.annotate(
                scene=frame, detections=detections, labels=labels
            )

        return frame

    def _draw_line_zones_with_counters(self, frame: np.ndarray) -> np.ndarray:
        """
        Dibuja las líneas de multa. Si _show_debug_counters=True muestra contadores,
        si no, dibuja líneas simples sin contadores.

        Args:
            frame: Frame donde dibujar las líneas

        Returns:
            Frame con las líneas de multa dibujadas
        """
        frame_with_lines = frame.copy()

        for line_zone in self.line_zones:
            frame_with_lines = self.line_zone_annotator.annotate(
                frame=frame_with_lines, line_counter=line_zone
            )
        return frame_with_lines

    def _draw_line_zones_without_counters(self, frame: np.ndarray) -> np.ndarray:
        """
        Dibuja las líneas de multa sin los contadores "in" y "out".

        Args:
            frame: Frame donde dibujar las líneas

        Returns:
            Frame con las líneas de multa dibujadas (sin contadores)
        """
        frame_with_lines = frame.copy()

        # Dibujar cada línea de zona manualmente sin contadores
        for line_zone in self.line_zones:
            # Obtener puntos de inicio y fin de la línea desde el vector
            start_point = (int(line_zone.vector.start.x), int(line_zone.vector.start.y))
            end_point = (int(line_zone.vector.end.x), int(line_zone.vector.end.y))

            # Dibujar la línea blanca sin texto
            cv2.line(
                img=frame_with_lines,
                pt1=start_point,
                pt2=end_point,
                color=(255, 255, 255),  # Blanco
                thickness=max(1, int(3 * self.video_processor.scale_factor)),
            )

        return frame_with_lines

    def _should_process_line_crossing(self, tracker_id: int, direction: str) -> bool:
        """
        Implementa histéresis temporal para prevenir ruido en detecciones de líneas.
        LÓGICA CORREGIDA: Una vez que un vehículo cruza en CUALQUIER dirección,
        se ignoran TODOS los cruzamientos de ese vehículo por X segundos.

        Esto previene el problema donde el bbox se achica y causa múltiples
        cruzamientos del mismo vehículo.

        Args:
            tracker_id: ID del objeto trackeado
            direction: 'in' o 'out'

        Returns:
            True si la detección debe procesarse, False si debe ignorarse por histéresis
        """
        current_time = time.time()

        # Si es la primera vez que vemos este tracker_id, permitir la detección
        if tracker_id not in self._vehicle_crossing_history:
            self._vehicle_crossing_history[tracker_id] = {
                "direction": direction,
                "timestamp": current_time,
            }
            return True

        last_crossing = self._vehicle_crossing_history[tracker_id]
        time_since_last = current_time - float(last_crossing["timestamp"])

        # Si ha pasado suficiente tiempo, permitir la detección
        if time_since_last >= self._hysteresis_time_seconds:
            self._vehicle_crossing_history[tracker_id] = {
                "direction": direction,
                "timestamp": current_time,
            }
            return True

        # LÓGICA CORREGIDA: Si NO ha pasado suficiente tiempo, ignorar CUALQUIER cruzamiento
        # (sin importar si es la misma dirección o dirección opuesta)
        self.logger.debug(
            f"🔇 Ignorando cruzamiento {direction} de tracker {tracker_id} "
            f"(último cruzamiento {last_crossing['direction']} hace {time_since_last:.2f}s)"
        )
        return False

    def _cleanup_old_crossing_history(self) -> None:
        """
        Limpia entradas del historial de cruzamientos que son muy antiguas.
        Evita memory leaks manteniendo solo entradas recientes.
        """
        current_time = time.time()
        cleanup_threshold = (
            self._hysteresis_time_seconds * 3
        )  # Mantener 3x el tiempo de histéresis

        # Crear lista de tracker_ids a eliminar para evitar modificar dict durante iteración
        to_remove = [
            tracker_id
            for tracker_id, crossing_data in self._vehicle_crossing_history.items()
            if current_time - float(crossing_data["timestamp"]) > cleanup_threshold
        ]

        for tracker_id in to_remove:
            del self._vehicle_crossing_history[tracker_id]

        if to_remove:
            self.logger.debug(
                f"🧹 Limpiados {len(to_remove)} registros antiguos del historial de cruzamientos"
            )

    def _draw_fine_lines_only(self, frame: np.ndarray) -> np.ndarray:
        """
        Dibuja únicamente las líneas de multa en un frame limpio.

        Args:
            frame: Frame limpio donde dibujar solo las líneas de multa

        Returns:
            Frame con solo las líneas de multa dibujadas
        """
        # Dibujar líneas de multa con o sin contadores según configuración de debug
        if self.settings.debug.show_multas_counter:
            return self._draw_line_zones_with_counters(frame)
        else:
            return self._draw_line_zones_without_counters(frame)

    def _process_fines(
        self, frame: np.ndarray, detections: sv.Detections, clean_frame: np.ndarray
    ) -> np.ndarray:
        """
        Realiza la deteccion de multas y guarda la foto de la multa.

        Args:
            frame (np.ndarray): Frame actual con todos los elementos visuales.
            detections (sv.Detections): Detecciones de objetos en el frame.
            clean_frame (np.ndarray): Frame limpio para generar imágenes de multa.

        Returns:
            np.ndarray: Frame resultante con las multas."""
        # https://supervision.roboflow.com/latest/detection/tools/line_zone/#supervision.detection.line_zone.LineZone.trigger

        for line_zone in self.line_zones:
            crossed_in, crossed_out = line_zone.trigger(detections)
            if detections.tracker_id is not None:
                for i, tracker_id in enumerate(detections.tracker_id):
                    # Aplicar histéresis temporal para prevenir ruido TANTO para "in" como "out"
                    should_process_out = crossed_out[
                        i
                    ] and self._should_process_line_crossing(tracker_id, "out")

                    # IMPORTANTE: También registrar "in" en histéresis (aunque no se procese)
                    # para prevenir "out" inmediatos después de "in"
                    if crossed_in[i]:
                        self._should_process_line_crossing(tracker_id, "in")

                    if (
                        should_process_out
                    ):  #! Verificar si el objeto cruzó la línea (con histéresis)
                        idx = np.where(detections.tracker_id == tracker_id)[0][0]
                        bbox = detections.xyxy[idx]
                        # class_id = detections.class_id[idx]  # Variable no utilizada

                        x1, y1, x2, y2 = map(
                            int, bbox
                        )  #! Convertir las coordenadas a enteros

                        # Crear frame limpio solo con líneas de multa para la imagen guardada
                        fine_frame = self._draw_fine_lines_only(clean_frame)
                        cropped_image = fine_frame[
                            round(y1 * 0.9) : round(y2 * 1.1),
                            round(x1 * 0.9) : round(x2 * 1.1),
                        ]

                        #! Crear carpeta solo cuando se va a guardar una multa (lazy creation)
                        if not self._fines_folder_created:
                            self._create_fines_folder()

                        #! Guardar la imagen recortada limpia con timestamp único
                        current_time = time.time()
                        timestamp = time.strftime(
                            "%H-%M-%S", time.localtime(current_time)
                        )
                        milliseconds = int((current_time % 1) * 1000)

                        file_name = os.path.join(
                            self.__fines_path,
                            f"multa_{timestamp}-{milliseconds:03d}.jpg",
                        )
                        cv2.imwrite(file_name, cropped_image)
                        self.logger.info(
                            f"🚨 Multa guardada (imagen limpia): {file_name}"
                        )

        # Las líneas de multa se dibujan siempre en _process_frame_base cuando están activadas
        # No es necesario dibujarlas aquí para evitar duplicados

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

        # Mantener una copia del frame limpio para las multas (después de rotación, antes de dibujos)
        clean_frame = frame.copy()

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
                frame = self._process_fines(frame, detections, clean_frame)
        else:
            # Cuando no hay detecciones activas, limpiar métricas
            self.detection_times_fps_normalized.clear()
            self._update_zone_metrics(0, 0)

        # Dibujar líneas de multa SIEMPRE que estén activadas (independiente de si hay detecciones)
        if self.video_processor.zone.fines_activated:
            # Crear carpeta de multas automáticamente al estar activadas
            if not self._fines_folder_created:
                self._create_fines_folder()
            # Dibujar líneas con o sin contadores según configuración de debug
            if self.settings.debug.show_multas_counter:
                frame = self._draw_line_zones_with_counters(frame)
            else:
                frame = self._draw_line_zones_without_counters(frame)

        # Limpieza periódica del historial de cruzamientos (cada ~100 frames)
        self._cleanup_counter += 1

        if self._cleanup_counter % 100 == 0:
            self._cleanup_old_crossing_history()

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
        enable_loop: bool = False,
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
            enable_loop: Si hacer loop infinito del video (solo para archivos de video)
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
            enable_loop=enable_loop,
        )

    def process_and_save_video(self, video_processor: VideoProcessor) -> None:
        """
        Procesa un video y guarda el resultado sin mostrarlo en una ventana en vivo.
        Usa StreamCoordinator para consistencia con otros métodos y soporte de rotación.
        """

        self.video_processor = video_processor

        # Aplicar lógica de orientación automática (como en _process_live_stream)
        eff_w, eff_h = self._prepare_orientation_for_stream()

        # Usar la resolución efectiva (después de rotación) para escalar las zonas
        self.video_processor.zone.scale_points((eff_w, eff_h))
        self.video_processor.zone.scale_fine_points((eff_w, eff_h))
        self._define_supervision_parameters()
        self.logger.info(
            f"⚙️ Factor de escala aplicado: {self.video_processor.scale_factor}"
        )
        self.logger.info(f"📐 Resolución efectiva (post-rotación): {eff_w}x{eff_h}")

        # Usar StreamCoordinator para procesamiento consistente y robusto
        # window_name=None indica procesamiento sin ventana (headless)
        self.stream_coordinator.process_stream_with_fps_callback(
            source_input=video_processor.origin_path,
            window_name=None,  # Sin ventana para dataset
            frame_processor_with_fps=self._process_frame_with_fps_callback,
            save_output=True,
            output_path=video_processor.result_path,
            scale_factor=getattr(self.video_processor, "scale_factor", 1.0),
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

        # Determinar si hacer loop infinito: cuando procesar=True y guardar=False
        enable_loop = (
            self.settings.un_video.procesar and not self.settings.un_video.guardar
        )
        if enable_loop:
            self.logger.info(
                "🔄 Loop infinito activado para el video (procesar=True, guardar=False)"
            )

        self._process_live_stream(
            source_input=video_processor.origin_path,
            window_name="Detectando en un video",
            save_output=save_output,
            output_path=video_processor.result_path if save_output else None,
            override_display_size=video_display_size,
            enable_loop=enable_loop,
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
