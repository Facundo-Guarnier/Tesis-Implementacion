import time, logging, inspect
import numpy as np
import tensorflow as tf
from numpy import ndarray as NDArray

from Decision.DQN.Api import ApiDecision

class DQN:
    def __init__(self, path_modelo:str):
        logging.basicConfig(level=logging.DEBUG)
        self.__api = ApiDecision("http://127.0.0.1:5000")
        self.model = tf.keras.models.load_model(path_modelo)
        self.state_size = 12
        self.__setEspacioAcciones()
    
    
    def __setEspacioAcciones(self) -> None:
        """
        Devuelve el espacio de acciones está formado por una lista de tuplas, donde cada tupla representa el estado de los 4 semaforos. 
        - Ej: [('GGGGGGrrrrr', 'GgGGrrrrGgGg', 'GgGgGgGGrrrr', 'GGGrrrrGGg'), ...]
        """
        semaforo_1 = ['GGGGGGrrrrr', 'rrrrrrGGgGG']
        semaforo_2 = ['GGGrrrrrGGg', 'rrrGGGGGrrr']
        semaforo_3 = ['GGgGGGrrrrr', 'rrrrrrGGGGG']
        semaforo_4 = ['GGGrrrrGGg', 'rrrGGGGrrr']
        
        self.__espacio_acciones = [f"{s1}-{s2}-{s3}-{s4}" for s1 in semaforo_1 for s2 in semaforo_2 for s3 in semaforo_3 for s4 in semaforo_4]



    def usar(self) -> None:
        """
        Utilizar el modelo entrenado.
        """
        logger = logging.getLogger(f' {self.__class__.__name__}.{inspect.currentframe().f_code.co_name}') # type: ignore
        
        #! Esperar a que la simulación esté lista
        while not self.__api.getSimulacionOK():
            logger.info(" Esperando a que la simulación esté lista...")
            time.sleep(1)
        logger.info(" La simulación está lista.")
        
        done = False
        while not done:
            state = self.__estado()
            action = self.model.predict(state, verbose=0)
            done = self.__avanzar(int(np.argmax(action)))
    
    
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


    def __avanzar(self, action:int) -> bool:
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
        respuesta = self.__api.putAvanzar(steps=10)
        
        done:bool = respuesta['done']    # type: ignore #! Si la simulación ha terminado 
        
        return done 