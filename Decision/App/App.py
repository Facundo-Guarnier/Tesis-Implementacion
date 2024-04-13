from Algoritmo import EntrenamientoSARSA

# cliente_api = ApiClient("http://127.0.0.1:5000")

# #! Obtener cantidad de vehículos en todas las zonas
# print(f"Cantidad de vehículos en todas las zonas: {cliente_api.obtener_cantidad_vehiculos_todas_zonas()}")

# #! Obtener cantidad de vehículos en una zona específica
# print(f"Cantidad de vehículos en la zona: {cliente_api.obtener_cantidad_vehiculos_zona('Zona B')}")

if __name__ == '__main__':
    # Ejemplo de uso
    algoritmo = EntrenamientoSARSA()
    Q = algoritmo.entrenar(num_epocas=1000, alpha=0.1, gamma=0.9, epsilon=0.3)

    # #! Cargar los valores Q desde el archivo
    # with open('q_values.pkl', 'rb') as f:  # Fix: Open the file in read mode
    #     Q = pickle.load(f)


    # #! Ejemplo de uso
    # state = __estado()      #! Obtener el estado actual del entorno
    # action = max(self.__espacio_acciones, key=lambda a: Q.get((state, a), 0))      #! Seleccionar la acción utilizando el modelo entrenado