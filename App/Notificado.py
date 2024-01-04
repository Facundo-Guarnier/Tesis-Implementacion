class Notificado:
    def __init__(self):
        self.__notificaciones = []
    
    def notificar(self, notificacion):
        self.__notificaciones.append(notificacion)
    
    def getNotificaciones(self):
        return self.__notificaciones