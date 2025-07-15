import pickle

from src.traffic_system.api_client.data_source_client import DecisionAPI


class SARSA:
    def __init__(self, path_Q: str):
        self.__setEspacioAcciones()
        self.__Q = self.__inicializar_Q(path_Q)
        self.__api = DecisionAPI("http://127.0.0.1:5000")

    def __setEspacioAcciones(self) -> None:
        """
        Devuelve el espacio de acciones está formado por una lista de tuplas, donde cada tupla representa el estado de los 4 semaforos.
        - Ej: [('GGGGGGrrrrr', 'GgGGrrrrGgGg', 'GgGgGgGGrrrr', 'GGGrrrrGGg'), ...]
        """
        semaforo_1 = ["GGGGGGrrrrr", "rrrrrrGGgGG", "rrGGGGGrGrr"]
        semaforo_2 = ["GgGGrrrrGgGg", "GGGGGGrrrrrr", "GrrrGGGGrrrr", "grrrrrrrGGGG"]
        semaforo_3 = ["GgGgGgGGrrrr", "rrrrGGGGGGrr", "rrrrGrrrGGGG", "GGGGgrrrrrrr"]
        semaforo_4 = ["GGGrrrrGGg", "rrrGGGGrrr"]
        self.__espacio_acciones = [
            f"{s1}-{s2}-{s3}-{s4}"
            for s1 in semaforo_1
            for s2 in semaforo_2
            for s3 in semaforo_3
            for s4 in semaforo_4
        ]

    def usar(self):
        """
        Utilizar el modelo entrenado.
        """
        done = False

        while not done:
            state = self.__estado()
            action = max(
                self.__espacio_acciones, key=lambda a: self.__Q.get((state, a), 0)
            )
            done = self.__avanzar(action)

    def __inicializar_Q(self, path) -> dict[tuple, float]:
        """
        Cargar los valores Q desde el archivo.
        """
        with open(path, "rb") as f:
            Q = pickle.load(f)

        return Q

    def __estado(self) -> tuple:
        """
        Define el estado:
        - La cantidad de vehículos en cada calle/zona.
        - No incluye el color de los semáforos porque estaría duplicando datos con respecto a la accion.
        - Ej: [1,3,5,0,1,2,4,2,6,3,9,10]
        """
        quantities_response = self.__api.get_quantities()
        if quantities_response is None:
            raise RuntimeError("No se pudo obtener las cantidades de vehículos")

        vehiculos = tuple(quantities_response.cantidades.values())

        return vehiculos

    def __avanzar(self, action: list) -> bool:
        """
        Realiza las siguientes tareas:
        1. Ejecuta la acción en SUMO.
        2. Devuelve el nuevo estado, la recompensa y si se ha terminado la época.
        """

        #! Cambiar el estado de los semáforos en SUMO
        if isinstance(action, str):
            action_list = action.split("-")
        else:
            action_list = action
        self.__api.set_traffic_light_states(states=action_list)

        #! Avanzar en SUMO con la acción seleccionada
        respuesta = self.__api.advance_simulation(steps=10)
        if respuesta is None:
            raise RuntimeError("No se pudo avanzar la simulación")

        done: bool = respuesta.done

        return done
