import time, requests # type: ignore

from Decision.DQN.DQN import DQN
from Decision.DQN.EntrenamientoDQN import EntrenamientoDQN

class AppDecision:
    
    def __init__(self):
        pass

    def entrenar(self, base_path:str) -> None:
        """
        Entrenar el modelo.
        """
        print("Entrenar DQN")
        
        conextion = False
        
        while not conextion:
            try:
                algoritmo1 = EntrenamientoDQN(
                    base_path=base_path
                )
                Q = algoritmo1.main(
                    num_epocas=50, 
                    gamma=0.99, 
                    epsilon=1,
                    epsilon_decay=0.999,
                    batch_size=32,
                )
                conextion = True
            
            except ConnectionError as e:
                print("Reintentando conexión...")
                time.sleep(1)
            
            except Exception as e:
                print("[ERROR DQN.App]:", e)
                break
    
    def usar(self) -> None:
        """
        Usar el modelo entrenado.
        """
        print("Usar DQN")
        
        conextion = False
        
        while not conextion:
            try:
                algoritmo2 = DQN(path_modelo="Decision/Resultados_entrenamiento/DQN_2024-04-18_17-22/epoca_15.h5")
                algoritmo2.usar()
                conextion = True
            
            except requests.exceptions.ConnectionError as e:
                print("Reintentando conexión...")
                time.sleep(1)
            
            except Exception as e:
                print("[ERROR DQN.App]:", e)
                break


# if __name__ == "__main__":
    
#     app = AppDecision()
#     # app.entrenar()
#     app.usar()