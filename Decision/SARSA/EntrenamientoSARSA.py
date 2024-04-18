
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


#T* Version 2: Aprendizaje por refuerzo
#* Q-learning, SARSA, Deep Q-Network (DQN) y Proximal Policy Optimization (PPO):  35.79 %, 51.63 %, 63.40 % y 63.49 %
#* SARSA
import csv, os, pickle
import time
import numpy as np

# from Decision.App.Api import ApiClient
from Api import ApiClient

class EntrenamientoSARSA:
    def __init__(self):
        self.__api = ApiClient("http://127.0.0.1:5000")
        self.__setEspacioAcciones()
        self.__setPath()


    def __setPath(self) -> None:
        """
        Establece la ruta donde se guardarán los archivos.
        """
        path = f'Decision/Resultados_entrenamiento/SARSA_{time.strftime("%Y-%m-%d_%H-%M")}'
        if not os.path.exists(path):
            os.makedirs(path)
        self.__path = path


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


    def entrenar(self, num_epocas:int, alpha:float, gamma:float, epsilon:float) -> None:
        """
        Entrenamiento del algoritmo SARSA de aprendizaje por refuerzo.
        - num_epocas: Número de épocas de entrenamiento.
        - alpha: Tasa de aprendizaje.
        - gamma: Factor de descuento.
        - epsilon: Tasa de exploración vs explotación.
        """
        Q: dict[tuple, float] = {}
        Q_anterior = Q.copy()

        for epoca in range(num_epocas):
            print(f"Entrenando epoca: {epoca+1} de {num_epocas} epcoas.")
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
                metricas_convergencia = self.__calcular_metrica_convergencia(Q, Q_anterior)
            else:
                metricas_convergencia = 0.0

            Q_anterior = Q.copy()
            
            recompensas_acumuladas = total_reward
            tasas_exploracion_explotacion = epsilon
            
            if epsilon > 0.1:
                epsilon *= 0.97  #! Tasa de exploración
            alpha *= 0.99 #! Tasa de aprendizaje 
            
            self.__guardar_valores_Q(Q=Q, epoca=epoca)
            
            self.__guardar_metricas(
                epoca=epoca, 
                duracion=time.time() - start_time,
                recompensas_acumuladas=recompensas_acumuladas, 
                tasas_exploracion_explotacion=tasas_exploracion_explotacion, 
                metricas_convergencia=metricas_convergencia
            )


    def __guardar_metricas(self, epoca:int, duracion:float, recompensas_acumuladas:float, tasas_exploracion_explotacion:float, metricas_convergencia:float) -> None:
        """
        Guardar las métricas en un archivo CSV.
        """
        with open(self.__path + '/entrenamiento_data.csv', mode='a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([epoca+1, duracion, recompensas_acumuladas, tasas_exploracion_explotacion, metricas_convergencia])


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
        - ❎ La cantidad de vehículos en cada calle/zona.
        - El tiempo de espera de los vehículos en las intersecciones.
        - No incluye el color de los semáforos porque estaría duplicando datos con respecto a la accion.
        - Ej: [1,3,5,0,1,2,4,2,6,3,9,10]
        """
        #! Cantidad
        # estado = tuple([cantidad for cantidad in self.__api.getCantidades().values()])
        
        #! Tiempo
        estado = tuple(self.__api.getTiemposEspera()["tiempos_espera"])
        tiempo_maximo_espera = max(estado)

        #! Normalizar los tiempos de espera
        estado = tuple([round(tiempo_espera / tiempo_maximo_espera , 2) for tiempo_espera in estado])
        return estado


    def __recompensa(self) -> float:
        """
        Calcula la recompensa en función del estado actual. 
        La inversa de:
        - (0%) El tiempo de espera de los vehículos en las intersecciones controladas por los semáforos.
        - (0%) La cantidad de vehículos en cada calle/zona.
        """
        tiempo = self.__api.getTiemposEspera()["tiempo_espera_total"]
        return 100 / ((tiempo) + 100)


    # def __reiniciar(self) -> tuple:
    #     """
    #     Reinicia el entorno a un estado inicial donde ya hay autos (ej: step 250 de SUMO) y devuelve el estado
    #     """
    #     return self.__estado()


    def __avanzar(self, action:str) -> tuple[tuple, float, bool]:
        """
        Realiza las siguientes tareas:
        1. Ejecuta la acción en SUMO.
        2. Simula 15 pasos (para tener una recompensa mas realista).
        3. Devuelve el nuevo estado, la recompensa y si se ha terminado la epoca.
        """
        
        #! Cambiar el estado de los semáforos en SUMO
        self.__api.putEstados(accion=action.split('-'))
        
        #! Avanzar en SUMO con la acción seleccionada
        respuesta = self.__api.putAvanzar(steps=15)
        
        done:bool = respuesta['done']    #! Si la simulación ha terminado
        
        return self.__estado(), self.__recompensa(), done    #! Estado, recompensa, si terminó la simulacion o no 


    def main(self, num_epocas:int, alpha:float, gamma:float, epsilon:float):
        """
        Método principal.
        """
    
        #! Verificar si el archivo ya existe
        if not os.path.isfile(self.__path + '/entrenamiento_data.csv'):
            with open(self.__path + '/entrenamiento_data.csv', mode='w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(['Epoca', 'Duracion', 'Recompensa Acumulada', 'Tasa de Exploración vs Explotación (Epsilon)', 'Metrica de Convergencia'])
        
        
        #! Ver la recompensa con semaforos con tiempo fijo
        total_reward = 0.0
        done = False
        print("Calculando recompensa con semaforos con tiempo fijo.")
        while not done:
            total_reward += self.__recompensa()
            done = self.__api.putAvanzar(steps=10)['done'] 
            
        self.__guardar_metricas(
            epoca=-1, 
            duracion=-1.0,
            recompensas_acumuladas=total_reward, 
            tasas_exploracion_explotacion=-1.0, 
            metricas_convergencia=-1.0
        )
        
        #! Entrenar
        self.entrenar(num_epocas, alpha, gamma, epsilon)