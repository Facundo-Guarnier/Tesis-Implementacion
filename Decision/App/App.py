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
        algoritmo1 = EntrenamientoSARSA()
        Q = algoritmo1.entrenar(num_epocas=30, alpha=0.15, gamma=0.85, epsilon=0.3)

    else:
        #T* Usar SARSA
        algoritmo2 = SARSA("Decision/App/Valores_Q_2024-04-14_11-31/epoca_61.pkl")
        algoritmo2.usar()