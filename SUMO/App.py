import traci

from SUMO.zonas.ZonaList import ZonaList


class App:
    _instance = None

    def __new__(cls):
        if not cls._instance:
            cls._instance = super().__new__(cls)
            #! Iniciar la simulación de SUMO
            traci.start(["sumo-gui", "-c", "SUMO/Mapa/osm.sumocfg"])
        return cls._instance


    def __init__(self):
        self.zonas = ZonaList()
    
    def getVehiculos(self, zona_name: str) -> int:
        """
        Obtener la cantidad de vehículos en una calle
        """
        #! Buscar zona por su nombre
        zona = next((zona for zona in self.zonas.zonas if zona.nombre == zona_name), self.zonas.get()[0])
        
        return traci.edge.getLastStepVehicleNumber(zona.id)


    def cambiarEstado(self, semaforo: str, estado: str) -> None:
        """
        Cambiar el color del semáforo (ejemplo: ponerlo en verde)
        """
        traci.trafficlight.setRedYellowGreenState(semaforo, estado)


    def getEstado(self, semaforo: str) -> str:
        """
        Obtener el estado actual del semáforo
        """
        return traci.trafficlight.getRedYellowGreenState(semaforo)    
    
    
    def iniciar_simulacion(self) -> None:
        while traci.simulation.getMinExpectedNumber() > 0:
            print(f"\nPaso simulación: {traci.simulation.getTime()}")
            
            #! Establecer la cantidad detectada en cada zona.
            for zona in self.zonas.zonas:
                zona.cantidad_detecciones = self.getVehiculos(zona.nombre)
            
            
            #! Avanzar la simulación un paso
            traci.simulationStep()
    
        #! Detener la simulación de SUMO al finalizar
        traci.close()