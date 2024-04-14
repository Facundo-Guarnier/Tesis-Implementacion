
#T* Version 1
# #* Se puede definir diferentes prioridades para cada carril.
# #* Poner en verde según la cantidad que hay.
# #* Poner rojo si los autos no avanzan.
# import numpy as np

# # Datos de densidad de vehículos en cada carril (simulados para este ejemplo)
# densidad_carril1 = 0.5  # Ejemplo: vehículos por metro
# densidad_carril2 = 0.8
# densidad_carril3 = 0.6

# # Parámetros de ajuste (puedes modificarlos según tus necesidades)
# factor_densidad = 0.1  # Cuánto afecta la densidad al tiempo de verde
# tiempo_verde_base = 30  # Tiempo base de verde (segundos)

# # Calculamos el tiempo de verde para cada carril
# tiempo_verde_carril1 = tiempo_verde_base + factor_densidad * densidad_carril1
# tiempo_verde_carril2 = tiempo_verde_base + factor_densidad * densidad_carril2
# tiempo_verde_carril3 = tiempo_verde_base + factor_densidad * densidad_carril3

# # Imprimimos los resultados
# print(f"Tiempo de verde para carril 1: {tiempo_verde_carril1:.2f} segundos")
# print(f"Tiempo de verde para carril 2: {tiempo_verde_carril2:.2f} segundos")
# print(f"Tiempo de verde para carril 3: {tiempo_verde_carril3:.2f} segundos")


#T* Version 2: Red neuronal
# https://www.youtube.com/watch?v=CQu4wFLC79U
#* Una vez que la red neuronal decidió el color, deberían pasar 5 segundo (cantidad de tics de la simulacion) en los 
#* cuales existe la transición de verde a rojo (5 segundo de amarillo).

#* Red neuronal que tenga como entrada la densidad de vehículos en cada carril (12 neuronas) y devuelva el color de cada semaforo.

#* La recompensa o la forma de saber si está haciendo bien su trabajo será la cantidad de vehículos que pasan por el 
#* semáforo en un tiempo determinado (en el video es la inversa del valor de furia/espera: 1/furia=score). 

#* En el video tiene 18 entradas, 2 capas ocultas de 10 y la salida que es de 10 (10 posibles estado del semaforo) con funcion de activación tanh.  


#T* Version 3: Aprendizaje por refuerzo
# import traci  # Para interactuar con SUMO
# import numpy as np

# # Función de recompensa
# def reward_function(state):
#     # Implementa tu función de recompensa aquí
#     pass

# # Algoritmo SARSA
# def sarsa(env, num_epocas, alpha, gamma, epsilon):
#     Q = {}  # Diccionario para almacenar los valores Q

#     for epoca in range(num_epocas):
#         state = env.reset()
#         done = False

#         # Selecciona la acción utilizando una política epsilon-greedy
#         action = epsilon_greedy_policy(state, Q, epsilon)

#         while not done:
#             # Ejecuta la acción y observa el nuevo estado y la recompensa
#             next_state, reward, done = env.step(action)

#             # Selecciona la próxima acción utilizando una política epsilon-greedy
#             next_action = epsilon_greedy_policy(next_state, Q, epsilon)

#             # Actualiza el valor Q utilizando la ecuación SARSA
#             if (state, action) not in Q:
#                 Q[(state, action)] = 0
#             if (next_state, next_action) not in Q:
#                 Q[(next_state, next_action)] = 0
#             Q[(state, action)] += alpha * (reward + gamma * Q[(next_state, next_action)] - Q[(state, action)])

#             # Actualiza el estado y la acción para el próximo paso
#             state = next_state
#             action = next_action

#     return Q

# # Política epsilon-greedy
# def epsilon_greedy_policy(state, Q, epsilon):
#     if np.random.uniform(0, 1) < epsilon:
#         # Acción aleatoria
#         return np.random.choice(env.action_space)
#     else:
#         # Acción óptima según los valores Q
#         return max(env.action_space, key=lambda a: Q.get((state, a), 0))

# # Clase para el entorno SUMO
# class SumoEnvironment:
#     def __init__(self):
#         # Inicializa SUMO y configura tu escenario aquí
#         pass
    
#     def reset(self):
#         # Reinicia el entorno a un estado inicial y devuelve el estado
#         pass
    
#     def step(self, action):
#         # Ejecuta la acción en SUMO, simula un paso y devuelve el nuevo estado, la recompensa y si se ha terminado el episodio
#         pass

# # Ejemplo de uso
# env = SumoEnvironment()
# Q = sarsa(env, num_epocas=1000, alpha=0.1, gamma=0.9, epsilon=0.1)

