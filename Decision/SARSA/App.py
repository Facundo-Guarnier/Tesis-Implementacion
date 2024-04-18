from SARSA import SARSA
from EntrenamientoSARSA import EntrenamientoSARSA

# cliente_api = ApiClient("http://127.0.0.1:5000")

# #! Obtener cantidad de vehículos en todas las zonas
# print(f"Cantidad de vehículos en todas las zonas: {cliente_api.obtener_cantidad_vehiculos_todas_zonas()}")

# #! Obtener cantidad de vehículos en una zona específica
# print(f"Cantidad de vehículos en la zona: {cliente_api.obtener_cantidad_vehiculos_zona('Zona B')}")

if __name__ == '__main__':
    
    entrenar = True
    
    if entrenar:
        #T* Entrenar
        print("Entrenar SARSA")
        algoritmo1 = EntrenamientoSARSA()
        Q = algoritmo1.main(num_epocas=55, alpha=0.1, gamma=0.99, epsilon=1)

    else:
        #T* Usar SARSA
        print("Usar SARSA")
        algoritmo2 = SARSA(path_Q="Decision/Valores_Q_2024-04-17_09-03/epoca_30.pkl")
        algoritmo2.usar()