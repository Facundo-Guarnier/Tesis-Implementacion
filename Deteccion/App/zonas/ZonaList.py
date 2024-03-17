from typing import List
import numpy as np
import yaml

from App.zonas.Zona import Zona

class ZonaList:
    """
    Clase de tipo "Singleton" que:
    - Representa una lista de zonas (List[Zona]).
    - Se encarga de cargar las zonas desde un archivo YAML.
    """
    _instance = None

    def __new__(cls):
        if not cls._instance:
            cls._instance = super().__new__(cls)
            cls._instance.zonas = cls.__cargar_zonas()
        return cls._instance


    @staticmethod
    def __cargar_zonas() -> List[Zona]:
        with open('App/zonas/zonas.yaml', 'r') as archivo:
            datos_yaml = yaml.safe_load(archivo)
            return [Zona(zona['Nombre'], tuple(zona['Resolucion']), np.array(zona['Puntos'])) for zona in datos_yaml['Zonas']]


    def get_cantidades(self) -> dict:
        """
        Cantidades de vehículos en todas las zonas.
        """
        cantidad_detecciones = {}
        for zona in self.zonas:
            cantidad_detecciones[zona.nombre] = zona.cantidad_detecciones
        
        return cantidad_detecciones


    def get_cantidad_zona(self, zona_nombre: str) -> int:
        """
        Cantidad de vehículos en una zona específica.
        """
        for zona in self.zonas:
            if zona.nombre == zona_nombre:
                return zona.cantidad_detecciones
        
        return -1  #! Retornar -1 si la zona no se encuentra
