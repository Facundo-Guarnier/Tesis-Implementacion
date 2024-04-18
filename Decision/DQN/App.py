from DQN import DQN
from EntrenamientoDQN import EntrenamientoDQN

if __name__ == "__main__":
    
    entrenar = False
    
    if entrenar:
        #T* Entrenar
        print("Entrenar DQN")
        algoritmo1 = EntrenamientoDQN()
        Q = algoritmo1.main(
            num_epocas=50, 
            gamma=0.99, 
            epsilon=1,
            epsilon_decay=0.999,
            batch_size=32,
        )

    else:
        #T* Usar SARSA
        print("Usar DQN")
        algoritmo2 = DQN(path_modelo="Decision/Resultados_entrenamiento/epoca_12.h5")
        algoritmo2.usar()
        
