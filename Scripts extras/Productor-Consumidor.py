import multiprocessing
import time
import _queue

class Notificado:
    def __init__(self):
        manager = multiprocessing.Manager()
        self.__notificaciones = manager.Queue(maxsize=1)

    def notificar(self, notificacion):
        # Intenta retirar una notificación existente antes de poner la nueva
        try:
            self.__notificaciones.get_nowait()
        except _queue.Empty:
            pass    
        self.__notificaciones.put(notificacion)

    def getNotificaciones(self):
        while True:
            time.sleep(0.00001)
            notificacion = self.__notificaciones.get()
            # Procesa la notificación aquí
            print(f"Notificación recibida: {notificacion}")
            self.__notificaciones.task_done()


class Detector:
    def __init__(self, notificado):
        self.notificado = notificado

    def detectar(self, m):
        # Detecta algo y notifica
        self.notificado.notificar(f"Algo detectado {m}")
        print(f"Notificando {m}")

if __name__ == "__main__":
    notificado = Notificado()
    detector = Detector(notificado)

    # Inicia el proceso del consumidor
    p = multiprocessing.Process(target=notificado.getNotificaciones)
    p.start()

    time.sleep(1)
    # El productor notifica algo
    for i in range(10):
        detector.detectar(i)

    p.kill()