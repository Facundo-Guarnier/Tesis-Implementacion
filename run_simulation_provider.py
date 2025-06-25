# run_simulation_provider.py

import inspect
import logging
import os
import signal
import sys
from threading import Thread

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__))))

from traci.exceptions import FatalTraCIError

from src.traffic_system.api.simulation_server import ApiSUMO
from src.traffic_system.simulation.AppSUMO import AppSUMO

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(message)s")
logger = logging.getLogger("SimulationProvider")


# def main():
#     logger.info("Iniciando el Servicio de Proveedor de Datos por Simulación...")
#     try:
#         settings = load_app_settings()
#         os.environ["SUMO_HOME"] = settings.sumo.path_sumo
#     except ConfigValidationError as e:
#         logger.error(f"Error de configuración: {e}")
#         sys.exit(1)

#     try:
#         api_server = ApiSUMO(name="API_SUMO")
#         # ApiSUMO ya inicia AppSUMO y la conexión a traci, según tu código.
#         host, port = settings.base_url.split("//")[1].split(":")
#         logger.info(f"✅ Servidor API de SUMO iniciado en http://{host}:{port}")
#         api_server.run(host=host, port=int(port), debug=False)
#     except Exception as e:
#         logger.error(
#             f"No se pudo iniciar el servicio de simulación SUMO: {e}", exc_info=True
#         )
#         sys.exit(1)


def main() -> None:
    """
    Simulación de tráfico con SUMO.
    """
    logger = logging.getLogger(f" {__name__}.{inspect.currentframe().f_code.co_name}")  # type: ignore

    try:
        app = AppSUMO()
        app.iniciar()

    except FatalTraCIError as e:
        logger.error(" Error en la simulación de tráfico:", e)
        shutdown_handler(0, 0)
        exit(1)


def api_service() -> None:
    """
    Inicia la API de SUMO.
    """
    api = ApiSUMO(name="API SUMO")
    api.run(debug=False)


def shutdown_handler(signum, frame):
    logger.info("⚠️ Cerrando el servicio de simulación...")
    sys.exit(0)


if __name__ == "__main__":
    logger.info("✅ Iniciando el Servicio de Proveedor de Datos por Simulación...")
    signal.signal(signal.SIGINT, shutdown_handler)
    # main()
    app = Thread(target=main)
    app.start()

    api_service()
