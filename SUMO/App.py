import os
import time
from typing import Any
import traci

from SUMO.zonas.ZonaList import ZonaList
# import traci.step


class App:
    _instance = None

    def __new__(cls):
        if not cls._instance:
            cls._instance = super().__new__(cls)
            #! Iniciar la simulación de SUMO
            traci.start(["sumo-gui", "-c", "SUMO/MapaDe0/mapa.sumocfg"])
        return cls._instance
    
    
    def __init__(self):
        self.zonas = ZonaList()
    
    
    def iniciar(self) -> None:
        print("Iniciando...")
        try: 
            #! Para que haya un mínimo de vehículos en la simulación.
            while traci.simulation.getMinExpectedNumber() > 0 and traci.simulation.getTime() < 250:
                traci.simulationStep()
            
        except traci.exceptions.FatalTraCIError as e:
            print(f"Error en la simulación de SUMO: '{e}'")
            os._exit(0)
    
    
    def setVehiculo(self) -> None:
        """
        Obtener la cantidad de vehículos en una calle
        """
        for zona in self.zonas.zonas:
            zona.cantidad_detecciones = traci.edge.getLastStepVehicleNumber(zona.id)
    
    
    def cambiarEstado(self, semaforo: str, estado: str) -> None:
        """
        Cambiar el color del semáforo (ejemplo: ponerlo en verde)
        """
        traci.trafficlight.setRedYellowGreenState(semaforo, estado)
    
    
    def getSemaforoEstado(self, semaforo: str) -> str:
        """
        Obtener el estado actual del semáforo
        """
        return traci.trafficlight.getRedYellowGreenState(semaforo)    
    
    
    def getSemaforosEstados(self) -> list:
        """
        Obtener el estado actual de todos los semáforos.
        """
        return [traci.trafficlight.getRedYellowGreenState(semaforo) for semaforo in ["1", "2", "3", "4"]]
    
    
    def getTiempoEspera(self, zona_id:str) -> tuple|Any:
        """
        Obtener el tiempo de espera en una zona.
        """
        #edge.getLastStepVehicleIDs (self, edgeID) -> list(str). Devuelve los identificadores de los vehículos durante el último paso en el borde dado.
        #vehicle.getWaitingTime (self, ID de borde) -> double. Devuelve la suma del tiempo de espera de todos los vehículos actualmente en ese borde (consulte traci.vehicle.getWaitingTime).
        #vehicle.getLastStepHaltingNumber (self, ID de borde) -> int. Devuelve el número total de vehículos detenidos durante el último paso de tiempo en el borde dado. Se considera parada una velocidad inferior a 0,1 m/s.
        
        # t =  traci.vehicle.getWaitingTime()
        # t = traci.edge.getLastStepVehicleIDs()
        
        return  traci.edge.getWaitingTime(zona_id)
    
    
    def getTiemposEspera(self) -> tuple|Any:
        """
        Obtener el tiempo de espera en todas las zonas.
        """
        
        while traci.simulation.getTime() < 250:
            traci.simulationStep()
        
        return (sum(traci.edge.getWaitingTime(zona.id) for zona in self.zonas.zonas))
    
    
    def avanzar(self, steps:int) -> bool:
        """
        Avanzar la cantidad de steps especificada.
        """
        print(f"Avanzar simulación... {steps} steps")
        for _ in range(steps):
            if self.puedoSeguir():
                traci.simulationStep()
                done = False
            else:
                print("Done TRUE")
                done = True
                self.reiniciar()
                break
        
        return done
    
    
    def reiniciar(self) -> None:
        """
        Reiniciar la simulación.
        """
        print("Cerrando...")
        traci.close()
        print("Reiniciando...")
        traci.start(["sumo-gui", "-c", "SUMO/MapaDe0/mapa.sumocfg"])
        self.iniciar()
    
    
    def puedoSeguir(self) -> bool:
        """
        Verificar si la simulación puede seguir. Para eso hay que saber:
        - Si está por debajo del tiempo/steps 19500.
        - Si hay vehículos en la simulación.
        """
        return traci.simulation.getTime() <= 19500 and traci.simulation.getMinExpectedNumber() > 0
    
    
    def finalizar(self) -> None:
        """
        Finalizar la simulación.
        """
        traci.close()