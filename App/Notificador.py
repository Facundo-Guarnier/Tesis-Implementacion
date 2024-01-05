import socket

class Notificador:
    def __init__(self) -> None:
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind(('localhost', 5555))
        self.server_socket.listen(1)

        print("Notificador esperando conexión...")
        self.client_socket, self.address = self.server_socket.accept()
        print(f"Conexión establecida con '{self.address}'")

    def notificar(self, notificacion):
        print(f"Notificación enviada: '{notificacion}'")
        self.client_socket.send(notificacion.encode())

    def finalizar(self):
        print("Finalizando conexión...")
        self.client_socket.close()