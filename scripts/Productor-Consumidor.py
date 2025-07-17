import multiprocessing
import queue
import time
from typing import Any


class Notificado:
    def __init__(self) -> None:
        manager = multiprocessing.Manager()
        self.__notificaciones = manager.Queue(maxsize=1)

    def notificar(self, notificacion: Any) -> None:
        # Intenta retirar una notificación existente antes de poner la nueva
        try:
            self.__notificaciones.get_nowait()
        except queue.Empty:
            pass
        self.__notificaciones.put(notificacion)

    def getNotificaciones(self) -> None:
        while True:
            time.sleep(0.00001)
            notificacion = self.__notificaciones.get()
            # Procesa la notificación aquí
            print(f"Notificación recibida: {notificacion}")
            self.__notificaciones.task_done()


class Detector:
    def __init__(self, notificado: Notificado) -> None:
        self.notificado = notificado

    def detectar(self, m: Any) -> None:
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
