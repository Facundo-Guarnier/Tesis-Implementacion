import time, requests, logging, inspect # type: ignore

from Decision.DQN.DQN import DQN
from Decision.DQN.EntrenamientoDQN import EntrenamientoDQN

from config import configuracion

class AppDecision:
    
    def __init__(self):
        logging.basicConfig(level=logging.DEBUG)
    
    
    def entrenar(self) -> None:
        """
        Entrenar el modelo.
        """
        logger = logging.getLogger(f' {self.__class__.__name__}.{inspect.currentframe().f_code.co_name}') # type: ignore
        
        logger.info("Entrenar DQN")
        
        conextion = False
        
        while not conextion:
            try:
                algoritmo1 = EntrenamientoDQN()
                algoritmo1.main()
                conextion = True
            
            except requests.exceptions.ConnectionError as e:
                logger.info("Reintentando conexión...")
                time.sleep(1)
            
            except Exception as e:
                logger.error(e)
                break
    
    
    def usar(self) -> None:
        """
        Usar el modelo entrenado.
        """
        logger = logging.getLogger(f' {self.__class__.__name__}.{inspect.currentframe().f_code.co_name}') # type: ignore
        
        logger.info("Usar DQN")
        path_modelo = configuracion["decision"]["path_modelo_entrenado"]
        conextion = False
        
        while not conextion:
            try:
                algoritmo2 = DQN(path_modelo=path_modelo)
                algoritmo2.usar()
                conextion = True
            
            except requests.exceptions.ConnectionError as e:
                logger.info("Reintentando conexión...")
                time.sleep(1)
            
            except Exception as e:
                logger.error(e)
                break