
#T* Version 2: Red neuronal (Reinforcement Learning Neural Network)
# https://www.youtube.com/watch?v=CQu4wFLC79U
#* Una vez que la red neuronal decidió el color, deberían pasar 5 segundo (cantidad de tics de la simulacion) en los 
#* cuales existe la transición de verde a rojo (5 segundo de amarillo).

#* Red neuronal que tenga como entrada la densidad de vehículos en cada carril (12 neuronas) y devuelva el color de cada semaforo.

#* La recompensa o la forma de saber si está haciendo bien su trabajo será la cantidad de vehículos que pasan por el 
#* semáforo en un tiempo determinado (en el video es la inversa del valor de furia/espera: 1/furia=score). 

#* En el video tiene 18 entradas, 2 capas ocultas de 10 y la salida que es de 10 (10 posibles estado del semaforo) con funcion de activación tanh.  


#* Q-learning, SARSA, Deep Q-Network (DQN) y Proximal Policy Optimization (PPO):  35.79 %, 51.63 %, 63.40 % y 63.49 %
#* Deep Q-network
import csv
import os
import random
import time
import numpy as np
import tensorflow as tf
from collections import deque
from numpy import ndarray as NDArray

from Api import ApiClient

class EntrenamientoDQN:
    def __init__(self):
        self.__setEspacioAcciones()
        self.memory = deque(maxlen=2000)
        self.__api = ApiClient("http://127.0.0.1:5000")
        self.__setPath()


    def __setEspacioAcciones(self) -> None:
        """
        Devuelve el espacio de acciones está formado por una lista de tuplas, donde cada tupla representa el estado de los 4 semaforos. 
        - Ej: [('GGGGGGrrrrr', 'GgGGrrrrGgGg', 'GgGgGgGGrrrr', 'GGGrrrrGGg'), ...]
        """
        # semaforo_1 = ['GGGGGGrrrrr', 'rrrrrrGGgGG', 'rrGGGGGrGrr']
        # semaforo_2 = ['GgGGrrrrGgGg', 'GGGGGGrrrrrr', 'GrrrGGGGrrrr', 'grrrrrrrGGGG']
        # semaforo_3 = ['GgGgGgGGrrrr', 'rrrrGGGGGGrr', 'rrrrGrrrGGGG', 'GGGGgrrrrrrr']
        # semaforo_4 = ['GGGrrrrGGg', 'rrrGGGGrrr']
        
        semaforo_1 = ['GGGGGGrrrrr', 'rrrrrrGGgGG']
        semaforo_2 = ['GgGGrrrrGgGg', 'GrrrGGGGrrrr']
        semaforo_3 = ['GgGgGgGGrrrr', 'rrrrGrrrGGGG']
        semaforo_4 = ['GGGrrrrGGg', 'rrrGGGGrrr']
        
        self.__espacio_acciones = [f"{s1}-{s2}-{s3}-{s4}" for s1 in semaforo_1 for s2 in semaforo_2 for s3 in semaforo_3 for s4 in semaforo_4]


    def __setPath(self) -> None:
        """
        Establece la ruta donde se guardarán los archivos.
        """
        path = f'Decision/Resultados_entrenamiento/DQN_{time.strftime("%Y-%m-%d_%H-%M")}'
        if not os.path.exists(path):
            os.makedirs(path)
        self.__path = path


    def _build_model(self):
        """
        Define la arquitectura de la red neuronal utilizando TensorFlow.
        """
        model = tf.keras.Sequential([
            tf.keras.layers.Dense(64, input_dim=self.state_size, activation='relu'),
            tf.keras.layers.Dense(64, activation='relu'),
            tf.keras.layers.Dense(len(self.__espacio_acciones), activation='linear')
        ])
        model.compile(loss='mse', optimizer=tf.keras.optimizers.Adam(lr=self.learning_rate))
        return model


    def remember(self, state:NDArray, action:int, reward:float, next_state:NDArray, dode:bool):
        """
        Almacena la experiencia del agente en la memoria de reproducción.
        """
        self.memory.append((state, action, reward, next_state, dode))


    def __poilitica(self, state:NDArray) -> int: 
        """
        Elige una acción basada en el estado actual del agente, utilizando una política ε-greedy para el control de la exploración.
        """
        if np.random.rand() <= self.epsilon:
            return np.random.choice(len(self.__espacio_acciones))
        else:
            act_values = self.model.predict(state)
            return int(np.argmax(act_values[0]))


    def replay(self, batch_size:int):
        """
        Realiza el proceso de repetición, donde la red neuronal se entrena utilizando muestras de experiencia de la memoria de reproducción.
        """
        
        minibatch = random.sample(self.memory, batch_size)
        
        #T* V1
        # for state, action, reward, next_state, done in minibatch:
        #     target = reward
        #     if not done:
        #         target = (reward + self.gamma * np.amax(self.model.predict(next_state)[0]))
        #     target_f = self.model.predict(state, verbose=0, use_multiprocessing=True)
        #     target_f[0][action] = target
        #     self.model.fit(state, target_f, epochs=1, verbose=0, use_multiprocessing=True)
            
        # if self.epsilon > self.epsilon_min:
        #     self.epsilon *= self.epsilon_decay
        
        #T* V2
        # states = []
        # targets = []
        # t1 = time.time()
        
        # for state, action, reward, next_state, done in minibatch:
        #     target = reward
            
        #     if not done:
        #         target = (reward + self.gamma * np.amax(self.model.predict(next_state, verbose=0, use_multiprocessing=True)[0]))
            
        #     target_f = self.model.predict(state, verbose=0, use_multiprocessing=True)
        #     target_f[0][action] = target
        #     states.append(state[0])
        #     targets.append(target_f[0])
        
        # self.model.fit(np.array(states), np.array(targets), epochs=1, verbose=0, batch_size=batch_size, use_multiprocessing=True)
        
        # if self.epsilon > self.epsilon_min:
        #     self.epsilon *= self.epsilon_decay
        
        # print(f" - Tiempo de entrenamiento: {(time.time() - t1):.2f}")
        
        
        
        #T* V3
        t1 = time.time()

        all_predictions = self.model.predict(np.array([s[0] for s, _, _, _, _ in minibatch]), batch_size=batch_size, verbose=0, use_multiprocessing=True)
        all_predictions_copy = all_predictions.copy()

        states = []
        targets = []

        for i, (state, action, reward, next_state, done) in enumerate(minibatch):
            target = reward
                    
            if not done:
                target = (reward + self.gamma * np.amax(all_predictions_copy[i]))

            target_f = all_predictions_copy[i]
            target_f[action] = target
            states.append(state[0])
            targets.append(target_f)

        self.model.fit(np.array(states), np.array(targets), epochs=1, verbose=0, batch_size=batch_size, use_multiprocessing=True)

        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay

        print(f" - Tiempo de entrenamiento: {(time.time() - t1):.2f}")

        
    
    
    def train(self):
        for e in range(self.num_epocas):
            print(f"Entrenando epoca: {e+1} de {self.num_epocas} epcoas.")
            state = self.__estado()
            done = False
            total_reward = 0
            
            r = 0
            
            while not done:
                action = self.__poilitica(state)
                next_state, reward, done = self.__avanzar(action)
                
                total_reward += reward
                self.remember(state, action, reward, next_state, done)
                
                state = next_state
                if len(self.memory) > self.batch_size:
                    print(f"\nRepeticion: {r+1}, Epoca: {e+1}")
                    self.replay(self.batch_size)
                    r += 1
                
            self.model.save(self.__path + f"/epoca_{e+1}.h5")


    def __estado(self) -> NDArray:
        """
        Define el estado: 
        - El tiempo de espera de los vehículos en las intersecciones.
        - No incluye el color de los semáforos porque estaría duplicando datos con respecto a la accion.
        - Ej: [1,3,5,0,1,2,4,2,6,3,9,10]
        """
        #! Tiempo
        estado = tuple(self.__api.getTiemposEspera()["tiempos_espera"])
        tiempo_maximo_espera = max(estado)

        #! Normalizar los tiempos de espera
        estado = tuple([round(tiempo_espera / tiempo_maximo_espera , 2) for tiempo_espera in estado])
        return np.reshape(estado, [1, self.state_size])
    
    
    def __avanzar(self, action:int) -> tuple[NDArray, float, bool]:
        """
        Realiza las siguientes tareas:
        1. Ejecuta la acción en SUMO.
        2. Simula 15 pasos (para tener una recompensa mas realista).
        3. Devuelve el nuevo estado, la recompensa y si se ha terminado la epoca.
        """
        
        action2 = self.__espacio_acciones[action]
        
        #! Cambiar el estado de los semáforos en SUMO
        self.__api.putEstados(accion=action2.split('-'))
        
        #! Avanzar en SUMO con la acción seleccionada
        respuesta = self.__api.putAvanzar(steps=15)
        
        done:bool = respuesta['done']    #! Si la simulación ha terminado
        
        return self.__estado(), self.__recompensa(), done 


    def __recompensa(self) -> float:
        """
        Calcula la recompensa en función del estado actual. 
        La inversa de:
        - (0%) El tiempo de espera de los vehículos en las intersecciones controladas por los semáforos.
        - (0%) La cantidad de vehículos en cada calle/zona.
        """
        tiempo = self.__api.getTiemposEspera()["tiempo_espera_total"]
        # cantidad = sum(self.__api.getCantidades().values())
        return 100 / ((tiempo) + 100)
    
    
    def main(self, batch_size:int, num_epocas:int, gamma:float, epsilon:float):
        """
        Método principal.
        """
    
        #! Verificar si el archivo ya existe
        if not os.path.isfile(self.__path + '/entrenamiento_data.csv'):
            with open(self.__path + '/entrenamiento_data.csv', mode='w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(['Epoca', 'Duracion', 'Recompensa Acumulada', 'Tasa de Exploración vs Explotación (Epsilon)', 'Metrica de Convergencia'])
        
        
        # #! Ver la recompensa con semaforos con tiempo fijo
        # total_reward = 0.0
        # done = False
        # print("Calculando recompensa con semaforos con tiempo fijo.")
        # while not done:
        #     total_reward += self.__recompensa()
        #     done = self.__api.putAvanzar(steps=10)['done'] 
            
        
        self.num_epocas = num_epocas
        self.gamma = gamma              #! Factor de descuento, que determina la importancia de las recompensas futuras.
        
        self.epsilon = epsilon          #! Probabilidad de exploración
        self.epsilon_decay = 0.995
        self.epsilon_min = 0.01
        
        self.state_size = 12            #! Cantidad de estados
        self.batch_size = batch_size    #! Tamaño del lote de datos que se utilizará en cada paso de entrenamiento
        self.learning_rate = 0.001      #! Tasa de aprendizaje
        
        self.model = self._build_model()
        
        self.train()
