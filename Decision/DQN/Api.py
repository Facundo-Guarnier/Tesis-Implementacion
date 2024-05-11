import requests # type: ignore

class ApiDecision:
    def __init__(self, base_url):
        self.base_url = base_url
    
    def getCantidades(self) -> dict[str, int]|None:
        """
        Obtener la cantidad de vehículos en cada una de las zonas.
        
        Returns:
            dict[str, int]: {zona_nombre: cantidad_detecciones}
        """
        endpoint = '/cantidad'
        response = requests.get(self.base_url + endpoint)
        if response.status_code == 200:
            return response.json()
        
        else:
            return None
    
    
    def getCantidadZona(self, zona_name: str) -> dict|None:
        """
        Obtener la cantidad de vehículos en una zona específica.
        """
        endpoint = f'/cantidad/{zona_name}'
        response = requests.get(self.base_url + endpoint)
        if response.status_code == 200:
            return response.json()
        else:
            return None
    
    
    def getEstados(self) -> dict|None:
        """
        Obtener el estado de todos los semáforos.
        
        Returns:
            dict: {"estado": list[str]} 
                list[str]: [estado_semaforo_1, estado_semaforo_2, ...]
        """
        endpoint = '/semaforo'
        response = requests.get(self.base_url + endpoint)
        if response.status_code == 200:
            return response.json()
        else:
            return None
    
    
    def getEstado(self, id:int) -> dict|None:
        """
        Obtener el estado de un semáforo.
        """
        endpoint = f'/semaforo/{id}'
        response = requests.get(self.base_url + endpoint)
        if response.status_code == 200:
            return response.json()
        else:
            return None
    
    
    def getTiempoEspera(self, zona_id) -> dict|None:
        """
        Obtener el tiempo total de espera de una zona en la simulación.
        """
        endpoint = f'/espera/{zona_id}'
        response = requests.get(self.base_url + endpoint)
        if response.status_code == 200:
            return response.json()
        else:
            return None
    
    
    def getTiemposEspera(self) -> dict|None:
        """
        Obtener el tiempo total de espera de todas las zonas en la simulación.
        
        Returns:
            dict: {"tiempo_espera_total": int, "tiempos_espera": list[float]}
        """
        endpoint = '/espera'
        response = requests.get(self.base_url + endpoint)
        if response.status_code == 200:
            return response.json()
        else:
            return None 
    
    
    def putAvanzar(self, steps:int) -> dict|None:
        """
        Avanzar la simulación un número de pasos.
        """
        
        endpoint = f'/avanzar'
        response = requests.put(self.base_url + endpoint,  params={'steps': steps})
        if response.status_code == 200:
            return response.json()
        else:
            return None
    
    
    def putEstados(self, accion:list) -> dict|None:
        """
        Cambiar el estado de un semáforo.
        """
        endpoint = f'/semaforo'
        
        data = []
        for semaforo_id in range(len(accion)):
            data.append(
                {
                    "id": str(semaforo_id+1), 
                    "estado": accion[semaforo_id]
                }
            )
        
        response = requests.put(self.base_url + endpoint, json={"data": data})
        
        if response.status_code == 200:
            return response.json()
        else:
            return None
    
    
    def getSimulacionOK(self) -> bool:
        """
        Verificar si la simulación está en ejecución.
        """
        endpoint = '/simulacion'
        response = requests.get(self.base_url + endpoint)
        if response.status_code == 200:
            return response.json()["simulacion"]
        else:
            return False