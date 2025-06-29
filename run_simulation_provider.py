# run_simulation_provider.py

import logging
import os
import signal
import sys
from threading import Thread

import traci
from traci.exceptions import FatalTraCIError, TraCIException

from src.traffic_system.api.simulation_server import ApiSUMO
from src.traffic_system.core.config_loader import load_app_settings
from src.traffic_system.simulation.AppSUMO import AppSUMO
from src.traffic_system.simulation.zonas.ZonaList import ZonaList

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(message)s")
logger = logging.getLogger("SimulationProvider")

# Variables globales para compartir las instancias entre los hilos
app_s1: AppSUMO | None = None
app_s2: AppSUMO | None = None


def start_traci_connection(
    label: str, config_file: str, use_gui: bool
) -> traci.connection.Connection:
    """
    Inicia una conexión con SUMO y devuelve el objeto de conexión.

    Args:
        label: Identificador de la conexión (ej. 's1', 's2').
        config_file: Ruta al archivo de configuración de SUMO.
        use_gui: Si True, inicia SUMO en modo GUI; si False, en modo consola.
    """
    sumo_binary = "sumo-gui" if use_gui else "sumo"
    command = [sumo_binary, "-c", config_file, "--no-warnings"]
    if use_gui:
        os.environ["SUMO_LOG"] = "error"

    traci.start(cmd=command, label=label)
    return traci.getConnection(label)


def simulation_loop(app: AppSUMO) -> None:
    """
    Bucle principal para una instancia de simulación.
    Avanza la simulación paso a paso mientras sea posible.
    """
    logger = logging.getLogger(f" {__name__}.simulation_loop[{app.label}]")
    try:
        # Bucle de calentamiento inicial
        while app.traci.simulation.getTime() < 250:
            if not app.puedo_seguir():
                logger.warning(
                    f"Simulación '{app.label}' finalizada durante el calentamiento."
                )
                break
            app.traci.simulationStep()

        logger.info(f"Calentamiento de la simulación '{app.label}' completado.")

        # Bucle principal de la simulación
        while app.puedo_seguir():
            app.avanzar(1)

        logger.info(f"La simulación '{app.label}' ha finalizado.")

    except (TraCIException, FatalTraCIError) as e:
        logger.error(f"Error en el bucle de la simulación '{app.label}': {e}")
    finally:
        logger.info(f"Cerrando conexión traci para '{app.label}'.")
        app.traci.close()


def api_service(app_instance_s1: AppSUMO, app_instance_s2: AppSUMO | None) -> None:
    """
    Inicia el servidor API de Flask.
    """
    logger.info("Iniciando el servicio API de SUMO...")
    try:
        api = ApiSUMO(name="API_SUMO", app_s1=app_instance_s1, app_s2=app_instance_s2)
        # TODO: Cargar host y port desde la configuración.
        api.run(host="0.0.0.0", port=5000, debug=False)
    except Exception as e:
        logger.error(f"No se pudo iniciar el servicio API: {e}", exc_info=True)


def shutdown_handler(signum, frame):
    logger.info("⚠️  Cerrando el servicio de simulación...")
    sys.exit(0)


if __name__ == "__main__":
    signal.signal(signal.SIGINT, shutdown_handler)
    logger.info("Iniciando el Servicio de Proveedor de Datos por Simulación...")

    try:
        settings = load_app_settings()
        os.environ["SUMO_HOME"] = settings.sumo.path_sumo
    except Exception as e:
        logger.error(f"Error cargando la configuración: {e}")
        sys.exit(1)

    try:
        zonas = ZonaList()
        # TODO: Cargar zonas desde un archivo o base de datos si es necesario
        config_file_path = "assets/sumo_maps/MapaDe0/mapa.sumocfg"

        logger.info("Iniciando conexión TraCI para la simulación principal (s1)...")
        traci_s1 = start_traci_connection(
            label="s1", config_file=config_file_path, use_gui=settings.sumo.gui
        )
        app_s1 = AppSUMO(traci_conn=traci_s1, zonas=zonas, label="s1")

        # Iniciar simulación de comparación (S2) si está habilitada
        if settings.sumo.comparar:
            logger.info(
                "Iniciando conexión TraCI para la simulación de comparación (s2)..."
            )
            traci_s2 = start_traci_connection(
                label="s2", config_file=config_file_path, use_gui=settings.sumo.gui
            )
            app_s2 = AppSUMO(traci_conn=traci_s2, zonas=zonas, label="s2")

            # Iniciar el bucle de la simulación S2 en un hilo
            sim_thread_s2 = Thread(target=simulation_loop, args=(app_s2,))
            sim_thread_s2.daemon = True  # El hilo morirá si el principal muere
            sim_thread_s2.start()

        # Iniciar el bucle de la simulación S1 en un hilo
        sim_thread_s1 = Thread(target=simulation_loop, args=(app_s1,))
        sim_thread_s1.daemon = True
        sim_thread_s1.start()

        # Iniciar el servicio API en el hilo principal
        # El servidor Flask bloqueará este hilo
        api_service(app_s1, app_s2)

    except (TraCIException, FatalTraCIError) as e:
        logger.error(f"Error fatal al iniciar Traci: {e}")
        shutdown_handler(0, 0)
    except FileNotFoundError:
        logger.error(
            f"No se encontró el archivo de configuración de SUMO en '{config_file_path}'. Asegúrate de que la ruta es correcta."
        )
        shutdown_handler(0, 0)
    except Exception as e:
        logger.error(
            f"Ocurrió un error inesperado durante el inicio: {e}", exc_info=True
        )
        shutdown_handler(0, 0)
