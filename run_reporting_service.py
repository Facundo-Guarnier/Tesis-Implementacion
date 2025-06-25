# run_detection_provider.py

import logging
import os
import signal
import sys

# Añadir la raíz al path para que las importaciones funcionen desde cualquier lugar
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__))))


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(message)s")
logger = logging.getLogger("ReportingService")


def main() -> None:
    """
    Genera el reporte de la simulación.
    """
    from src.traffic_system.reporting.App import AppReporte

    app = AppReporte()
    app.generar_reporte()


def shutdown_handler(signum, frame):
    logger.info("⚠️ Cerrando el servicio de simulación...")
    sys.exit(0)


if __name__ == "__main__":
    signal.signal(signal.SIGINT, shutdown_handler)
    main()
