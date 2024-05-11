from typing import List

from SUMO.zonas.Zona import Zona

class ZonaList:
    """
    Clase de tipo "Singleton" que:
    - Representa una lista de zonas (List[Zona]).
    """
    _instance = None

    def __new__(cls):
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance


    def __init__(self):
        self.zonas = self.__definir_zonas()


    def __definir_zonas(self) -> List[Zona]:
        """
        Definir las zonas de la simulación.
        """
        return [
            Zona(nombre="Zona A", id="A"),
            Zona(nombre="Zona B", id="B"),
            Zona(nombre="Zona C", id="C"),
            Zona(nombre="Zona D", id="D"),
            Zona(nombre="Zona E", id="E"),
            Zona(nombre="Zona F", id="F"),
            Zona(nombre="Zona G", id="G"),
            Zona(nombre="Zona H", id="H"),
            Zona(nombre="Zona I", id="I"),
            Zona(nombre="Zona J", id="J"),
            Zona(nombre="Zona K", id="K"),
            Zona(nombre="Zona L", id="L"),
        ]

    def get(self) -> List[Zona]:
        """
        Devuelve la lista de todas las zonas.
        """
        return self.zonas