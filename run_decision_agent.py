# run_decision_agent.py

import logging
import os
import signal
import sys

from src.traffic_system.core.config_loader import load_app_settings
from src.traffic_system.decision.DQN.App import AppDecision

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__))))


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(message)s")
logger = logging.getLogger("DecisionAgent")


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
    settings = load_app_settings()
    app = AppDecision()
    if settings.decision.entrenamiento.entrenar:
        app.entrenar()
        shutdown_handler(0, 0)

    else:
        app.usar()


def shutdown_handler(signum, frame):
    logger.info("Cerrando el agente de decisión...")
    sys.exit(0)


if __name__ == "__main__":
    signal.signal(signal.SIGINT, shutdown_handler)
    main()
