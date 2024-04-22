import time, requests, logging, inspect # type: ignore

from Decision.DQN.DQN import DQN
from Decision.DQN.EntrenamientoDQN import EntrenamientoDQN

class AppDecision:
    
    def __init__(self):
        logging.basicConfig(level=logging.DEBUG)

    def entrenar(self, base_path:str, num_epocas:int, batch_size:int, steps:int, learning_rate:float, learning_rate_decay:float, learning_rate_min:float, epsilon:float, epsilon_decay:float, epsilon_min:float, gamma:float, hidden_layers:list[int]) -> None:
        """
        Entrenar el modelo.
        """
        logger = logging.getLogger(f' {self.__class__.__name__}.{inspect.currentframe().f_code.co_name}') # type: ignore
        
        logger.info("Entrenar DQN")
        
        conextion = False
        
        while not conextion:
            try:
                algoritmo1 = EntrenamientoDQN(
                    base_path=base_path,
                    num_epocas=num_epocas,
                    batch_size=batch_size,
                    steps=steps,

                    #! Tasa de aprendizaje
                    learning_rate=learning_rate,
                    learning_rate_decay=learning_rate_decay,
                    learning_rate_min=learning_rate_min,
                    
                    #! Exploración
                    epsilon=epsilon,
                    epsilon_decay=epsilon_decay,
                    epsilon_min=epsilon_min,
                    
                    #! Importancia futuras
                    gamma=gamma,
                    
                    #! Red
                    hidden_layers=hidden_layers,
                )
                Q = algoritmo1.main()
                conextion = True
            
            except requests.exceptions.ConnectionError as e:
                logger.info("Reintentando conexión...")
                time.sleep(1)
            
            except Exception as e:
                logger.error(e)
                break
    
    def usar(self, path_modelo:str) -> None:
        """
        Usar el modelo entrenado.
        """
        logger = logging.getLogger(f' {self.__class__.__name__}.{inspect.currentframe().f_code.co_name}') # type: ignore

        logger.info("Usar DQN")
        
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


# if __name__ == "__main__":
    
#     app = AppDecision()
#     # app.entrenar()
#     app.usar()