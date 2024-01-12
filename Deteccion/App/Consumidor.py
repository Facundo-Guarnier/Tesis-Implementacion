import socket

class Consumidor:
    def __init__(self):
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect(('localhost', 5555))

    def recibir(self):
        while True:
            data = self.client_socket.recv(1024).decode()
            if not data:
                print("El socket del lado del productor se ha cerrado. Finalizando...")
                break
            
            lista_de_notificaciones = data.split(' | ')
            if lista_de_notificaciones[-1] == '':
                lista_de_notificaciones.pop()
            
            print(f"Notificación: {lista_de_notificaciones[-1]}")
        
    def finalizar(self):
        self.client_socket.close()

if __name__ == "__main__":
    n = Consumidor()
    n.recibir()