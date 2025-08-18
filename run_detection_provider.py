import logging
import os
import signal
import sys
import threading
from threading import Thread
from typing import Any

from src.traffic_system.core.config_loader import load_app_settings

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__))))

from src.traffic_system.api.detection_server import DetectionAPI
from src.traffic_system.detection.App import DetectionApp
from src.traffic_system.detection.zones.zone_list import ZoneList

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(message)s")
logger = logging.getLogger("DetectionProvider")

shared_zones = ZoneList()

# Variable global para controlar el cierre del sistema
shutdown_event = threading.Event()
api_server: DetectionAPI | None = None


def main() -> None:
    """
    Inicia la detección de vehículos con YOLO.
    """
    try:
        # Verificar si se debe terminar antes de comenzar
        if shutdown_event.is_set():
            logger.info("🛑 Shutdown solicitado antes de iniciar detección")
            return

        settings = load_app_settings()
        app = DetectionApp()
        # Pasar shutdown_event al detector para shutdown coordinado
        app.detector.shutdown_event = shutdown_event

        #! Procesar toda la carpetas del dataset.
        if settings.deteccion.carpeta_dataset.procesar and not shutdown_event.is_set():
            logger.info("📁 Iniciando procesamiento de carpeta dataset")
            app.analyze_video_folder()

        #! Procesar un video específico del dataset.
        if settings.deteccion.un_video.procesar and not shutdown_event.is_set():
            logger.info("🎬 Iniciando procesamiento de video individual")
            app.analyze_single_video()

        #! Deteccion con cámara en vivo.
        if settings.deteccion.procesar_camara and not shutdown_event.is_set():
            logger.info("📹 Iniciando detección con cámara en vivo")
            app.analyze_camera()

        if not shutdown_event.is_set():
            logger.info("✅ Procesamiento de detección completado")

    except KeyboardInterrupt:
        logger.info("⚠️ Interrupción de usuario en el hilo de detección")
        shutdown_event.set()
    except Exception:
        logger.error("❌ Error crítico en el servicio de detección", exc_info=True)
        shutdown_event.set()  # Señalar error a otros hilos
    finally:
        # Señalar que el hilo de detección ha terminado
        shutdown_event.set()
        logger.debug("🔄 Hilo de detección finalizado")


def api_client() -> None:
    """
    Inicia la API de detección de vehículos con verificación de shutdown_event.
    """
    global api_server
    try:
        # Verificar si se debe terminar antes de comenzar
        if shutdown_event.is_set():
            logger.info("🛑 Shutdown solicitado antes de iniciar API")
            return

        logger.info("🚀 Iniciando servidor API de detección")
        api_server = DetectionAPI(name="API Deteccion")

        # Configurar Flask para cerrar correctamente
        import atexit

        atexit.register(lambda: logger.info("📤 API de detección finalizada"))

        # Función para verificar shutdown_event y terminar proceso
        def shutdown_monitor() -> None:
            import time

            while not shutdown_event.is_set():
                time.sleep(0.5)  # Verificar cada 500ms

            # Cuando shutdown_event se activa, terminar el proceso
            logger.info("🛑 Shutdown detectado, terminando proceso...")
            import os

            os._exit(0)  # Forzar salida del proceso completo

        # Iniciar monitor de shutdown en hilo separado
        import threading

        shutdown_thread = threading.Thread(target=shutdown_monitor, daemon=True)
        shutdown_thread.start()

        # El servidor Flask bloqueará hasta que termine
        api_server.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)
    except KeyboardInterrupt:
        logger.info("⚠️ Interrupción de usuario en API")
        shutdown_event.set()
    except Exception:
        logger.error("❌ Error crítico en API de detección", exc_info=True)
        shutdown_event.set()  # Señalar error a otros hilos
    finally:
        shutdown_event.set()
        logger.debug("🔄 Hilo de API finalizado")


def shutdown_handler(sig_num: int, frame: Any) -> None:
    """
    Maneja la señal de cierre del sistema de manera robusta.
    """
    global api_server

    logger.info(
        f"⚠️ Señal de cierre recibida (señal {sig_num}) - iniciando cierre ordenado..."
    )

    try:
        # Señalar a todos los hilos que deben terminar
        shutdown_event.set()
        logger.info("📡 Señal de shutdown enviada a todos los hilos")

        # Dar tiempo a los hilos para que terminen limpiamente
        import time

        time.sleep(1)

        # Cleanup de recursos OpenCV si hay ventanas activas
        try:
            import cv2

            cv2.destroyAllWindows()
            cv2.waitKey(1)
            logger.info("🪟 Ventanas OpenCV cerradas")
        except Exception:
            logger.debug("ℹ️ No hay ventanas OpenCV para cerrar")

        # Intentar cerrar el servidor Flask si existe
        if api_server is not None:
            try:
                logger.info("🛑 Cerrando servidor API...")
                # Para Flask, la mejor forma es terminar el proceso después del cleanup
                api_server = None
            except Exception:
                logger.error("❌ Error cerrando servidor API", exc_info=True)

        logger.info("✅ Cierre del servicio de detección completado")

        # Usar sys.exit en lugar de os._exit para permitir cleanup adecuado
        sys.exit(0)

    except Exception:
        logger.error("❌ Error crítico durante shutdown", exc_info=True)
        # Solo en caso de error crítico, usar exit forzado
        os._exit(1)


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


# Nuevos errores:
# - Al procesar con la cámara o un_video, no puedo cerrar la ventana con la imagen utilizando la cruz de cerrado, sino que debo apretar la tecla "q".
# - Al procesar con la cámara o un_video y Al intentar cerrar una ventana con la cruz de cerrar, esta se vuelve a abrir con el tamaño original del video. Si o si hay que cerrar con la "q".
# - El factor de escala de las zonas es incorrecto al comento de procesar carpeta_dataset de 576x1024
