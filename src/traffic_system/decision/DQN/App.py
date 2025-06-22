import inspect
import logging
import time  # type: ignore

import requests

from src.traffic_system.core.config_loader import load_app_settings
from src.traffic_system.core.config_models import DecisionSettings
from src.traffic_system.decision.DQN.DQN import DQN
from src.traffic_system.decision.DQN.EntrenamientoDQN import EntrenamientoDQN


class AppDecision:

    def __init__(self, decision_settings: DecisionSettings | None = None) -> None:
        logging.basicConfig(level=logging.DEBUG)
        # TODO: Eliminar el uso de load_app_settings, ya que deberia cargar desde la configuración global.
        self.settings = load_app_settings().decision

    def entrenar(self) -> None:
        """
        Entrenar el modelo.
        """
        logger = logging.getLogger(f" {self.__class__.__name__}.{inspect.currentframe().f_code.co_name}")  # type: ignore

        logger.info("Entrenar DQN")

        conextion = False

        while not conextion:
            try:
                algoritmo1 = EntrenamientoDQN()
                algoritmo1.main()
                conextion = True

            except requests.exceptions.ConnectionError:
                logger.info("Reintentando conexión...")
                time.sleep(1)

            except Exception as e:
                logger.error(e)
                break

    def usar(self) -> None:
        """
        Usar el modelo entrenado.
        """
        logger = logging.getLogger(f" {self.__class__.__name__}.{inspect.currentframe().f_code.co_name}")  # type: ignore

        logger.info("Usar DQN")
        path_modelo = self.settings.path_modelo_entrenado
        conextion = False

        while not conextion:
            try:
                algoritmo2 = DQN(path_modelo=path_modelo)
                algoritmo2.usar()
                conextion = True

            except requests.exceptions.ConnectionError:
                logger.info("Reintentando conexión...")
                time.sleep(1)

            except Exception as e:
                logger.error(e)
                break
