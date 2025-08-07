# run_detection_provider.py

import logging
import os
import signal
import sys
import threading
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

# Variable global para controlar el cierre del sistema
shutdown_event = threading.Event()
api_server: DetectionAPI | None = None


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
            logger.info("📁 Iniciando procesamiento de carpeta dataset")
            app.analyze_video_folder()

        #! Procesar un video específico del dataset.
        if settings.deteccion.un_video.procesar:
            logger.info("🎬 Iniciando procesamiento de video individual")
            app.analyze_single_video()

        #! Deteccion con cámara en vivo.
        if settings.deteccion.procesar_camara:
            logger.info("📹 Iniciando detección con cámara en vivo")
            app.analyze_camera()

        logger.info("✅ Procesamiento de detección completado")

    except KeyboardInterrupt:
        logger.info("⚠️ Interrupción de usuario en el hilo de detección")
    except Exception:
        logger.error("❌ Error crítico en el servicio de detección", exc_info=True)
    finally:
        # Señalar que el hilo de detección ha terminado
        shutdown_event.set()


def api_client() -> None:
    """
    Inicia la API de detección de vehículos.
    """
    global api_server
    try:
        logger.info("🚀 Iniciando servidor API de detección")
        api_server = DetectionAPI(name="API Deteccion")

        # Configurar Flask para cerrar correctamente
        import atexit

        atexit.register(lambda: logger.info("📤 API de detección finalizada"))

        api_server.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)
    except KeyboardInterrupt:
        logger.info("⚠️ Interrupción de usuario en API")
    except Exception:
        logger.error("❌ Error crítico en API de detección", exc_info=True)
    finally:
        shutdown_event.set()


def shutdown_handler(sig_num: int, frame: Any) -> None:
    """
    Maneja la señal de cierre del sistema de manera robusta.
    """
    global api_server

    logger.info("⚠️ Señal de cierre recibida - iniciando cierre ordenado...")

    # Señalar a todos los hilos que deben terminar
    shutdown_event.set()

    # Intentar cerrar el servidor Flask si existe
    if api_server is not None:
        try:
            logger.info("🛑 Cerrando servidor API...")
            # Flask no tiene un método directo de shutdown, pero podemos forzar el cierre
            os._exit(0)  # Forzar cierre inmediato
        except Exception:
            logger.error("❌ Error cerrando servidor API", exc_info=True)

    logger.info("✅ Cierre del servicio de detección completado")
    sys.exit(0)


if __name__ == "__main__":
    # Configurar manejo de señales
    signal.signal(signal.SIGINT, shutdown_handler)
    signal.signal(signal.SIGTERM, shutdown_handler)

    logger.info("🎯 Iniciando servicio de detección en modo híbrido (app + API)")

    # Crear y configurar el hilo de detección
    detection_thread = Thread(target=main, name="DetectionThread")
    detection_thread.daemon = (
        True  # Hilo daemon para que termine con el proceso principal
    )
    detection_thread.start()

    try:
        # Ejecutar la API en el hilo principal
        api_client()
    except KeyboardInterrupt:
        logger.info("⚠️ Interrupción de usuario detectada")
        shutdown_handler(0, None)
    except Exception:
        logger.error("❌ Error crítico en el proceso principal", exc_info=True)
        shutdown_handler(0, None)
