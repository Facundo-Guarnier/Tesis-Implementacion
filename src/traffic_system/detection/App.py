import os

from src.traffic_system.core.config_loader import load_app_settings
from src.traffic_system.core.config_models import DeteccionSettings
from src.traffic_system.detection.detector_service import Detector
from src.traffic_system.detection.video import Video
from src.traffic_system.detection.zonas.ZonaList import ZoneList


class AppDetection:
    def __init__(self, detection_settings: DeteccionSettings | None = None) -> None:
        # TODO: Eliminar el uso de load_app_settings, ya que deberia cargar desde la configuración global.
        self.settings = load_app_settings().deteccion
        self.detector = Detector()
        self.zonas = ZoneList()

    def analizar_carpeta_videos(self) -> None:
        """
        Procesa todos los videos en la carpeta de origen y guarda los resultados en la carpeta de destino.
        """
        print("Procesando videos...")
        i = 0
        origen = self.settings.carpeta_dataset.path_origen
        destino = self.settings.carpeta_dataset.path_destino

        #! Crear la carpeta de resultados si no existe
        if not os.path.exists(destino):
            os.makedirs(destino)

        try:
            #! Recorrer todas las carpetas en la carpeta de entrada
            for carpeta_video in os.listdir(origen):
                carpeta_video_ruta = os.path.join(origen, carpeta_video)

                #! Verificar si es una carpeta
                if os.path.isdir(carpeta_video_ruta):
                    print(f"\nProcesando carpeta: {carpeta_video}")

                    #! Crear la carpeta de salida espejo
                    carpeta_salida_ruta = os.path.join(destino, carpeta_video)
                    if not os.path.exists(carpeta_salida_ruta):
                        os.makedirs(carpeta_salida_ruta)

                    #! Procesar todos los archivos en la carpeta de video
                    for archivo_video in os.listdir(carpeta_video_ruta):
                        archivo_video_ruta_entrada = os.path.join(
                            carpeta_video_ruta, archivo_video
                        )
                        archivo_video_ruta_salida = os.path.join(
                            carpeta_salida_ruta, archivo_video
                        )

                        #! Verificar si es un archivo y tiene una extensión de video
                        if os.path.isfile(
                            archivo_video_ruta_entrada
                        ) and archivo_video_ruta_entrada.lower().endswith(
                            (".mp4", ".avi", ".mkv")
                        ):
                            video = Video(
                                origin_path=archivo_video_ruta_entrada,
                                result_path=archivo_video_ruta_salida,
                                zone=next(
                                    (
                                        zona
                                        for zona in self.zonas.get()
                                        if zona.nombre == carpeta_video
                                    ),
                                    self.zonas.get()[0],
                                ),  #! Busca la clase correspondiente a la zona actual, sino devuelve la primera zona (Default).
                            )

                            print(f" -Video N°{i}: {archivo_video}")
                            self.detector.procesar_y_guardar_video(video=video)
                            print("  Videos procesado\n")

            print("\nVideos procesados con éxito.")

        except Exception as e:
            print(
                f"[ERROR Deteccion.App.App]: Error al procesar la carpeta: {origen} \n{e}"
            )

    def analizar_un_video(self) -> None:
        """
        Ejecuta el modelo y realiza la detección de objetos en el video mostrando el resultado en tiempo real.
        """

        video = Video(
            origin_path=self.settings.un_video.path_origen,
            zone=next(
                (
                    zona
                    for zona in self.zonas.get()
                    if zona.nombre == self.settings.un_video.zona
                ),
                self.zonas.get()[0],
            ),
        )

        print("Procesando video...")
        self.detector.procesar_y_mostrar_resultado_en_vivo(video=video)
        print("Video procesado.")

    def analizar_camara(self) -> None:
        """
        Ejecuta el modelo y realiza la detección de objetos en tiempo real.
        """

        video = Video(
            origin_path="",
            scale_factor=0.2,
            zone=next(
                (zona for zona in self.zonas.get() if zona.nombre == "Camara"),
                self.zonas.get()[0],
            ),
        )

        print("Procesando cámara...")
        self.detector.procesar_camara(video=video)
        print("Cámara procesada.")
