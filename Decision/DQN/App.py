from DQN import EntrenamientoDQN

if __name__ == "__main__":
    
    entrenar = True
    
    if entrenar:
        #T* Entrenar
        print("Entrenar SARSA")
        algoritmo1 = EntrenamientoDQN()
        Q = algoritmo1.main(
            num_epocas=50, 
            gamma=0.99, 
            epsilon=1,
            batch_size=32,
        )

    else:
        #T* Usar SARSA
        print("Usar SARSA")
        # algoritmo2 = SARSA(path_Q="Decision/Valores_Q_2024-04-17_09-03/epoca_30.pkl")
        # algoritmo2.usar()
        
