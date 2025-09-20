import logging
import os
import signal
import sys
import threading
from typing import Any

from flask import Flask, jsonify

from src.traffic_system.reporting.App import ReportApp

# TODO: Revisar el uso de sys.path.append
# Añadir la raíz al path para que las importaciones funcionen desde cualquier lugar
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__))))


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(message)s")
logger = logging.getLogger("ReportingService")


def create_health_server() -> Flask:
    """Crea un servidor Flask simple para health checks."""
    app = Flask(__name__)

    @app.route("/health", methods=["GET"])
    def health_check() -> Any:
        return jsonify({"status": "ok"})

    return app


def start_health_server() -> None:
    """Inicia el servidor de health check en un hilo separado."""
    health_app = create_health_server()

    def run_server() -> None:
        health_app.run(host="0.0.0.0", port=8081, debug=False, use_reloader=False)

    health_thread = threading.Thread(target=run_server, daemon=True)
    health_thread.start()
    logger.info("Servidor de health check iniciado en puerto 8081")


def main() -> None:
    """
    Genera el reporte de la simulación.
    """
    # Iniciar servidor de health check
    start_health_server()

    app = ReportApp()
    app.generate_report()


def shutdown_handler(sig_num: int, frame: Any) -> None:
    logger.info("⚠️ Cerrando el servicio de simulación...")
    sys.exit(0)


if __name__ == "__main__":
    signal.signal(signal.SIGINT, shutdown_handler)
    main()
