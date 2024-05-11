import csv, os

from Reporte.Api import ApiReporte

from config import configuracion

class Reporte:
    def __init__(self) -> None:
        self.__api = ApiReporte()
    
    
    def generarReporte(self) -> None:
        """
        Generar reporte de la simulación.
        """
        
        if not self.__api.getSimulacionOK():
            return
        
        #! Obtener los datos de la simulación
        datos = self.__api.getReporte()
        
        #! Calcular el tiempo de espera total
        total = sum(datos["tiempos_espera"])
        datos["tiempo_espera_total"] = total
        
        if total > configuracion["reporte"]["tiempo_espera_maximo"]:
            self.alertar()
        
        #! Crear carpeta
        path_reporte = configuracion["reporte"]["path_reporte"]
        if not os.path.exists(os.path.dirname(path_reporte)):
            os.makedirs(os.path.dirname(path_reporte))
        
        #! Escribir los datos en un archivo CSV
        with open(path_reporte, 'w', newline='') as archivo_csv:
            campos = ["steps" "tiempo_espera_total", "tiempos_espera", "estados_semaforos"]
            escritor_csv = csv.DictWriter(archivo_csv, fieldnames=campos)
            
            escritor_csv.writeheader()  # Escribir encabezados
            
            for fila in datos:  # type: ignore
                fila_para_csv = {
                    "steps": fila["steps"],  # "steps" es el número de iteración, es decir, el "tiempo
                    "tiempo_espera_total": fila["tiempo_espera_total"],
                    "tiempos_espera": ','.join(map(str, fila["tiempos_espera"])),  # Convertir la lista de flotantes a una cadena separada por comas
                    "estados_semaforos": ','.join(fila["estados_semaforos"])  # Convertir la lista de strings a una cadena separada por comas
                }
                escritor_csv.writerow(fila_para_csv)  # Escribir filas
    
    
    def alertar(self) -> None:
        """
        Alertar a los agentes de tránsito.
        """
        
        print("\n+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++\n+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++\nAlerta: El tiempo de espera total es mayor al tiempo de espera máximo permitido.\n+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++\n+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
        
        
        