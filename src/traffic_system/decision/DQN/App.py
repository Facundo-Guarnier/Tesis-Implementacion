import inspect
import logging
import os
import time  # type: ignore

import requests

from src.traffic_system.core.config_loader import load_app_settings
from src.traffic_system.core.config_models import DecisionSettings
from src.traffic_system.decision.DQN.dqn_model import DQNModel
from src.traffic_system.decision.DQN.dqn_trainer import DQNTrainer
from src.traffic_system.decision.DQN.dqn_trainer_simplified import SimplifiedDQNTrainer


class DecisionApp:
    def __init__(self, decision_settings: DecisionSettings | None = None) -> None:
        logging.basicConfig(level=logging.DEBUG)
        # TODO: Eliminar el uso de load_app_settings, ya que deberia cargar desde la configuración global.
        self.settings = load_app_settings().decision

    def train_model1(self) -> None:
        """
        Entrenar el modelo.
        """
        logger = logging.getLogger(
            f" {self.__class__.__name__}.{inspect.currentframe().f_code.co_name}"  # type: ignore
        )

        logger.info("Entrenar DQN")

        is_connected = False

        while not is_connected:
            try:
                dqn_trainer = DQNTrainer()
                dqn_trainer.start_training_process()
                is_connected = True

            except requests.exceptions.ConnectionError:
                logger.info("Reintentando conexión...")
                time.sleep(1)

            except Exception as e:
                logger.error(e)
                break

    def train_model(self) -> None:
        """
        Entrenar el modelo.
        """
        logger = logging.getLogger(
            f" {self.__class__.__name__}.{inspect.currentframe().f_code.co_name}"  # type: ignore
        )

        logger.info("Entrenar DQN Simplificado")

        is_connected = False

        while not is_connected:
            try:
                dqn_trainer = SimplifiedDQNTrainer()
                dqn_trainer.start_training_process()
                is_connected = True

            except requests.exceptions.ConnectionError:
                logger.info("Reintentando conexión...")
                time.sleep(1)

            except Exception as e:
                logger.error(e)
                break

    def run_model_inference(self) -> None:
        """
        Usar el modelo entrenado.
        """
        logger = logging.getLogger(
            f" {self.__class__.__name__}.{inspect.currentframe().f_code.co_name}"  # type: ignore
        )

        logger.info("Usar DQN")
        model_path = self.settings.path_modelo_entrenado

        # Convertir a ruta absoluta si es relativa
        if not os.path.isabs(model_path):
            model_path = os.path.abspath(model_path)

        dqn_model = None
        is_connected = False

        try:
            print(f"Intentando cargar modelo desde: {model_path}")
            dqn_model = DQNModel(path_modelo=model_path)
            logger.info(f"Modelo cargado exitosamente desde: {model_path}")
        except Exception as e:
            logger.error(f"Error al cargar el modelo: {e}")
            logger.error("No se puede continuar sin el modelo. Terminando...")
            return

        is_connected = False

        while not is_connected:
            try:
                dqn_model.run_inference()
                is_connected = True

            except requests.exceptions.ConnectionError:
                logger.info("Reintentando conexión...")
                time.sleep(1)

            except Exception as e:
                logger.error(e)
                break

    def run_model_inference1(self) -> None:
        """
        Usar el modelo entrenado (método original).
        """
        logger = logging.getLogger(
            f" {self.__class__.__name__}.{inspect.currentframe().f_code.co_name}"  # type: ignore
        )

        logger.info("Usar DQN")
        model_path = self.settings.path_modelo_entrenado

        # Convertir a ruta absoluta si es relativa
        if not os.path.isabs(model_path):
            model_path = os.path.abspath(model_path)

        dqn_model = None
        is_connected = False

        try:
            print(f"Intentando cargar modelo desde: {model_path}")
            dqn_model = DQNModel(path_modelo=model_path)
            logger.info(f"Modelo cargado exitosamente desde: {model_path}")
        except Exception as e:
            logger.error(f"Error al cargar el modelo: {e}")
            logger.error("No se puede continuar sin el modelo. Terminando...")
            return

        is_connected = False

        while not is_connected:
            try:
                dqn_model.run_inference()
                is_connected = True

            except requests.exceptions.ConnectionError:
                logger.info("Reintentando conexión...")
                time.sleep(1)

            except Exception as e:
                logger.error(e)
                break
