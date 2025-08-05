# run_detection_provider.py

import logging
import os
import signal
import sys
from threading import Thread
from typing import Any

from src.traffic_system.core.config_loader import load_app_settings

# Añadir la raíz al path para que las importaciones funcionen desde cualquier lugar
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__))))

from src.traffic_system.api.detection_server import DetectionAPI
from src.traffic_system.detection.App import DetectionApp
from src.traffic_system.detection.zones.zone_list import ZoneList

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(message)s")
logger = logging.getLogger("DetectionProvider")

# Objeto compartido que el hilo de procesamiento y la API usarán para comunicarse.
shared_zones = ZoneList()


# def video_processing_worker(settings, detector):
#     """Lógica de procesamiento de video que se ejecuta en un hilo separado."""
#     logger.info("Iniciando hilo de procesamiento de video...")
#     try:
#         if settings.un_video.procesar:
#             video = Video(
#                 path_origen=settings.un_video.path_origen,
#                 zona=next(
#                     z for z in shared_zones.get() if z.nombre == settings.un_video.zona
#                 ),
#             )
#             detector.procesar_y_mostrar_resultado_en_vivo(video)
#         elif settings.procesar_camara:
#             # Lógica para la cámara iría aquí
#             logger.info("Procesando desde la cámara...")
#             # detector.procesar_camara(...)
#         logger.info("El hilo de procesamiento de video ha finalizado.")
#     except Exception as e:
#         logger.error(f"Error fatal en el hilo de video: {e}", exc_info=True)
#         os.kill(
#             os.getpid(), signal.SIGINT
#         )  # Cierra el proceso principal si el hilo falla


# def main():
#     logger.info("Iniciando el Servicio de Proveedor de Datos por Detección...")
#     try:
#         settings = load_app_settings()
#     except ConfigValidationError as e:
#         logger.error(f"Error de configuración: {e}")
#         sys.exit(1)

#     # El detector ahora se crea aquí y se pasa a las funciones que lo necesiten.
#     detector = Detector(
#         detection_settings=settings.deteccion, zonas_instance=shared_zones
#     )

#     # Iniciar el hilo de procesamiento de video
#     processing_thread = Thread(
#         target=video_processing_worker, args=(settings.deteccion, detector)
#     )
#     processing_thread.daemon = True
#     processing_thread.start()

#     # Iniciar el servidor API en el hilo principal
#     api_server = ApiDeteccion(name="API_Deteccion", zonas_instance=shared_zones)
#     host, port = settings.base_url.split("//")[1].split(":")
#     logger.info(f"Servidor API de Detección escuchando en http://{host}:{port}")
#     api_server.run(host=host, port=int(port), debug=False)


def main() -> None:
    """
    Inicia la detección de vehículos con YOLO.
    """
    try:
        settings = load_app_settings()
        app = DetectionApp()

        #! Procesar toda la carpetas del dataset.
        if settings.deteccion.carpeta_dataset.procesar:
            app.analyze_video_folder()

        #! Procesar un video específico del dataset.
        if settings.deteccion.un_video.procesar:
            app.analyze_single_video()

        #! Deteccion con cámara en vivo.
        if settings.deteccion.procesar_camara:
            app.analyze_camera()

    except Exception as e:
        print("Error:", e)
        shutdown_handler(0, 0)


def api_client() -> None:
    """
    Inicia la API de detección de vehículos.
    """
    api = DetectionAPI(name="API Deteccion")
    api.run(host="0.0.0.0", port=5000, debug=False)


def shutdown_handler(sig_num: int, frame: Any) -> None:
    logger.info("Cerrando el servicio de detección...")
    sys.exit(0)


if __name__ == "__main__":
    signal.signal(signal.SIGINT, shutdown_handler)
    # main()
    app = Thread(target=main)
    app.start()

    api_client()
