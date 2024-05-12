import csv, os, time

from Reporte.Api import ApiReporte

from config import configuracion

class Reporte:
    def __init__(self) -> None:
        self.__api = ApiReporte()
        self.__path_reporte = os.path.join(configuracion["reporte"]["path_reporte"], f"Reporte_{time.strftime('%Y-%m-%d_%H-%M-%S')}")
    
    
    def main(self) -> None:
        """
        Método principal para generar el reporte de la simulación.
        - Crea la carpeta para el reporte.
        - Verifica si la simulación está en curso.
        - Genera el reporte de la simulación.
        """
        
        #! Crear carpeta
        if not os.path.exists(os.path.dirname(self.__path_reporte)):
            os.makedirs(os.path.dirname(self.__path_reporte))
        
        #! Verificar si la simulación fue exitosa
        while not self.__api.getSimulacionOK():
            time.sleep(5)
        
        #! Generar reporte
        e = 0
        while True and e < 5:
            if not self.generarReporte():
                print("Error al generar el reporte.")
                e += 1
                time.sleep(configuracion["reporte"]["tiempo_entre_reportes"])
            else:
                e = 0
    
    
    def generarReporte(self) -> bool:
        """
        Generar reporte de la simulación.
        
        Returns:
            bool: True si el reporte fue generado exitosamente, False en caso contrario.
        """
        
        if not self.__api.getSimulacionOK():
            return False
        
        #! Obtener los datos de la simulación
        datos = self.__api.getReporte()
        
        #! Calcular el tiempo de espera total
        total = sum(datos["tiempos_espera"])
        datos["tiempo_espera_total"] = total
        
        if total > configuracion["reporte"]["tiempo_espera_maximo"]:
            self.alertar()
        
        #! Crear carpeta
        if not os.path.exists(self.__path_reporte):
            os.makedirs(self.__path_reporte)
        
        #! Escribir los datos en un archivo CSV
        path_csv = self.__path_reporte + "/reporte.csv"
        
        #! Verificar si el archivo ya existe
        if not os.path.isfile(path_csv):
            with open(path_csv, mode='w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow([
                    "Steps", 
                    "Semaforo 1", 
                    "Semaforo 2", 
                    "Semaforo 3", 
                    "Semaforo 4", 
                    "Tiempo de espera total", 
                    "Zona A", "Zona B", "Zona C", "Zona D", "Zona E", "Zona F", "Zona G", "Zona H", "Zona I", "Zona J", "Zona K", "Zona L"
                ])
        
        #! Escribir los datos en el archivo
        with open(path_csv, mode='a', newline='') as file:
                writer = csv.writer(file)
                writer.writerow([
                    datos["steps"], 
                    datos["estados_semaforos"][0], 
                    datos["estados_semaforos"][1], 
                    datos["estados_semaforos"][2], 
                    datos["estados_semaforos"][3], 
                    datos["tiempo_espera_total"], 
                    datos["tiempos_espera"][0], 
                    datos["tiempos_espera"][1], 
                    datos["tiempos_espera"][2], 
                    datos["tiempos_espera"][3], 
                    datos["tiempos_espera"][4], 
                    datos["tiempos_espera"][5], 
                    datos["tiempos_espera"][6], 
                    datos["tiempos_espera"][7], 
                    datos["tiempos_espera"][8], 
                    datos["tiempos_espera"][9], 
                    datos["tiempos_espera"][10], 
                    datos["tiempos_espera"][11], 
                ])
        return True
    
    
    def alertar(self) -> None:
        """
        Alertar a los agentes de tránsito.
        """
        
        print("\n+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++\n+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++\nAlerta: El tiempo de espera total es mayor al tiempo de espera máximo permitido.\n+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++\n+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
