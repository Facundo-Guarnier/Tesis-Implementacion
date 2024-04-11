
#T* Version 1
#* Se puede definir diferentes prioridades para cada carril.
import numpy as np

# Datos de densidad de vehículos en cada carril (simulados para este ejemplo)
densidad_carril1 = 0.5  # Ejemplo: vehículos por metro
densidad_carril2 = 0.8
densidad_carril3 = 0.6

# Parámetros de ajuste (puedes modificarlos según tus necesidades)
factor_densidad = 0.1  # Cuánto afecta la densidad al tiempo de verde
tiempo_verde_base = 30  # Tiempo base de verde (segundos)

# Calculamos el tiempo de verde para cada carril
tiempo_verde_carril1 = tiempo_verde_base + factor_densidad * densidad_carril1
tiempo_verde_carril2 = tiempo_verde_base + factor_densidad * densidad_carril2
tiempo_verde_carril3 = tiempo_verde_base + factor_densidad * densidad_carril3

# Imprimimos los resultados
print(f"Tiempo de verde para carril 1: {tiempo_verde_carril1:.2f} segundos")
print(f"Tiempo de verde para carril 2: {tiempo_verde_carril2:.2f} segundos")
print(f"Tiempo de verde para carril 3: {tiempo_verde_carril3:.2f} segundos")


#T* Version 2
# https://www.youtube.com/watch?v=CQu4wFLC79U
# Una vez que la red neuronal decidió el color, deberían pasar 5 segundo (cantidad de tics de la simulacion) en los 
# cuales existe la transición de verde a rojo (5 segundo de amarillo).

# Red neuronal que tenga como entrada la densidad de vehículos en cada carril (12 neuronas) y devuelva el color de cada semaforo.

# La recompensa o la forma de saber si está haciendo bien su trabajo será la cantidad de vehículos que pasan por el 
# semáforo en un tiempo determinado (en el video es la inversa del valor de furia/espera: 1/furia=score). 

# En el video tiene 18 entradas, 2 capas ocultas de 10 y la salida que es de 10 (10 posibles estado del semaforo) con funcion de activación tanh.  