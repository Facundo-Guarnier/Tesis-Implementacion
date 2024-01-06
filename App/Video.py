import cv2


class Video:
    def __init__(self, path_origen, path_resultado, zona):
        
        self.path_origen = path_origen
        self.path_resultado = path_resultado
        self.zona = zona
        
        self.nombre = path_origen.split("/")[-1]
        self.carpeta = path_origen.split("/")[-2]
        
        self.fps = self.__fps()
        self.resolucion = self.__obtener_resolucion()
        self.factor_escala = self.__calcular_factor_escala()


    def __obtener_resolucion(self):
        cap = cv2.VideoCapture(self.path_origen)
        ancho = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        alto = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        cap.release()
        return ((ancho, alto))

    def __fps(self):
        cap = cv2.VideoCapture(self.path_origen)
        fps = cap.get(cv2.CAP_PROP_FPS)
        cap.release()
        return fps

    def __calcular_factor_escala(self):
        """
        Escala los distintos elementos (letras y lineas) en base a la resolución del video.
        Lo elementos fueron diseñados para una resolución de 1080x1920.
        """
        ancho_original, alto_original = (1080, 1920)
        ancho_actual, alto_actual, = self.resolucion 
        return ancho_actual / ancho_original