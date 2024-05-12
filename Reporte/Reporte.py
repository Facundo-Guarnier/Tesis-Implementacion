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
        
        #! Verificar si la simulación fue exitosa
        while not self.__api.getSimulacionOK():
            time.sleep(1)
        
        self.crearCSV()
        
        #! Generar reporte
        e = 0
        while True and e < 5:
            datos = self.obtenerDatos()
            
            if datos == {} or not self.generarReporte(datos=datos):
                print(f"Error al generar el reporte. Reintentando... ({e + 1}/{5})")
                e += 1
                time.sleep(configuracion["reporte"]["tiempo_entre_reportes"])
                
            else:
                e = 0
                self.alertar(datos=datos)
        
        print("Falló 5 veces seguidas al intentar generar el reporte.")
    
    
    def obtenerDatos(self) -> dict:
        """
        Obtener los datos de la simulación.
        
        Returns:
            dict: Datos de la simulación.
        """
        
        if not self.__api.getSimulacionOK():
            return {}
        
        #! Obtener los datos de la simulación
        datos = self.__api.getReporte()
        
        #! Calcular el tiempo de espera total
        total = sum(datos["tiempos_espera"])
        datos["tiempo_espera_total"] = total
        
        return datos
    
    
    def crearCSV(self) -> None:
        """
        Crear la carpeta y el archivo CSV para el reporte.
        """
        #! Crear carpeta
        if not os.path.exists((self.__path_reporte)):
            os.makedirs((self.__path_reporte))
        
        self.__path_reporte = self.__path_reporte + "/reporte.csv"
        
        #! Verificar si el archivo ya existe
        if not os.path.isfile(self.__path_reporte):
            with open(self.__path_reporte, mode='w', newline='') as file:
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
    
    
    def generarReporte(self, datos: dict) -> bool:
        """
        Generar reporte de la simulación.
        
        Args:
            datos (dict): Datos de la simulación.
        
        Returns:
            bool: True si el reporte fue generado exitosamente, False en caso contrario.
        """
        try: 
            #! Escribir los datos en el archivo
            with open(self.__path_reporte, mode='a', newline='') as file:
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
        
        except Exception as e:
            print(f"Error al generar el reporte: {e}")
            return False
    
    
    def alertar(self, datos: dict) -> None:
        """
        Revisa si se tiene que generar alguna alerta. Condiciones: 
        - Tiempo de espera total mayor al tiempo de espera máximo permitido.
        - Tiempo de espera de una zona mayor al tiempo de espera máximo permitido.
        
        Args:
            datos (dict): Datos de la simulación.
        """
        
        if datos["tiempo_espera_total"] > configuracion["reporte"]["tiempo_total_espera_maximo"]:
            print(f"\n+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++\n+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++\nAlerta {datos['steps']}: El tiempo de espera total es mayor al tiempo de espera máximo permitido.\n+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++\n+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
        
        if max(datos["tiempos_espera"]) > configuracion["reporte"]["tiempo_zona_espera_maximo"]:
            print(f"\n+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++\n+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++\nAlerta {datos['steps']}: El tiempo de espera de una zona es mayor al tiempo de espera máximo permitido.\n+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++\n+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