#* Q-learning, SARSA, Deep Q-Network (DQN) y Proximal Policy Optimization (PPO):  35.79 %, 51.63 %, 63.40 % y 63.49 %
#* SARSA
import csv, os, pickle
import time
import numpy as np

# from Decision.App.Api import ApiClient
from Api import ApiClient

class EntrenamientoSARSA:
    """
    Clase para el entorno SUMO
    """
    
    def __init__(self):
        self.__api = ApiClient("http://127.0.0.1:5000")
        self.__setEspacioAcciones()
        self.__setPath()

    def __setPath(self) -> None:
        """
        Establece la ruta donde se guardarán los archivos.
        """
        path = f'Decision/App/Valores_Q_{time.strftime("%Y-%m-%d_%H-%M")}'
        if not os.path.exists(path):
            os.makedirs(path)
        self.__path = path


    def __setEspacioAcciones(self) -> None:
        """
        Devuelve el espacio de acciones está formado por una lista de tuplas, donde cada tupla representa el estado de los 4 semaforos. 
        - Ej: [('GGGGGGrrrrr', 'GgGGrrrrGgGg', 'GgGgGgGGrrrr', 'GGGrrrrGGg'), ...]
        """
        semaforo_1 = ['GGGGGGrrrrr', 'rrrrrrGGgGG', 'rrGGGGGrGrr']
        semaforo_2 = ['GgGGrrrrGgGg', 'GGGGGGrrrrrr', 'GrrrGGGGrrrr', 'grrrrrrrGGGG']
        semaforo_3 = ['GgGgGgGGrrrr', 'rrrrGGGGGGrr', 'rrrrGrrrGGGG', 'GGGGgrrrrrrr']
        semaforo_4 = ['GGGrrrrGGg', 'rrrGGGGrrr']
        self.__espacio_acciones = [f"{s1}-{s2}-{s3}-{s4}" for s1 in semaforo_1 for s2 in semaforo_2 for s3 in semaforo_3 for s4 in semaforo_4]


    def entrenar(self, num_epocas:int, alpha:float, gamma:float, epsilon:float) -> dict[tuple, float]:
        """
        Entrenamiento del algoritmo SARSA de aprendizaje por refuerzo.
        """
        Q: dict[tuple, float] = {}  # Diccionario para almacenar los valores Q
        Q_anterior = Q.copy()
        recompensas_acumuladas:list[float] = []
        tasas_exploracion_explotacion:list[float] = []
        metricas_convergencia:list[float] = []
        
        #! Ver la recompensa con semaforos con tiempo fijo
        total_reward = 0.0
        done = False
        print("Calculando recompensa con semaforos con tiempo fijo.")
        while not done:
            total_reward += self.__recompensa()
            done = self.__api.putAvanzar(steps=10)['done'] 
            
        recompensas_acumuladas.append(total_reward)
        tasas_exploracion_explotacion.append(0.0)
        metricas_convergencia.append(0.0)
        
        #! Entrenar
        for epoca in range(num_epocas):
            print(f"Entrenando epoca: {epoca} de {num_epocas} epcoas.")
            start_time = time.time()
            state = self.__estado()
            done = False
            total_reward = 0.0

            #! Selecciona la acción utilizando una política epsilon-greedy
            action = self.__politica(state, Q, epsilon)
            
            while not done:
                #! Ejecuta la acción y observa el nuevo estado y la recompensa
                next_state, reward, done = self.__avanzar(action)

                #! Selecciona la próxima acción utilizando una política epsilon-greedy
                next_action = self.__politica(next_state, Q, epsilon)
                
                total_reward += reward

                #! Actualiza el valor Q utilizando la ecuación SARSA
                if (state, action) not in Q:
                    Q[(state, action)] = 0
                if (next_state, next_action) not in Q:
                    Q[(next_state, next_action)] = 0
                Q[(state, action)] += alpha * (reward + gamma * Q[(next_state, next_action)] - Q[(state, action)])

                #! Actualiza el estado y la acción para el próximo paso
                state = next_state
                action = next_action
            
            if epoca > 0:
                metrica = self.__calcular_metrica_convergencia(Q, Q_anterior)
                metricas_convergencia.append(metrica)
            else:
                metricas_convergencia.append(0.0)

            Q_anterior = Q.copy()
            
            recompensas_acumuladas.append(total_reward)
            tasas_exploracion_explotacion.append(epsilon)
            
            epsilon *= 0.94  #! Tasa de exploración
            alpha *= 0.98 #! Tasa de aprendizaje 
            
            self.__guardar_valores_Q(Q=Q, epoca=epoca)
            
            self.__guardar_metricas(
                epoca=epoca, 
                duracion=time.time() - start_time,
                recompensas_acumuladas=recompensas_acumuladas, 
                tasas_exploracion_explotacion=tasas_exploracion_explotacion, 
                metricas_convergencia=metricas_convergencia
            )
        
        return Q


    def __guardar_metricas(self, epoca:int, duracion:float, recompensas_acumuladas:list, tasas_exploracion_explotacion:list, metricas_convergencia:list) -> None:
        """
        Guardar las métricas en un archivo CSV.
        """
        path = self.__path + '/entrenamiento_data.csv'

        #! Verificar si el archivo ya existe
        if not os.path.isfile(path):
            with open(path, mode='w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(['Epoca', 'Duracion', 'Recompensa Acumulada', 'Tasa de Exploración vs Explotación (Epsilon)', 'Metrica de Convergencia'])

        with open(path, mode='a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([epoca, duracion, recompensas_acumuladas[epoca], tasas_exploracion_explotacion[epoca], metricas_convergencia[epoca]])


    def __guardar_valores_Q(self, Q:dict, epoca:int) -> None:
        """
        Guardar los valores Q en un archivo.
        """
        path = self.__path + f'/epoca_{epoca+1}.pkl'
        with open(path, 'wb') as f:
            pickle.dump(Q, f)


    def __calcular_metrica_convergencia(self, Q, Q_anterior) -> float:
        """
        Calcular la diferencia absoluta promedio entre los valores Q de dos epocas consecutivas.
        """
        # diferencias = []
        # for key in Q:
        #     if key in Q_anterior and key in Q:
        #         diferencias.append(abs(Q[key] - Q_anterior[key]))
                
        diferencias = [(abs(Q[key] - Q_anterior[key])) if key in Q_anterior and key in Q else 0 for key in Q]
        return sum(diferencias) / len(diferencias)


    def __politica(self, state, Q, epsilon) -> str:
        """
        Política epsilon-greedy para seleccionar la acción a realizar.
        Episilon: Tasa de exploración vs explotación, es decir, probabilidad de explorar nuevas acciones o explotar las mejores acciones.
        Cuando epsilon es alto, hay más probabilidad de realizar acciones aleatorias, lo que fomenta la exploración del espacio de acciones.
        """
        if np.random.uniform(0, 1) < epsilon:
            return np.random.choice(self.__espacio_acciones)       #! Acción aleatoria
        else:
            return max(self.__espacio_acciones, key=lambda a: Q.get((state, a), 0)) # type: ignore #! Acción óptima según los valores Q 
        

    def __estado(self) -> tuple:
        """
        Define el estado: 
        - La cantidad de vehículos en cada calle/zona.
        - No incluye el color de los semáforos porque estaría duplicando datos con respecto a la accion.
        - Ej: [1,3,5,0,1,2,4,2,6,3,9,10]
        """
        vehiculos = tuple([cantidad for cantidad in self.__api.getCantidades().values()])
        
        return vehiculos


    def __recompensa(self) -> float:
        """
        Calcula la recompensa en función del estado actual. 
        La inversa de:
        - (0%) El tiempo de espera de los vehículos en las intersecciones controladas por los semáforos.
        - (0%) La cantidad de vehículos en cada calle/zona.
        """
        tiempo = self.__api.getTiemposEspera()["tiempo_espera"]
        cantidad = sum(self.__api.getCantidades().values())
        return 100 / ((tiempo*0.15 + cantidad*0.85) + 100)


    def __reiniciar(self) -> tuple:
        """
        Reinicia el entorno a un estado inicial donde ya hay autos (ej: step 250 de SUMO) y devuelve el estado
        """
        return self.__estado()


    def __avanzar(self, action:str) -> tuple[tuple, float, bool]:
        """
        Realiza las siguientes tareas:
        1. Ejecuta la acción en SUMO.
        2. Simula 10 pasos (para tener una recompensa mas realista).
        3. Devuelve el nuevo estado, la recompensa y si se ha terminado la epoca.
        """
        
        #! Cambiar el estado de los semáforos en SUMO
        self.__api.putEstados(accion=action.split('-'))
        
        #! Avanzar en SUMO con la acción seleccionada
        respuesta = self.__api.putAvanzar(steps=10)
        
        done:bool = respuesta['done']    #! Si la simulación ha terminado
        
        return self.__estado(), self.__recompensa(), done    #! Estado, recompensa, si terminó la simulacion o no 