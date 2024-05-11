
class Zona:
    """
    Clase que representa una zona (calle) en SUMO.
    """
    
    def __init__(self, nombre: str, id:str) -> None:
        self.nombre = nombre
        self.id = id
        self.tiempo_espera:int = 0