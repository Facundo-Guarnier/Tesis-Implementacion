import numpy as np
import yaml

from Deteccion.App.zonas.Zona import Zona

class ZonaList:
    """
    Clase de tipo "Singleton" que:
    - Se encarga de cargar las zonas desde un archivo YAML.
    - Representa una lista de zonas (List[Zona]).
    """
    _instance = None
    
    def __new__(cls):
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    
    def __init__(self):
        self.zonas = self.__cargar_zonas()
    
    
    def __cargar_zonas(self) -> list[Zona]:
        with open('Deteccion/App/zonas/zonas.yaml', 'r') as archivo:
            datos_yaml = yaml.safe_load(archivo)
            return [Zona(nombre=zona['Nombre'], resolucion=tuple(zona['Resolucion']), puntos_originales=np.array(zona['Puntos']), puntos_multa_originales=np.array(zona['Multa'])) for zona in datos_yaml['Zonas']]
    
    
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
    
    
    def get_tiempos(self) -> list[int]:
        """
        Tiempos de detección en todas las zonas.
        """
        tiempos = []
        for zona in self.zonas:
            if "Zona" in zona.nombre:
                tiempos.append(zona.tiempo_espera)
        
        return tiempos
    
    
    def get_tiempos_total(self) -> int:
        """
        Tiempos de detección en todas las zonas.
        """
        
        return sum(zona.tiempo_espera for zona in self.zonas)
    
    
    def get(self) -> list[Zona]:
        """
        Devuelve la lista de todas las zonas.
        """
        return self.zonas
    
    
    def activar_multas(self, zona_nombre:str) -> bool:
        """
        Activa/desactiva las multas en las zonas.
        
        Args:
            zona_nombre (str): Nombre de la zona. Ej: "Zona A"
        
        Returns:
            bool: Estado de las multas de la zona.
        """
        
        for zona in self.zonas:
            if zona.nombre == zona_nombre:
                zona.multas_activadas = not zona.multas_activadas
                return zona.multas_activadas
        
        return False