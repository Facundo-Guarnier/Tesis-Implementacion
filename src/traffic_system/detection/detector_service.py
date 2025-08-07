import logging
import os
import time

import cv2
import matplotlib.path as mplPath
import numpy as np
import supervision as sv
import ultralytics as ul

from src.traffic_system.core.config_loader import load_app_settings
from src.traffic_system.core.config_models import DeteccionSettings
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
    ) -> None:
        # TODO: Eliminar el uso de load_app_settings, ya que deberia cargar desde la configuración global.
        self.settings = load_app_settings().deteccion
        self.model = ul.YOLO(f"assets/yolo_models/{self.settings.modelo}")
        self._selected_classes = [2, 3, 5, 7]  # Auto, Moto, Camion, Bus
        self._class_names = self.model.model.names

        self.zones = zones_instance if zones_instance is not None else ZoneList()

        self.detection_times: dict[int, int] = (
            {}
        )  # Diccionario para almacenar tiempos de detección

        self.logger = logging.getLogger(f"{self.__class__.__name__}[DetectorService]")

    def _create_fines_folder(self) -> None:
        """
        Crea la carpeta de multas si no existe y devuelve la ruta.
        """

        self.__fines_path = os.path.join(
            "Resultados_multa",
            f"Multa_{time.strftime('%Y-%m-%d_%H-%M-%S')}",
            self.video_processor.zone.name,
        )
        log_dir = os.path.join(self.__fines_path)
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

    def _define_supervision_parameters(self) -> None:
        """
        Define los parámetros de supervisión necesario para la edición de los frames en base a la resolución del video.
        """

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
        self.bounding_box_annotator = sv.BoundingBoxAnnotator(
            thickness=max(1, int(3 * self.video_processor.scale_factor)),
        )
        self.label_annotator = sv.LabelAnnotator(
            text_thickness=max(1, int(2 * self.video_processor.scale_factor)),
            text_scale=max(1, int(1 * self.video_processor.scale_factor)),
        )

        #! Línea de multas
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

    def _draw_detection_polygon_and_centers_cv2(
        self, frame: np.ndarray, detections: sv.Detections
    ) -> np.ndarray:
        """
        - Dibuja el centro de los objetos y el polígono de detección.
        - Cuenta los objetos que están dentro del polígono.
        """

        #! Dibujar el polígono de detección
        cv2.polylines(
            img=frame,
            pts=[self.video_processor.zone.rescaled_points],
            isClosed=True,
            color=(0, 0, 255),
            thickness=max(1, int(10 * self.video_processor.scale_factor)),
        )

        #! Lista de IDs de objetos que ya no están en la imagen
        ids_out_of_frame = [
            id for id in self.detection_times if id not in detections.tracker_id
        ]
        for id in ids_out_of_frame:
            del self.detection_times[id]

        #! Dibujar el centro de los objetos
        polygon_detections_count = 0
        for box, _mask, _confidence, _class_id, tracker_id, _data in detections:
            #! Centros
            #  xmin, ymin, xmax, ymax
            #   0     1     2     3
            x = int((box[0] + box[2]) // 2)
            y = int((box[1] + box[3]) // 2)

            #! Validar el punto dentro del polígono
            color: list[int]  # BGR
            if mplPath.Path(self.video_processor.zone.rescaled_points).contains_point(
                (x, y)
            ):
                polygon_detections_count += 1
                color = [255, 80, 0]

                #! Contar el tiempo de detección
                if tracker_id in self.detection_times:
                    self.detection_times[tracker_id] += 1
                else:
                    self.detection_times[tracker_id] = 1

            else:
                color = [0, 0, 255]
                #! Reiniciar el tiempo de detección
                self.detection_times[tracker_id] = 0

            cv2.circle(
                img=frame,
                center=(x, y),
                radius=max(1, int(10 * self.video_processor.scale_factor)),
                color=color,
                thickness=max(1, int(10 * self.video_processor.scale_factor)),
            )

        total_frames_in_zone = sum(self.detection_times.values())
        total_seconds_in_zone = total_frames_in_zone // self.video_processor.fps

        #! Escribir la cantidad de detecciones en el frame
        cv2.putText(
            img=frame,
            text=f"Vehiculos {polygon_detections_count} {total_seconds_in_zone}",
            org=(
                max(1, int(250 * self.video_processor.scale_factor)),
                max(1, int(1800 * self.video_processor.scale_factor)),
            ),
            fontFace=cv2.FONT_HERSHEY_PLAIN,
            fontScale=max(1, int(6 * self.video_processor.scale_factor)),
            color=(50, 50, 200),
            thickness=max(1, int(6 * self.video_processor.scale_factor)),
        )

        #! Guardar la cantidad de detecciones en la clase Zona para la API.
        # self.video.zona.cantidad_detecciones = detecciones_poligono
        updated_zone = self.zones.get_zone_by_name(self.video_processor.zone.name)
        if updated_zone:
            updated_zone.detection_count = polygon_detections_count
            updated_zone.wait_time = int(total_seconds_in_zone)
        self.video_processor.zone.wait_time = int(total_seconds_in_zone)

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
            detection_time_frames = self.detection_times.get(tracker_id, 0)
            label = f"{detection_time_frames} frames"
            labels.append(label)

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

    def _process_frame_callback(
        self, frame: np.ndarray, frame_number: int
    ) -> np.ndarray:
        """
        - Procesamiento de video.
        - Se ejecuta por cada frame del video.
        """

        #! Realizar la detección/predicción de objetos
        model_results = self.model(frame, verbose=False)[0]
        detections = sv.Detections.from_ultralytics(model_results)

        #! Filtrar las clases que no se necesitan
        detections = detections[np.isin(detections.class_id, self._selected_classes)]

        #! Seguimiento de objetos
        detections = self.byte_tracker.update_with_detections(detections)

        #! Si hay detecciones
        if detections.tracker_id.size > 0:
            frame = self._draw_detection_polygon_and_centers_cv2(frame, detections)

            frame = self.trace_annotator.annotate(frame, detections=detections)

            frame = self._annotate_boxes_sv(frame, detections)

            if self.video_processor.zone.fines_activated:
                frame = self._process_fines(frame, detections)

        return frame

    def process_and_save_video(self, video_processor: VideoProcessor) -> None:
        """
        Procesa un video y guarda el resultado sin mostrarlo en una ventana en vivo.
        """

        self.video_processor = video_processor
        self._create_fines_folder()
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
        self._create_fines_folder()
        save_output = self.settings.un_video.guardar
        cap = cv2.VideoCapture(self.video_processor.origin_path)
        self.video_processor.zone.scale_fine_points(self.video_processor.resolution)
        self._define_supervision_parameters()

        if save_output:
            output_writer = cv2.VideoWriter(
                filename=self.video_processor.result_path,
                fourcc=1983148141,  #! mp4v
                fps=cap.get(cv2.CAP_PROP_FPS),
                frameSize=(
                    int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),  #! width
                    int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),  #! height
                ),
            )

        fps = 0
        frames_in_second = 0
        second_start_time = time.time()
        total_frames_processed = 0

        cv2.namedWindow("Detectando en un video", cv2.WINDOW_NORMAL)
        cv2.resizeWindow("Detectando en un video", 460, 820)

        while True:
            frames_in_second += 1
            total_frames_processed += 1

            #! Salir si no hay más frames
            ret, frame = cap.read()
            if not ret:
                break

            #! Procesar el frame
            frame = self._process_frame_callback(frame, total_frames_processed)

            #! Guardar el frame sin mostrar los fps.
            if save_output:
                output_writer.write(frame)

            #! Mostrar el FPS
            if time.time() - second_start_time >= 1:
                fps = frames_in_second
                frames_in_second = 0
                second_start_time = time.time()

            cv2.putText(
                frame,
                f"FPS: {fps}",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                1 * self.video_processor.scale_factor,
                (0, 255, 0),
                2,
            )

            #! Mostrar el frame en la ventana
            cv2.imshow("Detectando en un video", frame)

            #! Salir del bucle con la tecla 'q'.
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

        cap.release()
        cv2.destroyAllWindows()
        if save_output:
            self.logger.info(
                f"💾 Video guardado en: {self.video_processor.result_path}"
            )

    def process_camera(self, video_processor: VideoProcessor) -> None:
        """
        Procesa la cámara en vivo y muestra el resultado en tiempo real.
        """

        cap = cv2.VideoCapture(0)
        self.video_processor = video_processor
        self._create_fines_folder()
        self._define_supervision_parameters()

        fps = 0
        frames_in_second = 0
        second_start_time = time.time()
        total_frames_processed = 0

        cv2.namedWindow("Detectando con camara", cv2.WINDOW_NORMAL)
        cv2.resizeWindow("Detectando con camara", 820, 460)

        while True:
            frames_in_second += 1

            #! Salir si no hay más frames
            ret, frame = cap.read()
            if not ret:
                break

            #! Rescalar el frame
            frame = cv2.resize(frame, (820, 460))

            #! Procesar el frame
            frame = self._process_frame_callback(frame, total_frames_processed)

            #! Mostrar el FPS
            if time.time() - second_start_time >= 1:
                fps = frames_in_second
                frames_in_second = 0
                second_start_time = time.time()

            cv2.putText(
                frame,
                f"FPS: {fps}",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 255, 0),
                2,
            )

            #! Mostrar el frame en la ventana
            cv2.imshow("Detectando con camara", frame)

            #! Salir del bucle con la tecla 'q'.
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

        cap.release()
        cv2.destroyAllWindows()
