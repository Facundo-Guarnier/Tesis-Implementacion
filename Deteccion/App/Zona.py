import numpy as np


class Zona:
    """
    Clase que representa una zona de la pantalla.
    - Puntos: np.array de puntos_originales (x, y) que representan los vértices de la zona.
    - Resolución: resolución de la pantalla en la que se ha tomado la zona.
    - Puntos reescalados: puntos_originales reescalados a la resolución de la pantalla en la que se va a mostrar la zona.
    """
    
    def __init__(self, nombre: str, resolucion: tuple, puntos_originales: np.array):
        self.nombre = nombre
        self.resolucion = resolucion
        self.puntos_originales = puntos_originales
        self.puntos_reescalados = puntos_originales


    def escalar_puntos(self, resolucion_objetivo: tuple) -> None:
        """
        Escala los puntos_originales de la zona a la resolución objetivo.
        """
        if self.resolucion != resolucion_objetivo:
        
            puntos_objetivos = []
            for punto in self.puntos_originales:
                x_original, y_original = punto
                
                ancho_original, alto_original = self.resolucion
                ancho_objetivo, alto_objetivo = resolucion_objetivo

                #! Calcular las proporciones de escala en x e y
                escala_x = ancho_objetivo / ancho_original
                escala_y = alto_objetivo / alto_original

                #! Aplicar la escala al punto
                x_objetivo = int(x_original * escala_x)
                y_objetivo = int(y_original * escala_y)

                puntos_objetivos.append([x_objetivo, y_objetivo])

            self.puntos_reescalados = np.array(puntos_objetivos)

    def __str__(self) -> str:
        return f"{self.nombre} ({self.resolucion[0]}x{self.resolucion[1]})"