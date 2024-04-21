
class Zona:
    """
    Clase que representa una zona (calle) en SUMO.
    """
    
    def __init__(self, nombre: str, id:str) -> None:
        self.nombre = nombre
        self.id = id
        self.cantidad_detecciones:int = 0
        self.tiempo_espera:int = 0

    def __str__(self) -> str:
        return f"Zona: {self.nombre}, ID: {self.id}, Cantidad de detecciones: {self.cantidad_detecciones}"