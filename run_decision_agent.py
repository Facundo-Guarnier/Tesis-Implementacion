# run_decision_agent.py

import logging
import os
import signal
import sys
import threading
import time
from typing import Any

from flask import Flask, jsonify

from src.traffic_system.core.config_loader import load_app_settings
from src.traffic_system.decision.DQN.App import DecisionApp

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__))))


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(message)s")
logger = logging.getLogger("DecisionAgent")

# Variables globales para control del servicio
service_thread: threading.Thread | None = None
service_stop_event = threading.Event()
current_app: Any = None


def run_service() -> None:
    """Ejecutar el servicio principal en un thread separado."""
    global current_app
    try:
        settings = load_app_settings()
        current_app = DecisionApp()

        if settings.decision.entrenamiento_completo.entrenar:
            current_app.train_model()
        else:
            current_app.run_model_inference()

    except Exception as e:
        logger.error(f"Error en el servicio: {e}", exc_info=True)


def start_service() -> None:
    """Iniciar el servicio en un thread separado."""
    global service_thread

    if service_thread and service_thread.is_alive():
        logger.warning("Servicio ya está ejecutándose")
        return

    service_stop_event.clear()
    service_thread = threading.Thread(target=run_service, daemon=False)
    service_thread.start()
    logger.info("Servicio iniciado en thread separado")


def stop_service() -> None:
    """Detener el servicio de forma graceful."""
    global service_thread, current_app

    service_stop_event.set()

    # Intentar detener la app si tiene método de stop
    if current_app and hasattr(current_app, "stop"):
        try:
            current_app.stop()
        except Exception as e:
            logger.warning(f"Error deteniendo app: {e}")

    # Esperar a que el thread termine
    if service_thread and service_thread.is_alive():
        service_thread.join(timeout=5)
        if service_thread.is_alive():
            logger.warning("El servicio no se detuvo en el tiempo esperado")
        else:
            logger.info("Servicio detenido correctamente")

    current_app = None


def restart_service() -> bool:
    """Reiniciar solo el servicio (no Flask)."""
    try:
        logger.info("Reiniciando servicio...")
        stop_service()
        start_service()
        return True
    except Exception as e:
        logger.error(f"Error reiniciando servicio: {e}")
        return False


def create_health_server() -> Flask:
    """Crea un servidor Flask simple para health checks."""
    app = Flask(__name__)

    @app.route("/health", methods=["GET"])
    def health_check() -> Any:
        return jsonify({"status": "ok"})

    @app.route("/restart", methods=["POST"])
    def restart_service_endpoint() -> Any:
        """Reinicia solo el servicio DQN, mantiene Flask funcionando."""
        try:
            logger.info("Solicitud de reinicio de servicio recibida")

            success = restart_service()

            if success:
                return jsonify(
                    {
                        "status": "restarted",
                        "message": "Servicio reiniciado correctamente",
                    }
                )
            else:
                return (
                    jsonify(
                        {"status": "error", "message": "Error al reiniciar servicio"}
                    ),
                    500,
                )

        except Exception as e:
            logger.error(f"Error en endpoint restart: {e}")
            return jsonify({"status": "error", "message": str(e)}), 500

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
    """Inicializar el servicio con Flask y servicio DQN en threads separados."""
    logger.info("Iniciando Decision Agent con arquitectura multi-thread")

    # Iniciar servidor Flask de health check
    start_health_server()

    # Iniciar servicio DQN en thread separado
    start_service()

    # Mantener el proceso principal vivo
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Interrupción recibida, cerrando servicios...")
        stop_service()
        sys.exit(0)


def shutdown_handler(sig_num: int, frame: Any) -> None:
    logger.info("Cerrando el agente de decisión...")
    stop_service()
    sys.exit(0)


if __name__ == "__main__":
    signal.signal(signal.SIGINT, shutdown_handler)
    main()
