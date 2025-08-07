import logging
import os

from src.traffic_system.core.config_loader import load_app_settings
from src.traffic_system.core.config_models import DeteccionSettings
from src.traffic_system.detection.detector_service import DetectorService
from src.traffic_system.detection.video_processor import VideoProcessor
from src.traffic_system.detection.zones.zone_list import ZoneList


class DetectionApp:
    def __init__(self, detection_settings: DeteccionSettings | None = None) -> None:
        # TODO: Eliminar el uso de load_app_settings, ya que deberia cargar desde la configuración global.
        self.settings = load_app_settings().deteccion
        self.detector = DetectorService()
        self.zones = ZoneList()
        self.logger = logging.getLogger(f"{self.__class__.__name__}[DetectionApp]")

    def analyze_video_folder(self) -> None:
        """
        Procesa todos los videos en la carpeta de origen y guarda los resultados en la carpeta de destino.
        """
        self.logger.info("🎥 Iniciando procesamiento de videos...")
        video_count = 0
        origin_folder = self.settings.carpeta_dataset.path_origen
        destination_folder = self.settings.carpeta_dataset.path_destino

        #! Crear la carpeta de resultados si no existe
        if not os.path.exists(destination_folder):
            os.makedirs(destination_folder)
            self.logger.info(f"📁 Carpeta de destino creada: {destination_folder}")

        try:
            #! Recorrer todas las carpetas en la carpeta de entrada
            for video_subfolder in os.listdir(origin_folder):
                video_subfolder_path = os.path.join(origin_folder, video_subfolder)

                #! Verificar si es una carpeta
                if os.path.isdir(video_subfolder_path):
                    self.logger.info(f"📂 Procesando carpeta: {video_subfolder}")

                    #! Crear la carpeta de salida espejo
                    output_subfolder_path = os.path.join(
                        destination_folder, video_subfolder
                    )
                    if not os.path.exists(output_subfolder_path):
                        os.makedirs(output_subfolder_path)

                    #! Procesar todos los archivos en la carpeta de video
                    for video_file in os.listdir(video_subfolder_path):
                        input_video_path = os.path.join(
                            video_subfolder_path, video_file
                        )
                        output_video_path = os.path.join(
                            output_subfolder_path, video_file
                        )

                        #! Verificar si es un archivo y tiene una extensión de video
                        if os.path.isfile(
                            input_video_path
                        ) and input_video_path.lower().endswith(
                            (".mp4", ".avi", ".mkv")
                        ):
                            video_processor_instance = VideoProcessor(
                                origin_path=input_video_path,
                                result_path=output_video_path,
                                zone=next(
                                    (
                                        zone_obj
                                        for zone_obj in self.zones.get_all_zones()
                                        if zone_obj.name == video_subfolder
                                    ),
                                    self.zones.get_all_zones()[0],
                                ),  #! Busca la clase correspondiente a la zona actual, sino devuelve la primera zona (Default).
                            )

                            self.logger.info(f"🎞️ Video N°{video_count}: {video_file}")
                            self.detector.process_and_save_video(
                                video_processor=video_processor_instance
                            )
                            self.logger.info("✅ Video procesado")
                            video_count += 1

            self.logger.info(
                f"🎉 Todos los videos procesados exitosamente. Total: {video_count}"
            )

        except Exception:
            self.logger.error(
                f"❌ Error al procesar la carpeta: {origin_folder}", exc_info=True
            )

    def analyze_single_video(self) -> None:
        """
        Ejecuta el modelo y realiza la detección de objetos en el video mostrando el resultado en tiempo real.
        """

        video_processor_instance = VideoProcessor(
            origin_path=self.settings.un_video.path_origen,
            zone=next(
                (
                    zone_obj
                    for zone_obj in self.zones.get_all_zones()
                    if zone_obj.name == self.settings.un_video.zona
                ),
                self.zones.get_all_zones()[0],
            ),
        )

        self.logger.info(
            f"🎬 Iniciando procesamiento de video: {self.settings.un_video.path_origen}"
        )
        self.logger.info(f"🎯 Zona seleccionada: {self.settings.un_video.zona}")
        self.detector.process_and_show_live_video(
            video_processor=video_processor_instance
        )
        self.logger.info("✅ Video procesado exitosamente")

    def analyze_camera(self) -> None:
        """
        Ejecuta el modelo y realiza la detección de objetos en tiempo real.
        """

        video_processor_instance = VideoProcessor(
            origin_path="",
            scale_factor=0.2,
            zone=next(
                (
                    zone_obj
                    for zone_obj in self.zones.get_all_zones()
                    if zone_obj.name == "Camara"
                ),
                self.zones.get_all_zones()[0],
            ),
        )

        self.logger.info("📹 Iniciando procesamiento de cámara en vivo")
        self.detector.process_camera(video_processor=video_processor_instance)
        self.logger.info("✅ Cámara procesada exitosamente")
