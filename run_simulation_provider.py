import logging
import signal
import sys
from typing import Any

import traci
from traci.exceptions import FatalTraCIError, TraCIException

from src.traffic_system.api.simulation_server import SumoAPI
from src.traffic_system.core.config_loader import load_app_settings
from src.traffic_system.core.config_models import SumoSettings
from src.traffic_system.simulation.app import SumoApp
from src.traffic_system.simulation.comparison_logger import ComparisonLogger
from src.traffic_system.simulation.zones.zone_list import ZoneList

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(message)s")
logger = logging.getLogger("SimulationProvider")

# Variable global para persistir semilla aleatoria entre reinicios
_persistent_random_seed: int | None = None


def start_traci_connection(
    label: str, config_file: str, use_gui: bool, sumo_settings: SumoSettings
) -> traci.connection.Connection | Any:
    global _persistent_random_seed

    sumo_binary = "sumo-gui" if use_gui else "sumo"
    command = [sumo_binary, "-c", config_file, "--no-warnings"]

    # Configurar semillas aleatorias según la configuración
    if sumo_settings.use_random_seed:
        if sumo_settings.persist_random_seed:
            # Generar semilla UNA VEZ y reutilizarla en reinicios
            if _persistent_random_seed is None:
                import time

                _persistent_random_seed = int(time.time()) % 100000
                logger.info(
                    f"🎲 Generando nueva semilla persistente: {_persistent_random_seed}"
                )
            else:
                logger.info(
                    f"🔄 Reutilizando semilla persistente: {_persistent_random_seed}"
                )

            command.extend(["--seed", str(_persistent_random_seed)])
        else:
            # Generar nueva semilla en CADA reinicio
            command.append("--random")
            logger.info("🎲 Generando nueva semilla aleatoria en cada reinicio")
    elif sumo_settings.fixed_seed is not None:
        command.extend(["--seed", str(sumo_settings.fixed_seed)])
        logger.info(f"🎯 Usando semilla fija: {sumo_settings.fixed_seed}")
    else:
        # Usar el comportamiento por defecto de SUMO (seed=23423)
        logger.info("🔄 Usando semilla por defecto de SUMO (23423)")

    traci.start(cmd=command, label=label)
    return traci.getConnection(label)


def api_service(
    app_s1: SumoApp, app_s2: SumoApp | None, comp_logger: ComparisonLogger | None
) -> None:
    logger.info("Iniciando el servicio API de SUMO...")

    try:
        api = SumoAPI(
            name="API_SUMO", app_s1=app_s1, app_s2=app_s2, comparison_logger=comp_logger
        )
        api.run(host="0.0.0.0", port=5000, debug=False, threaded=False)
    except Exception as e:
        logger.error(f"No se pudo iniciar el servicio API: {e}", exc_info=True)


def shutdown_handler(sig_num: int, frame: Any) -> None:
    logger.info("⚠️  Cerrando el servicio de simulación...")
    traci.close()  # Cierra todas las conexiones activas
    sys.exit(0)


if __name__ == "__main__":
    signal.signal(signal.SIGINT, shutdown_handler)
    logger.info("✅ Iniciando el Servicio de Proveedor de Datos por Simulación...")

    try:
        settings = load_app_settings()
    except Exception as e:
        logger.error(f"Error cargando la configuración: {e}")
        sys.exit(1)

    app_s1 = None
    app_s2 = None
    comparison_logger = None

    try:
        zonas = ZoneList()
        config_file_path = "assets/sumo_maps/MapaDe0/mapa.sumocfg"

        logger.info("Iniciando conexión Traci para la simulación principal (s1)...")
        traci_s1 = start_traci_connection(
            "s1", config_file_path, settings.sumo.gui, settings.sumo
        )
        app_s1 = SumoApp(
            traci_s1,
            zonas,
            "s1",
            config_file_path,
            settings.sumo.gui,
            lambda label, config, gui: start_traci_connection(
                label, config, gui, settings.sumo
            ),
        )

        if settings.sumo.comparar:
            logger.info("Modo de comparación habilitado.")
            logger.info(
                "Iniciando conexión Traci para la simulación de comparación (s2)..."
            )
            traci_s2 = start_traci_connection(
                "s2", config_file_path, settings.sumo.gui, settings.sumo
            )
            app_s2 = SumoApp(
                traci_s2,
                zonas,
                "s2",
                config_file_path,
                settings.sumo.gui,
                lambda label, config, gui: start_traci_connection(
                    label, config, gui, settings.sumo
                ),
            )
            comparison_logger = ComparisonLogger(interval_seconds=15)

            # Verificar sincronización inicial
            tiempo_s1 = app_s1.traci.simulation.getTime()
            tiempo_s2 = app_s2.traci.simulation.getTime()
            diferencia_inicial = abs(tiempo_s1 - tiempo_s2)
            logger.info(
                f"Sincronización inicial: S1={tiempo_s1:.1f}s, S2={tiempo_s2:.1f}s, diff={diferencia_inicial:.1f}s"
            )

            # Usar la misma lógica permisiva que en la API
            if diferencia_inicial > 2.0:
                logger.warning(
                    "⚠️  Las simulaciones tienen una diferencia inicial mayor a 2 segundos!"
                )
            else:
                logger.info(
                    "✅ Simulaciones con diferencia inicial aceptable (fase inicial)"
                )
                if diferencia_inicial <= 1.0:
                    logger.info("✅ Simulaciones perfectamente sincronizadas")

        # Las simulaciones son pasivas. No se inician hilos para ellas.
        # La API se inicia en el hilo principal y bloquea la ejecución,
        # esperando llamadas para avanzar las simulaciones.
        api_service(app_s1, app_s2, comparison_logger)

    except (TraCIException, FatalTraCIError) as e:
        logger.error(f"Error fatal al iniciar Traci: {e}")
        shutdown_handler(0, 0)
    except Exception as e:
        logger.error(
            f"Ocurrió un error inesperado durante el inicio: {e}", exc_info=True
        )
        shutdown_handler(0, 0)
