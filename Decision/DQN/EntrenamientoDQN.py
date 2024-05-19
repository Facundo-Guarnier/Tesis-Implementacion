import csv, os, random, time, logging, inspect
import numpy as np
import tensorflow as tf
from collections import deque
from numpy import ndarray as NDArray

from Decision.DQN.Api import ApiDecision
from config import configuracion

class EntrenamientoDQN:
    """
    Entrenamiento de un agente utilizando el algoritmo DQN (Deep Q-Learning).
    
    - La red neuronal se entrena utilizando la experiencia almacenada en la memoria de reproducción.
    - La política ε-greedy se utiliza para la exploración.
    - La recompensa se calcula en función del tiempo de espera de los vehículos en las intersecciones.
    - La red neuronal se guarda en un archivo .h5 por cada epoca.
    - Las métricas de entrenamiento se guardan en un archivo CSV.
    - Los hiperparámetros se guardan en un archivo CSV.
    
    Attributes:
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
    def __init__(self) -> None:
        logging.basicConfig(level=logging.DEBUG)
        self.memory:deque = deque(maxlen=configuracion["decision"]["entrenamiento"]["memory"])    #! Memoria de reproducción
        self.__api = ApiDecision("http://127.0.0.1:5000")
        
        self.__setEspacioAcciones()
        self.__setPath()
        self.state_size = 12
        
        #! Hiperparámetros
        self.num_epocas = configuracion["decision"]["entrenamiento"]["num_epocas"]
        self.batch_size = configuracion["decision"]["entrenamiento"]["batch_size"]
        self.steps = configuracion["decision"]["entrenamiento"]["steps"]
        
        self.learning_rate = configuracion["decision"]["entrenamiento"]["learning_rate"]
        self.learning_rate_decay = configuracion["decision"]["entrenamiento"]["learning_rate_decay"]
        self.learning_rate_min = configuracion["decision"]["entrenamiento"]["learning_rate_min"]
        
        self.epsilon = configuracion["decision"]["entrenamiento"]["epsilon"]
        self.epsilon_decay = configuracion["decision"]["entrenamiento"]["epsilon_decay"]
        self.epsilon_min = configuracion["decision"]["entrenamiento"]["epsilon_min"]
        
        self.gamma = configuracion["decision"]["entrenamiento"]["gamma"]
        self.hidden_layers = configuracion["decision"]["entrenamiento"]["hidden_layers"]
    
    
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
    
    
    def __setPath(self) -> None:
        """
        Establece la ruta donde se guardarán los archivos.
        """
        self.__path = os.path.join(
            configuracion["decision"]["entrenamiento"]["path_resultado"], 
            f'DQN_{time.strftime("%Y-%m-%d_%H-%M")}',
            )
        if not os.path.exists(self.__path):
            os.makedirs(self.__path)
    
    
    def __build_model(self) -> tf.keras.Model:
        """
        Define la arquitectura de la red neuronal utilizando TensorFlow.
        
        Returns:
            tf.keras.Model: Modelo de la red neuronal.
        """
        logger = logging.getLogger(f' {self.__class__.__name__}.{inspect.currentframe().f_code.co_name}') # type: ignore
        
        #! Construir el modelo en base a self.hidden_layers
        model = tf.keras.Sequential()
        model.add(tf.keras.layers.Dense(self.hidden_layers[0], input_dim=self.state_size, activation='relu'))
        
        for i in range(1, len(self.hidden_layers)):
            model.add(tf.keras.layers.Dense(self.hidden_layers[i], activation='relu'))
        
        model.add(tf.keras.layers.Dense(len(self.__espacio_acciones), activation='linear'))
        
        model.compile(loss='mse', optimizer=tf.keras.optimizers.Adam(lr=self.learning_rate))
        logger.info(f" {model.summary()}")
        return model
    
    
    def __remember(self, state:NDArray, action:int, reward:float, next_state:NDArray, done:bool) -> None:
        """
        Almacena la experiencia del agente en la memoria de reproducción.
        """
        self.memory.append((state, action, reward, next_state, done))
    
    
    def __politica(self, state:NDArray) -> int: 
        """
        Elige una acción basada en el estado actual del agente, utilizando una política ε-greedy para el control de la exploración.
        
        returns:
            int: Índice de la acción seleccionada.
        """
        if np.random.rand() <= self.epsilon:
            return np.random.choice(len(self.__espacio_acciones))
        else:
            act_values = self.model.predict(state, verbose=0)
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
        realiza el proceso de repetición.
        - 19500 segundos / 15 steps  = 1300 repeticiones por epoca
        """
        logger = logging.getLogger(f' {self.__class__.__name__}.{inspect.currentframe().f_code.co_name}') # type: ignore
        
        for e in range(self.num_epocas):
            state = self.__estado()
            done = False
            total_reward = 0.0
            
            t1 = time.time()
            while not done:
                id_action = self.__politica(state)
                next_state, reward, done = self.__avanzar(id_action)
                
                total_reward += reward
                self.__remember(state, id_action, reward, next_state, done)
                
                state = next_state
                if len(self.memory) > self.batch_size:
                    self.__replay()
            
            #! Guardar los datos de entrenamiento por epoca
            self.model.save(self.__path + f"/epoca_{e+1}.h5")
            
            #! Guardar métricas de entrenamiento en un archivo CSV
            with open(self.__path + '/entrenamiento_data.csv', mode='a', newline='') as file:
                writer = csv.writer(file)
                writer.writerow([e+1, f"{(time.time()-t1):.2f}" , f"{total_reward:.2f}", f"{self.epsilon:.5f}", f"{self.learning_rate:.5f}"])
            
            logger.info(f" Epoca: {e+1}/{self.num_epocas}: {total_reward:.2f} recompensa acumulada.")
    
        logger.info(" Entrenamiento finalizado.")
        
        
    
    
    def __estado(self) -> NDArray:
        """
        Define el estado (El tiempo de espera de los vehículos en las intersecciones) normalizado en un rango de 0 a 1.
        returns:
            NDArray: Estado normalizado. [1,3,5,0,1,2,4,2,6,3,9,10] -> [0.1, 0.3, 0.5, 0.0, 0.1, 0.2, 0.4, 0.2, 0.6, 0.3, 0.9, 1.0]
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
    
    
    def __avanzar(self, id_action:int) -> tuple[NDArray, float, bool]:
        """
        Realiza las siguientes tareas:
        1. Ejecuta la acción en SUMO.
        2. Simula x pasos.
        3. Devuelve el nuevo estado, la recompensa y si se ha terminado la epoca.
        
        returns:
            NDArray: Nuevo estado.
            float: Recompensa.
            bool: Si la simulación ha terminado.
        """
        
        action = self.__espacio_acciones[id_action]
        
        #! Cambiar el estado de los semáforos en SUMO
        self.__api.putEstados(accion=action.split('-'))
        
        #! Avanzar en SUMO con la acción seleccionada
        respuesta = self.__api.putAvanzar(steps=self.steps)
        
        done:bool = respuesta['done'] # type: ignore #! Si la simulación ha terminado
        
        return self.__estado(), self.__recompensa(), done 
    
    
    def __recompensa(self) -> float:
        """
        Calcula la recompensa en función del estado actual. 
        La inversa del tiempo de espera de los vehículos en las intersecciones controladas por los semáforos.
        - 100 / (tiempo_espera_total + 100)
        """
        tiempo = self.__api.getTiemposEspera()["tiempo_espera_total"] # type: ignore
        return 100 / ((tiempo) + 100)
    
    
    def main(self) -> None:
        """
        Inicia el proceso de entrenamiento del agente.
        1. Espera a que la simulación esté lista.
        2. Guarda los hiperparámetros en un archivo CSV.
        3. Calcula la recompensa con semaforos con tiempo fijo.
        4. Guarda los datos de los semaforos con tiempo fijo en un archivo CSV.
        5. Inicializa la red neuronal.
        6. Inicia el entrenamiento del agente.
        """
        logger = logging.getLogger(f' {self.__class__.__name__}.{inspect.currentframe().f_code.co_name}') # type: ignore
        
        #! Esperar a que la simulación esté lista
        while not self.__api.getSimulacionOK():
            logger.info(" Esperando a que la simulación esté lista...")
            time.sleep(1)
        logger.info(" La simulación está lista")
        
        #! Verificar si el archivo ya existe
        if not os.path.isfile(self.__path + '/entrenamiento_data.csv'):
            with open(self.__path + '/entrenamiento_data.csv', mode='w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(['Epoca', 'Duración', 'Recompensa Acumulada', 'Epsilon', 'Tasa de Aprendizaje'])
        
        #! Guardar hiperparámetros
        with open(self.__path + '/hiperparametros.csv', mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['Num Epocas', 'Batch size', 'Steps', 'Learning rate', 'Learning rate decay', 'Learning rate min', 'Epsilon', 'Epsilon decay', 'Epsilon min', 'Gamma', "Memoria de reproducción" ,"Red neuronal"])
            layers = f"{self.state_size} | "
            for i in range(len(self.hidden_layers)):
                layers += f"{self.hidden_layers[i]} | "
            layers += f"{len(self.__espacio_acciones)}"
            writer.writerow([self.num_epocas, self.batch_size, str(self.steps)+"+3", str(self.learning_rate), self.learning_rate_decay, self.learning_rate_min, self.epsilon, self.epsilon_decay, self.epsilon_min, self.gamma, self.memory.maxlen, layers])
        
        #! Calcular la recompensa con semaforos con tiempo fijo
        total_reward = 0.0
        done = False
        logger.info(" Calculando recompensa con semaforos con tiempo fijo.")
        while not done:
            total_reward += self.__recompensa()
            done = self.__api.putAvanzar(steps=self.steps)['done']  # type: ignore
        
        #! Guardar los datos de los semaforos con tiempo fijo
        with open(self.__path + '/entrenamiento_data.csv', mode='a', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(["-", "-" , total_reward, "-", "-"])
        
        self.model = self.__build_model()
        
        self.__train()