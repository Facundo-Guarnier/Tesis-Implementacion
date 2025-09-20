# run_decision_agent.py

import logging
import os
import signal
import sys
import threading
from typing import Any

from flask import Flask, jsonify

from src.traffic_system.core.config_loader import load_app_settings
from src.traffic_system.decision.DQN.App import DecisionApp

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__))))


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(message)s")
logger = logging.getLogger("DecisionAgent")


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
        health_app.run(host="0.0.0.0", port=8080, debug=False, use_reloader=False)

    health_thread = threading.Thread(target=run_server, daemon=True)
    health_thread.start()
    logger.info("Servidor de health check iniciado en puerto 8080")


# def main():
#     logger.info("Iniciando el Agente de Toma de Decisiones...")
#     try:
#         settings = load_app_settings()
#     except ConfigValidationError as e:
#         logger.error(f"Error de configuración: {e}")
#         sys.exit(1)

#     if not settings.decision.decision:
#         logger.info("El agente de decisión está desactivado en la configuración.")
#         return

#     if settings.decision.entrenamiento.entrenar:
#         logger.info("Modo ENTRENAMIENTO no implementado en este script todavía.")
#         # Aquí iría la lógica de EntrenamientoDQN
#     else:
#         logger.info("Iniciando agente en modo de USO.")
#         try:
#             agent = DQN(
#                 path_modelo=settings.decision.path_modelo_entrenado,
#                 decision_settings=settings.decision,
#             )
#             agent.usar()  # El bucle principal vive dentro de este método
#         except Exception as e:
#             logger.error(f"Error durante la ejecución del agente: {e}", exc_info=True)

#     logger.info("El agente de decisión ha finalizado.")


def main() -> None:
    """
    Inicial el modelo de toma de decisiones.
    Puede:
    - Entrenar el modelo.
    - Utilizar un modelo ya entrenado.
    """
    # Iniciar servidor de health check
    start_health_server()

    settings = load_app_settings()
    app = DecisionApp()
    if settings.decision.entrenamiento_completo.entrenar:
        app.train_model()
        shutdown_handler(0, 0)

    else:
        app.run_model_inference()


def shutdown_handler(sig_num: int, frame: Any) -> None:
    logger.info("Cerrando el agente de decisión...")
    sys.exit(0)


if __name__ == "__main__":
    signal.signal(signal.SIGINT, shutdown_handler)
    main()
