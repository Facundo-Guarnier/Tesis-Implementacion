# run_detection_provider.py

import logging
import os
import signal
import sys
from threading import Thread

# Añadir la raíz al path para que las importaciones funcionen desde cualquier lugar
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__))))

from src.traffic_system.api.detection_server import ApiDeteccion
from src.traffic_system.core.config_exceptions import ConfigValidationError
from src.traffic_system.core.config_loader import load_app_settings
from src.traffic_system.detection.Detector import Detector
from src.traffic_system.detection.Video import Video
from src.traffic_system.detection.zonas.ZonaList import ZonaList

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(message)s")
logger = logging.getLogger("DetectionProvider")

# Objeto compartido que el hilo de procesamiento y la API usarán para comunicarse.
shared_zones = ZonaList()


def video_processing_worker(settings, detector):
    """Lógica de procesamiento de video que se ejecuta en un hilo separado."""
    logger.info("Iniciando hilo de procesamiento de video...")
    try:
        if settings.un_video.procesar:
            video = Video(
                path_origen=settings.un_video.path_origen,
                zona=next(
                    z for z in shared_zones.get() if z.nombre == settings.un_video.zona
                ),
            )
            detector.procesar_y_mostrar_resultado_en_vivo(video)
        elif settings.procesar_camara:
            # Lógica para la cámara iría aquí
            logger.info("Procesando desde la cámara...")
            # detector.procesar_camara(...)
        logger.info("El hilo de procesamiento de video ha finalizado.")
    except Exception as e:
        logger.error(f"Error fatal en el hilo de video: {e}", exc_info=True)
        os.kill(
            os.getpid(), signal.SIGINT
        )  # Cierra el proceso principal si el hilo falla


def main():
    logger.info("Iniciando el Servicio de Proveedor de Datos por Detección...")
    try:
        settings = load_app_settings()
    except ConfigValidationError as e:
        logger.error(f"Error de configuración: {e}")
        sys.exit(1)

    # El detector ahora se crea aquí y se pasa a las funciones que lo necesiten.
    detector = Detector(
        detection_settings=settings.deteccion, zonas_instance=shared_zones
    )

    # Iniciar el hilo de procesamiento de video
    processing_thread = Thread(
        target=video_processing_worker, args=(settings.deteccion, detector)
    )
    processing_thread.daemon = True
    processing_thread.start()

    # Iniciar el servidor API en el hilo principal
    api_server = ApiDeteccion(name="API_Deteccion", zonas_instance=shared_zones)
    host, port = settings.base_url.split("//")[1].split(":")
    logger.info(f"Servidor API de Detección escuchando en http://{host}:{port}")
    api_server.run(host=host, port=int(port), debug=False)


def shutdown_handler(signum, frame):
    logger.info("Cerrando el servicio de detección...")
    sys.exit(0)


if __name__ == "__main__":
    signal.signal(signal.SIGINT, shutdown_handler)
    main()
