
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
import csv, os, random, time, logging, inspect
import numpy as np
import tensorflow as tf
from collections import deque
from numpy import ndarray as NDArray

from Decision.DQN.Api import ApiDecision

class EntrenamientoDQN:
    def __init__(self, base_path:str, num_epocas:int, batch_size:int, steps:int, learning_rate:float, learning_rate_decay:float, learning_rate_min:float, epsilon:float, epsilon_decay:float, epsilon_min:float, gamma:float, hidden_layers: list[int]) -> None:
        """
        Inicializa el agente de aprendizaje por refuerzo utilizando el algoritmo DQN.
        
        Args:
            base_path (str): Ruta donde se guardarán los archivos.
            steps (int): Pasos que se avanzará en la simulación por cada acción.
            learning_rate (float): Tasa de aprendizaje.
            learning_rate_decay (float): Decaimiento de la tasa de aprendizaje.
            learning_rate_min (float): Minima tasa de aprendizaje.
            epsilon (float): Exploración/explotación inicial.
            epsilon_decay (float): Decaimiento de la exploración/explotación.
            epsilon_min (float): Exploración/explotación mínima.
            num_epocas (int): Cantidad de épocas.
            batch_size (int): Tamaño del lote de datos que se utilizará en cada paso de entrenamiento.
            gamma (float): Factor de descuento, que determina la importancia de las recompensas futuras.
        """
        logging.basicConfig(level=logging.DEBUG)
        self.memory:deque = deque(maxlen=4000)
        self.__api = ApiDecision("http://127.0.0.1:5000")
        
        self.__setEspacioAcciones()
        self.__setPath(base_path)
        self.state_size = 12
        
        #! Hiperparámetros
        self.num_epocas = num_epocas
        self.batch_size = batch_size
        self.steps = steps
        
        self.learning_rate = learning_rate
        self.learning_rate_decay = learning_rate_decay
        self.learning_rate_min = learning_rate_min
        
        self.epsilon = epsilon
        self.epsilon_decay = epsilon_decay
        self.epsilon_min = epsilon_min
        
        self.gamma = gamma
        self.hidden_layers = hidden_layers
        
    
    
    def __setEspacioAcciones(self) -> None:
        """
        Establece el espacio de acciones está formado por una lista de tuplas, donde cada tupla representa el estado de los 4 semaforos. 
        - Ej: [('GGGGGGrrrrr', 'GgGGrrrrGgGg', 'GgGgGgGGrrrr', 'GGGrrrrGGg'), (...), ...]
        """
        
        semaforo_1 = ['GGGGGGrrrrr', 'rrrrrrGGgGG']
        semaforo_2 = ['GGGrrrrrGGg', 'rrrGGGGGrrr']
        semaforo_3 = ['GGgGGGrrrrr', 'rrrrrrGGGGG']
        semaforo_4 = ['GGGrrrrGGg', 'rrrGGGGrrr']
        
        self.__espacio_acciones = [f"{s1}-{s2}-{s3}-{s4}" for s1 in semaforo_1 for s2 in semaforo_2 for s3 in semaforo_3 for s4 in semaforo_4]
    
    
    def __setPath(self, base_path: str) -> None:
        """
        Establece la ruta donde se guardarán los archivos.
        """
        self.__path = os.path.join(base_path, f'Decision/Resultados_entrenamiento/DQN_{time.strftime("%Y-%m-%d_%H-%M")}')
        if not os.path.exists(self.__path):
            os.makedirs(self.__path)
    
    
    def __build_model(self) -> tf.keras.Model:
        """
        Define la arquitectura de la red neuronal utilizando TensorFlow.
        """
        logger = logging.getLogger(f' {self.__class__.__name__}.{inspect.currentframe().f_code.co_name}') # type: ignore

        #! Construir el modelo en base a self.hidden_layers
        model = tf.keras.Sequential()
        model.add(tf.keras.layers.Dense(self.hidden_layers[0], input_dim=self.state_size, activation='relu'))
        
        for i in range(1, len(self.hidden_layers)):
            model.add(tf.keras.layers.Dense(self.hidden_layers[i], activation='relu'))
        
        model.add(tf.keras.layers.Dense(len(self.__espacio_acciones), activation='linear'))
        
        # model = tf.keras.Sequential([
        #     tf.keras.layers.Dense(10, input_dim=self.state_size, activation='relu'),
        #     tf.keras.layers.Dense(10, activation='relu'),
        #     tf.keras.layers.Dense(len(self.__espacio_acciones), activation='linear')
        # ])
        model.compile(loss='mse', optimizer=tf.keras.optimizers.Adam(lr=self.learning_rate))
        logger.info(f"{model.summary()}")
        return model
    
    
    def __remember(self, state:NDArray, action:int, reward:float, next_state:NDArray, done:bool) -> None:
        """
        Almacena la experiencia del agente en la memoria de reproducción.
        """
        self.memory.append((state, action, reward, next_state, done))
    
    
    def __politica(self, state:NDArray) -> int: 
        """
        Elige una acción basada en el estado actual del agente, utilizando una política ε-greedy para el control de la exploración.
        """
        if np.random.rand() <= self.epsilon:
            return np.random.choice(len(self.__espacio_acciones))
        else:
            act_values = self.model.predict(state)
            return int(np.argmax(act_values[0]))
    
    
    def __replay(self) -> None:
        """
        Realiza el proceso de repetición, donde la red neuronal se entrena utilizando muestras de experiencia de la memoria de reproducción.
        """
        
        minibatch = random.sample(self.memory, self.batch_size)
        
        all_predictions = self.model.predict(np.array([s[0] for s, _, _, _, _ in minibatch]), batch_size=self.batch_size, verbose=0, use_multiprocessing=True)
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

        self.model.fit(np.array(states), np.array(targets), epochs=1, verbose=0, batch_size=self.batch_size, use_multiprocessing=True)

        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay
        
        if self.learning_rate > self.learning_rate_min:
            self.learning_rate *= self.learning_rate_decay
    
    
    def __train(self) -> None:
        """
        Entrena el agente utilizando el algoritmo DQN.
        Por cada epoca, el agente realiza una serie de acciones en el entorno, almacenando la 
        experiencia en la memoria de reproducción.
        Cuando el tamaño de la memoria de reproducción alcanza el tamaño del lote, el agente 
        realiza el proceso de repetición (19500/15 = 1300 repeticiones).
        """
        logger = logging.getLogger(f' {self.__class__.__name__}.{inspect.currentframe().f_code.co_name}') # type: ignore
        
        for e in range(self.num_epocas):
            logger.info(f"Entrenando epoca: {e+1} de {self.num_epocas} épocas.")
            state = self.__estado()
            done = False
            total_reward = 0.0
            
            t1 = time.time()
            while not done:
                action = self.__politica(state)
                next_state, reward, done = self.__avanzar(action)
                
                total_reward += reward
                self.__remember(state, action, reward, next_state, done)
                
                state = next_state
                if len(self.memory) > self.batch_size:
                    self.__replay()
            
            #! Guardar los datos de entrenamiento por epoca
            self.model.save(self.__path + f"/epoca_{e+1}.h5")
            
            #! Guardar métricas de entrenamiento en un archivo CSV
            with open(self.__path + '/entrenamiento_data.csv', mode='a', newline='') as file:
                writer = csv.writer(file)
                writer.writerow([e+1, f"{(time.time()-t1):.2f}" , f"{total_reward:.2f}", f"{self.epsilon:.5f}", f"{self.learning_rate:.5f}"])
    
    
    def __estado(self) -> NDArray:
        """
        Define el estado: 
        - El tiempo de espera de los vehículos en las intersecciones.
        - No incluye el color de los semáforos porque estaría duplicando datos con respecto a la accion.
        - Ej: [1,3,5,0,1,2,4,2,6,3,9,10]
        """
        #! Tiempo
        estado = tuple(self.__api.getTiemposEspera()["tiempos_espera"]) # type: ignore
        tiempo_maximo_espera = max(estado)
        
        if tiempo_maximo_espera == 0:
            return np.reshape(estado, [1, self.state_size])
        else:
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
        respuesta = self.__api.putAvanzar(steps=self.steps)
        
        done:bool = respuesta['done'] # type: ignore #! Si la simulación ha terminado
        
        return self.__estado(), self.__recompensa(), done 
    
    
    def __recompensa(self) -> float:
        """
        Calcula la recompensa en función del estado actual. 
        La inversa de:
        - (0%) El tiempo de espera de los vehículos en las intersecciones controladas por los semáforos.
        - (0%) La cantidad de vehículos en cada calle/zona.
        """
        tiempo = self.__api.getTiemposEspera()["tiempo_espera_total"] # type: ignore
        # cantidad = sum(self.__api.getCantidades().values())
        return 100 / ((tiempo) + 100)
    
    
    def main(self):
        """
        Método principal.
        """
        logger = logging.getLogger(f' {self.__class__.__name__}.{inspect.currentframe().f_code.co_name}') # type: ignore
        
        #! Esperar a que la simulación esté lista
        while not self.__api.getSimulacionOK():
            logger.info("Esperando a que la simulación esté lista...")
            time.sleep(1)
        logger.info("La simulación está lista")
        
        #! Verificar si el archivo ya existe
        if not os.path.isfile(self.__path + '/entrenamiento_data.csv'):
            with open(self.__path + '/entrenamiento_data.csv', mode='w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(['Epoca', 'Duración', 'Recompensa Acumulada', 'Epsilon', 'Tasa de Aprendizaje'])
        
        #! Guardar hiperparámetros
        with open(self.__path + '/hiperparametros.csv', mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['Num Epocas', 'Batch size', 'Steps', 'Learning rate', 'Learning rate decay', 'Learning rate min', 'Epsilon', 'Epsilon decay', 'Epsilon min', 'Gamma', "Red neuronal"])
            layers = f"{self.state_size} | "
            for i in range(len(self.hidden_layers)):
                layers += f"{self.hidden_layers[i]} | "
            layers += f"{len(self.__espacio_acciones)}"
            writer.writerow([self.num_epocas, self.batch_size, self.steps, str(self.learning_rate), self.learning_rate_decay, self.learning_rate_min, self.epsilon, self.epsilon_decay, self.epsilon_min, self.gamma, layers])
        
        #! Calcular la recompensa con semaforos con tiempo fijo
        total_reward = 0.0
        done = False
        logger.info("Calculando recompensa con semaforos con tiempo fijo.")
        while not done:
            total_reward += self.__recompensa()
            done = self.__api.putAvanzar(steps=self.steps)['done']  # type: ignore
        
        #! Guardar los datos de los semaforos con tiempo fijo
        with open(self.__path + '/entrenamiento_data.csv', mode='a', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(["-", "-" , total_reward, "-", "-"])
        
        self.model = self.__build_model()
        
        self.__train()