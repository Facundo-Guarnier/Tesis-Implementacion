from typing import List
import numpy as np
import yaml

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
            Zona(nombre="Zona A", id="376549265"),
            Zona(nombre="Zona B", id="93893687#1"),
            Zona(nombre="Zona C", id="-93893687#3"),
            Zona(nombre="Zona D", id="E9"),
            Zona(nombre="Zona E", id="-93893687#1"),
            Zona(nombre="Zona F", id="-105241833#4"),
            Zona(nombre="Zona G", id="45896901#0"),
            Zona(nombre="Zona H", id="-105241833#3"),
            Zona(nombre="Zona I", id="105241833#1"),
            Zona(nombre="Zona J", id="E5"),
            Zona(nombre="Zona K", id="105241833#3"),
            Zona(nombre="Zona L", id="105241833#4"),
        ]


    def get_cantidades(self) -> dict:
        """
        Cantidades de vehículos en todas las zonas.
        """
        cantidad_detecciones = {}
        for zona in self.zonas:
            cantidad_detecciones[zona.nombre] = zona.cantidad_detecciones
        
        return cantidad_detecciones


    def get_cantidad_zona(self, zona_nombre:str) -> int:
        """
        Cantidad de vehículos en una zona específica.
        """
        for zona in self.zonas:
            if zona.nombre == zona_nombre:
                return zona.cantidad_detecciones
        
        return -1  #! Retornar -1 si la zona no se encuentra
    
    
    def get(self) -> List[Zona]:
        """
        Devuelve la lista de todas las zonas.
        """
        return self.zonas
