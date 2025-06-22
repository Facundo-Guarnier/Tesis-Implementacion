import inspect
import logging
import os
import signal
import sys
from threading import Thread

from traci.exceptions import FatalTraCIError
from ultralytics import settings

from src.traffic_system.api.detection_server import ApiDeteccion
from src.traffic_system.api.simulation_server import ApiSUMO
from src.traffic_system.core.config_exceptions import ConfigValidationError
from src.traffic_system.core.config_loader import AppSettings, load_app_settings
from src.traffic_system.decision.DQN.App import AppDecision
from src.traffic_system.detection.App import AppDetection
from src.traffic_system.simulation.AppSUMO import AppSUMO


def cerrar(nro_senial: int, marco) -> None:
    logger = logging.getLogger(f" {__name__}.{inspect.currentframe().f_code.co_name}")  # type: ignore
    logger.info(f"Finalizando el proceso ID: {os.getpid()}")
    os._exit(0)


# T* Deteccion
def run_app_deteccion() -> None:
    """
    Inicia la detección de vehículos con YOLO.
    """
    try:
        app = AppDetection()

        #! Procesar toda la carpetas del dataset.
        if settings.deteccion.carpeta_dataset.procesar:
            app.analizar_carpeta_videos()

        #! Procesar un video específico del dataset.
        if settings.deteccion.un_video.procesar:
            app.analizar_un_video()

        #! Deteccion con cámara en vivo.
        if settings.deteccion.procesar_camara:
            app.analizar_camara()

    except Exception as e:
        print("Error:", e)
        cerrar(0, 0)


def run_api_deteccion() -> None:
    """
    Inicia la API de detección de vehículos.
    """
    api = ApiDeteccion(name="API Deteccion")
    api.run(debug=False)


# T* SUMO
def run_app_sumo() -> None:
    """
    Simulación de tráfico con SUMO.
    """
    logger = logging.getLogger(f" {__name__}.{inspect.currentframe().f_code.co_name}")  # type: ignore

    try:
        app = AppSUMO()
        app.iniciar()

    except FatalTraCIError as e:
        logger.error(" Error en la simulación de tráfico:", e)
        cerrar(0, 0)
        exit(1)


def run_api_sumo() -> None:
    """
    Inicia la API de SUMO.
    """
    api = ApiSUMO(name="API SUMO")
    api.run(debug=False)


# T* Decision
def run_app_decision() -> None:
    """
    Inicial el modelo de toma de decisiones.
    Puede:
    - Entrenar el modelo.
    - Utilizar un modelo ya entrenado.
    """
    app = AppDecision()
    if settings.decision.entrenamiento.entrenar:
        app.entrenar()
        cerrar(0, 0)

    else:
        app.usar()


# T* Reporte
def run_app_reporte() -> None:
    """
    Genera el reporte de la simulación.
    """
    from src.traffic_system.reporting.App import AppReporte

    app = AppReporte()
    app.generar_reporte()


def main() -> None:
    settings: AppSettings = load_app_settings()
    print(settings)
    logger.info("✅ Configuración cargada correctamente.")

    logging.basicConfig(level=logging.DEBUG)
    os.environ["SUMO_HOME"] = settings.sumo.path_sumo
    signal.signal(signal.SIGINT, cerrar)

    if settings.deteccion.detectar:
        app = Thread(target=run_app_deteccion)
        app.start()
        run_api_deteccion()

    if settings.sumo.simular:
        app = Thread(target=run_app_sumo)
        app.start()

    if settings.decision.decision:
        app2 = Thread(target=run_app_decision)
        app2.start()

    if settings.reporte.generar:
        reporte = Thread(target=run_app_reporte)
        reporte.start()

    # ? Estos va siempre al final
    if settings.sumo.simular:
        run_api_sumo()

    app.join()
    if settings.decision.decision:
        app2.join()

    if settings.reporte.generar:
        reporte.join()


logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
)
logger = logging.getLogger(__name__)

if __name__ == "__main__":

    logger.info("✅ Iniciando la aplicación del Sistema de Semáforos Inteligentes...")

    try:
        main()

    except ConfigValidationError as e:
        # Si la configuración falla, atrapamos nuestro error personalizado.
        logger.error(
            "No se puede iniciar la aplicación debido a un error de configuración."
        )
        # Imprimimos el mensaje de error formateado que viene en la excepción.
        print(str(e))
        # Salimos del programa con un código de error para indicar que algo salió mal.
        sys.exit(1)

    except Exception as e:
        # Capturamos cualquier otro error inesperado.
        logger.error("Ocurrió un error inesperado:", exc_info=True)
        print("Error inesperado:", e)
        cerrar(0, 0)
        sys.exit(1)
