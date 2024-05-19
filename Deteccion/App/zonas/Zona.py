import numpy as np

class Zona:
    """
    Clase que representa una zona de la pantalla.
    - Puntos: np.array de puntos_originales (x, y) que representan los vértices de la zona.
    - Resolución: resolución de la pantalla en la que se ha tomado la zona.
    - Puntos reescalados: puntos_originales reescalados a la resolución de la pantalla en la que se va a mostrar la zona.
    - Cantidad de detecciones: cantidad de detecciones que han ocurrido en la zona.
    
    Attributes:
        - nombre (str): Nombre de la zona. Ejemplo: "Zona A".
        - resolucion (tuple): Resolución de la pantalla en la que se ha tomado la zona.
        - puntos_originales (np.ndarray): Puntos de la zona en la resolución original.
        - puntos_reescalados (np.ndarray): Puntos de la zona reescalados a la resolución objetivo.
        
        - multas_activadas (bool): Indica si las multas están activadas en la zona.
        
        - cantidad_detecciones (int): Cantidad de detecciones que han ocurrido en la zona.
        - tiempo_espera (int): Tiempo de espera en la zona.
    """
    
    def __init__(self, nombre: str, resolucion: tuple, puntos_originales:np.ndarray, puntos_multa_originales:np.ndarray) -> None:
        self.nombre = nombre
        self.__resolucion = resolucion
        self.puntos_originales = puntos_originales
        self.puntos_reescalados = puntos_originales
        
        self.multas_activadas:bool = False
        self.puntos_multa_originales:np.ndarray = puntos_multa_originales
        self.puntos_multa_reescalados:np.ndarray = puntos_multa_originales
        
        self.cantidad_detecciones:int = 0
        self.tiempo_espera:int = 0


    def escalar_puntos(self, resolucion_objetivo: tuple) -> None:
        """
        Escala los puntos_originales de la zona a la resolución objetivo.
        """
        if self.__resolucion != resolucion_objetivo:
            puntos_objetivos = []
            
            for punto in self.puntos_originales:
                x_original, y_original = punto
                
                ancho_original, alto_original = self.__resolucion
                ancho_objetivo, alto_objetivo = resolucion_objetivo

                #! Calcular las proporciones de escala en x e y
                escala_x = ancho_objetivo / ancho_original
                escala_y = alto_objetivo / alto_original

                #! Aplicar la escala al punto
                x_objetivo = int(x_original * escala_x)
                y_objetivo = int(y_original * escala_y)

                puntos_objetivos.append([x_objetivo, y_objetivo])

            self.puntos_reescalados = np.array(puntos_objetivos)
    
    
    def escalar_puntos_multa(self, resolucion_objetivo: tuple) -> None:
        """
        Escala los puntos originales de la multas de la zona a la resolución objetivo.
        
        Args:
            resolucion_objetivo (tuple): Resolución a la que se quiere escalar los puntos de la multa.
        """
        
        if self.__resolucion != resolucion_objetivo:
            puntos_objetivos = []
            
            for punto in self.puntos_multa_originales:
                x_original, y_original = punto
                
                ancho_original, alto_original = self.__resolucion
                ancho_objetivo, alto_objetivo = resolucion_objetivo
                
                #! Calcular las proporciones de escala en x e y
                escala_x = ancho_objetivo / ancho_original
                escala_y = alto_objetivo / alto_original
                
                #! Aplicar la escala al punto
                x_objetivo = int(x_original * escala_x)
                y_objetivo = int(y_original * escala_y)
                
                puntos_objetivos.append([x_objetivo, y_objetivo])
            
            self.puntos_multa_reescalados = np.array(puntos_objetivos)


    def __str__(self) -> str:
        return f"{self.nombre} ({self.__resolucion[0]}x{self.__resolucion[1]})"